from functools import lru_cache
from typing import cast, Dict, List, Optional

import pandas as pd

from config.logging import timer, get_logger
from core.insurers.mapper import map_insurer

logger = get_logger(__name__)


EXCLUDED_INSURERS = frozenset(['top-5', 'top-10', 'top-20', 'total'])


def get_top_insurers(df: pd.DataFrame, top_n: int = 0) -> List[str]:
    """Get ordered list of top insurers based on value sums."""
    value_sums = df.groupby('insurer')['value'].sum()
    ordered = value_sums.nlargest(
        top_n).index.tolist() if top_n > 0 else value_sums.sort_values(
        ascending=False).index.tolist()
    ordered = [ins for ins in ordered if ins not in EXCLUDED_INSURERS]

    if top_n > 0 and f'top-{top_n}' in EXCLUDED_INSURERS:
        ordered.append(f'top-{top_n}')
    elif top_n == 0:
        ordered.extend(x for x in EXCLUDED_INSURERS if x != 'total')

    if 'total' not in ordered:
        ordered.append('total')
    return ordered


@timer
def process_insurers_df(df: pd.DataFrame, latest_df: pd.DataFrame,
                        top_insurers: int, split_mode: str
                        ) -> pd.DataFrame:
    """Process DataFrame based on mode and generate full index."""

    def create_full_index(combinations: pd.DataFrame,
                          metrics_quarters: pd.DataFrame) -> pd.MultiIndex:
        return pd.MultiIndex.from_frame(combinations
                                        .merge(metrics_quarters, how='cross'))

    def get_valid_combinations(data: pd.DataFrame,
                               use_all: bool = False) -> pd.DataFrame:
        if use_all:
            idx = pd.MultiIndex.from_product([
                data['insurer'].unique(), data['linemain'].unique()],
                names=['insurer', 'linemain'])
            return pd.DataFrame(index=idx).reset_index()
        return data[['insurer', 'linemain']].drop_duplicates()

    def reindex_df(data: pd.DataFrame,
                   valid_combos: Optional[pd.DataFrame] = None,
                   use_all: bool = False) -> pd.DataFrame:
        metric_quarters = data[['metric', 'year_quarter']].drop_duplicates()
        combinations = get_valid_combinations(
            data, use_all) if valid_combos is None else valid_combos
        full_idx = create_full_index(combinations, metric_quarters)
        return data.set_index(
            ['insurer', 'linemain', 'metric', 'year_quarter']
        ).reindex(full_idx).reset_index()

    if split_mode == 'insurer':
        filtered_insurers = get_top_insurers(latest_df, top_insurers)
        filtered_df = df[df['insurer'].isin(filtered_insurers)].copy()
        filtered_df['insurer'] = pd.Categorical(filtered_df['insurer'],
                                                categories=filtered_insurers,
                                                ordered=True)

        return reindex_df(filtered_df, use_all=True)

    # For line mode
    result_parts = []
    for line in df['linemain'].unique():
        line_data = latest_df[latest_df['linemain'] == line]
        line_insurers = get_top_insurers(line_data, top_insurers)

        line_df = df[(df['linemain'] == line) & (
            df['insurer'].isin(line_insurers))].copy()
        if not line_df.empty:
            line_df['insurer'] = pd.Categorical(line_df['insurer'],
                                                categories=line_insurers,
                                                ordered=True)
            result_parts.append(line_df)

    if not result_parts:
        return pd.DataFrame()

    combined_df = pd.concat(result_parts, ignore_index=True)
    # Use all combinations when top_insurers is 0
    use_all = top_insurers == 0

    return reindex_df(combined_df, use_all=use_all)


def get_rankings(df: pd.DataFrame, quarters: List[str]
                 ) -> Dict[str, Dict[str, Dict[str, int]]]:
    """Calculate rankings for current and previous quarters."""
    def calculate_quarter_rankings(quarter_df: pd.DataFrame
                                   ) -> Dict[str, Dict[str, int]]:
        rankings: Dict[str, Dict[str, int]] = {}
        for line, line_df in quarter_df.groupby('linemain'):
            if not line_df.empty:
                # Cast line to str to ensure type safety
                line_str = cast(str, line)
                sorted_insurers = line_df.sort_values(
                    'value', ascending=False)['insurer'].astype(str)
                rankings[line_str] = dict(zip(
                    sorted_insurers,
                    range(1, len(line_df) + 1)
                ))
        return rankings

    latest_df = df[df['year_quarter'] == quarters[-1]]
    prev_df = df[df['year_quarter'] == quarters[-2]] if len(
        quarters) > 1 else pd.DataFrame()

    return {
        'current_ranks': calculate_quarter_rankings(latest_df),
        'prev_ranks': calculate_quarter_rankings(prev_df) if not prev_df
        .empty else {}
    }


@lru_cache(maxsize=1024)
def cached_map_insurer(insurer: str) -> str:
    return map_insurer(insurer)


def get_insurer_options(insurers: List[str]) -> List[Dict[str, str]]:
    """Generate insurer options for UI."""
    return [{'label': cached_map_insurer(ins), 'value': ins}
            for ins in insurers if ins not in EXCLUDED_INSURERS]