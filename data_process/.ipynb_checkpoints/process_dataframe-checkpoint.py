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
from data_process.insurer_options import get_insurer_options, get_insurers_for_ranking


from data_process.data_utils import default_insurer_options, save_df_to_csv, log_dataframe_info, category_structure, insurer_name_map

from constants.filter_options import METRICS, base_metrics, calculated_metrics, calculated_ratios, calculated_metrics_options


from logging_config import setup_logging, set_debug_level, DebugLevels, get_logger, debug_log, intensive_debug_log, custom_profile

logger = get_logger(__name__)

'''    logger.debug(f"top_n_insurers: {top_n_insurers}")
    logger.info(f"compare_options: {compare_options}")
    logger.info(f"insurer_options: {insurer_options}")
    logger.debug(f"unique insurers before process insurers data: {df['insurer'].unique().tolist()}")
    logger.debug(f"unique insurers: {df['insurer'].unique().tolist()}")
    logger.debug(f"metric unique: {df['metric'].unique().tolist()}")
    logger.debug(f"red_metrics: {required_metrics}")
    #df = optimize_dtypes(df)

    #logger.debug(f"Unique insurers df before process_dataframe: {df['insurer'].unique().tolist()}")
    #logger.debug(f"uniqu values in year quarter before process_dataframe{df['year_quarter'].unique().tolist()}")

    logger.info(f"main_insurer start of process dataframe: {main_insurer}")
    logger.info(f"selected_insurers start of process dataframe: {selected_insurers}")
    logger.debug(f"number_of_insurers e: {number_of_insurers}")

    logger.info(f"selected_metrics start of process dataframe: {selected_metrics}")
    logger.debug(f"unique insurers after process insurers data: {df['insurer'].unique().tolist()}")
    logger.debug(f"unique insurers: {df['insurer'].unique().tolist()}")

    '''


@custom_profile
def get_processed_dataframe(
    df: pd.DataFrame,
    premium_loss_selection: List[str],
    selected_metrics: List[str],
    selected_linemains: List[str],
    period_type: str,
    start_quarter: str,
    end_quarter: str,
    num_periods: int,
    quarter_value: int,
    chart_columns: List[str] = None,
    show_data_table: bool = False,
    main_insurer: List[str] = None,
    selected_insurers: List[str] = None,
    number_of_insurers: int = None,
    top_n_list: List[int] = None,
    top_n_insurers: List[int] = None,
    reinsurance_form: Optional[Any] = None,
    reinsurance_geography: Optional[Any] = None,
    reinsurance_type: Optional[Any] = None
) -> pd.DataFrame:

    logger.debug("Started get_processed_dataframe function")


    required_metrics = get_required_metrics(
        selected_metrics, premium_loss_selection, calculated_metrics, calculated_ratios, base_metrics)
    logger.warning(f"required_metrics: {required_metrics}")


    df = (
        df
        .pipe(
            combined_filter_function,
            show_data_table=show_data_table,
            chart_columns=chart_columns,

            reinsurance_form=reinsurance_form,
            reinsurance_geography=reinsurance_geography,
            reinsurance_type=reinsurance_type,
            selected_linemains=selected_linemains,
            required_metrics=required_metrics,
        )
        .pipe(
            filter_by_date_range_and_period_type,
            period_type=period_type,
            start_quarter=start_quarter,
            end_quarter=end_quarter,
            quarter_value=quarter_value,
            num_periods=num_periods
        )
        .pipe(
            add_calculated_metrics,
            selected_metrics=selected_metrics
        )
    )

    if show_data_table:
        selected_insurers = get_insurers_for_ranking(df, number_of_insurers, top_n_list, selected_metrics, base_metrics)

    insurer_options, compare_options = get_insurer_options(df, main_insurer, top_n_list, selected_metrics, base_metrics)


    df = (
        df
        .pipe(
            process_insurers_data,
            selected_insurers,
            top_n_list,
            show_data_table,
            selected_metrics
        )

        .pipe(
            add_market_share_rows,
            selected_insurers,
            selected_metrics,
            show_data_table
        )
        .pipe(
            add_averages_and_ratios,
            selected_metrics,
            base_metrics,
            calculated_metrics_options
        )
        .pipe(
            add_growth_rows_long,
            selected_metrics,
            num_periods,
            period_type,
        )


    )


    save_df_to_csv(df, f"process_dataframe.csv")
    logger.debug(f"Unique insurers df after process_dataframe: {df['insurer'].unique().tolist()}")
    logger.debug("Finished get_processed_dataframe function")

    return df, insurer_options, compare_options, selected_insurers


