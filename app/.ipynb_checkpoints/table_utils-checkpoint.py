import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Union
from .data_utils import log_dataframe_info
import os
# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)
from translations import translate
from .filter_options import METRICS
import re

def save_df_to_csv(df, filename, max_rows=500):
    """
    Save a DataFrame to a CSV file with a maximum number of rows.

    Args:
        df (pd.DataFrame): The DataFrame to save
        filename (str): The name of the file to save to
        max_rows (int): The maximum number of rows to save (default: 500)
    """
    output_dir = 'intermediate_outputs_table'
    os.makedirs(output_dir, exist_ok=True)

    df_to_save = df.head(max_rows)
    full_path = os.path.join(output_dir, filename)
    df_to_save.to_csv(full_path, index=False)
    logger.info(f"Saved {len(df_to_save)} rows to {full_path}")

def format_quarter(quarter: pd.Period) -> str:
    """Format quarter consistently."""
    return f"{quarter.year}Q{quarter.quarter}"

def identify_top_n_insurers(df: pd.DataFrame, selected_metric: str, last_quarter: pd.Period, n: int = 20) -> List[str]:
    """
    Identify top N insurers based on the selected metric for the last quarter.
    If the exact column is not found, it looks for a column matching the pattern "*_{last_quarter}".
    """
    target_column = f"{selected_metric}_{last_quarter}"
    logger.info(f"Target column for analysis: '{target_column}'")
    logger.info(f"Unique columns in df: {df.columns.tolist()}")

    if target_column not in df.columns:
        logger.warning(f"Exact target column '{target_column}' not found. Searching for a matching pattern.")
        pattern = re.compile(f".*_{last_quarter}$")
        matching_columns = [col for col in df.columns if pattern.match(col)]

        if not matching_columns:
            raise ValueError(f"No columns found matching the pattern '*_{last_quarter}'")

        if len(matching_columns) > 1:
            logger.warning(f"Multiple columns found matching the pattern: {matching_columns}")
            logger.warning(f"Selecting the first matching column: {matching_columns[0]}")

        target_column = matching_columns[0]
        logger.info(f"Using column: '{target_column}'")

    grouped = df.groupby('insurer')[target_column].sum().reset_index()
    top_n_insurers = grouped.nlargest(n, target_column)['insurer'].tolist()
    return top_n_insurers


def calculate_summary_rows(df: pd.DataFrame, n_values: List[int]) -> pd.DataFrame:
    """
    Calculate summary rows (Total and Top N) for given metrics.
    """
    columns_to_aggregate = [col for col in df.columns if col != 'insurer']
    summary_data = {'insurer': ['Total'] + [f'Top {n}' for n in n_values]}

    for metric in columns_to_aggregate:
        total = df[metric].sum()
        top_n_values = [df.nlargest(min(n, len(df)), metric)[metric].sum() for n in n_values]
        summary_data[metric] = [total] + top_n_values

    summary_rows = pd.DataFrame(summary_data)
    return summary_rows

