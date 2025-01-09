#pre_processing_data.py

import os
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, OrderedDict, Any, Union, Se
import logging
from dataclasses import dataclass
from .data_utils import save_df_to_csv, log_dataframe_info, category_structure
from .filter_options import MARKET_METRIC_OPTIONS, METRICS
import json


# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)


metrics = list(MARKET_METRIC_OPTIONS.keys())


def filter_by_date_range_and_line_type(
    df: pd.DataFrame,
    fig_type: List[str],
    start_quarter: str,
    end_quarter: str,
    num_periods: int,
    aggregation_type: str,
    premium_loss_selection: Optional[List[str]] = None,
    reinsurance_form: Optional[List[str]] = None,
    reinsurance_geography: Optional[List[str]] = None,
    reinsurance_type: Optional[List[str]] = None,
    line_types: Optional[List[str]] = None

) -> pd.DataFrame:

    # Convert quarters to datetime
    start_date = pd.to_datetime(start_quarter)
    end_date = pd.to_datetime(end_quarter)
    df = df[(df['year_quarter'] >= start_date) & (df['year_quarter'] <= end_date)]

    mask = pd.Series(True, index=df.index)


    # Filter by line_type if specified
    if line_types is not None and 'line_type' in df.columns:
        mask &= df['line_type'].isin(line_types)

    if fig_type not in ['reinsurance_form', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_line']:

        if premium_loss_selection is not None and 'metric' in df.columns:
            exclude_metrics = []
            if 'direct' not in premium_loss_selection:
                exclude_metrics.extend(['direct_premiums', 'direct_losses'])
            if 'inward' not in premium_loss_selection:
                exclude_metrics.extend(['inward_premiums', 'inward_losses'])
            if exclude_metrics:
                mask &= ~df['metric'].isin(exclude_metrics)

    for col, values in [
        ('reinsurance_form', reinsurance_form),
        ('reinsurance_geography', reinsurance_geography),
        ('reinsurance_type', reinsurance_type)
    ]:
        if values is not None and col in df.columns:
            mask &= df[col].isin(values)


    df = df[mask]
    df = df.drop(columns='line_type', errors='ignore')

    return df


def filter_by_insurance_lines(
    df: pd.DataFrame,
    selected_linemains: List[str]
) -> pd.DataFrame:
    """
    Filters and aggregates insurance data based on selected linemains and categories.
    For special categories, aggregated linemains are removed to prevent double-counting.

    Args:
        df (pd.DataFrame): The input DataFrame containing insurance data.
        selected_linemains (List[str]): List of linemains to filter.
        category_structure_file (str): Path to the JSON file containing category structure.

    Returns:
        pd.DataFrame: The processed DataFrame with aggregated categories.
    """
    logger.info("Starting filter_by_insurance_lines function")
    logger.info(f"selected_linemains: {selected_linemains}")

    # Define Special Categories
    special_categories = {
        "страхование нежизни",
        "страхование жизни",
        "имущество юр.лиц",
        "ж/д",
        "море, грузы",
        "авиа",
        "спец. риски",
        "прочее"
    }

    # Step 1: Define an Inner Recursive Function to Get All Descendant Linemains
    def recurse(category: str, all_children: Set[str], visited: Set[str]):
        """
        Recursively collects all descendant linemains for a given category.

        Args:
            category (str): The category to process.
            all_children (set): The set to accumulate descendant linemains.
            visited (set): The set to track visited categories to prevent infinite loops.
        """
        if category in visited:
            logger.error(f"Circular reference detected at category '{category}'. Skipping to prevent infinite recursion.")
            return
        visited.add(category)

        children = set(category_structure.get(category, {}).get('children', []))
        logger.debug(f"Processing category '{category}': children -> {children}")

        for child in children:
            if child in special_categories:
                logger.debug(f"Category '{child}' is a special category. Recursing into it.")
                recurse(child, all_children, visited)
            else:
                logger.debug(f"Adding child '{child}' to all_children.")
                all_children.add(child)

    # Step 2: Pivot the DataFrame to Have Linemains as Columns
    index_columns = [col for col in df.columns if col not in ['linemain', 'value']]
    logger.info(f"Index columns for pivot: {index_columns}")

    try:
        df_pivoted = df.pivot_table(
            index=index_columns,
            columns='linemain',
            values='value',
            aggfunc='sum'
        ).fillna(0)
        logger.info(f"Pivoted DataFrame shape: {df_pivoted.shape}")
    except KeyError as e:
        logger.error(f"Error pivoting DataFrame: {e}")
        raise

    # Step 3: Aggregate Special Categories
    for category in selected_linemains:
        if category in special_categories:
            logger.info(f"Processing special category '{category}'")

            # Initialize sets for collecting children and tracking visited categories
            all_children = set()
            visited = set()

            # Recursively gather all descendants
            recurse(category, all_children, visited)
            logger.info(f"Descendant linemains for '{category}': {all_children}")

            # Check if the children exist in the pivoted DataFrame
            available_children = [child for child in all_children if child in df_pivoted.columns]
            logger.info(f"Available children for '{category}': {available_children}")

            if available_children:
                # Sum the values of the children into the special category
                df_pivoted[category] = df_pivoted[available_children].sum(axis=1)
                logger.info(f"Aggregated special category '{category}' from children: {available_children}")

                # Remove the aggregated children columns to prevent double-counting
                df_pivoted.drop(columns=available_children, inplace=True)
                logger.info(f"Removed aggregated children for '{category}': {available_children}")
            else:
                logger.warning(f"No available children found for special category '{category}'. Skipping aggregation.")

    # Step 4: Calculate 'all_lines' as the Sum of Selected Categories
    available_linemains = [line for line in selected_linemains if line in df_pivoted.columns]
    if available_linemains:
        df_pivoted['all_lines'] = df_pivoted[available_linemains].sum(axis=1)
        logger.info("Added 'all_lines' column as the sum of selected linemains")
    else:
        logger.warning("No selected linemains available for 'all_lines' calculation. Setting 'all_lines' to 0.")
        df_pivoted['all_lines'] = 0  # Default to 0 if no categories are available

    # Step 5: Unpivot the DataFrame Back to Long Forma
    try:
        df_unpivoted = df_pivoted.reset_index().melt(
            id_vars=index_columns,
            var_name='linemain',
            value_name='value'
        )
        logger.info(f"Unpivoted DataFrame shape: {df_unpivoted.shape}")
    except Exception as e:
        logger.error(f"Error unpivoting DataFrame: {e}")
        raise

    # Step 6: Filter to Keep Only Selected Categories and 'all_lines'
    linemains_to_keep = available_linemains + ['all_lines']
    df_result = df_unpivoted[df_unpivoted['linemain'].isin(linemains_to_keep)]
    logger.info(f"Final DataFrame shape after filtering: {df_result.shape}")

    logger.info("Completed filter_by_insurance_lines function successfully.")
    return df_resul

def pivot_data_by_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot the DataFrame to create a table with 'year_quarter', 'insurer', 'linemain',
    and additional columns (if they exist) as the index, 'metric' as the columns, and 'value' as the values.

    Args:
        df (pd.DataFrame): The input DataFrame.
    Returns:
        pd.DataFrame: The pivoted DataFrame.
    """

    index_columns = [col for col in df.columns if col not in ['metric', 'value']]
    logger.info(f"Pivoting with index columns: {index_columns}")

    pivot_df = df.pivot_table(
        index=index_columns,
        columns='metric',
        values='value',
        aggfunc='sum'
    ).reset_index()

    logger.info(f"Pivot completed. Shape: {pivot_df.shape}")

    # Get the list of metric columns (all columns except index columns)
    metric_columns = pivot_df.columns.difference(index_columns)

    logger.info(f"Converting the following columns to numeric: {metric_columns.tolist()}")

    # Convert metric columns to numeric, replacing NaN and non-numeric with zeros
    for col in metric_columns:
        pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)

    logger.info("Numeric conversion completed")
    logger.debug(f"DataFrame head after conversion: {pivot_df.head()}")

    return pivot_df


def filter_by_aggregation_type(df: pd.DataFrame, aggregation_type: str) -> pd.DataFrame:
    logger.info(f"Starting filter_by_aggregation_type with aggregation_type: {aggregation_type}")
    logger.info(f"Input DataFrame shape: {df.shape}")

    df = df.copy()
    logger.info("Created a copy of the input DataFrame")

    df.loc[:, :] = df.fillna(0)
    logger.info("Filled NA values with 0")

    most_recent_quarter_value = df['year_quarter'].max().quarter
    logger.info(f"Most recent quarter value: {most_recent_quarter_value}")

    oldest_valid_quarter = df[df['year_quarter'].dt.quarter == (most_recent_quarter_value % 4) + 1].iloc[0]['year_quarter']
    logger.info(f"Oldest valid quarter: {oldest_valid_quarter}")

    logger.info(f"Columns in DataFrame: {df.columns}")
    logger.info(f"DataFrame info:\n{df.info()}")

    group_cols = [col for col in df.columns if col in ['insurer', 'linemain', 'reinsurance_geography', 'reinsurance_form', 'reinsurance_type']]
    value_cols = [col for col in df.columns if col not in group_cols + ['year_quarter']]

    logger.info(f"Grouping by columns: {group_cols}")
    logger.info(f"Value columns: {value_cols}")

    if aggregation_type == 'same_q_last_year_ytd':
        logger.info("Applying 'same_q_last_year_ytd' aggregation")
        df.loc[:, value_cols] = df.groupby(group_cols)[value_cols].rolling(window=most_recent_quarter_value, min_periods=1).sum().reset_index(level=group_cols, drop=True)
        df = df[df['year_quarter'].dt.quarter == most_recent_quarter_value]
    elif aggregation_type == 'same_q_last_year':
        logger.info("Applying 'same_q_last_year' aggregation")
        df.loc[:, value_cols] = df.groupby(group_cols)[value_cols].rolling(window=1, min_periods=1).sum().reset_index(level=group_cols, drop=True)
        df = df[df['year_quarter'].dt.quarter == most_recent_quarter_value]
    elif aggregation_type in ['previous_q_mat', 'same_q_last_year_mat']:
        logger.info(f"Applying '{aggregation_type}' aggregation")
        df.loc[:, value_cols] = df.groupby(group_cols)[value_cols].rolling(window=4, min_periods=1).sum().reset_index(level=group_cols, drop=True)
        df = df[df['year_quarter'] >= oldest_valid_quarter]
        if aggregation_type == 'same_q_last_year_mat':
            df = df[df['year_quarter'].dt.quarter == most_recent_quarter_value]
    elif aggregation_type == 'cumulative_sum':
        logger.info("Applying 'cumulative_sum' aggregation")
        df = df.sort_values(by=group_cols + ['year_quarter'])
        df.loc[:, value_cols] = df.groupby(group_cols)[value_cols].cumsum()
    else:
        logger.warning(f"Unknown aggregation_type: {aggregation_type}")

    logger.info(f"Output DataFrame shape: {df.shape}")
    return df



def add_calculated_metrics(df: pd.DataFrame, fig_type: List[str]) -> pd.DataFrame:
    logger.info("Entering add_calculated_metrics function")
    logger.info(f"Input DataFrame shape: {df.shape}")
    logger.info(f"Columns in input DataFrame: {df.columns.tolist()}")

    if fig_type in ['reinsurance_form', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_line']:
        df['total_premiums'] = df['inward_premiums']
        df['total_losses'] = df['inward_losses']
    else:
        df['total_premiums'] = df.get('direct_premiums', 0) + df.get('inward_premiums', 0)
        df['total_losses'] = df.get('direct_losses', 0) + df.get('inward_losses', 0)

    # Calculate derived columns, using .get() to handle missing columns
    df['net_premiums'] = df.get('total_premiums', 0) - df.get('ceded_premiums', 0)
    df['net_losses'] = df.get('total_losses', 0) - df.get('ceded_losses', 0)
    df['net_balance'] = df.get('ceded_losses', 0) - df.get('ceded_premiums', 0)
    df['gross_result'] = df.get('total_premiums', 0) - df.get('total_losses', 0)
    df['net_result'] = (df.get('gross_result', 0) +
        df.get('ceded_losses', 0) -
        df.get('ceded_premiums', 0)
    )

    logger.info(f"Filtered DataFrame shape: {df.shape}")
    logger.info(f"Columns in filtered DataFrame: {df.columns.tolist()}")

    return df


def get_preprocessed_df(
    df: pd.DataFrame,
    fig_type: List[str],
    selected_linemains: List[str],
    premium_loss_selection: List[str],
    aggregation_type: str,
    start_quarter: str = '2023Q1',
    end_quarter: str = '2024Q1',
    reinsurance_form: Optional[List[str]] = None,
    reinsurance_geography: Optional[List[str]] = None,
    reinsurance_type: Optional[List[str]] = None,
    num_periods: int = 2,

) -> pd.DataFrame:


    df = filter_by_date_range_and_line_type(df, fig_type, start_quarter, end_quarter, num_periods, aggregation_type, premium_loss_selection, reinsurance_form, reinsurance_geography, reinsurance_type)
    save_df_to_csv(df, "01_filter_by_date_range_and_line_type.csv")

    df = filter_by_insurance_lines(df, selected_linemains)
    save_df_to_csv(df, "02_filter_by_insurance_lines.csv")

    df = pivot_data_by_metrics(df)
    save_df_to_csv(df, "03_pivot_data_by_metrics.csv")

    df = filter_by_aggregation_type(df, aggregation_type)
    save_df_to_csv(df, "04_filter_by_aggegation_type.csv")

    processed_df = add_calculated_metrics(df, fig_type)
    save_df_to_csv(processed_df, "05_processed_df.csv")


    return processed_df