def get_required_metrics(
    selected_metrics: List[str],
    premium_loss_selection: List[str],
    calculated_metrics: Dict[str, List[str]],
    calculated_ratios: Dict[str, List[str]],
    base_metrics: Set[str]
) -> Set[str]:
    logger.debug("Starting get_required_metrics function")
    logger.debug(f"Function get_required_metrics called with selected metrics: {selected_metrics}")

    def update_required_metrics(selected_metrics, calculated_metrics, base_metrics):
        required_metrics = set(selected_metrics)
        metrics_to_process = list(selected_metrics)
        processed_metrics = set()

        # Add base metrics that are prefixes of selected metrics
        for selected_metric in selected_metrics:
            for base_metric in base_metrics:
                if selected_metric.startswith(base_metric):
                    logger.debug(f"Found base metric {base_metric} as prefix of {selected_metric}")
                    required_metrics.add(base_metric)
                    if base_metric not in processed_metrics:
                        metrics_to_process.append(base_metric)

        while metrics_to_process:
            current_metric = metrics_to_process.pop(0)
            if current_metric in processed_metrics:
                continue

            processed_metrics.add(current_metric)

            logger.debug(f"Processing metric: {current_metric}")

            for calc_metric, base_metrics_for_calc in calculated_metrics.items():
                if calc_metric in current_metric or current_metric.startswith(calc_metric):
                    logger.debug(f"Found related calc_metric: {calc_metric}")
                    new_metrics = set(base_metrics_for_calc) - required_metrics
                    required_metrics.update(new_metrics)
                    metrics_to_process.extend(new_metrics)

                    if current_metric.startswith(calc_metric):
                        required_metrics.add(calc_metric)
                        if calc_metric not in processed_metrics:
                            metrics_to_process.append(calc_metric)

            logger.debug(f"Current required_metrics: {required_metrics}")
            logger.debug(f"Metrics left to process: {metrics_to_process}")

        return required_metrics

    # Use the function with base_metrics parameter
    required_metrics = update_required_metrics(selected_metrics, calculated_metrics, base_metrics)

    logger.info(f"Final required_metrics: {required_metrics}")
    '''for selected_metric in selected_metrics:

        for base_metric in base_metrics:
            if selected_metric.startswith(base_metric):
                required_metrics.add(base_metric)'''

    if 'direct' not in premium_loss_selection:
        required_metrics.difference_update(['direct_premiums', 'direct_losses'])
    if 'inward' not in premium_loss_selection:
        required_metrics.difference_update(['inward_premiums', 'inward_losses'])

    logger.debug(f"List of required metrics: {required_metrics}")
    logger.debug("Finished get_required_metrics function")
    required_metrics = list(required_metrics)
    logger.debug(f"List of required metrics: {required_metrics}")

    return required_metrics


def combined_filter_function(
    df: pd.DataFrame,
    show_data_table: bool = False,
    chart_columns: List[str] = None,
    line_types: Optional[List[str]] = None,
    reinsurance_form: Optional[List[str]] = None,
    reinsurance_geography: Optional[List[str]] = None,
    reinsurance_type: Optional[List[str]] = None,
    selected_linemains: Optional[List[str]] = None,
    required_metrics: Optional[List[str]] = None
) -> pd.DataFrame:

    logger.debug("Starting comprehensive insurance filter function")
    logger.debug(f"Initial columns: {df.columns}")
    logger.debug(f"Input parameters: {locals()}")
    logger.debug(f"Unique lines in df before filtering: {df['linemain'].unique().tolist()}")
    logger.debug(f" required_metrics: {required_metrics}")

    # Define all filters
    filters = {
        'line_type': line_types,
        'reinsurance_form': reinsurance_form,
        'reinsurance_geography': reinsurance_geography,
        'reinsurance_type': reinsurance_type,
        'linemain': selected_linemains,
        'metric': required_metrics
    }

    # Process all standard filters
    for column, values in filters.items():
        if values and column in df.columns:
            if not isinstance(values, (list, tuple, pd.Series)):
                logger.info(f"Invalid type for {column}: {type(values)}. Expected list-like object. Skipping this filter.")
                continue
            if len(values) == 0:
                logger.info(f"Empty list provided for {column}. Skipping this filter.")
                continue
            df = df[df[column].isin(values)]
            logger.debug(f"Applied filter for '{column}' with values: {values}")
            logger.debug(f"DataFrame shape after filtering {column}: {df.shape}")

    # Drop the 'line_type' column if it exists
    if 'line_type' in df.columns:
        df = df.drop(columns=['line_type'])
        logger.debug("Dropped 'line_type' column")

    logger.debug(f"show_data_table: {show_data_table}")
    if (chart_columns and 'linemain' not in chart_columns) or show_data_table:
        group_columns = [col for col in df.columns if col not in ['linemain', 'value']]
        df = df.groupby(group_columns)['value'].sum().reset_index()
        df['linemain'] = 'all_lines'


    #result_df = pd.concat([df, df_all_lines], ignore_index=True)


    if df.empty:
        logger.info("Final DataFrame is empty after all filtering operations")
    else:
        logger.debug("Finished comprehensive insurance filter function")
        logger.debug(f"Final columns: {df.columns}")
        logger.debug(f"Final DataFrame shape combined_filter_function: {df.shape}")
        logger.debug(f"Unique quarters in df after combined_filter_function: {df['year_quarter'].unique().tolist() if 'year_quarter' in df.columns else 'N/A'}")
        logger.debug(f"Unique lines in df after combined_filter_function: {df['linemain'].unique().tolist()}")
        logger.debug(f"Unique metric in df after combined_filter_function: {df['metric'].unique().tolist()}")

    return df


