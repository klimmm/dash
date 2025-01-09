#data_processing.py

import pandas as pd
import numpy as np
import os
from typing import List, Tuple, Optional, Dict, OrderedDict, Any, Union, Se
import logging
from dataclasses import dataclass
from .data_utils import save_df_to_csv, log_dataframe_info, category_structure, insurer_name_map
from datetime import datetime
import re
from .filter_options import MARKET_METRIC_OPTIONS, METRICS, base_metrics, calculated_metrics, calculated_ratios, REINSURANCE_FIG_TYPES, INSURANCE_FIG_TYPES
from .mapping import map_insurer
from .table_data import create_table_data

import json
import pandas as pd
from collections import OrderedDic
from typing import Lis


# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)

logging.getLogger('fsevents').setLevel(logging.WARNING)
logging.getLogger('watchdog').setLevel(logging.WARNING)
metrics = list(MARKET_METRIC_OPTIONS.keys())


def filter_by_date_range_and_line_type(
    df: pd.DataFrame,
    start_quarter: str,
    end_quarter: str,
    fig_type: str | None = None,
    premium_loss_selection: Optional[List[str]] = None,
    reinsurance_form: Optional[List[str]] = None,
    reinsurance_geography: Optional[List[str]] = None,
    reinsurance_type: Optional[List[str]] = None,
    line_types: Optional[List[str]] = None

) -> pd.DataFrame:

    logger.debug(f"end_quarter: {end_quarter}")
    logger.debug(f"fig_type: {fig_type}")
    logger.debug(f"premium_loss_selection: {premium_loss_selection}")

    # Convert quarters to datetime
    start_date = pd.to_datetime(start_quarter)

    end_date = pd.to_datetime(end_quarter)
    logger.debug(f"end_date: {end_date}")

    df = df[(df['year_quarter'] >= start_date) & (df['year_quarter'] <= end_date)]
    logger.debug(f"columns before: {df.head()}")
    logger.debug(f"unique year quarters:  {df['year_quarter'].unique().tolist()}")


    if fig_type is None:
        mask = pd.Series(True, index=df.index)

        # Filter by line_type if specified
        if line_types is not None and 'line_type' in df.columns:
            mask &= df['line_type'].isin(line_types)

        if premium_loss_selection is not None and 'metric' in df.columns:
            exclude_metrics = []
            if 'direct' not in premium_loss_selection:
                exclude_metrics.extend(['direct_premiums', 'direct_losses'])
            if 'inward' not in premium_loss_selection:
                exclude_metrics.extend(['inward_premiums', 'inward_losses'])
            if exclude_metrics:
                mask &= ~df['metric'].isin(exclude_metrics)

        df = df[mask]
        df = df.drop(columns='line_type', errors='ignore')

    elif fig_type in REINSURANCE_FIG_TYPES:
        mask = pd.Series(True, index=df.index)

        for col, values in [
            ('reinsurance_form', reinsurance_form),
            ('reinsurance_geography', reinsurance_geography),
            ('reinsurance_type', reinsurance_type)
        ]:
            if values is not None and col in df.columns:
                mask &= df[col].isin(values)
        df = df.loc[mask]

        if fig_type == "reinsurance_line":
            df = df.groupby(['year_quarter', 'metric', 'linemain', 'insurer'])['value'].sum().reset_index()

        elif fig_type == "reinsurance_geography":
            df = df.groupby(['year_quarter', 'reinsurance_geography', 'metric', 'linemain', 'insurer'])['value'].sum().reset_index()

        elif fig_type == "reinsurance_form":
            df = df.groupby(['year_quarter', 'reinsurance_form', 'metric', 'linemain', 'insurer'])['value'].sum().reset_index()

        elif fig_type == "reinsurance_type":
            df = df.groupby(['year_quarter', 'reinsurance_type', 'metric', 'linemain', 'insurer'])['value'].sum().reset_index()





    logger.debug(f"columns after: {df.head()}")

    return df



import logging

def filter_required_metrics(df: pd.DataFrame, selected_metrics: List[str]) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.debug(f"Starting to filter metrics. Selected metrics: {selected_metrics}")

    original_columns = df.columns.tolist()

    relevant_metrics = set()
    for selected_metric in selected_metrics:
        logger.debug(f"Processing selected metric: {selected_metric}")

        # Check for exact matches firs
        if selected_metric in base_metrics:
            relevant_metrics.add(selected_metric)
            logger.debug(f"Exact match found in base_metrics: {selected_metric}")
        elif selected_metric in calculated_metrics:
            relevant_metrics.update(calculated_metrics[selected_metric])
            logger.debug(f"Exact match found in calculated_metrics: {selected_metric}. Adding base metrics: {calculated_metrics[selected_metric]}")
        elif selected_metric in calculated_ratios:
            relevant_metrics.update(calculated_ratios[selected_metric])
            logger.debug(f"Exact match found in calculated_ratios: {selected_metric}. Adding base metrics: {calculated_ratios[selected_metric]}")

        # Check for substring matches
        for metric in base_metrics:
            if metric in selected_metric:
                relevant_metrics.add(metric)
                logger.debug(f"Substring match found in base_metrics: {metric} for selected metric: {selected_metric}")

        for calc_metric, base_deps in calculated_metrics.items():
            if calc_metric in selected_metric:
                relevant_metrics.update(base_deps)
                logger.debug(f"Substring match found in calculated_metrics: {calc_metric} for selected metric: {selected_metric}. Adding base metrics: {base_deps}")

        for ratio_metric, base_deps in calculated_ratios.items():
            if ratio_metric in selected_metric:
                relevant_metrics.update(base_deps)
                logger.debug(f"Substring match found in calculated_ratios: {ratio_metric} for selected metric: {selected_metric}. Adding base metrics: {base_deps}")

    logger.debug(f"Relevant metrics after processing: {relevant_metrics}")

    # Filter the DataFrame without copying if possible
    filtered_df = df[df['metric'].isin(relevant_metrics)]
    filtered_df = filtered_df.reindex(columns=original_columns)

    logger.debug(f"Filtered DataFrame shape: {filtered_df.shape}")
    return filtered_df



