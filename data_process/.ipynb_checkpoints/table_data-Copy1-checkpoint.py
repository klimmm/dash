import dash
import pandas as pd
import logging
import numpy as np
import re
from dash import dcc, Input, Output, State, ALL, MATCH, dash_table, html
from dash import dash_table
from typing import List, Tuple, Optional, Dict, OrderedDict, Any, Union, Se
from datetime import datetime
from app.table_styles import generate_dash_table_config
from data_process.process_market_metrics import process_market_metrics
from data_process.data_utils import save_df_to_csv
from constants.mapping import map_line, map_insurer
from constants.filter_options import MAIN_METRICS_OPTIONS_TABLE
from constants.translations import translate
from logging_config import get_logger

logger = get_logger(__name__)


def update_data_table(df, table_selected_metric, selected_linemains, premium_loss_selection,
                      period_type, start_quarter, end_quarter,
                      num_periods, number_of_insurers, top_n_insurers, top_n_list, num_periods_table,
                      toggle_selected_market_share, toggle_selected_qtoq,
                      toggle_additional_market_share, toggle_additional_qtoq):
    logger.debug(f"Updating data table. table_selected_metric: {table_selected_metric}")


    ranking_insurers_df = df[df['linemain'] == 'all_lines']
    logger.info(f"top_n_insurers: {top_n_insurers}")
    logger.info(f"ranking_insurers_df: {ranking_insurers_df}")

    num_periods_growth = num_periods_table - 1
    df = process_market_metrics(ranking_insurers_df, table_selected_metric, [],
                                period_type, num_periods_table, num_periods_growth)


    table_df = table_data_filter(df, top_n_insurers, number_of_insurers, table_selected_metric, top_n_list)

    table_data = table_data_pivot(table_df, table_selected_metric)

    metrics_options = MAIN_METRICS_OPTIONS_TABLE

    table_config = generate_dash_table_config(
        df=table_data,
        toggle_selected_market_share=toggle_selected_market_share,
        toggle_selected_qtoq=toggle_selected_qtoq,
        toggle_additional_market_share=toggle_additional_market_share,
        toggle_additional_qtoq=toggle_additional_qtoq
    )

    data_table = dash_table.DataTable(**table_config)

    mapped_lines = map_line(selected_linemains)
    table_title_row1 = f"Топ {number_of_insurers} страховщиков по {', '.join(mapped_lines) if isinstance(mapped_lines, list) else mapped_lines}"
    table_title_row2 = f"{translate(period_type)}"

    return (
        data_table,  # data-table.children
        dash.no_update,  # charts-container.children
        dash.no_update,  # x-column.options
        dash.no_update,  # series-column.options
        dash.no_update,  # group-column.options
        dash.no_update,  # main-insurer.options
        dash.no_update,  # compare-insurers-main.options
        dash.no_update,  # primary-y-metric.options
        dash.no_update,  # secondary-y-metric.options
        metrics_options,  # table-additional-metric.options
        table_title_row1,  # table-title-row1.children
        table_title_row2,  # table-title-row2.children
    )


def table_data_filter(
    df: pd.DataFrame,
    top_n_insurers: List[str],
    number_of_insurers: int,
    all_metrics: List[str],
    top_n_list: List[int] = [5, 10, 20]
) -> pd.DataFrame:
    """
    Processes the DataFrame to generate a pivot table with sorted metric columns.
    """
    logger.info(f"Top N insurers: {top_n_insurers}")
    logger.info(f"Number of insurers to select: {number_of_insurers}")
    save_df_to_csv(df, "16_1_table_inter.csv")  # Ensure this function handles paths correctly

    # Filter for 'all_lines'
    if 'all_lines' not in df['linemain'].values:
        group_columns = [col for col in df.columns if col not in ['linemain', 'value']]
        df = df.groupby(group_columns)['value'].sum().reset_index()
        df['linemain'] = 'all_lines'
    else:
        df = df[df['linemain'] == 'all_lines']
    # Define summary rows
    save_df_to_csv(df, "16_2_table_inter.csv")  # Ensure this function handles paths correctly

    summary_rows = [f'top-{n}' for n in top_n_list] + ['total']
    logger.info(f"Summary rows: {summary_rows}")
    insurers_to_keep = top_n_insurers + summary_rows
    logger.info(f"insurers_to_keep: {insurers_to_keep}")

    # Create a list of metrics to keep
    metrics_to_keep = (
        all_metrics +
        [f"{m}_q_to_q_change" for m in all_metrics] +
        [f"{m}_market_share" for m in all_metrics] +
        [f"{m}_market_share_q_to_q_change" for m in all_metrics]
    )
    logger.debug(f"Metrics to keep: {metrics_to_keep}")

    # Filter the DataFrame to keep only the selected insurers and metrics
    df = df[df['metric'].isin(metrics_to_keep)].copy()
    df = df[df['insurer'].isin(insurers_to_keep)]

    save_df_to_csv(df, "16_3_table_inter.csv")  # Ensure this function handles paths correctly

    # Sort the grouped DataFrame by year_quarter (most recent first), then by the original insurer order
    df_sorted = df.sort_values(['year_quarter', 'metric'], ascending=[False, True])
    logger.debug("Sorted the grouped DataFrame by 'year_quarter' and 'metric'.")

    # Log the unique values present in the sorted DataFrame
    logger.info(f"Insurers present in df_grouped_sorted: {df_sorted['insurer'].unique()}")
    logger.info(f"Metrics present in df_grouped_sorted: {df_sorted['metric'].unique()}")
    logger.info(f"Year quarters present in df_grouped_sorted: {df_sorted['year_quarter'].unique()}")

    return df_sorted


