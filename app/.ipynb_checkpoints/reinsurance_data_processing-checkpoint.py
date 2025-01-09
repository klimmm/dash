#data_processing.py

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, OrderedDict, Any, Union, Se
import logging
from dataclasses import dataclass
from .data_utils import save_df_to_csv, log_dataframe_info


from .filter_options import MARKET_METRIC_OPTIONS, METRICS
import json
import pandas as pd

# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)

import os

metrics = list(MARKET_METRIC_OPTIONS.keys())


def process_linemains(df: pd.DataFrame, fig_type: str) -> pd.DataFrame:
    logger.info(f"Starting process_linemains with fig_type: {fig_type}")

    if df is None:
        logger.error("Input DataFrame is None")
        return None

    logger.debug(f"Input DataFrame shape: {df.shape}")
    logger.debug(f"Input DataFrame columns: {df.columns}")

    if fig_type == "reinsurance_line":
        logger.info("Filtering for 'all_lines'")
        df_filtered = df[df['linemain'] != 'all_lines']
    else:
        logger.info("Filtering for 'all_lines'")
        df_filtered = df[df['linemain'] == 'all_lines']

    logger.debug(f"Filtered DataFrame shape: {df_filtered.shape}")

    if df_filtered.empty:
        logger.warning(f"Filtered DataFrame is empty for fig_type: {fig_type}")

    logger.info("Finished processing linemains")
    return df_filtered





def melt_data(df: pd.DataFrame) -> pd.DataFrame:
    # Define the additional columns we want to keep if they exis
    group_columns = [col for col in df.columns if col in ['reinsurance_geography', 'reinsurance_form', 'reinsurance_type', 'insurer', 'linemain']]

    # Create the list of id_vars for melting
    id_vars = ['year_quarter'] + group_columns

    # Sort the dataframe
    df_sorted = df.sort_values(id_vars)

    # Identify value columns (all columns except those in id_vars)
    value_columns = df.columns.difference(id_vars)

    print(df.columns)

    # Melt the dataframe
    melted_df = pd.melt(df,
                        id_vars=id_vars,
                        var_name='metric',
                        value_name='value').fillna(0)

    melted_df = melted_df[~melted_df['metric'].str.contains('total_market', case=False, na=False)]
    logger.warning(f"columns present in melted_df: {melted_df['metric'].unique()}")

    return melted_df

def filter_data(df: pd.DataFrame, reinsurance_form: List[str], reinsurance_type: List[str], reinsurance_geography: List[str]) -> pd.DataFrame:

    filtered_df = df.copy()
    # Filter by line_type if specified
    if reinsurance_form:
        if not isinstance(reinsurance_form, list):
            reinsurance_form = [reinsurance_form]  # Convert to list if single string is provided
        filtered_df = filtered_df[filtered_df['reinsurance_form'].isin(reinsurance_form)]

    if reinsurance_type:
        if not isinstance(reinsurance_type, list):
            reinsurance_type = [reinsurance_type]  # Convert to list if single string is provided
        filtered_df = filtered_df[filtered_df['reinsurance_type'].isin(reinsurance_type)]

    if reinsurance_geography:
        if not isinstance(reinsurance_geography, list):
            reinsurance_geography = [reinsurance_geography]  # Convert to list if single string is provided
        filtered_df = filtered_df[filtered_df['reinsurance_geography'].isin(reinsurance_geography)]


    return filtered_df



def create_chart_data(df: pd.DataFrame, fig_type: str) -> pd.DataFrame:

    #df_filtered = df[df['insurer'] == 'total']
        # Filter out rows where 'linemain' is 'all_lines'


    if fig_type == "reinsurance_line":
        df = df.groupby(['year_quarter', 'linemain', 'metric'])['value'].sum().reset_index()


        return df

    elif fig_type == "reinsurance_geography":
        df = df.groupby(['year_quarter', 'reinsurance_geography', 'metric'])['value'].sum().reset_index()

        return df

    elif fig_type == "reinsurance_form":
        df = df.groupby(['year_quarter', 'reinsurance_form', 'metric'])['value'].sum().reset_index()

        return df

    elif fig_type == "reinsurance_type":
        df = df.groupby(['year_quarter', 'reinsurance_type', 'metric'])['value'].sum().reset_index()

        return df

    else:
        logger.error(f"Unsupported fig_type: {fig_type}")
        raise ValueError(f"Unsupported fig_type: {fig_type}")

def get_processed_reinsurance_data(
    df: pd.DataFrame,
    fig_type: str,
    main_metric: str,
    reinsurance_form: List[str],
    reinsurance_type: List[str],
    reinsurance_geography: List[str],
    comparison_metrics: List[str],

) -> pd.DataFrame:


    process_linemains_df = process_linemains(df, fig_type)
    #save_df_to_csv(process_linemains_df, "07_processed_linemains_reinsurance_df.csv")

    melted_df = melt_data(process_linemains_df)
    #save_df_to_csv(melted_df, "11_melt_data_reinsurance.csv")

    all_selected_metrics = [main_metric] + comparison_metrics

    melted_df = melted_df[melted_df['metric'].isin(all_selected_metrics)]

    save_df_to_csv(melted_df, "13_filter_metric_reinsurance.csv")
    logger.warning(f"metrics present in processed_df: {melted_df['metric'].unique()}")

    filtered_data = filter_data(melted_df, reinsurance_form, reinsurance_type, reinsurance_geography)
    save_df_to_csv(filtered_data, "11_filtered_data_reinsurance.csv")


    chart_data = create_chart_data(filtered_data, fig_type)

    save_df_to_csv(chart_data, "14_chart_data_reinsurance.csv")


    return chart_data


