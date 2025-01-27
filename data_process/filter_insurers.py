import pandas as pd
from typing import List, Dict, Set, Tuple
from config.logging_config import get_logger, monitor_memory, memory_monitor
from data_process.data_utils import save_df_to_csv

logger = get_logger(__name__)

def get_rankings(
    df: pd.DataFrame,
    quarters: List[str],
    line_ids: Set[str],
    quarter_offset: int = -2
) -> Dict[str, Dict[str, int]]:
    """
    Calculate rankings for each line of business for a specific quarter offset.
    
    Args:
        df: DataFrame containing the ranking data
        quarters: List of quarters sorted chronologically
        line_ids: Set of unique line IDs to process
        quarter_offset: Offset from the last quarter (-1 for current, -2 for previous)
    
    Returns:
        Dictionary mapping line IDs to their insurer rankings
    """
    if len(quarters) < abs(quarter_offset):
        return {}

    target_quarter = quarters[quarter_offset]
    quarter_df = df[df['year_quarter'] == target_quarter]

    rankings = {}
    for line_id in line_ids:
        line_df = quarter_df[quarter_df['linemain'] == line_id]
        save_df_to_csv(line_df, f" {line_id}_{target_quarter}_line_df.csv")
        logger.debug(f"target_quarter {target_quarter}")
        logger.debug(f"line_df {line_df['insurer'].unique()}")
        
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
    selected_insurers: List[str],
    ranking_metric: str
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
        (~line_df['insurer'].isin(excluded_insurers) &
        (line_df['metric'] == ranking_metric)
        )
    ]
    logger.warning(f"excluded_insurers {excluded_insurers}")
    logger.warning(f"selected_insurers {selected_insurers}")
    logger.warning(f"num_insurers {num_insurers}")
    logger.warning(f"selected_insurers inexcluded_insurers  {any(insurer in excluded_insurers for insurer in selected_insurers)}")

    if any(insurer.startswith('top-') for insurer in selected_insurers):
        top_insurers = (
            latest_line_df.groupby('insurer', observed=True)['value']
            .sum()
            .nlargest(num_insurers)
            .index
            .tolist()
        )

        # Filter to include only top insurers and excluded insurers
        line_df_top_insurers = line_df[
            line_df['insurer'].isin(top_insurers + list(excluded_insurers) + selected_insurers)
        ]
        line_dfs.append(line_df_top_insurers)

    else:
        selected_insurers = [selected_insurers] if isinstance(selected_insurers, str) else selected_insurers
        line_df_selected_insurers = line_df[
            line_df['insurer'].isin(selected_insurers + list(excluded_insurers))
        ]
        line_dfs.append(line_df_selected_insurers)

    # Calculate top-N aggregations
    ''' group_cols = [col for col in line_df.columns if col not in ['insurer', 'value']]

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

    # Add filtered original data
    original_df = line_df[~line_df['insurer'].str.startswith('top-')]
    line_dfs.append(original_df)'''

    return line_dfs

def process_insurers_data(
    df: pd.DataFrame,
    selected_metrics: List[str],
    selected_insurers: List[str] = None,
    top_n_list: List[int] = [5, 10, 20],
    show_data_table: bool = True,
    number_of_insurers: int = 20
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
    


    
    if 'top-5' in selected_insurers:
        number_of_insurers = 5
    elif 'top-10' in selected_insurers:
        number_of_insurers = 10
    elif 'top-20' in selected_insurers:
        number_of_insurers = 20
    else:
        number_of_insurers = 20

    logger.warning(f"number_of_insurers {number_of_insurers}")
    if df.empty:
        return pd.DataFrame(), {}, 0
    logger.debug(f"Starting process_insurers_data")
    # memory_monitor.log_memory("before_process_insurers", logger)
    # Calculate number of insurers to process
    latest_quarter = df['year_quarter'].max()
    unique_insurers = df[df['year_quarter'] == latest_quarter]['insurer'].unique()
    num_insurers = min(number_of_insurers, len(unique_insurers))

    if len(df['insurer'].unique()) <= 1:
        return df, {}, num_insurers

    # Set up excluded insurers and ranking metric
    excluded_insurers = {f'top-{n}' for n in top_n_list} | {'total'}
    
    logger.debug(f"selected_metrics {selected_metrics}")
    
    ranking_metric = next(
        (m for m in selected_metrics if m in df['metric'].unique()),
        df['metric'].iloc[0]
    )
    logger.debug(f"ranking_metric {ranking_metric}")
    logger.debug(f"metric_unique {df['metric'].unique()}")
    # Get rankings DataFrame
    ranking_df = df[
        (~df['insurer'].isin(excluded_insurers)) &
        (df['metric'] == ranking_metric)
    ]
    logger.debug(f"ranking_df lines {ranking_df['linemain'].unique()}")

    # Calculate previous rankings
    quarters = sorted(ranking_df['year_quarter'].unique())
    line_ids = df['linemain'].unique()

    current_ranks = get_rankings(ranking_df, quarters, line_ids, quarter_offset=-1)
    prev_ranks = get_rankings(ranking_df, quarters, line_ids, quarter_offset=-2)
 
    logger.debug(f"current_ranks{current_ranks}")
    logger.debug(f"prev_ranks{prev_ranks}")
    # Process each line of business
    processed_dfs = []
    for line_id in line_ids:
        line_dfs = _process_line_data(
            df, line_id, top_n_list, num_insurers,
            excluded_insurers, selected_insurers, ranking_metric
        )
        processed_dfs.extend(line_dfs)

    result_df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else df
    # memory_monitor.log_memory("after_process_insurers", logger)
    logger.debug(f"Finished process_insurers_data")
    logger.warning(f"insurer unique {df['insurer'].unique()}")
    return result_df, prev_ranks, current_ranks, num_insurers