#@profile
def filter_by_date_range_and_period_type(
    df: pd.DataFrame,
    period_type: str,
    start_quarter: str,
    end_quarter: str,
    quarter_value: int,
    num_periods: int,
) -> pd.DataFrame:

    logger.debug("Started filter_by_date_range_and_period_type function")
    save_df_to_csv(df, f"sample.csv")

    logger.debug(f"period_type: {period_type}")
    logger.debug(f"start_quarter: {start_quarter}")
    logger.debug(f"end_quarter: {end_quarter}")
    logger.debug(f"num_periods: {num_periods}")
    logger.debug(f"df index: {df.index}")
    logger.debug(f"df dtypes: {df.dtypes}")

    logger.debug(f"columns before: filter_by_date_range_and_period_type {df.head()}")
    if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
        df['year_quarter'] = pd.to_datetime(df['year_quarter'], errors='coerce')
        if df['year_quarter'].isnull().any():
            logger.debug("Some 'year_quarter' entries could not be converted to datetime.")


    #logger.debug(f"uniqu values in year quarter before filter{df['year_quarter'].unique().tolist()}")

    end_quarter_date = pd.to_datetime(end_quarter)
    start_quarter_date = pd.to_datetime(start_quarter)
    logger.debug(f"end_quarter_datee {end_quarter_date}")

    df = df[(df['year_quarter'] <= end_quarter_date) & (df['year_quarter'] >= start_quarter_date)]
    df = df.copy()

    df.loc[:, 'year'] = df['year_quarter'].dt.year
    df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter

    grouping_cols = [col for col in df.columns if col not in {'year_quarter', 'value', 'year', 'quarter'}]


    end_quarter_num = end_quarter_date.quarter


    if period_type == 'previous_quarter':
        pass

    elif period_type == 'same_q_last_year':

        df = df[df['year_quarter'].dt.quarter == end_quarter_num]


    elif period_type in ['same_q_last_year_ytd', 'previous_q_mat', 'same_q_last_year_mat', 'cumulative_sum']:



        if period_type == 'same_q_last_year_ytd':


            df = (df[df['year_quarter'].dt.quarter <= quarter_value]
                  #.sort_values(grouping_cols + ['year_quarter'])
                  .assign(year=lambda x: x['year_quarter'].dt.year,
                          ytd_value=lambda x: x.groupby(['year'] + grouping_cols)['value'].cumsum())
                  .assign(value=lambda x: x['ytd_value'])
                  .drop(columns=['ytd_value'])
                  .loc[lambda x: x['year_quarter'].dt.quarter == quarter_value]
                  .reset_index(drop=True))


        elif period_type in ['previous_q_mat', 'same_q_last_year_mat']:

            df = df.sort_values(grouping_cols + ['year_quarter'])
            df.set_index('year_quarter', inplace=True)

            # Perform rolling sum calculation
            df['value'] = df.groupby(grouping_cols)['value'].transform(
                lambda x: x.sort_index().rolling(window='365D', min_periods=1).sum()
            )

            df.reset_index(inplace=True)

            if period_type == 'same_q_last_year_mat':
                df = df[df['quarter'] == end_quarter_num]

        elif period_type == 'cumulative_sum':
            df = df[df['year_quarter'] >= start_quarter_date]

            df['cumsum'] = df.groupby(grouping_cols)['value'].cumsum()
            df['value'] = df['cumsum']
            df = df.drop(columns=['cumsum'])

    years_to_keep = sorted(df['year'].unique(), reverse=True)[:num_periods + 1]
    df = df[df['year'].isin(years_to_keep)]

    df = df.drop(columns=['year', 'quarter'])

    logging.debug("Finished filter_by_date_range_and_period_type function")
    logging.debug(f"Unique quarters in df after filter_by_period_type: {df['year_quarter'].unique().tolist()}")
    save_df_to_csv(df, f"after filter_by_date.csv")

    return df




