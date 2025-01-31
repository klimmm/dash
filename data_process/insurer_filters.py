from typing import List

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


def filter_by_insurer(
    df: pd.DataFrame,
    selected_metrics: List[str],
    selected_insurers: List[str] = None,
    top_n_list: List[int] = [5, 10, 20],
    split_mode: str = 'line'
) -> pd.DataFrame:
    """

    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    if df.empty or len(df['insurer'].unique()) <= 1:
        return pd.DataFrame()
    logger.debug(f" selected_insurers {selected_insurers}")

    if any(insurer.startswith('top-') for insurer in selected_insurers):

        number_of_insurers = next(
            (n for n in [5, 10, 20] if f'top-{n}' in (selected_insurers or []))
        )
    else:
        number_of_insurers = 0

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

    # Latest data for ranking calculations
    latest_df = df[
        (df['year_quarter'] == latest_quarter) & 
        (~df['insurer'].isin(excluded_insurers)) &
        (df['metric'] == ranking_metric)
    ]

    if split_mode == 'insurer':
        # Aggregate values across all lines for each insurer
        total_values = (
            latest_df.groupby('insurer', observed=True)['value']
            .sum()
            .nlargest(number_of_insurers)
            .index
            .tolist()
        )

        # Filter the original dataframe to include only top insurers and specific insurers
        filtered_insurers = list(set(total_values + specific_insurers))
        if filtered_insurers:
            filtered_df = df[
                df['insurer'].isin(
                    filtered_insurers + list(excluded_insurers)
                )
            ]
            processed_dfs.append(filtered_df)

    else:  # split_mode == 'line'
        top_insurers_by_line = {}
        # First pass: Identify top insurers for each line
        for line_id in line_ids:
            line_df = latest_df[latest_df['linemain'] == line_id]
            if line_df.empty:
                continue

            if any(insurer.startswith('top-') for insurer in (selected_insurers or [])):
                top_insurers = (
                    line_df.groupby('insurer', observed=True)['value']
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

    if split_mode == 'insurer':
        # Get all unique combinations needed
        all_insurers = result_df['insurer'].unique()
        all_lines = line_ids
        all_metrics = result_df['metric'].unique()
        all_quarters = result_df['year_quarter'].unique()

        # Create a complete index of all possible combinations
        multi_index = pd.MultiIndex.from_product(
            [all_insurers, all_lines, all_metrics, all_quarters],
            names=['insurer', 'linemain', 'metric', 'year_quarter']
        )

        # Get valid metric-quarter combinations
        valid_combos = set(map(tuple, result_df[['metric', 'year_quarter']].values))

        # Filter multi_index to keep only valid metric-quarter combinations
        valid_idx = [idx for idx in multi_index if (idx[2], idx[3]) in valid_combos]
        multi_index = pd.MultiIndex.from_tuples(valid_idx, names=multi_index.names)

        # Rest of the code
        result_df_indexed = result_df.set_index(
            ['insurer', 'linemain', 'metric', 'year_quarter']
        )
        complete_df = result_df_indexed.reindex(multi_index)
        result_df = complete_df.reset_index()


    # Apply final filters
    if 999 not in top_n_list:
        result_df = result_df[~(result_df['insurer'] == 'total')]

    numbers_to_filter = [n for n in [5, 10, 20] if n not in top_n_list]
    if numbers_to_filter:
        result_df = result_df[~result_df['insurer'].str.match('|'.join(f'top-{n}' for n in numbers_to_filter))]

    return result_df