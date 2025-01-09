
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from collections import OrderedDic

from typing import List, Tuple, Optional, Dict, OrderedDict, Any, Union, Se
from dataclasses import dataclass
from memory_profiler import profile
import logging

from data_process.data_utils import save_df_to_csv, log_dataframe_info
from constants.filter_options import METRICS, base_metrics
from constants.mapping import map_insurer



from logging_config import get_logger, custom_profile
logger = get_logger(__name__)



#@custom_profile

def process_for_ranks(
    df: pd.DataFrame,
    main_insurer: str,
    benchmark: List[str],
    comparison_insurers: List[str],
    primary_y_metrics: List[str],
    secondary_y_metrics: List[str],
    number_of_insurers: int,
    top_n_list = [5, 10, 20]
) -> pd.DataFrame:

    selected_insurers = [main_insurer] + (comparison_insurers or []) + (benchmark or [])
    logger.debug(f"Unique insurers before Step 2: {df['insurer'].unique().tolist()}")

    selected_metrics = (primary_y_metrics or []) + (secondary_y_metrics or [])
    extended_metrics = (selected_metrics or []) + ['total_premiums', 'total_losses']

    ranking_df = add_top_n_rows(df, top_n_list)

    '''ranking_df = add_others_rows(
        df, selected_insurers, top_n_list)'''
    logger.debug(f"Unique insurers ranking_df : {ranking_df['insurer'].unique().tolist()}")

    top_n_insurers, insurer_options, benchmark_options, compare_options = get_top_n_insurers_and_insurer_options(
            ranking_df, main_insurer, number_of_insurers, extended_metrics, top_n_list)

    logger.debug(f"Unique insurers after Step 2: {df['insurer'].unique().tolist()}")
    #logger.debug(f"top_n_insurers {top_n_insurers}")
    #logger.debug(f"insurer_options {insurer_options}")
    #logger.debug(f"benchmark_options {benchmark_options}")
    #logger.debug(f"compare_options {compare_options}")

    save_df_to_csv(ranking_df, f"step_2_ranking_processed.csv")

    return ranking_df, top_n_insurers, insurer_options, benchmark_options, compare_options





def get_top_n_insurers_and_insurer_options(df: pd.DataFrame, selected_insurer: str, number_of_insurers: int, extended_metrics: List[str], top_n_list: Optional[List[int]] = None) -> List[str]:

    #logger.debug(f"Starting get_top_n_insurers function with n={number_of_insurers} and metrics={extended_metrics}")
    #logger.debug(f"Input DataFrame shape: {df.shape}")

    df = df[df['linemain'] == 'all_lines']
    logger.debug(f"df unique insurers get_top_n_insurers_and_insurer_options: {df['insurer'].unique()}")


    all_insurers_original = set(df['insurer'].unique())
    logger.debug(f"all_insurers_original: {all_insurers_original}")




    # Get the most recent year_quarter and filter df
    end_quarter = df['year_quarter'].max()
    end_quarter_df = df[df['year_quarter'] == end_quarter]
    #logger.debug(f"end_quarter: {end_quarter}")

    # Filter df to get insurer options sorted based on total premiums

    insurer_options_df = end_quarter_df[end_quarter_df['metric'] != 'total_premiums']
    insurer_options_df = insurer_options_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)

    all_insurers_last_quarter = insurer_options_df['insurer'].unique().tolist()

    insurers_not_in_last_quarter = list(all_insurers_original - set(all_insurers_last_quarter))
    all_insurers = all_insurers_last_quarter + insurers_not_in_last_quarter


    benchmark_insurers = [f"top-{n}-benchmark" for n in top_n_list]
    top_rows = [f"top-{n}" for n in top_n_list]


    df_top_insurers = df[df['insurer'].isin(top_rows)]
    df = df[~df['insurer'].isin(top_rows)]

    logger.info(f"df unique insurers: {df['insurer'].unique()}")


    top_insurers_options = [{'label': map_insurer(insurer), 'value': insurer}
                         for insurer in top_rows + ['total']]

    insurer_options = [
        {'label': map_insurer(insurer), 'value': insurer}
        for insurer in all_insurers if insurer not in benchmark_insurers and insurer != 'others' and insurer not in top_rows
    ]

    benchmark_options = [{'label': map_insurer(insurer), 'value': insurer}
                         for insurer in (benchmark_insurers + top_rows)  + ['total'] + ['others']]

    compare_options = [{'label': map_insurer(insurer), 'value': insurer}
                       for insurer in all_insurers if insurer not in benchmark_insurers and insurer not in top_rows and insurer != 'total' and insurer != 'others' and insurer != selected_insurer]

    ranking_metric = extended_metrics[0] if extended_metrics[0] in base_metrics else 'total_premiums'
    logger.info(f"Ranking insurers based on metric: {ranking_metric}")
    ranking_df = end_quarter_df[end_quarter_df['metric'] == ranking_metric]
    logger.info(f"ranking_df unique insurers: {ranking_df['insurer'].unique()}")


    insurers_to_exclude = ['others'] + top_rows + benchmark_insurers + ['total']

    ranking_df = ranking_df[~ranking_df['insurer'].isin(insurers_to_exclude)]

    ranking_df = ranking_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)
    logger.info(f"ranking_df unique insurers: {ranking_df['insurer'].unique()}")

    # Get the top-n insurers
    top_n_insurers = ranking_df['insurer'].head(number_of_insurers).tolist()

    logger.info(f"Top {number_of_insurers} insurers: {top_n_insurers}")
    #logger.debug(f"Top {number_of_insurers} {ranking_metric} values: {sorted_df[ranking_metric].head(number_of_insurers).tolist()}")

    all_insurers_options = insurer_options + top_insurers_options

    return top_n_insurers, all_insurers_options, benchmark_options, compare_options