def filter_by_insurance_lines(
    df: pd.DataFrame,
    selected_linemains: List[str]
) -> pd.DataFrame:
    """
    Filters and aggregates insurance data based on selected insurance lines.

    Args:
        df (pd.DataFrame): The input DataFrame containing insurance data.
        selected_linemains (List[str]): List of lines to filter.

    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    logger.debug("Starting filter_by_insurance_lines function")
    logger.debug(f"Input DataFrame shape: {df.shape}")

    logger.debug(f"selected_linemains: {selected_linemains}")

    # Define special categories and their subcategories
    parent_lines = {
        'страхование жизни': ['1', '2'],
        'имущество юр.лиц': ['4.1.7', '4.3'],
        'ж/д': ['4.1.2', '4.2.2'],
        'море, грузы': ['4.1.4', '4.1.5', '4.2.4'],
        'авиа': ['4.1.3', '4.2.3'],
        'спец. риски': ['4.1.3', '4.2.3', '4.1.4', '4.1.5', '4.2.4', '4.1.2', '4.2.2', '4.4'],
        'прочее': ['4.1.6', '4.2.1', '4.2.5', '4.2.6', '4.2.7', '4.2.8', '5', '7', '8'],
        'страхование нежизни': ['3.1', '3.2', '4.1.1', '6', '4.1.3', '4.2.3', '4.1.4', '4.1.5', '4.2.4', '4.1.2', '4.2.2', '4.4', '4.1.7', '4.3', '4.1.8', '4.1.6', '4.2.1', '4.2.5', '4.2.6', '4.2.7', '4.2.8', '5', '7', '8']
    }

    # Create a mapping from subcategories to their special categories, but only for selected special categories
    subline_to_parent = {
        sub: paren
        for parent, subs in parent_lines.items()
        for sub in subs
        if parent in selected_linemains
    }

    # Create a set of all relevant linemains (selected + subcategories of selected special categories)
    relevant_lines = set(selected_linemains)
    for line in selected_linemains:
        if line in parent_lines:
            relevant_lines.update(parent_lines[line])

    original_columns = df.columns.tolist()

    # Filter the DataFrame to include only relevant linemains
    df_filtered = df[df['linemain'].isin(relevant_lines)].copy()

    # Rename sublines their parents' names, but only if the parent is selected
    df_filtered['linemain'] = df_filtered['linemain'].map(lambda x: subline_to_parent.get(x, x))

    # Perform the groupby aggregation
    index_columns = [col for col in df.columns if col not in ['linemain', 'value']]
    df = df_filtered.groupby(index_columns + ['linemain'])['value'].sum().reset_index()

    df_all_lines = df.groupby(index_columns)['value'].sum().reset_index()
    df_all_lines['linemain'] = 'all_lines'

    result_df = pd.concat([df, df_all_lines], ignore_index=True)
    result_df = result_df.reindex(columns=original_columns)
    logger.debug(f"Final DataFrame shape: {result_df.shape}")
    logger.debug("Completed aggregate_insurance_lines function successfully.")

    return result_df



def filter_by_period_type(df: pd.DataFrame, period_type: str, end_quarter, num_periods: int) -> pd.DataFrame:

    end_quarter_date = pd.to_datetime(end_quarter)
    end_quarter_num = end_quarter_date.quarter
    grouping_cols  = [col for col in df.columns if col not in ['year_quarter', 'value']]

    df = df.sort_values(grouping_cols + ['year_quarter'], ascending=True)

    N = num_periods + 1

    if period_type == 'previous_quarter':
        pass

    elif period_type == 'same_q_last_year':
        df = df[df['year_quarter'].dt.quarter == end_quarter_num]


    elif period_type in ['same_q_last_year_ytd', 'previous_q_mat', 'same_q_last_year_mat', 'cumulative_sum']:

        df = df.sort_values(grouping_cols + ['year_quarter'], ascending=True)

        if period_type == 'same_q_last_year_ytd':
            df = df[df['year_quarter'].dt.quarter <= end_quarter_num]
            df['year'] = df['year_quarter'].dt.year
            df['ytd_value'] = df.groupby(['year'] + grouping_cols)['value'].cumsum()
            df = df.reset_index(drop=True)
            df['value'] = df['ytd_value']
            df = df.drop(columns=['year', 'ytd_value'])
            df = df[df['year_quarter'].dt.quarter == end_quarter_num]

        elif period_type in ['previous_q_mat', 'same_q_last_year_mat']:
            df.set_index('year_quarter', inplace=True)
            df['last_4_quarters_sum'] = df.groupby(grouping_cols)['value'].rolling(window='365D', min_periods=1).sum().reset_index(level=grouping_cols, drop=True)
            df.reset_index(inplace=True)
            df['value'] = df['last_4_quarters_sum']
            df = df.drop(columns=['last_4_quarters_sum'])
            if period_type == 'same_q_last_year_mat':
                df = df[df['year_quarter'].dt.quarter == end_quarter_num]

        elif period_type == 'cumulative_sum':
            df['cumsum'] = df.groupby(grouping_cols)['value'].cumsum()
            df['value'] = df['cumsum']
            df = df.drop(columns=['cumsum'])


    df = df.sort_values(by='year_quarter', ascending=False)
    result = df[df['year_quarter'].isin(df['year_quarter'].unique()[:N])]

    return resul



def add_calculated_metrics(df: pd.DataFrame, selected_metrics: List[str]) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    logger.debug(f"Starting to calculate metrics. Selected metrics: {selected_metrics}")
    df.to_csv('test_df.csv')

    # Identify grouping columns
    grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
    logger.debug(f"Grouping columns: {grouping_cols}")

    def calculate_for_group(group):
        metrics_dict = dict(zip(group['metric'], group['value']))
        new_rows = []

        for metric, base_metrics_list in calculated_metrics.items():
            if metric in selected_metrics:
                logger.debug(f"Calculating {metric}")
                try:
                    # Get values for base metrics, use 0 if missing
                    base_values = [metrics_dict.get(base, 0) for base in base_metrics_list]

                    if metric == 'net_balance':
                        result = base_values[0] - base_values[1]  # ceded_losses - ceded_premiums
                    elif metric == 'total_premiums':
                        result = base_values[0] + base_values[1]  # direct_premiums + inward_premiums
                    elif metric == 'net_premiums':
                        result = base_values[0] + base_values[1] - base_values[2]  # direct_premiums + inward_premiums - ceded_premiums
                    elif metric == 'total_losses':
                        result = base_values[0] + base_values[1]  # direct_losses + inward_losses
                    elif metric == 'net_losses':
                        result = base_values[0] + base_values[1] - base_values[2]  # direct_losses + inward_losses - ceded_losses
                    elif metric == 'gross_result':
                        result = base_values[0] + base_values[1] - base_values[2] - base_values[3]  # direct_premiums + inward_premiums - direct_losses - inward_losses
                    elif metric == 'net_result':
                        result = (base_values[0] + base_values[1] - base_values[4]) - (base_values[2] + base_values[3] - base_values[5])
                        # (direct_premiums + inward_premiums - ceded_premiums) - (direct_losses + inward_losses - ceded_losses)

                    # Create a new row with all columns filled
                    new_row = {col: group[col].iloc[0] for col in grouping_cols}
                    new_row.update({'metric': metric, 'value': result})
                    new_rows.append(new_row)

                    logger.debug(f"Calculated {metric} successfully")

                    # Log if any base metrics were missing
                    missing = [base for base in base_metrics_list if base not in metrics_dict]
                    if missing:
                        logger.debug(f"Calculated {metric} with missing base metrics treated as 0: {missing}")
                except Exception as e:
                    logger.error(f"Error calculating {metric}: {str(e)}")

        if new_rows:
            return pd.concat([group, pd.DataFrame(new_rows)], ignore_index=True)
        return group

    # Apply calculations to each group
    result_df = df.groupby(grouping_cols).apply(calculate_for_group).reset_index(drop=True)
    result_df.to_csv('test_result_df.csv')

    logger.debug(f"Resulting DataFrame shape: {result_df.shape}")
    return result_df


def get_top_n_insurers_and_insurer_options(df: pd.DataFrame, selected_insurer: str, number_of_insurers: int, all_selected_metrics: List[str], top_n_list: Optional[List[int]] = None) -> List[str]:

    logger.debug(f"Starting get_top_n_insurers function with n={number_of_insurers} and metrics={all_selected_metrics}")
    logger.debug(f"Input DataFrame shape: {df.shape}")
    df = df[df['linemain'] == 'all_lines']


    # Get the most recent year_quarter and filter df
    end_quarter = df['year_quarter'].max()
    end_quarter_df = df[df['year_quarter'] == end_quarter]

    logger.debug(f"end_quarter: {end_quarter}")

    # Filter df to get insurer options sorted based on total premiums

    insurer_options_df = end_quarter_df[end_quarter_df['metric'] != 'total_premiums']
    insurer_options_df = insurer_options_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)
    all_insurers = insurer_options_df['insurer'].unique().tolist()

    logger.debug(f"all_insurers: {all_insurers}")

    if top_n_list is None:
        top_n_list = [5, 10, 20]

    benchmark_insurers = [f"top-{n}-benchmark" for n in top_n_list]

    insurer_options = [{'label': map_insurer('total'), 'value': 'total'}] + [
        {'label': map_insurer(insurer), 'value': insurer}
        for insurer in all_insurers if insurer not in benchmark_insurers
    ]

    benchmark_options = [{'label': map_insurer(insurer), 'value': insurer}
                         for insurer in benchmark_insurers + ['total']]

    compare_options = [{'label': map_insurer(insurer), 'value': insurer}
                       for insurer in all_insurers if insurer not in benchmark_insurers and insurer != selected_insurer]

    # Sort the DataFrame by the first metric in all_selected_metrics in descending order
    ranking_metric = all_selected_metrics[0] if all_selected_metrics[0] in df.columns else 'total_premiums' if 'total_premiums' in df.columns else 'direct_premiums'
    logger.debug(f"Ranking insurers based on metric: {ranking_metric}")
    ranking_df = end_quarter_df[end_quarter_df['metric'] == ranking_metric]
    ranking_df = ranking_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)

    # Get the top-n insurers
    top_n_insurers = ranking_df['insurer'].head(number_of_insurers).tolist()

    logger.debug(f"Top {number_of_insurers} insurers: {top_n_insurers}")
    #logger.debug(f"Top {number_of_insurers} {ranking_metric} values: {sorted_df[ranking_metric].head(number_of_insurers).tolist()}")

    return top_n_insurers, insurer_options, benchmark_options, compare_options



def add_total_rows(df: pd.DataFrame) -> pd.DataFrame:

    original_columns = df.columns.tolist()

    # Identify identifier columns (all except 'insurer' and 'value')
    id_columns = [col for col in df.columns if col not in ['insurer', 'value']]

    # Calculate total rows
    df_total = df.groupby(id_columns)['value'].sum().reset_index()
    df_total['insurer'] = 'total'
    result_df = pd.concat([df, df_total], ignore_index=True)
    result_df = result_df.reindex(columns=original_columns)

    return result_df





def add_total_top_bench_rows(
    df: pd.DataFrame,
    main_insurer: str,
    top_n_insurers: List[str],
    selected_insurers: List[str],
    end_quarter: str,
    top_n_list: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Adds aggregate rows for 'Total', top-N largest 'value' entries within each group, and top-N benchmarks.

    Parameters:
    - df (pd.DataFrame): The original DataFrame containing data.
    - main_insurer (str): The main insurer to exclude during top-N calculation.
    - top_n_insurers (List[str]): A list of insurers for the final filtering.
    - selected_insurers (List[str]): Additional insurers for final filtering.
    - end_quarter (str): The specific quarter to filter when calculating top-N benchmarks.
    - top_n_list (List[int], optional): A list of integers specifying the top-N aggregates to add.

    Returns:
    - pd.DataFrame: The DataFrame augmented with 'Total', 'Top N', and 'Top N Benchmark' aggregate rows.
    """
    if top_n_list is None:
        top_n_list = [5, 10, 20]

    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()

    # Convert 'year_quarter' to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
        df['year_quarter'] = pd.to_datetime(df['year_quarter'], errors='coerce')
        if df['year_quarter'].isnull().any():
            logger.debug("Some 'year_quarter' entries could not be converted to datetime.")

    # Convert 'insurer' to string to maintain consistency
    df['insurer'] = df['insurer'].astype(str)

    # Convert end_quarter to datetime
    try:
        end_quarter_dt = pd.to_datetime(end_quarter)
    except Exception as e:
        logger.error(f"Error converting end_quarter '{end_quarter}' to datetime: {e}")
        raise

    # Identify identifier columns (all except 'insurer' and 'value')
    id_columns = [col for col in df.columns if col not in ['insurer', 'value']]

    # Calculate total rows
    df_total = df[df['insurer'] == 'total']
    logger.debug(f"df_total head'{df_total.head()}")


    df = df[df['insurer'] != 'total']
    logger.debug(f"df_not total head'{df.head()}")

    # Store DataFrames for each Top-N and Top-N Benchmark
    df_top_n_list = []

    for n in top_n_list:
        # Sort by identifier columns and 'value' to get largest values firs
        df_sorted = df.sort_values(by=id_columns + ['value'], ascending=False)

        # Select top N 'value' entries per group
        df_top_n = df_sorted.groupby(id_columns).head(n).copy()
        df_top_n_grouped = df_top_n.groupby(id_columns)['value'].sum().reset_index()
        df_top_n_grouped['insurer'] = f'top-{n}'
        df_top_n_list.append(df_top_n_grouped)
        logger.debug(f"Added top-{n} aggregate rows.")

        # Identify top-N insurers for 'direct_premiums' in the specified end_quarter
        df_benchmark = df[
            (df['insurer'] != main_insurer) &
            (df['year_quarter'] == end_quarter_dt) &
            (df['metric'] == 'direct_premiums')
        ]

        if df_benchmark.empty:
            logger.debug(f"No benchmark data found for end_quarter '{end_quarter}' and metric 'direct_premiums'. Skipping top-{n}-benchmark.")
            continue

        # Select top N insurers by value
        top_n_benchmark_insurers = df_benchmark.groupby('insurer')['value'].sum().nlargest(n).index.tolist()
        logger.debug(f"Top-{n} benchmark insurers: {top_n_benchmark_insurers}")

        # Filter the original DataFrame for these top-N benchmark insurers
        df_benchmark_top_n = df[df['insurer'].isin(top_n_benchmark_insurers)]

        if df_benchmark_top_n.empty:
            logger.debug(f"No data found for top-{n} benchmark insurers.")
            continue

        # Aggregate their values across all dimensions
        df_benchmark_aggregated = df_benchmark_top_n.groupby(id_columns)['value'].sum().reset_index()
        df_benchmark_aggregated['insurer'] = f'top-{n}-benchmark'
        df_top_n_list.append(df_benchmark_aggregated)
        logger.debug(f"Added top-{n}-benchmark aggregate rows.")

    # Concatenate original DataFrame with totals and aggregates
    result_df = pd.concat([df, df_total] + df_top_n_list, ignore_index=True)
    logger.debug(f"result_df head'{result_df.head()}")


    logger.debug("Concatenated original DataFrame with total and aggregate rows.")

    # Perform sorting
    result_df = result_df.sort_values(by=id_columns + ['value'], ascending=False)
    logger.debug("Sorted sthe final DataFrame.")
    logger.debug(f"result_df unique insurers: {result_df['insurer'].unique()}")
    logger.debug(f"result_df selected_insurers: {selected_insurers}")
    logger.debug(f"result_df main_insurer: {main_insurer}")
    logger.debug(f"top_n_insurers: {top_n_insurers}")

    # Final filtering: combine top_n_insurers, main_insurer, and selected_insurers
    final_insurers_list = list(set(
        top_n_insurers + [main_insurer] + selected_insurers +
        ['total'] +
        [f'top-{n}' for n in top_n_list] +
        [f'top-{n}-benchmark' for n in top_n_list]
    ))

    # Ensure that 'total', 'top-{n}', 'top-{n}-benchmark', 'main_insurer', and selected_insurers are in the final lis
    result_df = result_df[result_df['insurer'].isin(final_insurers_list)]
    logger.debug("Filtered the final DataFrame based on the specified insurers.")

    return result_df



