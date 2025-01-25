import pandas as pd
from typing import List, Dict, Set, Tuple
from config.logging_config import get_logger

logger = get_logger(__name__)

def _get_rankings(
    df: pd.DataFrame,
    quarters: List[str],
    line_ids: Set[str]
) -> Dict[str, Dict[str, int]]:
    """
    Calculate previous quarter rankings for each line of business.

    Args:
        df: DataFrame containing the ranking data
        quarters: List of quarters sorted chronologically
        line_ids: Set of unique line IDs to process

    Returns:
        Dictionary mapping line IDs to their insurer rankings
    """
    if len(quarters) < 2:
        return {}

    prev_quarter = quarters[-2]
    prev_df = df[df['year_quarter'] == prev_quarter]

    rankings = {}
    for line_id in line_ids:
        line_df = prev_df[prev_df['linemain'] == line_id]
        if line_df.empty:
            continue

        sorted_df = line_df.sort_values('value', ascending=False).reset_index(drop=True)
        rankings[line_id] = {
            str(row['insurer']): idx + 1 
            for idx, row in sorted_df.iterrows()
        }

    return rankings

def _process_line_data(
    df: pd.DataFrame,
    line_id: str,
    top_n_list: List[int],
    num_insurers: int,
    excluded_insurers: Set[str],
    selected_insurers: List[str]
) -> List[pd.DataFrame]:
    """
    Process data for a single line of business.

    Args:
        df: DataFrame containing all insurance data
        line_id: ID of the line of business to process
        top_n_list: List of N values for top-N calculations
        num_insurers: Number of top insurers to include
        excluded_insurers: Set of insurer names to exclude
        selected_insurers: selected_insurers

    Returns:
        List of processed DataFrames for this line
    """
    
    logger.debug(f"unique_insurerss {df['insurer'].unique()}")
    
    line_df = df[df['linemain'] == line_id]
    line_dfs = []

    # Get top insurers for this line
    latest_quarter = df['year_quarter'].max()
    latest_line_df = line_df[
        (line_df['year_quarter'] == latest_quarter) & 
        (~line_df['insurer'].isin(excluded_insurers))
    ]

    if selected_insurers == 'total':
        top_insurers = (
            latest_line_df.groupby('insurer', observed=True)['value']
            .sum()
            .nlargest(num_insurers)
            .index
            .tolist()
        )

        # Filter to include only top insurers and excluded insurers
        line_df_top_insurers = line_df[
            line_df['insurer'].isin(top_insurers + list(excluded_insurers))
        ]
        line_dfs.append(line_df_top_insurers)

    else:
        selected_insurers = [selected_insurers] if isinstance(selected_insurers, str) else selected_insurers
        line_df_selected_insurers = line_df[
            line_df['insurer'].isin(selected_insurers + list(excluded_insurers))
        ]
        line_dfs.append(line_df_selected_insurers)

    # Calculate top-N aggregations
    group_cols = [col for col in line_df.columns if col not in ['insurer', 'value']]

    for n in top_n_list:
        top_n_df = (
            line_df[~line_df['insurer'].isin(excluded_insurers)]
            .groupby(group_cols)
            .apply(lambda x: x.nlargest(n, 'value'))
            .reset_index(drop=True)
            .groupby(group_cols, observed=True)['value']
            .sum()
            .reset_index()
        )
        top_n_df['insurer'] = f'top-{n}'
        line_dfs.append(top_n_df)



    ''' # Add filtered original data
    original_df = line_df[~line_df['insurer'].str.startswith('top-')]
    line_dfs.append(original_df)'''

    return line_dfs

def process_insurers_data(
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_n_list: List[int],
    show_data_table: bool,
    selected_metrics: List[str],
    number_of_insurers: int = 10
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]], int]:
    """
    Process insurance data to calculate rankings and generate summary statistics.

    @API_STABILITY: BACKWARDS_COMPATIBLE

    Args:
        df: DataFrame containing insurance data
        selected_insurers: List of insurers to include
        top_n_list: List of N values for top-N calculations
        show_data_table: Whether to show the data table
        selected_metrics: List of metrics to consider
        number_of_insurers: Maximum number of insurers to include

    Returns:
        Tuple containing:
        - Processed DataFrame
        - Dictionary of previous rankings
        - Number of insurers processed
    """
    if df.empty:
        return pd.DataFrame(), {}, 0

    # Calculate number of insurers to process
    latest_quarter = df['year_quarter'].max()
    unique_insurers = df[df['year_quarter'] == latest_quarter]['insurer'].unique()
    num_insurers = min(number_of_insurers, len(unique_insurers))

    if len(df['insurer'].unique()) <= 1:
        return df, {}, num_insurers

    # Set up excluded insurers and ranking metric
    excluded_insurers = {f'top-{n}' for n in top_n_list} | {'total'}
    ranking_metric = next(
        (m for m in selected_metrics if m in df['metric'].unique()),
        df['metric'].iloc[0]
    )

    # Get rankings DataFrame
    ranking_df = df[
        (~df['insurer'].isin(excluded_insurers)) &
        (df['metric'] == ranking_metric)
    ]

    # Calculate previous rankings
    quarters = sorted(ranking_df['year_quarter'].unique())
    line_ids = df['linemain'].unique()
    prev_ranks = _get_rankings(ranking_df, quarters, line_ids)

    # Process each line of business
    processed_dfs = []
    for line_id in line_ids:
        line_dfs = _process_line_data(
            df, line_id, top_n_list, num_insurers,
            excluded_insurers, selected_insurers
        )
        processed_dfs.extend(line_dfs)

    result_df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else df

    return result_df, prev_ranks, num_insurers