def process_insurers_data(df: pd.DataFrame, selected_insurers: List[str], top_n_list: List[int], show_data_table: bool, selected_metrics: List[int]) -> pd.DataFrame:
    # Define categories

    logger.debug(f"Unique insurers df before process insurers: {df['insurer'].unique().tolist()}")
    logger.debug(f"selected_insurers: {selected_insurers}")

    benchmark_metric = 'direct_premiums'
    benchmark_insurers = {f"top-{n}-benchmark" for n in top_n_list}
    top_n_rows = {f"top-{n}" for n in top_n_list}
    total_rows = {'total'}
    others_rows = {'others'}


    group_columns = [col for col in df.columns if col not in ['insurer', 'value']]

    dataframes_to_concat = []

    logger.debug(f"main_insurer: {selected_insurers[0]}")
    logger.debug(f"selected_insurers: {selected_insurers}")


    # Calculate top_n rows
    if len(df['insurer'].unique()) > 1:

        insurers_to_exclude = top_n_rows | benchmark_insurers | others_rows | total_rows
        df_top_n_row = df[~df['insurer'].isin(insurers_to_exclude)]
        logger.debug(f"Unique insurers df afterfilter to exculde for top n calc: {df['insurer'].unique().tolist()}")

        for n in top_n_list:
            df_top_n_row = df.groupby(group_columns).apply(lambda x: x.nlargest(n, 'value'))
            df_top_n_row = df_top_n_row.reset_index(drop=True)
            df_top_n_row = df_top_n_row.groupby(group_columns)['value'].sum().reset_index()
            df_top_n_row['insurer'] = f'top-{n}'
            dataframes_to_concat.append(df_top_n_row)
            logging.debug(f"dataframes_to_concat: {dataframes_to_concat}")


    # Calculate total rows
    if 'total' not in df['insurer'].unique():
        insurers_to_exclude = top_n_rows | benchmark_insurers | others_rows
        df_total = df[~df['insurer'].isin(insurers_to_exclude)]
        df_total = df_total.groupby(group_columns)['value'].sum().reset_index()
        df_total['insurer'] = 'total'
        dataframes_to_concat.append(df_total)
        #logging.debug(f"dataframes_to_concat: {dataframes_to_concat}")
    logger.debug(f"selected_insurers: {selected_insurers}")

    # Calculate benchmark rows

    if selected_insurers is not None:
        if any(insurer in benchmark_insurers for insurer in selected_insurers):
            insurers_to_exclude = set(selected_insurers[0]) | benchmark_insurers | top_n_rows | total_rows | others_rows
            end_quarter_dt = df['year_quarter'].max()

            end_quarter_df = df[
                (~df['insurer'].isin(insurers_to_exclude)) &
                (df['year_quarter'] == end_quarter_dt) &
                (df['metric'] == benchmark_metric)
            ]

            for n in top_n_list:
                benchmark_insurers_list = end_quarter_df.groupby('insurer')['value'].sum().nlargest(n).index.tolist()
                df_benchmark_n = df[df['insurer'].isin(benchmark_insurers_list)]
                df_benchmark_n = df_benchmark_n.groupby(group_columns)['value'].sum().reset_index()
                df_benchmark_n['insurer'] = f'top-{n}-benchmark'
                dataframes_to_concat.append(df_benchmark_n)

        # Calculate others rows
        if any(insurer in others_rows for insurer in selected_insurers):
            #selected_insurers = [insurer for insurer in selected_insurers if insurer not in others_rows]
            insurers_to_exclude = set(selected_insurers) | top_n_rows | benchmark_insurers | total_rows
            df_others = df[~df['insurer'].isin(insurers_to_exclude)]
            df_others = df_others.groupby(group_columns)['value'].sum().reset_index()

            selected_top_n = next((f'top-{n}' for n in top_n_list if f'top-{n}' in selected_insurers or f'top-{n}-benchmark' in selected_insurers), None)

            if selected_top_n:
                df_top_n = df[df['insurer'] == selected_top_n]
                df_others = df_others.merge(df_top_n[group_columns + ['value']],
                                            on=group_columns, how='left', suffixes=('', '_top_n'))
                df_others['value'] = df_others['value'] - df_others['value_top_n'].fillna(0)
                df_others = df_others.drop(columns=['value_top_n'])

            df_others['insurer'] = 'others'
            df_others = df_others[df_others['value'] > 0]
            dataframes_to_concat.append(df_others)

    insurers_to_exclude_original_df = benchmark_insurers | top_n_rows | others_rows
    original_df = df[~df['insurer'].isin(insurers_to_exclude_original_df)]
    dataframes_to_concat.insert(0, original_df)  # Add original_df at the beginning of the lis

    # Concatenate all DataFrames
    concat_df = pd.concat(dataframes_to_concat, ignore_index=True)
    logger.debug(f"Unique insurers in concat_df: {concat_df['insurer'].unique().tolist()}")


    if not show_data_table:

        if not any(metric.endswith(("market_share", "market_share_q_to_q_change")) for metric in selected_metrics):
            insurers_to_keep = selected_insurers
        else:
            insurers_to_keep = (selected_insurers or []) + list(total_rows)

    else:
            insurers_to_keep = (selected_insurers or []) + list(top_n_rows) + list(total_rows)


    logger.debug(f"selected_insurers: {selected_insurers}")
    logger.debug(f"insurers_to_keep: {insurers_to_keep}")

    result_df = concat_df[concat_df['insurer'].isin(insurers_to_keep)]
    logger.debug(f"Unique insurers df after process insurers: {result_df['insurer'].unique().tolist()}")
    logger.debug(f"Unique values df after process_insurers: {result_df['value'].unique().tolist()}")
    save_df_to_csv(df, f"after process_insurance.csv")

    return result_df