def add_market_share_rows(df):
    logger.debug("Starting add_market_share_rows function.")

    # Log unique 'metric' values before processing
    unique_metrics_before = df['metric'].unique()
    logger.debug(f"Unique 'metric' values BEFORE processing: {unique_metrics_before}")

    # Step 1: Define the group columns (exclude 'insurer' and 'value')
    group_cols = [col for col in df.columns if col not in ['insurer', 'value']]
    logger.debug(f"Grouping columns: {group_cols}")

    # Step 2: Extract total values for each group
    total_df = df[df['insurer'] == 'total'][group_cols + ['value']].rename(columns={'value': 'total_value'})
    logger.debug(f"Extracted total_df with {len(total_df)} rows.")

    # Step 3: Merge total values back to the original DataFrame
    df_merged = df.merge(total_df, on=group_cols, how='left')
    logger.debug(f"Merged DataFrame has {len(df_merged)} rows.")

    # Step 4: Calculate market share
    df_merged['market_share'] = df_merged['value'] / df_merged['total_value']

    # Optional: Handle cases where total_value is zero to avoid division by zero
    df_merged['market_share'] = df_merged['market_share'].fillna(0)
    logger.debug("Calculated 'market_share' for all applicable rows.")

    # Step 5: Prepare the market share DataFrame
    # Optionally exclude the 'total' insurer if desired
    # df_market_share = df_merged[df_merged['insurer'] != 'total'].copy()
    df_market_share = df_merged.copy()

    # Modify the 'metric' column to indicate market share
    df_market_share['metric'] = df_market_share['metric'] + '_market_share'
    logger.debug("Modified 'metric' column to include '_market_share'.")

    # Select the necessary columns without duplicating 'metric'
    market_share_cols = [col for col in group_cols if col != 'metric'] + ['metric', 'insurer', 'market_share']
    df_market_share_new = df_market_share[market_share_cols].rename(columns={'market_share': 'value'})
    logger.debug("Prepared the market share DataFrame.")

    # Step 6: Append the market share rows to the original DataFrame
    df_final = pd.concat([df, df_market_share_new], ignore_index=True)
    logger.debug(f"Appended market share rows. Original rows: {len(df)}, Market share rows: {len(df_market_share_new)}, Total rows after append: {len(df_final)}")

    # Optional: Sort the DataFrame for better readability
    df_final = df_final.sort_values(by=group_cols + ['insurer']).reset_index(drop=True)
    logger.debug("Sorted the final DataFrame.")

    # Log unique 'metric' values after processing
    unique_metrics_after = df_final['metric'].unique()
    logger.debug(f"Unique 'metric' values AFTER processing: {unique_metrics_after}")

    logger.debug("Completed add_market_share_rows function.")

    return df_final