def table_data_pivot(df: pd.DataFrame, all_metrics: List[str]) -> pd.DataFrame:
    try:
        logger.info(f"Starting table_data_pivot with DataFrame shape: {df.shape}")
        logger.info(f"Columns in input DataFrame: {df.columns}")
        logger.info(f"First few rows of input DataFrame:\n{df.head()}")

        if df.empty:
            logger.info("Input DataFrame is empty. Returning empty DataFrame.")
            return pd.DataFrame()

        # Step 1 & 2: Convert 'year_quarter' to datetime and format as 'YYYYQX'
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)

        # Step 3: Define the order of attributes
        attributes_order = ['', 'q_to_q_change', 'market_share', 'market_share_q_to_q_change']

        # Step 4 & 5: Extract 'base_metric' and 'attribute'
        def extract_metric_attribute(metric, base_metrics):
            for base in base_metrics:
                if metric.startswith(base):
                    suffix = metric[len(base):].lstrip('_')
                    return base, suffix or ''
            return metric, ''

        # Use pandas' apply with result_type='expand' to ensure two columns are created
        df[['base_metric', 'attribute']] = df.apply(
            lambda row: pd.Series(extract_metric_attribute(row['metric'], all_metrics)),
            axis=1
        )

        logger.info(f"DataFrame after extracting base_metric and attribute:\n{df.head()}")

        # Step 6 & 7: Create unified column names
        df['column_name'] = df.apply(
            lambda row: f"{row['base_metric']}_{row['year_quarter']}{'_' + row['attribute'] if row['attribute'] else ''}",
            axis=1
        )

        # Step 8 & 9: Pivot the table to wide forma
        pivot_df = df.pivot_table(
            index='insurer',
            columns='column_name',
            values='value',
            aggfunc='first'
        ).reset_index()

        logger.info(f"Pivot DataFrame shape: {pivot_df.shape}")
        logger.info(f"Columns in pivot DataFrame: {pivot_df.columns}")

        # Step 10: Sort years in descending order
        years_sorted = sorted(df['year_quarter'].unique(), reverse=True)

        # Step 11 & 12: Create desired columns lis
        desired_columns = ['insurer'] + [
            f"{metric}_{year}{'_' + attr if attr else ''}"
            for metric in all_metrics
            for attr in attributes_order
            for year in years_sorted
        ]

        # Step 13: Remove duplicates while preserving order
        desired_columns = list(OrderedDict.fromkeys(desired_columns))

        # Step 14 & 15: Add missing columns and reorder
        for col in desired_columns:
            if col not in pivot_df.columns:
                pivot_df[col] = pd.NA
        df = pivot_df[desired_columns]

        # Step 16: Remove columns with all zeros or NaNs (except first column)
        mask = ~((df.iloc[:, 1:] == 0) | df.iloc[:, 1:].isna()).all() & ~df.iloc[:, 1:].isna().all()
        df = df.loc[:, ['insurer'] + list(mask[mask].index)]
        df = df.fillna('n/a')

        # Separate and sort main insurers and summary rows
        summary_prefixes = ('top', 'total')
        summary_df = df[df['insurer'].str.lower().str.startswith(summary_prefixes)]
        main_df = df[~df['insurer'].str.lower().str.startswith(summary_prefixes)]

        sorting_col = df.columns[1]  # First column after 'insurer'

        main_df.loc[:, sorting_col] = pd.to_numeric(main_df[sorting_col], errors='coerce')
        summary_df.loc[:, sorting_col] = pd.to_numeric(summary_df[sorting_col], errors='coerce')

        sorted_main = main_df.sort_values(by=sorting_col, ascending=False)
        sorted_summary = summary_df.sort_values(by=sorting_col, ascending=True)

        # Concatenate sorted DataFrames
        sorted_df = pd.concat([sorted_main, sorted_summary], ignore_index=True)

        # Add sequential numbering column
        sorted_df['N'] = [*range(1, len(sorted_main) + 1), *[np.nan] * len(sorted_summary)]

        # Reorder columns
        pivot_df = sorted_df[['N'] + [col for col in sorted_df.columns if col != 'N']]

        logger.info(f"Final DataFrame shape: {pivot_df.shape}")
        logger.info(f"Columns in final DataFrame: {pivot_df.columns}")

        return pivot_df

    except Exception as e:
        logger.exception(f"An error occurred in table_data_pivot: {str(e)}")
        raise