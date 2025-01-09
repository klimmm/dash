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


from data_process.data_utils import default_insurer_options, save_df_to_csv, log_dataframe_info, category_structure, insurer_name_map, strip_metric_suffixes, get_required_metrics

from constants.filter_options import METRICS, base_metrics, calculated_metrics, calculated_ratios, calculated_metrics_options, calculated_ratio_options


from logging_config import setup_logging, set_debug_level, DebugLevels, get_logger, debug_log, intensive_debug_log, custom_profile

logger = get_logger(__name__)



#@profile
def get_processed_df(
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_n_list: List[int],
    show_data_table: bool,
    selected_metrics: List[str],
    base_metrics: Set[str],
    calculated_metrics_options: Set[str],
    num_periods: int,
    period_type: str

) -> pd.DataFrame:

    logger.debug("Started get_processed_dataframe function")

    logger.debug(f"Unique insurers df before get_processed_df: {df['insurer'].unique().tolist()}")


    #if show_data_table or any(insurer.startswith(("top")) for insurer in selected_insurers):

    #    df = process_insurers_data(df, selected_insurers, top_n_list, show_data_table, selected_metrics)

    logger.warning(f"Unique insurers df process_insurers_data: {df['insurer'].unique().tolist()}")
    logger.warning(f"Unique metric before add_market_share_rows: {df['metric'].unique().tolist()}")
    logger.warning(f"selected metrics before add_market_share_rows: {selected_metrics}")
    logger.warning(f"show_data_table before add_market_share_rows: {show_data_table}")

    if show_data_table or any(metric.endswith(("market_share", "market_share_q_to_q_change")) for metric in selected_metrics):

        df = add_market_share_rows(df, selected_insurers, selected_metrics, show_data_table)

    required_metrics = get_required_metrics(
        selected_metrics,
        calculated_ratios
    )
    logger.debug(f"required_metrics in procesds_df: {required_metrics}")
    logger.debug(f"Unique metric before add_averages_and_ratios: {df['metric'].unique().tolist()}")

    if set(required_metrics) - base_metrics:

        df = add_averages_and_ratios(df, required_metrics)

    logger.debug(f"Unique metric after add_averages_and_ratios: {df['metric'].unique().tolist()}")

    if show_data_table or any(metric.endswith(("q_to_q_change")) for metric in selected_metrics):

        df = add_growth_rows_long(df, selected_insurers, show_data_table, num_periods, period_type)

    logger.debug(f"Unique metric after add_growth_rows_long: {df['metric'].unique().tolist()}")



    save_df_to_csv(df, f"process_dataframe.csv")
    logger.debug(f"Unique insurers df after get_processed_df: {df['insurer'].unique().tolist()}")
    logger.debug("Finished processd df function")

    return df


#@custom_profile
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
            logger.debug(f"Unique insurers df before benchmark calculation: {end_quarter_df['insurer'].unique().tolist()}")

            for n in top_n_list:
                benchmark_insurers_list = end_quarter_df.groupby('insurer')['value'].sum().nlargest(n).index.tolist()
                df_benchmark_n = df[df['insurer'].isin(benchmark_insurers_list)]
                df_benchmark_n = df_benchmark_n.groupby(group_columns)['value'].sum().reset_index()
                df_benchmark_n['insurer'] = f'top-{n}-benchmark'
                dataframes_to_concat.append(df_benchmark_n)

        # Calculate others rows
        if any(insurer in others_rows for insurer in selected_insurers) and 'others' not in df['insurer'].unique():
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




#@custom_profile
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



        # Start with basic validation
        if df.empty:
            logger.debug("Empty DataFrame provided")
            return df

        required_cols = {'insurer', 'value', 'metric'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")

        logger.debug(f"Processing DataFrame with {len(df):,} rows")
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


        logger.debug(f"Added {len(new_metrics)} new market share metrics")
        logger.debug(f"New market share metrics: {new_metrics}")
        logger.debug(f"Unique metric df after market sharee: {result['metric'].unique().tolist()}")



        return resul

    except Exception as e:
        logger.error(f"Error in market share calculation: {str(e)}")
        raise



#@custom_profile
def add_averages_and_ratios(
    df: pd.DataFrame,
    required_metrics: List[str]
) -> pd.DataFrame:
    """

    """
    logger.debug(f"Unique metric df before add_averages_and_ratios: {df['metric'].unique().tolist()}")

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

    def transform_metrics(data: pd.DataFrame) -> pd.DataFrame:
        """Transform metrics in-place using vectorized operations."""
        for metric, transform_func in METRIC_GROUPS['transform'].items():
            if metric in required_metrics:
                mask = data['metric'] == metric
                data.loc[mask, 'value'] = transform_func(data.loc[mask, 'value'])
        return data

    def calculate_ratios(pivot_df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all required ratios efficiently."""
        results = {}
        for group in ['averages', 'ratios']:
            for metric, (deps, formula) in METRIC_GROUPS[group].items():
                if metric in required_metrics:
                    try:
                        if all(dep in pivot_df.columns for dep in deps):
                            results[metric] = formula(pivot_df)
                            logger.debug(f"Calculated {metric} successfully")
                    except Exception as e:
                        logger.error(f"Error calculating {metric}: {str(e)}")
        return results

    try:
        # Copy input DataFrame and transform metrics
        result_df = transform_metrics(df.copy())

        # Calculate complex ratios if needed
        calc_metrics = [m for m in required_metrics if any(m in group
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



#@custom_profile
def add_growth_rows_long(
    df: pd.DataFrame,
    selected_metrics: List[str],
    show_data_table: bool,

    num_periods: int = 2,
    period_type: str = 'previous_quarter'
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
        logger.debug(f"Using group columns: {group_cols}")

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
        if show_data_table:

            num_periods_growth = num_periods - 1

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

        logger.debug(f"Added growth metrics for {len(growth_df['metric'].unique())} metrics")
        logger.debug(f"Final DataFrame shape: {result.shape}")

        return resul

    except Exception as e:
        logger.error(f"Error in growth calculation: {str(e)}")
        raise