def add_averages_and_ratios(
    df: pd.DataFrame,
    selected_metrics: List[str]) -> pd.DataFrame:
    """
    Calculates new metric ratios based on selected_metrics and calculated_ratios,
    and transforms existing metrics if needed.
    Parameters:
    - df (pd.DataFrame): The input DataFrame with columns ['year_quarter', 'metric', 'linemain', 'insurer', 'value'].
    - selected_metrics (List[str]): A list of metric names for which ratios need to be calculated or transformed.
    Returns:
    - pd.DataFrame: The original DataFrame with additional rows for the calculated ratios and transformed metrics.
    """
    # Define the formula mapping for each calculated ratio and metric transformation
    formula_mapping = {
        'average_sum_insured': lambda df: df['sums_end'] / df['contracts_end'] / 1000000,
        'average_new_sum_insured': lambda df: df['new_sums'] / df['new_contracts'] / 1000000,
        'average_new_premium': lambda df: df['direct_premiums'] / df['new_contracts'],
        'average_loss': lambda df: df['total_losses'] / df['claims_settled'],
        'ceded_premiums_ratio': lambda df: df['ceded_premiums'] / df['total_premiums'],
        'ceded_losses_ratio': lambda df: df['ceded_losses'] / df['total_losses'],
        'ceded_losses_to_ceded_premiums_ratio': lambda df: df['ceded_losses'] / df['ceded_premiums'],
        'gross_loss_ratio': lambda df: df['total_losses'] / df['total_premiums'],
        'net_loss_ratio': lambda df: (df['total_losses'] - df['ceded_losses']) / (df['total_premiums'] - df['ceded_premiums']),
        'effect_on_loss_ratio': lambda df: (df['total_losses'] / df['total_premiums']) - ((df['total_losses'] - df['ceded_losses']) / (df['total_premiums'] - df['ceded_premiums'])),
        'ceded_ratio_diff': lambda df: (df['ceded_losses'] / df['total_losses']) - (df['ceded_premiums'] / df['total_premiums']),
        'sums_end': lambda x: x / 1000,
        'new_sums': lambda x: x / 1000,
        'new_contracts': lambda x: x * 1000,
        'contracts_end': lambda x: x * 1000,
        'claims_settled': lambda x: x * 1000,
        'claims_reported': lambda x: x * 1000,


    }

    logger.debug(f"selected_metrics: {selected_metrics}")
    logger.debug(f"unique metric values: {df['metric'].unique()}")

    # Create a copy of the original DataFrame to avoid modifying the inpu
    new_df = df.copy()

    # Separate metrics that need transformation from those that need calculation
    transform_metrics = ['sums_end', 'new_sums', 'new_contracts', 'contracts_end', 'claims_settled', 'claims_reported']
    calc_metrics = [m for m in selected_metrics if m not in transform_metrics]

    # Transform existing metrics
    for metric in transform_metrics:
        if metric in selected_metrics:
            mask = new_df['metric'] == metric
            new_df.loc[mask, 'value'] = new_df.loc[mask, 'value'].apply(formula_mapping[metric])

    # Calculate new metrics
    if calc_metrics:
        index_columns = [col for col in df.columns if col not in ['metric', 'value']]

        # Prepare the data for calculation
        pivoted_data = new_df.pivot_table(
            values='value',
            index=index_columns,
            columns='metric'
        ).reset_index()

        # Calculate and add new rows for each ratio
        for ratio in calc_metrics:
            if ratio in formula_mapping:
                # Apply the formula
                pivoted_data[ratio] = formula_mapping[ratio](pivoted_data)
                # Prepare the new rows
                new_rows = pivoted_data.melt(
                    id_vars=index_columns,
                    value_vars=[ratio],
                    var_name='metric',
                    value_name='value'
                )

                # Append the new rows to the DataFrame
                new_df = pd.concat([new_df, new_rows], ignore_index=True)

    logger.debug(f"New DataFrame shape: {new_df.shape}")
    logger.debug(f"New metrics added: {new_df['metric'].unique()}")
    return new_df