#@profile

#@custom_profile
#@profile

def add_calculated_metrics(df: pd.DataFrame, selected_metrics: List[str]) -> pd.DataFrame:
    logger.debug("Starting add_calculated_metrics function")
    logger.debug(f"Input DataFrame shape: {df.shape}")
    logger.debug(f"Selected metrics: {selected_metrics}")
    logger.debug(f"Unique metrics in df before dd_calculated_metrics function: {df['metric'].unique().tolist()}")
    logger.debug(f"df index: {df.index}")
    logger.debug(f"df dtypes: {df.dtypes}")
    # Identify grouping columns




    required_metrics = set(selected_metrics)
    calculated_metrics.update(calculated_ratios)
    logger.debug(f"Initial required_metrics: {required_metrics}")
    logger.debug(f"calculated_metrics : {calculated_metrics}")

    for selected_metric in selected_metrics:
        logger.debug(f"Processing selected_metric: {selected_metric}")

        for calc_metric, base_metrics in calculated_metrics.items():
            logger.debug(f"Checking calc_metric: {calc_metric} with base_metrics: {base_metrics}")

            if calc_metric in selected_metric:
                logger.debug(f"calc_metric '{calc_metric}' found in selected_metric '{selected_metric}'")
                required_metrics.update(base_metrics)
                logger.debug(f"Updated required_metrics: {required_metrics}")

            if selected_metric.startswith(calc_metric):
                logger.debug(f"selected_metric '{selected_metric}' starts with calc_metric '{calc_metric}'")
                required_metrics.add(calc_metric)  # Add ratio_metric to the se
                required_metrics.update(base_metrics)
                logger.debug(f"Updated required_metrics: {required_metrics}")

    logger.debug(f"Final required_metrics: {required_metrics}")




    grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
    logger.debug(f"Grouping columns: {grouping_cols}")




    def calculate_for_group(group):
        metrics_dict = dict(zip(group['metric'], group['value']))
        new_rows = []
        logger.debug("Starting calculate_for_grous function")



        metrics_to_calculate = {
            'net_balance': lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0),
            'total_premiums': lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0),
            'net_premiums': lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0),
            'total_losses': lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0),
            'net_losses': lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0),
            'gross_result': lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('direct_losses', 0) - d.get('inward_losses', 0),
            'net_result': lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)) -
                                    (d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0))
        }



        for metric, calculation in metrics_to_calculate.items():
            if metric in required_metrics:
                logger.debug(f"Current metrics for {metric} calculation: {metrics_dict}")
                try:
                    result = calculation(metrics_dict)

                    # Create a new row with all columns filled
                    new_row = {col: group[col].iloc[0] for col in grouping_cols}
                    new_row.update({'metric': metric, 'value': result})
                    new_rows.append(new_row)

                    #logger.debug(f"Calculated {metric} successfully")

                    # Log if any required metrics were missing
                    missing = [key for key in calculation.__code__.co_varnames if key not in metrics_dict]
                    if missing:
                        logger.debug(f"Calculated {metric} with missing metrics treated as 0: {missing}")
                except Exception as e:
                    logger.error(f"Error calculating {metric}: {str(e)}")

        if new_rows:
            return pd.concat([group, pd.DataFrame(new_rows)], ignore_index=True)
        #logger.debug("Finishing calculate_for_grous function")

        return group

    # Apply calculations to each group
    result_df = df.groupby(grouping_cols).apply(calculate_for_group).reset_index(drop=True)
    #result_df = pd.concat(calculate_for_group(group) for _, group in df.groupby(grouping_cols))

    logger.debug(f"Resulting DataFrame shape: {result_df.shape}")
    logger.debug(f"Unique metrics in result_df: {result_df['metric'].unique().tolist()}")
    logger.debug("Finished add_calculated_metrics function")
    save_df_to_csv(result_df, f"calculate metricss.csv")
    logger.debug(f"Unique values df after calc metricss: {result_df['value'].unique().tolist()}")

    return result_df