def add_top_n_rows(df: pd.DataFrame, top_n_list: List[int]) -> pd.DataFrame:
    original_columns = df.columns.tolist()

    total_rows = {'total'}

    df_total = df[df['insurer'].isin(['total', 'others'])]
    df = df[~df['insurer'].isin(['total', 'others'])]

    # Define categories
    benchmark = {f"top-{n}-benchmark" for n in top_n_list}
    top_rows = {f"top-{n}" for n in top_n_list}
    total_rows = {'total'}
    others_rows = {'others'}

    #selected_insurers = [item for sublist in selected_insurers for item in (sublist if isinstance(sublist, list) else [sublist])]



    group_columns = [col for col in df.columns if col not in ['insurer', 'value']]

    #result_df = df.copy()

    for n in top_n_list:
        # Group by group_columns and get top N values for each group
        df_top_n = df.groupby(group_columns).apply(lambda x: x.nlargest(n, 'value'))

        # Reset index to flatten the resul
        df_top_n = df_top_n.reset_index(drop=True)

        # Sum the top N values
        df_top_n_sum = df_top_n.groupby(group_columns)['value'].sum().reset_index()

        # Add the 'insurer' column with the appropriate label
        df_top_n_sum['insurer'] = f'top-{n}'

        # Concatenate with the result DataFrame
        result_df = pd.concat([df, df_top_n_sum], ignore_index=True)


    # Reorder columns to match original order
    #result_df = result_df.reindex(columns=original_columns)

    df_final = pd.concat([result_df, df_total], ignore_index=True)
    save_df_to_csv(df_final, f"add_top_n_rows.csv")


    return df_final



'''def add_others_rows(df: pd.DataFrame, selected_insurers: List[str], top_n_list: List[int]) -> pd.DataFrame:

    # Remove 'others' from selected_insurers if presen
    logger.warning(f"df unique insurers add_others_rows: {df['insurer'].unique()}")
    #original_columns = df.columns.tolist()
    logger.warning(f"selected insurers add_others_rows: {selected_insurers}")

    # Define categories
    benchmark = {f"top-{n}-benchmark" for n in top_n_list}
    top_rows = {f"top-{n}" for n in top_n_list}
    total_rows = {'total'}
    others_rows = {'others'}

    selected_insurers = [item for sublist in selected_insurers for item in (sublist if isinstance(sublist, list) else [sublist])]


    if any(insurer in others_rows for insurer in selected_insurers):
        # Remove 'others' from selected_insurers if presen

        selected_insurers = [insurer for insurer in selected_insurers if insurer not in others_rows]

        # Define insurers to exclude from 'others' calculation
        insurers_to_exclude = set(selected_insurers) | top_rows | benchmark | total_rows

        # Calculate 'others' rows
        df_others = df[~df['insurer'].isin(insurers_to_exclude)]
        group_columns = [col for col in df_others.columns if col not in ['insurer', 'value']]
        df_others = df_others.groupby(group_columns)['value'].sum().reset_index()

        # If a top-N is selected, subtract its values from others to avoid double counting
        selected_top_n = next((f'top-{n}' for n in top_n_list if f'top-{n}' in selected_insurers or f'top-{n}-benchmark' in selected_insurers), None)
        # Adjust 'others' for selected top-N group if necessary
        if selected_top_n:
            logger.debug(f"Adjusting 'others' for selected top-N group: {selected_top_n}")
            df_top_n = df[df['insurer'] == selected_top_n]
            df_others = df_others.merge(df_top_n[id_columns + ['value']],
                                        on=group_columns, how='left', suffixes=('', '_top_n'))
            df_others['value'] = df_others['value'] - df_others['value_top_n'].fillna(0)
            df_others = df_others.drop(columns=['value_top_n'])

        df_others['insurer'] = 'others'
        # Remove rows where 'value' is 0 or negative after subtraction
        df_others = df_others[df_others['value'] > 0]

        result_df = pd.concat([df, df_others], ignore_index=True)
    else:
        result_df = df
    #result_df = result_df.reindex(columns=original_columns)
    save_df_to_csv(result_df, f"add_others_rows.csv")

    return result_df
'''