def add_growth_rows(df: pd.DataFrame) -> pd.DataFrame:

    # Step 1: Pivot the DataFrame
    index_columns = [col for col in df.columns if col not in ['metric', 'value']]

    pivot_df = df.pivot_table(
        index=index_columns,
        columns='metric',
        values='value',
        aggfunc='sum'
    ).reset_index()

    # Step 2: Calculate growth
    group_columns = [col for col in index_columns if col != 'year_quarter']

    # Create the list of id_vars for melting
    id_vars = ['year_quarter'] + group_columns

    # Sort the dataframe
    df_sorted = pivot_df.sort_values(by=id_vars)

    # Identify value columns (all columns except those in id_vars)
    value_columns = pivot_df.columns.difference(id_vars)

    # Calculate quarter-to-quarter growth
    q_to_q_growth = df_sorted.groupby(group_columns)[value_columns].pct_change()
    q_to_q_growth.columns = [f'{col}_q_to_q_change' for col in q_to_q_growth.columns]

    # Merge the growth data back with the original dataframe
    pivot_with_growth = pd.concat([df_sorted, q_to_q_growth], axis=1)

    # Step 3: Melt the DataFrame
    melted_df = pd.melt(
        pivot_with_growth,
        id_vars=id_vars,
        var_name='metric',
        value_name='value'
    ).fillna(0)

    return melted_df