def add_market_share_rows(
    df: pd.DataFrame,
    selected_insurers: List[str],
    selected_metrics: List[str],
    show_data_table: bool,
    total_insurer: str = 'total',
    suffix: str = '_market_share'
) -> pd.DataFrame:
    """
    Efficiently calculates market share metrics for insurance data.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame containing insurance metrics
    total_insurer : str, default='total'
        Identifier for the total/market insurer in the data
    suffix : str, default='_market_share'
        Suffix to append to metric names for market share columns

    Returns:
    --------
    pd.DataFrame
        DataFrame with additional market share metrics
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Unique metric df before market sharee: {df['metric'].unique().tolist()}")

    def get_group_cols(df: pd.DataFrame) -> List[str]:
        """Efficiently extract grouping columns."""
        return [col for col in df.columns if col not in {'insurer', 'value'}]

    def calculate_market_shares(
        group: pd.DataFrame,
        total_value: float,
    ) -> Optional[pd.DataFrame]:
        """Calculate market shares for a group efficiently."""


        if len(group) == 0:
            return None

        group = group.copy()
        group['value'] = (group['value'] / total_value).fillna(0)
        group['metric'] = group['metric'] + suffix
        return group

    try:

        if not any(metric.endswith(("market_share", "market_share_q_to_q_change")) for metric in selected_metrics):
            logger.debug("not market share in selected metrcis")
            return df

        # Start with basic validation
        if df.empty:
            logger.debug("Empty DataFrame provided")
            return df

        required_cols = {'insurer', 'value', 'metric'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        logger.info(f"Processing DataFrame with {len(df):,} rows")
        metrics_before: Set[str] = set(df['metric'].unique())

        # Get grouping columns once
        group_cols = get_group_cols(df)
        logger.debug(f"Using group columns: {group_cols}")

        # Extract totals efficiently
        total_mask = df['insurer'] == total_insurer
        totals = (df[total_mask]
                 .set_index(group_cols)
                 ['value']
                 .to_dict())

        if not totals:
            logger.debug(f"No rows found for total_insurer '{total_insurer}'")
            return df

        # Process groups in chunks for memory efficiency
        chunk_size = 100_000  # Adjust based on available memory
        result_dfs = [df]  # Start with original data

        for chunk_start in range(0, len(df), chunk_size):
            chunk = df.iloc[chunk_start:chunk_start + chunk_size]

            # Group the chunk and calculate market shares
            grouped = chunk.groupby(group_cols, observed=True)

            market_shares = []
            for group_key, group in grouped:
                if group_key not in totals:
                    continue

                total_value = totals[group_key]
                if total_value == 0:
                    continue

                result = calculate_market_shares(
                    group,
                    total_value,
                )

                if result is not None:
                    market_shares.append(result)

            if market_shares:
                result_dfs.append(pd.concat(market_shares, ignore_index=True))

        # Combine results efficiently
        result = pd.concat(result_dfs, ignore_index=True)

        # Sort only if the DataFrame is not too large
        if len(result) < 1_000_000:
            result.sort_values(by=group_cols + ['insurer'], inplace=True)
            result.reset_index(drop=True, inplace=True)

        metrics_after: Set[str] = set(result['metric'].unique())
        new_metrics = metrics_after - metrics_before

        if not show_data_table:
            result = result[result['insurer'].isin(selected_insurers)]


        logger.info(f"Added {len(new_metrics)} new market share metrics")
        logger.debug(f"New market share metrics: {new_metrics}")
        logger.debug(f"Unique metric df after market sharee: {result['metric'].unique().tolist()}")



        return resul

    except Exception as e:
        logger.error(f"Error in market share calculation: {str(e)}")
        raise




def add_averages_and_ratios(
    df: pd.DataFrame,
    selected_metrics: List[str],
    base_metrics: Set[str],
    calculated_metrics_options: Set[str]
) -> pd.DataFrame:
    """
    Calculates insurance metrics ratios and transforms existing metrics efficiently.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with columns ['year_quarter', 'metric', 'linemain', 'insurer', 'value']
    - selected_metrics (List[str]): List of metric names to calculate or transform

    Returns:
    - pd.DataFrame: DataFrame with additional rows for calculated ratios and transformed metrics
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Unique metric df before add_averages_and_ratios: {df['metric'].unique().tolist()}")

    if not set(selected_metrics) - base_metrics - calculated_metrics_options:
        return df

    # Pre-process selected metrics to remove duplicates and identify related metrics
    def identify_relevant_metrics(metrics: List[str]) -> Set[str]:
        """Identify all relevant metrics including those that start with calculated ratios."""
        relevant_metrics = set(metrics)
        calculated_ratios = set()

        # Build set of calculated ratios from metric groups
        for group in ['averages', 'ratios']:
            calculated_ratios.update(METRIC_GROUPS[group].keys())

        # Add base metrics that are needed for selected prefixed metrics
        for metric in metrics:
            for ratio_metric in calculated_ratios:
                if metric.startswith(ratio_metric):
                    relevant_metrics.add(ratio_metric)
                    logger.info(f"Added base metric {ratio_metric} for selected metric {metric}")

        logger.debug(f"relevant_metrics {relevant_metrics}")

        return relevant_metrics


    # Create metric groups for better organization and dependency tracking
    METRIC_GROUPS = {
        'transform': {
            'sums_end': lambda x: x / 10,
            'new_sums': lambda x: x / 10,
            'new_contracts': lambda x: x * 1000,
            'contracts_end': lambda x: x * 1000,
            'claims_settled': lambda x: x * 1000,
            'claims_reported': lambda x: x * 1000
        },
        'averages': {
            'average_sum_insured': (['sums_end', 'contracts_end'],
                                  lambda df: df['sums_end'] / df['contracts_end'] / 1_000),
            'average_new_sum_insured': (['new_sums', 'new_contracts'],
                                      lambda df: df['new_sums'] / df['new_contracts'] / 1_000),
            'average_new_premium': (['direct_premiums', 'new_contracts'],
                                  lambda df: df['direct_premiums'] / df['new_contracts']),
            'average_loss': (['direct_losses', 'claims_settled'],
                           lambda df: df['direct_losses'] / df['claims_settled'])
        },
        'ratios': {
            'ceded_premiums_ratio': (['ceded_premiums', 'total_premiums'],
                                   lambda df: df['ceded_premiums'].fillna(0) / df['total_premiums']),
            'ceded_losses_ratio': (['ceded_losses', 'total_losses'],
                                 lambda df: df['ceded_losses'].fillna(0) / df['total_losses']),
            'ceded_losses_to_ceded_premiums_ratio': (['ceded_losses', 'ceded_premiums'],
                                                    lambda df: df['ceded_losses'].fillna(0) / df['ceded_premiums'].fillna(1)),
            'gross_loss_ratio': (['direct_losses', 'inward_losses', 'direct_premiums', 'inward_premiums'],
                               lambda df: (df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0)) /
                                        (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0))),
            'net_loss_ratio': (['direct_losses', 'inward_losses', 'ceded_losses',
                               'direct_premiums', 'inward_premiums', 'ceded_premiums'],
                              lambda df: ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0) -
                                         df['ceded_losses'].fillna(0)) /
                                        (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0) -
                                         df['ceded_premiums'].fillna(0)))),
            'effect_on_loss_ratio': (['direct_losses', 'inward_losses', 'ceded_losses',
                                     'direct_premiums', 'inward_premiums', 'ceded_premiums'],
                                    lambda df: ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0)) /
                                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0))) -
                                             ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0) -
                                               df['ceded_losses'].fillna(0)) /
                                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0) -
                                               df['ceded_premiums'].fillna(0)))),
            'ceded_ratio_diff': (['ceded_losses', 'total_losses', 'ceded_premiums', 'total_premiums'],
                                lambda df: (df['ceded_losses'].fillna(0) / df['total_losses']) -
                                         (df['ceded_premiums'].fillna(0) / df['total_premiums']))
        }
    }

    # Process selected metrics to include all relevant base metrics
    selected_metrics = list(identify_relevant_metrics(selected_metrics))
    logger.info(f"Processing {len(selected_metrics)} metrics after including base metrics")

    def get_required_metrics(metric: str) -> Set[str]:
        """Cache and return required input metrics for a given calculated metric."""
        for group in METRIC_GROUPS.values():
            if metric in group:
                return set(group[metric][0]) if isinstance(group[metric], tuple) else set()
        return set()

    def transform_metrics(data: pd.DataFrame) -> pd.DataFrame:
        """Transform metrics in-place using vectorized operations."""
        for metric, transform_func in METRIC_GROUPS['transform'].items():
            if metric in selected_metrics:
                mask = data['metric'] == metric
                data.loc[mask, 'value'] = transform_func(data.loc[mask, 'value'])
        return data

    def calculate_ratios(pivot_df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required ratios efficiently."""
        results = {}
        for group in ['averages', 'ratios']:
            for metric, (deps, formula) in METRIC_GROUPS[group].items():
                if metric in selected_metrics:
                    try:
                        if all(dep in pivot_df.columns for dep in deps):
                            results[metric] = formula(pivot_df)
                            logger.info(f"Calculated {metric} successfully")
                    except Exception as e:
                        logger.error(f"Error calculating {metric}: {str(e)}")
        return results

    try:
        # Copy input DataFrame and transform metrics
        result_df = transform_metrics(df.copy())

        # Calculate complex ratios if needed
        calc_metrics = [m for m in selected_metrics if any(m in group
                       for group in [METRIC_GROUPS['averages'], METRIC_GROUPS['ratios']])]

        if calc_metrics:
            # Pivot data once for all calculations
            index_cols = [col for col in df.columns if col not in ['metric', 'value']]
            pivot_df = result_df.pivot_table(
                values='value',
                index=index_cols,
                columns='metric',
                aggfunc='first'
            ).reset_index()

            # Calculate all ratios
            new_metrics = calculate_ratios(pivot_df)

            # Add calculated ratios to resul
            for metric, values in new_metrics.items():
                new_rows = pd.DataFrame({
                    **{col: pivot_df[col] for col in index_cols},
                    'metric': metric,
                    'value': values
                })
                result_df = pd.concat([result_df, new_rows], ignore_index=True)

        return result_df

    except Exception as e:
        logger.error(f"Fatal error in add_averages_and_ratios: {str(e)}")
        raise




def add_growth_rows_long(
    df: pd.DataFrame,
    selected_metrics: List[str],

    num_periods: int = 2,
    period_type: str = 'previous_quarter',
    num_periods_growth: Optional[int] = None
) -> pd.DataFrame:
    """
    Calculate growth metrics for regular values and market share differences.

    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame with columns: year_quarter, metric, value, and grouping columns
    num_periods : int, default=2
        Number of periods to include in the resul
    period_type : str, default='previous_quarter'
        Type of period comparison
    num_periods_growth : Optional[int]
        Number of periods for growth calculation, if different from num_periods

    Returns:
    --------
    pd.DataFrame
        DataFrame with additional growth metrics
    """

    try:
        logger.debug(f"Unique metric df before add_growth_rows_long: {df['metric'].unique().tolist()}")
        logger.debug(f"selected_metrics: {selected_metrics}")

        if not any(metric.endswith(("q_to_q_change")) for metric in selected_metrics):
            return df


        # Input validation
        if df.empty:
            logger.debug("Empty DataFrame provided")
            return df

        required_cols = {'year_quarter', 'metric', 'value'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        # Convert year_quarter to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
            df['year_quarter'] = pd.to_datetime(df['year_quarter'], errors='coerce')
            invalid_dates = df['year_quarter'].isnull().sum()
            if invalid_dates:
                logger.debug(f"{invalid_dates} year_quarter entries could not be converted to datetime")

        # Get grouping columns
        group_cols = [col for col in df.columns if col not in ['year_quarter', 'metric', 'value']]
        logger.info(f"Using group columns: {group_cols}")

        # Sort data once
        sort_cols = group_cols + ['year_quarter']
        df_sorted = df.sort_values(by=sort_cols).copy()

        # Split metrics by type
        market_share_mask = df_sorted['metric'].str.endswith('market_share')

        # Process regular metrics (not market share)
        regular_metrics = df_sorted[~market_share_mask].copy()
        if len(regular_metrics) > 0:
            # Calculate growth for regular metrics using vectorized operations
            regular_grouped = regular_metrics.groupby(group_cols + ['metric'], observed=True)
            regular_metrics['previous'] = regular_grouped['value'].shift(1)

            # Handle division by zero and invalid values
            epsilon = 1e-9
            regular_metrics['growth'] = np.where(
                regular_metrics['previous'] > epsilon,
                (regular_metrics['value'] - regular_metrics['previous']) / regular_metrics['previous'],
                np.nan
            )

        # Process market share metrics
        market_share_metrics = df_sorted[market_share_mask].copy()
        if len(market_share_metrics) > 0:
            # Calculate absolute differences for market share metrics
            market_share_grouped = market_share_metrics.groupby(group_cols + ['metric'], observed=True)
            market_share_metrics['growth'] = market_share_grouped['value'].diff().fillna(0)

        # Combine processed metrics
        processed_dfs = []
        if len(regular_metrics) > 0:
            growth_regular = regular_metrics.copy()
            growth_regular['metric'] += '_q_to_q_change'
            growth_regular['value'] = growth_regular['growth']
            processed_dfs.append(growth_regular.drop(columns=['growth', 'previous']))

        if len(market_share_metrics) > 0:
            growth_market = market_share_metrics.copy()
            growth_market['metric'] += '_q_to_q_change'
            growth_market['value'] = growth_market['growth']
            processed_dfs.append(growth_market.drop(columns=['growth']))

        growth_df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else pd.DataFrame(columns=df.columns)

        # Filter periods if specified
        if num_periods_growth is not None:
            # Get the most recent periods
            recent_periods = (df_sorted['year_quarter']
                            .drop_duplicates()
                            .sort_values(ascending=False)
                            .iloc[:num_periods])

            recent_growth_periods = (df_sorted['year_quarter']
                                   .drop_duplicates()
                                   .sort_values(ascending=False)
                                   .iloc[:max(num_periods_growth, 1)])

            # Filter original and growth DataFrames
            df_filtered = df_sorted[df_sorted['year_quarter'].isin(recent_periods)].copy()
            growth_filtered = growth_df[growth_df['year_quarter'].isin(recent_growth_periods)].copy()

            # Combine filtered results
            result = pd.concat([df_filtered, growth_filtered], ignore_index=True)
        else:
            # Use all periods
            result = pd.concat([df_sorted, growth_df], ignore_index=True)

        # Final sorting
        result.sort_values(by=sort_cols + ['metric'], inplace=True)
        result.reset_index(drop=True, inplace=True)

        logger.info(f"Added growth metrics for {len(growth_df['metric'].unique())} metrics")
        logger.debug(f"Final DataFrame shape: {result.shape}")

        return resul

    except Exception as e:
        logger.error(f"Error in growth calculation: {str(e)}")
        raise
