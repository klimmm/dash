import pandas as pd
from typing import List, Dict, Tuple
from config.logging_config import get_logger

logger = get_logger(__name__)


def process_insurers_data(
    df: pd.DataFrame,
    selected_metrics: List[str],
    selected_insurers: List[str] = None,
    top_n_list: List[int] = [5, 10, 20],
    number_of_insurers: int = 20
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]], int]:
    """
    Process insurers data and calculate rankings.
    Includes both top-X insurers and specifically selected insurers.
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    if df.empty or len(df['insurer'].unique()) <= 1:
        return pd.DataFrame(), {}, 0

    # Determine number of insurers to process
    number_of_insurers = next(
        (n for n in [5, 10, 20] if f'top-{n}' in (selected_insurers or [])),
        number_of_insurers
    )

    latest_quarter = df['year_quarter'].max()
    num_insurers = min(
        number_of_insurers,
        len(df[df['year_quarter'] == latest_quarter]['insurer'].unique())
    )

    # Set up excluded insurers and ranking metric
    excluded_insurers = {f'top-{n}' for n in top_n_list} | {'total'}
    ranking_metric = next(
        (m for m in selected_metrics if m in df['metric'].unique()),
        df['metric'].iloc[0]
    )

    # Extract specifically selected insurers (non top-X)
    specific_insurers = [ins for ins in (selected_insurers or []) 
                        if not ins.startswith('top-') and ins not in excluded_insurers]

    line_ids = df['linemain'].unique()
    processed_dfs = []

    for line_id in line_ids:
        line_df = df[df['linemain'] == line_id]
        if line_df.empty:
            continue

        # Get top insurers for this line
        latest_line_df = line_df[
            (line_df['year_quarter'] == latest_quarter) & 
            (~line_df['insurer'].isin(excluded_insurers)) &
            (line_df['metric'] == ranking_metric)
        ]

        top_insurers = []
        if any(insurer.startswith('top-') for insurer in (selected_insurers or [])):
            top_insurers = (
                latest_line_df.groupby('insurer', observed=True)['value']
                .sum()
                .nlargest(num_insurers)
                .index
                .tolist()
            )

        # Combine top insurers and specifically selected insurers
        filtered_insurers = list(set(top_insurers + specific_insurers))

        if filtered_insurers:
            filtered_df = line_df[
                line_df['insurer'].isin(
                    filtered_insurers + list(excluded_insurers)
                )
            ]
            processed_dfs.append(filtered_df)

    df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else df

    if 999 not in top_n_list:
        df = df[~(df['insurer'] == 'total')]

    df = df[~df['insurer'].str.match('|'.join(f'top-{n}' for n in [5, 10, 20] if n not in top_n_list))]

    return df