def add_growth_rows_long(df: pd.DataFrame, num_periods: int = 2) -> pd.DataFrame:


    # Identify grouping columns (excluding 'year_quarter', 'metric', and 'value')
    grouping_columns = [col for col in df.columns if col not in ['year_quarter', 'metric', 'value']]

    # Sort the DataFrame by grouping columns and 'year_quarter'
    df_sorted = df.sort_values(by=grouping_columns + ['year_quarter']).copy()

    # Identify metrics that end with 'market_share'
    is_market_share = df_sorted['metric'].str.endswith('market_share')

    # Define a threshold for near-zero values
    epsilon = 1e-8

    # Handle non-market_share metrics
    non_ms = ~is_market_share
    group_cols = grouping_columns + ['metric']

    # Calculate previous values within each group
    df_sorted_non_ms = df_sorted[non_ms].copy()
    df_sorted_non_ms['previous'] = df_sorted_non_ms.groupby(group_cols)['value'].shift(1)

    # Calculate percentage change with safe handling
    df_sorted_non_ms['pct_change'] = np.where(
        df_sorted_non_ms['previous'] > epsilon,  # Valid denominator
        (df_sorted_non_ms['value'] - df_sorted_non_ms['previous']) / df_sorted_non_ms['previous'],  # pct_change
        np.nan  # Default value when denominator is near zero or invalid
    )

    #df_sorted_non_ms['pct_change'] = np.where(
    #    df_sorted_non_ms['previous'] < 0,
    #    1e-6,
    #    df_sorted_non_ms['pct_change']
    #)


    # Fill any remaining NaN values if necessary
    #df_sorted_non_ms['pct_change'] = df_sorted_non_ms['pct_change'].fillna(0)

    # Handle market_share metrics by calculating absolute difference
    df_sorted_ms = df_sorted[is_market_share].copy()
    df_sorted_ms['abs_diff'] = df_sorted_ms.groupby(group_cols)['value'].diff().fillna(0)


    # Initialize a new column for growth
    df_sorted['growth'] = 0

    # Assign calculated growth values appropriately
    df_sorted['growth'] = df_sorted['growth'].astype(float)  # Convert 'growth' to float if it's not already

    df_sorted.loc[non_ms, 'growth'] = df_sorted_non_ms['pct_change'].values
    df_sorted.loc[is_market_share, 'growth'] = df_sorted_ms['abs_diff'].values

    # Prepare the growth DataFrame
    growth_df = df_sorted.copy()
    growth_df['metric'] = growth_df['metric'] + '_q_to_q_change'
    growth_df['value'] = growth_df['growth']

    save_df_to_csv(growth_df, "09_growth_df.csv")

    # Select relevant columns for growth DataFrame
    growth_df = growth_df.drop(columns=['growth'])
    save_df_to_csv(growth_df, "09_growth_df_dropped.csv")
    original_df = df_sorted.drop(columns=['growth'])

    # Sort 'year_quarter' in descending order to identify the most recent periods
    original_df_sorted = original_df.sort_values(by='year_quarter', ascending=False).copy()
    growth_df_sorted = growth_df.sort_values(by='year_quarter', ascending=False).copy()

    # Get unique 'year_quarter' values sorted descending
    unique_quarters = original_df_sorted['year_quarter'].drop_duplicates().sort_values(ascending=False)

    # Determine quarters for original_df and growth_df
    quarters_original = unique_quarters.iloc[:num_periods]
    logger.debug(f"quarters_original: {quarters_original}")


    quarters_growth = unique_quarters.iloc[:max(num_periods - 1, 1)]  # Ensure at least 1 period
    logger.debug(f"quarters_growths: {quarters_growth}")

    # Filter original_df for the specified number of periods
    original_df_filtered = original_df_sorted[original_df_sorted['year_quarter'].isin(quarters_original)].copy()

    # Filter growth_df for num_periods - 1 periods
    growth_df_filtered = growth_df_sorted[growth_df_sorted['year_quarter'].isin(quarters_growth)].copy()

    # Concatenate the original and growth DataFrames
    result_df = pd.concat([original_df_filtered, growth_df_filtered], ignore_index=True)

    # Optionally, sort the result for better readability
    result_df = result_df.sort_values(by=grouping_columns + ['year_quarter', 'metric']).reset_index(drop=True)

    return result_df




