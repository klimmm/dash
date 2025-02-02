import time
from typing import List

from functools import wraps
import pandas as pd

from config.logging_config import get_logger


logger = get_logger(__name__)


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


@timer
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
    excluded_insurers = ['top-5', 'top-10', 'top-20', 'total']

    logger.debug(f" excluded_insurers {excluded_insurers}")
    # Get ranking metric
    ranking_metric = next(
        (m for m in selected_metrics if m in df['metric'].unique()),
        df['metric'].iloc[0]
    )

    # Extract specifically selected insurers (non top-X)
    specific_insurers = [ins for ins in (selected_insurers or []) 
                        if not ins.startswith('top-') and ins not in excluded_insurers]

    logger.debug(f" specific_insurers {specific_insurers}")
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
                    filtered_insurers + excluded_insurers
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
            logger.debug(f" line_id {line_id}")
            logger.debug(f" filtered_insurers {filtered_insurers}")
            if filtered_insurers:
                filtered_df = line_df[
                    line_df['insurer'].isin(
                        filtered_insurers + excluded_insurers
                    )
                ]
                all_insurers = list(set(list(line_top_insurers) + specific_insurers + excluded_insurers))
                all_lines = [line_id]
                all_metrics = filtered_df['metric'].unique()
                all_quarters = filtered_df['year_quarter'].unique()
                multi_index = pd.MultiIndex.from_product(
                    [all_insurers, all_lines, all_metrics, all_quarters],
                    names=['insurer', 'linemain', 'metric', 'year_quarter']
                )
                valid_combos = set(map(tuple, filtered_df[['metric', 'year_quarter']].values))
                valid_idx = [idx for idx in multi_index if (idx[2], idx[3]) in valid_combos]
                multi_index = pd.MultiIndex.from_tuples(valid_idx, names=multi_index.names)
                result_df_indexed = filtered_df.set_index(
                    ['insurer', 'linemain', 'metric', 'year_quarter']
                )
                complete_df = result_df_indexed.reindex(multi_index)
                result_df = complete_df.reset_index()
                processed_dfs.append(result_df)

    # Combine all processed data
    df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else df

    if split_mode == 'insurer':
        # Get all unique combinations needed
        all_insurers = df['insurer'].unique()
        all_lines = line_ids
        all_metrics = df['metric'].unique()
        all_quarters = df['year_quarter'].unique()

        # Create a complete index of all possible combinations
        multi_index = pd.MultiIndex.from_product(
            [all_insurers, all_lines, all_metrics, all_quarters],
            names=['insurer', 'linemain', 'metric', 'year_quarter']
        )

        # Get valid metric-quarter combinations
        valid_combos = set(map(tuple, df[['metric', 'year_quarter']].values))

        # Filter multi_index to keep only valid metric-quarter combinations
        valid_idx = [idx for idx in multi_index if (idx[2], idx[3]) in valid_combos]
        multi_index = pd.MultiIndex.from_tuples(valid_idx, names=multi_index.names)

        # Rest of the code
        result_df_indexed = df.set_index(
            ['insurer', 'linemain', 'metric', 'year_quarter']
        )
        complete_df = result_df_indexed.reindex(multi_index)
        df = complete_df.reset_index()


    # Apply final filters
    if 999 not in top_n_list:
        df = df[~(df['insurer'] == 'total')]

    numbers_to_filter = [n for n in [5, 10, 20] if n not in top_n_list]
    if numbers_to_filter:
        df = df[~df['insurer'].str.match('|'.join(f'top-{n}' for n in numbers_to_filter))]

    metric_to_use = next(m for m in selected_metrics if m in df['metric'].unique())
    latest_data = latest_df.groupby('insurer')['value'].sum().reset_index().sort_values('value', ascending=False)

    # Get sorted insurers from filtered data
    all_insurers_sorted = latest_data['insurer'].unique().tolist()
    logger.debug(f" all_insurers_sorted {all_insurers_sorted}")

    # Add the special categories at the end for insurers
    full_insurer_categories = all_insurers_sorted + excluded_insurers

    # Get all unique metrics from the dataframe
    all_metrics = df['metric'].unique().tolist()

    # Create ordered list of metrics:
    # First, include metrics from selected_metrics that exist in the data
    # Then, add remaining metrics that weren't in selected_metrics
    ordered_metrics = [m for m in selected_metrics if m in all_metrics]
    remaining_metrics = [m for m in all_metrics if m not in selected_metrics]
    full_metric_categories = ordered_metrics + remaining_metrics

    # Create and apply categorical dtypes for both insurers and metrics
    insurer_cat = pd.CategoricalDtype(categories=full_insurer_categories, ordered=True)
    metric_cat = pd.CategoricalDtype(categories=full_metric_categories, ordered=True)

    # Convert both columns to categorical
    df['insurer'] = df['insurer'].astype(insurer_cat)
    df['metric'] = df['metric'].astype(metric_cat)

    # Sort by both categorical columns
    df = df.sort_values(['metric', 'insurer'])

    # Convert back to string type after sorting
    df['insurer'] = df['insurer'].astype(str)
    df['metric'] = df['metric'].astype(str)

    return df