def add_market_share_and_calculated_metrics(df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
    """
    Add market share columns and calculated metrics.
    """
    calculated_metrics = {
        'ceded_premiums_ratio': ('ceded_premiums', 'total_premiums'),
        'ceded_losses_ratio': ('ceded_losses', 'total_losses'),
        'ceded_losses_to_premiums_ratio': ('ceded_losses', 'ceded_premiums'),
        'gross_loss_ratio': ('total_losses', 'total_premiums'),
        'net_loss_ratio': ('net_losses', 'net_premiums'),
        'effect_on_loss_ratio': ('net_loss_ratio', 'gross_loss_ratio'),
        'average_new_sum_insured': ('new_sums', 'new_contracts'),
        'average_loss': ('total_losses', 'claims_settled'),
        'average_new_premium': ('total_premiums', 'new_contracts')

    }

    for metric in metrics:
        metric_columns = [col for col in df.columns if col.startswith(f'{metric}_')]
        for col in metric_columns:
            total_market_value = df.loc[df['insurer'] == 'Total', col].iloc[0]
            if total_market_value != 0:
                market_share_column = f'{col}_market_share'
                df[market_share_column] = df[col] / total_market_value
                df.loc[df['insurer'] == 'Total', market_share_column] = 1.0  # Total market share is 100%
            else:
                logger.warning(f"Total market value for {col} is 0, skipping market share calculation")

        if metric in calculated_metrics:
            numerator, denominator = calculated_metrics[metric]
            numerator_cols = [col for col in df.columns if col.startswith(f'{numerator}_')]
            denominator_cols = [col for col in df.columns if col.startswith(f'{denominator}_')]
            for num_col, den_col in zip(numerator_cols, denominator_cols):
                quarter = num_col.split('_')[-1]
                df[f'{metric}_{quarter}'] = df[num_col] / df[den_col]

    # Calculate ceded_ratio_diff for each quarter
    ceded_premiums_ratio_cols = [col for col in df.columns if col.startswith('ceded_premiums_ratio_')]
    ceded_losses_ratio_cols = [col for col in df.columns if col.startswith('ceded_losses_ratio_')]

    for premiums_col, losses_col in zip(ceded_premiums_ratio_cols, ceded_losses_ratio_cols):
        quarter = premiums_col.split('_')[-1]
        df[f'ceded_ratio_diff_{quarter}'] = df[premiums_col] - df[losses_col]

    return df


def calculate_q_to_q_changes(df: pd.DataFrame, metrics: List[str], quarters: List[str]) -> pd.DataFrame:
    """
    Calculate quarter-to-quarter changes for given metrics.
    """
    for metric in metrics:
        metric_cols = [col for col in df.columns if col.startswith(f'{metric}_') and 'market_share' not in col and 'q_to_q_change' not in col]
        metric_cols.sort(reverse=True)

        for i in range(1, len(metric_cols)):
            current_col = metric_cols[i-1]
            previous_col = metric_cols[i]
            change_col = f'{current_col}_q_to_q_change'

            df[change_col] = (df[current_col] - df[previous_col]) / df[previous_col]
            df[change_col] = df[change_col].fillna(0)

            market_share_current = f'{current_col}_market_share'
            market_share_previous = f'{previous_col}_market_share'
            market_share_change_col = f'{market_share_current}_q_to_q_change'

            if market_share_current in df.columns and market_share_previous in df.columns:
                df[market_share_change_col] = df[market_share_current] - df[market_share_previous]
                df[market_share_change_col] = df[market_share_change_col].fillna(0)

    return df

def process_data_table(
    df: pd.DataFrame,
    selected_metrics: Union[str, List[str]],
    additional_metrics: List[str],
    num_periods: int = 2,
    columns_config: Optional[Dict[str, str]] = None,
    num_insurers: int = 10
) -> pd.DataFrame:
    try:
        if isinstance(selected_metrics, str):
            selected_metrics = [selected_metrics]
        df = df[df['linemain'] == 'all_lines']
        save_df_to_csv(df, "1_1_initial_process_data_table.csv")

        df['quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q')
        all_quarters = sorted(df['quarter'].unique(), reverse=True)
        unique_quarters = all_quarters[:num_periods]
        logger.info(f"Processing quarters: {unique_quarters}")

        # Save after initial data filtering and quarter processing
        save_df_to_csv(df, "1_2_after_quarter_processing.csv")
        all_metrics = [metric for metric in METRICS]

        n_values = [5, 10, 20, 50]
        quarterly_data = []
        for idx, quarter in enumerate(unique_quarters):
            logger.info(f"quarter df before adding new metrics data columns: {df.columns.tolist()}")
            #group_cols = [col for col in df.columns if col not in [metric_col, value_col]]

            available_metrics = [metric for metric in all_metrics if metric in df.columns]
            quarter_df = df[df['quarter'] == quarter].groupby('insurer')[available_metrics].sum().reset_index()
            logger.info(f"quarter df before adding new metrics data columns after groupby: {quarter_df.columns.tolist()}")

            quarter_str = format_quarter(quarter)
            quarter_df.columns = ['insurer'] + [f'{col}_{quarter_str}' for col in quarter_df.columns if col != 'insurer']

            # Save after processing each quarter
            save_df_to_csv(quarter_df, f"2_{idx+1}_quarter_{quarter_str}_processed.csv")

            summary_rows = calculate_summary_rows(quarter_df, n_values)

            # Concatenate original data and summary rows

            quarter_df = pd.concat([quarter_df, summary_rows], ignore_index=True)


            quarter_df = add_market_share_and_calculated_metrics(quarter_df, all_metrics)

            quarterly_data.append(quarter_df)

            # Save after adding summary rows and calculated metrics
            save_df_to_csv(quarter_df, f"3_{idx+1}_quarter_{quarter_str}_with_summaries.csv")

        df_merged = quarterly_data[0]

        for i in range(1, len(quarterly_data)):
            df_merged = pd.merge(df_merged, quarterly_data[i], on='insurer', how='outer')

        # Save after merging all quarters
        save_df_to_csv(df_merged, "4_merged_quarters.csv")
        logger.info(f"Unique columns in  df_merged before calculate_q_to_q_changes: {df_merged.columns.tolist()}")

        df_merged = calculate_q_to_q_changes(df_merged, all_metrics, [format_quarter(q) for q in unique_quarters])

        # Save after calculating quarter-to-quarter changes
        save_df_to_csv(df_merged, "5_with_q_to_q_changes.csv")
        logger.info(f"Unique columns in  df_merged: {df_merged.columns.tolist()}")

        # Check available metrics in df_merged
        all_metrics = selected_metrics + additional_metrics
        available_metrics = set()
        for column in df_merged.columns:
            match = re.match(r'(\w+)_', column)
            if match:
                available_metrics.add(match.group(1))

        # Compare with selected and additional metrics
        valid_metrics = [metric for metric in all_metrics if metric in available_metrics]
        invalid_metrics = set(all_metrics) - set(valid_metrics)

        if invalid_metrics:
            logger.warning(f"The following metrics are not available in the DataFrame: {invalid_metrics}")

        default_metrics = ['total_premiums']
        if not valid_metrics:
            logger.warning("No valid metrics found in the DataFrame. Using default metrics.")
            valid_metrics = [metric for metric in default_metrics if metric in available_metrics]
            if not valid_metrics:
                logger.error("No valid default metrics found in the DataFrame.")
                return None
        logger.warning(f"valid metrics: {valid_metrics}")

        columns_to_display = ['insurer']
        existing_columns = ['insurer']

        for metric in valid_metrics:
            # Check and add main metric columns
            metric_cols = [f'{metric}_{format_quarter(q)}' for q in unique_quarters]
            found_cols = [col for col in metric_cols if col in df_merged.columns]
            existing_columns.extend(found_cols)
            columns_to_display.extend(metric_cols)

            # Check and add quarter-to-quarter change columns
            q_to_q_cols = [f'{metric}_{format_quarter(q)}_q_to_q_change' for q in unique_quarters[:-1]]
            found_cols = [col for col in q_to_q_cols if col in df_merged.columns]
            existing_columns.extend(found_cols)
            columns_to_display.extend(q_to_q_cols)

            # Check and add market share columns
            market_share_cols = [f'{metric}_{format_quarter(q)}_market_share' for q in unique_quarters]
            found_cols = [col for col in market_share_cols if col in df_merged.columns]
            existing_columns.extend(found_cols)
            columns_to_display.extend(market_share_cols)

            # Check and add market share quarter-to-quarter change columns
            market_share_q_to_q_cols = [f'{metric}_{format_quarter(q)}_market_share_q_to_q_change' for q in unique_quarters[:-1]]
            found_cols = [col for col in market_share_q_to_q_cols if col in df_merged.columns]
            existing_columns.extend(found_cols)
            columns_to_display.extend(market_share_q_to_q_cols)

        # Remove duplicates while preserving order
        existing_columns = list(dict.fromkeys(existing_columns))

        if columns_config:
            existing_columns = [col for col in existing_columns if col in columns_config]

        logger.info(f"Existing columns to be displayed: {existing_columns}")
        logger.info(f"All columns considered for display: {columns_to_display}")

        missing_columns = set(columns_to_display) - set(existing_columns)
        if missing_columns:
            logger.warning(f"The following columns are missing from df_merged: {missing_columns}")

        df_display = df_merged[existing_columns].copy()

        # Save after column reordering
        save_df_to_csv(df_display, "6_reordered_columns.csv")

        summary_rows = [f'Top {n}' for n in n_values] + ['Total']

        if isinstance(selected_metrics, str):
            selected_metrics = [selected_metrics]  # Convert string to lis

        logger.info(f"selected_metrics: {selected_metrics}")
        top_n_insurers = identify_top_n_insurers(df_display, selected_metrics[0], unique_quarters[0])
        insurer_order = {insurer: i for i, insurer in enumerate(top_n_insurers + summary_rows)}


        df_display['sort_key'] = df_display['insurer'].map(insurer_order)
        df_display = df_display.sort_values('sort_key').drop('sort_key', axis=1)

        top_x = df_display[~df_display['insurer'].isin(summary_rows)].head(num_insurers)
        summary_rows_df = df_display[df_display['insurer'].isin(summary_rows)]
        #logger.info(f"Length of top_n_insurers: {len(top_n_insurers)}")
        #logger.info(f"Length of summary_rows: {len(summary_rows)}")
        #logger.info(f"Total length: {len(top_n_insurers) + len(summary_rows)}")
        final_df = pd.concat([top_x, summary_rows_df], ignore_index=True)
        final_df.insert(0, 'N', range(1, len(final_df) + 1))

        # Save final processed dataframe
        save_df_to_csv(final_df, "7_final_processed_data.csv")

        logger.info(f"Final data shape: {final_df.shape}")
        logger.info(f"Final data columns: {final_df.columns.tolist()}")

        return final_df

    except Exception as e:
        logger.error(f"Error in process_data_table: {str(e)}", exc_info=True)
        raise

__all__ = ['process_data_table']