def create_chart_data(df: pd.DataFrame, fig_type: str, main_insurer: str | None = None) -> pd.DataFrame:

    if fig_type == "combined":
        # Filter out rows where 'linemain' is 'all_lines'
        df = df[df['linemain'] == 'all_lines']
        df = df.groupby(['year_quarter', 'insurer', 'metric'])['value'].sum().reset_index()

    elif fig_type == "market":
        df = df[df['linemain'] != 'all_lines']
        df = df[df['insurer'] == main_insurer]
        df = df.groupby(['year_quarter', 'linemain', 'metric'])['value'].sum().reset_index()


    else:
        logger.error(f"Unsupported fig_type: {fig_type}")
        raise ValueError(f"Unsupported fig_type: {fig_type}")

    return df




def calculate_percent_column(df: pd.DataFrame, fig_type: str, is_entities_stacked: bool = False, is_metrics_stacked: bool = False):
    # Determine the entity_column based on fig_type
    entity_column_mapping = {
        'reinsurance_type': 'reinsurance_type',
        'reinsurance_form': 'reinsurance_form',
        'reinsurance_geography': 'reinsurance_geography',
        'reinsurance_line': 'linemain',
        'market': 'linemain',
        'combined': 'insurer'
    }
    entity_column = entity_column_mapping.get(fig_type, 'insurer')

    # Define grouping columns based on stacking conditions
    if is_entities_stacked and not is_metrics_stacked:
        groupby_columns = ['year_quarter', 'metric']
    elif not is_entities_stacked and is_metrics_stacked:
        groupby_columns = ['year_quarter', entity_column]
    elif is_entities_stacked and is_metrics_stacked:
        groupby_columns = ['year_quarter']
    else:  # not is_entities_stacked and not is_metrics_stacked
        groupby_columns = ['year_quarter', entity_column, 'metric']
    df = df.copy()

    # Calculate the total value for each group
    df['total_value'] = df.groupby(groupby_columns)['value'].transform('sum')

    # Calculate the percent column
    df['percent'] = df['value'] / df['total_value']

    # Drop the temporary total_value column
    df = df.drop(columns=['total_value'])
    #if fig_type in ['reinsurance_line', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_form']

    return df


