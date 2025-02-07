from functools import lru_cache
import pandas as pd

from typing import List, Dict, Tuple

from config.logging_config import get_logger, timer
from domain.insurers.mapper import map_insurer

logger = get_logger(__name__)

EXCLUDED_INSURERS = frozenset(['top-5', 'top-10', 'top-20', 'total'])


@lru_cache(maxsize=1024)
def cached_map_insurer(insurer: str) -> str:
    """Cached mapping of insurer names."""
    return map_insurer(insurer)


def get_filtered_df(df: pd.DataFrame, metric: str = None) -> pd.DataFrame:
    """Filter DataFrame by metric and excluded insurers."""
    return df[
        ~df['insurer'].isin(EXCLUDED_INSURERS) & 
        (df['metric'] == (metric or df['metric'].iloc[0]))
    ]


def get_rankings(df: pd.DataFrame, quarter: str) -> Dict[str, Dict[str, int]]:
    """Calculate rankings for each line in a given quarter."""
    quarter_df = df[df['year_quarter'] == quarter]
    return {
        line: dict(zip(
            line_df.sort_values('value', ascending=False)['insurer'].astype(str),
            range(1, len(line_df) + 1)
        ))
        for line, line_df in quarter_df.groupby('linemain')
        if not line_df.empty
    }


def get_insurer_order(df: pd.DataFrame, top_n: int = 0) -> List[str]:
    """Get ordered list of insurers based on value sums."""
    value_sums = df.groupby('insurer')['value'].sum()
    ordered_insurers = (
        value_sums.nlargest(top_n).index.tolist() if top_n > 0
        else value_sums.sort_values(ascending=False).index.tolist()
    )

    # Filter and extend with markers
    ordered_insurers = [
        ins for ins in ordered_insurers if ins not in EXCLUDED_INSURERS]
    if top_n == 0:
        ordered_insurers.extend(x for x in EXCLUDED_INSURERS if x != 'total')
    elif f'top-{top_n}' in EXCLUDED_INSURERS:
        ordered_insurers.append(f'top-{top_n}')

    if 'total' not in ordered_insurers:
        ordered_insurers.append('total')

    return ordered_insurers


def sort_df(df: pd.DataFrame, metrics: List[str], insurer_order: List[str]
            ) -> pd.DataFrame:
    """Sort DataFrame by metrics and insurers."""
    metric_order = [m for m in metrics if m in df['metric'].unique()]
    metric_order.extend(m for m in df['metric'].unique() if m not in metric_order)
    df['insurer'] = pd.Categorical(
        df['insurer'], categories=insurer_order, ordered=True)
    df['metric'] = pd.Categorical(
        df['metric'], categories=metric_order, ordered=True)
    return df.sort_values(['metric', 'insurer'])


def reindex_df(df: pd.DataFrame, valid_combinations: pd.DataFrame = None,
               use_all_combinations: bool = False) -> pd.DataFrame:
    """Reindex DataFrame with valid combinations.

    Args:
        df: Input DataFrame
        valid_combinations: DataFrame with valid insurer-line combinations
        use_all_combinations: If True, use all possible insurer-line combinations
    """
    # Store original metric-year_quarter combinations
    original_metric_quarter = df[['metric', 'year_quarter']].drop_duplicates()
    
    if use_all_combinations:
        idx_products = pd.MultiIndex.from_product([
            df['insurer'].unique(),
            df['linemain'].unique()
        ], names=['insurer', 'linemain'])
        valid_combinations = pd.DataFrame(index=idx_products).reset_index()
    elif valid_combinations is None:
        valid_combinations = df[['insurer', 'linemain']].drop_duplicates()

    # Create full index using only original metric-year_quarter combinations
    full_idx = pd.MultiIndex.from_frame(
        valid_combinations.merge(
            original_metric_quarter,
            how='cross'
        )
    )

    # Reindex the DataFrame
    result_df = df.set_index(
        ['insurer', 'linemain', 'metric', 'year_quarter']
    ).reindex(full_idx).reset_index()

    return result_df


def aggregate_data(df: pd.DataFrame, latest_df: pd.DataFrame,
                   top_insurers: int = None, split_mode: str = 'line'
                   ) -> pd.DataFrame:
    """Aggregate data based on top insurers and split mode."""
    if split_mode == 'insurer':
        filtered_insurers = get_insurer_order(latest_df, top_insurers)
        filtered_df = df[df['insurer'].isin(filtered_insurers)].copy()
        filtered_df['insurer'] = pd.Categorical(
            filtered_df['insurer'],
            categories=filtered_insurers,
            ordered=True
        )
        # For insurer mode, use all possible insurer-line combinations
        return reindex_df(filtered_df, use_all_combinations=True)

    # Process by line mode
    result_parts = []
    valid_combinations = []

    for line in df['linemain'].unique():
        line_data = latest_df[latest_df['linemain'] == line]
        line_insurers = get_insurer_order(line_data, top_insurers)

        line_df = df[
            (df['linemain'] == line) &
            (df['insurer'].isin(line_insurers))
        ].copy()

        if not line_df.empty:
            line_df['insurer'] = pd.Categorical(
                line_df['insurer'],
                categories=line_insurers,
                ordered=True
            )
            result_parts.append(line_df)
            # Track valid combinations for line mode
            valid_combinations.append(
                line_df[['insurer', 'linemain']].drop_duplicates()
            )

    if not result_parts:
        return pd.DataFrame()

    combined_df = pd.concat(result_parts, ignore_index=True)
    valid_combinations = pd.concat(valid_combinations, ignore_index=True)
    # Only filter line-insurer combinations in line mode
    return reindex_df(combined_df, valid_combinations)


@timer
def get_filtered_df_options_rankings(
    df: pd.DataFrame,
    metrics: List[str],
    lines: List[str],
    selected_insurers: List[str],
    top_insurers: int = None,
    split_mode: str = 'line'
) -> Tuple[pd.DataFrame,
           List[Dict[str, str]], Dict[str, Dict[str, Dict[str, int]]]]:
    """Process and filter insurance data."""
    ranking_metric = next(
        (m for m in metrics if m in df['metric'].unique()), None)
    rank_df = get_filtered_df(df, ranking_metric)
    quarters = sorted(df['year_quarter'].unique())[-2:]
    latest_df = rank_df[rank_df['year_quarter'] == quarters[-1]]

    rankings = {
        'current_ranks': get_rankings(rank_df, quarters[-1]),
        'prev_ranks': get_rankings(rank_df, quarters[-2])
    }

    insurer_order = get_insurer_order(latest_df, 0)

    if top_insurers == 0:
        options = [
            {'label': cached_map_insurer(ins), 'value': ins}
            for ins in insurer_order if ins not in EXCLUDED_INSURERS]
        filtered_df = reindex_df(
            df[df['insurer'].isin((selected_insurers or []) + ['total'])],
            use_all_combinations=True)
    else:
        options = []
        filtered_df = aggregate_data(df, latest_df, top_insurers, split_mode)

    return sort_df(filtered_df, metrics, insurer_order), options, rankings


__all__ = ['get_filtered_df_options_rankings']