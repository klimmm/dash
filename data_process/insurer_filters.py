import pandas as pd
from typing import List
from config.logging_config import get_logger

logger = get_logger(__name__)


def filter_by_insurer(
    df: pd.DataFrame,
    selected_metrics: List[str],
    selected_insurers: List[str] = None,
    top_n_list: List[int] = [5, 10, 20],
    number_of_insurers: int = 20
) -> pd.DataFrame:
    """
    Process insurers data and calculate rankings.
    Includes both top-X insurers and specifically selected insurers.
    Only includes insurer data for lines where they are in the top N.
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    if df.empty or len(df['insurer'].unique()) <= 1:
        return pd.DataFrame()

    # Determine number of insurers to process
    number_of_insurers = next(
        (n for n in [5, 10, 20] if f'top-{n}' in (selected_insurers or [])),
        number_of_insurers
    )

    latest_quarter = df['year_quarter'].max()
    excluded_insurers = {f'top-{n}' for n in [5, 10, 20]} | {'total'}

    # Get ranking metric
    ranking_metric = next(
        (m for m in selected_metrics if m in df['metric'].unique()),
        df['metric'].iloc[0]
    )

    # Extract specifically selected insurers (non top-X)
    specific_insurers = [ins for ins in (selected_insurers or []) 
                        if not ins.startswith('top-') and ins not in excluded_insurers]

    line_ids = df['linemain'].unique()
    processed_dfs = []
    top_insurers_by_line = {}  # Store top insurers for each line

    # First pass: Identify top insurers for each line
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

        if any(insurer.startswith('top-') for insurer in (selected_insurers or [])):
            top_insurers = (
                latest_line_df.groupby('insurer', observed=True)['value']
                .sum()
                .nlargest(number_of_insurers)
                .index
                .tolist()
            )
            top_insurers_by_line[line_id] = set(top_insurers)

    # Second pass: Filter data to only include insurers where they are top-ranked
    for line_id in line_ids:
        line_df = df[df['linemain'] == line_id]
        if line_df.empty:
            continue

        # Get relevant insurers for this line
        line_top_insurers = top_insurers_by_line.get(line_id, set())
        filtered_insurers = list(set(list(line_top_insurers) + specific_insurers))

        if filtered_insurers:
            filtered_df = line_df[
                line_df['insurer'].isin(
                    filtered_insurers + list(excluded_insurers)
                )
            ]
            processed_dfs.append(filtered_df)

    # Combine all processed data
    result_df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else df

    # Apply final filters
    if 999 not in top_n_list:
        result_df = result_df[~(result_df['insurer'] == 'total')]

    numbers_to_filter = [n for n in [5, 10, 20] if n not in top_n_list]
    if numbers_to_filter:
        result_df = result_df[~result_df['insurer'].str.match('|'.join(f'top-{n}' for n in numbers_to_filter))]

    return result_df