def get_preprocessed_df(
    insurance_df: pd.DataFrame,
    reinsurance_df: pd.DataFrame,
    main_insurer: str,
    selected_insurers: List[str],
    main_metric: str,
    selected_metrics: List[str],
    fig_types: List[str],  # Changed from str to List[str]
    selected_linemains: List[str],
    premium_loss_selection: List[str],
    period_type: str,
    start_quarter: str = '2023Q1',
    end_quarter: str = '2024Q1',
    number_of_insurers: int = 20,
    reinsurance_form: Optional[List[str]] = None,
    reinsurance_geography: Optional[List[str]] = None,
    reinsurance_type: Optional[List[str]] = None,
    num_periods: int = 2,
    is_entities_stacked: bool = False,
    is_metrics_stacked: bool = False,
    reinsurance_metrics: Optional[List[str]] = None  # Added for reinsurance

) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame, List[str], List[str], List[str]]:
    """
    Preprocess insurance and reinsurance data to generate chart data and table data for multiple fig_types.

    Returns:
        chart_data_dict: A dictionary where keys are fig_types and values are processed chart_data DataFrames.
        table_df: Processed data for tables.
        insurer_options: List of insurer options.
        benchmark_options: List of benchmark options.
        compare_options: List of comparison options.
    """

    extended_selected_metrics = selected_metrics + ['total_premiums', 'total_losses']


    def preprocess_general_insurance_lines(df: pd.DataFrame, extended_metrics: List[str], fig_type: str | None = None
) -> pd.DataFrame:


        df = filter_by_date_range_and_line_type(
            df, start_quarter, end_quarter, fig_type,
            premium_loss_selection, reinsurance_form, reinsurance_geography, reinsurance_type
        )
        df = filter_required_metrics(df, extended_metrics)
        df = filter_by_insurance_lines(df, selected_linemains)

        return df

    def preprocess_general_calculated_metrics(df: pd.DataFrame, period_type: str, extended_metrics: List[str]) -> pd.DataFrame:

        df = filter_by_period_type(df, period_type, end_quarter, num_periods)
        df = add_calculated_metrics(df, extended_metrics)

        return df


    # === Process insurance_df for General Outputs ===
    df_general_insurance_lines = preprocess_general_insurance_lines(insurance_df.copy(), extended_selected_metrics)
    save_df_to_csv(df_general_insurance_lines, f"01_preprocess_general_insurance_lines_combined.csv")


    df_general = df_general_insurance_lines[df_general_insurance_lines['linemain'] == 'all_lines']
    df_general = preprocess_general_calculated_metrics(df_general, period_type, extended_selected_metrics)
    save_df_to_csv(df_general, f"02_preprocess_general_calculated_metrics.csv")


    # Generate Top N Insurers and Options
    top_n_insurers, insurer_options, benchmark_options, compare_options = get_top_n_insurers_and_insurer_options(
        df_general, main_insurer, number_of_insurers, extended_selected_metrics
    )

    #logger.debug(f"Top N Insurers: {top_n_insurers}")
    #logger.debug(f"Insurer Options: {insurer_options}")
    #logger.debug(f"Benchmark Options: {benchmark_options}")
    #logger.debug(f"Compare Options: {compare_options}")

    df_general_total_rows = add_total_rows(df_general)
    save_df_to_csv(df_general, "03_add_total_rows_combined.csv")

    # Continue Processing General Outputs
    df_general = add_total_top_bench_rows(
        df_general, main_insurer, top_n_insurers, selected_insurers,
        end_quarter, top_n_list=[5, 10, 20]
    )
    save_df_to_csv(df_general, "04_add_total_top_benchmark_rows_combined.csv")

    df_general = add_market_share_rows(df_general)
    save_df_to_csv(df_general, "05_add_market_share_rows_combined.csv")

    df_general = add_averages_and_ratios(df_general, extended_selected_metrics)
    save_df_to_csv(df_general, "06_add_averages_and_ratios_combined.csv")

    melted_df_general = add_growth_rows_long(df_general, num_periods)
    save_df_to_csv(melted_df_general, "07_add_growth_df_combined.csv")

    table_df = create_table_data(
        melted_df_general, selected_metrics, top_n_insurers,
        number_of_insurers, top_n_list=[5, 10, 20]
    )
    save_df_to_csv(table_df, "08_table_df_general.csv")

    # === Prepare Chart Data for Each fig_type ===
    chart_data_dict: Dict[str, pd.DataFrame] = {}  # Initialize an empty dictionary

    for fig_type in fig_types:
        logger.debug(f"Processing chart_data for fig_type: {fig_type}")

        if fig_type in REINSURANCE_FIG_TYPES:
            extended_reinsurance_metrics = reinsurance_metrics + ['total_premiums', 'total_losses']

            # Use reinsurance_df for chart_data
            logger.debug(f"fig_type '{fig_type}' indicates reinsurance data. Processing reinsurance_df for chart_data.")
            df = preprocess_general_insurance_lines(reinsurance_df.copy(), extended_reinsurance_metrics, fig_type)
            save_df_to_csv(df, f"01_preprocess_general_insurance_lines_{fig_type}.csv")

            if fig_type == "reinsurance_line":
                df = df[df['linemain'] != 'all_lines']

            else:
                df = df[df['linemain'] == 'all_lines']

            df_chart = preprocess_general_calculated_metrics(df, period_type, extended_reinsurance_metrics)
            save_df_to_csv(df_chart, f"02_preprocess_general_calculated_metrics_{fig_type}.csv")

            df_chart = add_averages_and_ratios(df_chart, extended_selected_metrics)
            save_df_to_csv(df_chart, f"06_add_averages_and_ratios_{fig_type}.csv")

            melted_df_chart = add_growth_rows_long(df_chart, num_periods)
            save_df_to_csv(melted_df_chart, f"07_add_growth_df_{fig_type}.csv")

            melted_df_chart_filtered = melted_df_chart[melted_df_chart['metric'].isin(reinsurance_metrics)]
            save_df_to_csv(melted_df_chart_filtered, f"09_filter_metric_chart_{fig_type}.csv")

        elif fig_type == 'market':
            logger.debug(f"fig_type '{fig_type}' Reusing df_general_total_rows for chart_data.")

            df_chart =  df_general_insurance_lines.copy()
            df_chart = df_chart[df_chart['linemain'] != 'all_lines']

            df_chart = preprocess_general_calculated_metrics(df_chart, period_type, extended_selected_metrics)
            save_df_to_csv(df_chart, f"02_preprocess_general_calculated_metrics_{fig_type}.csv")

            df_chart = add_total_rows(df_chart)
            save_df_to_csv(df_chart, f"03_add_total_rows_{fig_type}.csv")

            #df_chart = df_chart[df_chart['metric'].isin(selected_metrics)]

            df_chart = add_market_share_rows(df_chart)
            save_df_to_csv(df_chart, f"05_add_market_share_rows_{fig_type}.csv")

            #group_cols = [col for col in df_chart.columns if col not in ['insurer', 'value']]
            #df_chart = df_chart.groupby(group_cols)['value'].sum().reset_index()

            df_chart = df_chart[df_chart['insurer'] == main_insurer]
            df_chart = add_averages_and_ratios(df_chart, extended_selected_metrics)
            save_df_to_csv(df_chart, f"06_add_averages_and_ratios_{fig_type}.csv")

            melted_df_chart = add_growth_rows_long(df_chart, num_periods)
            save_df_to_csv(melted_df_chart, f"07_add_growth_df_{fig_type}.csv")

            melted_df_chart_filtered = melted_df_chart[melted_df_chart['metric'].isin(selected_metrics)]
            save_df_to_csv(melted_df_chart_filtered, f"09_filter_metric_chart_{fig_type}.csv")

        elif fig_type  == 'combined':
            # Reuse melted_df_general for chart_data
            logger.debug(f"fig_type '{fig_type}' Reusing melted_df_general for chart_data.")
            melted_df_chart = melted_df_general.copy()

            melted_df_chart = melted_df_chart[melted_df_chart['insurer'].isin(selected_insurers)]
            save_df_to_csv(melted_df_chart, f"09_filter_insurer_df_chart_{fig_type}.csv")

            melted_df_chart_filtered = melted_df_chart[melted_df_chart['metric'].isin(selected_metrics)]
            save_df_to_csv(melted_df_chart_filtered, f"09_filter_metric_chart_{fig_type}.csv")

        else:
            logger.error(f"Unknown fig_type: {fig_type}")
            raise ValueError(f"Unknown fig_type: {fig_type}")

        # Create chart data
        #chart_data = create_chart_data(melted_df_chart_filtered, fig_type, main_insurer)
        #save_df_to_csv(chart_data, f"17_chart_data_{fig_type}.csv")

        # Calculate percentage columns if needed
        chart_data = calculate_percent_column(melted_df_chart_filtered, fig_type, is_entities_stacked, is_metrics_stacked)
        save_df_to_csv(chart_data, f"10_chart_data_with_percent_{fig_type}.csv")
        #chart_data = chart_data.sort_values(['value'], ascending=[False]).reset_index(drop=True)
        #print(chart_data.head())
        # Add to the dictionary
        chart_data_dict[fig_type] = chart_data

    return chart_data_dict, table_df, insurer_options, benchmark_options, compare_options




__all__ = [' get_preprocessed_df']

