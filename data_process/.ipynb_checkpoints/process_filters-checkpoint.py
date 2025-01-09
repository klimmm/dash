# data_process.process_filters

import pandas as pd
import numpy as np
import gc
import logging
import time
from typing import List, Tuple, Dict
from dataclasses import dataclass
# from memory_profiler import profile
from data_process.data_utils import save_df_to_csv, get_required_metrics, map_insurer
from constants.filter_options import (
    BASE_METRICS, CALCULATED_METRICS, CALCULATED_RATIOS
)
from config.logging_config import get_logger
logger = get_logger(__name__)


@dataclass
class MetricsProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    #@profile
    def process_general_filters(
        self,
        df: pd.DataFrame,
        show_data_table: bool,
        premium_loss_selection: List[str],
        selected_metrics: List[str],
        selected_linemains: List[str],
        period_type: str,
        start_quarter: str,
        end_quarter: str,
        num_periods: int,
        line_type: List[str] = None,
        chart_columns: List[str] = None,
        selected_insurers: List[str] = None,
        reinsurance_form: List[str] = None,
        reinsurance_geography: List[str] = None,
        reinsurance_type: List[str] = None,
        number_of_insurers: int = 150,
        top_n_list: List[int] = None,
        main_insurer: str = None
    ) -> Tuple[pd.DataFrame, List[Dict], List[Dict], List[str]]:

        #self.logger.debug(f"Initial DataFrame shape: {df.shape}")
        current_time = time.time()

        logger.debug(f"process_general_filters called, Time: {current_time}")
        start_time = time.perf_counter_ns()  # Nanosecond precision
        try:
            gc.enable()
            # Build mask incrementally without intermediate Series objects
            mask = pd.Series(True, index=df.index)
            # Get required metrics and convert to set once
            required_metrics_set = set(get_required_metrics(
                selected_metrics,
                {**CALCULATED_METRICS, **CALCULATED_RATIOS},
                premium_loss_selection,
                BASE_METRICS
            ))
            logger.debug(f"required_metrics_set: {required_metrics_set}")
            logger.debug(f"metrics unique: {df['metric'].unique()}")
            logger.debug(f"linemain unique: {df['linemain'].unique()}")
            # Apply linemain filter using isin() directly
            mask &= df['linemain'].isin(selected_linemains)
            mask &= df['metric'].isin(required_metrics_set)

            # Handle datetime filtering
            if start_quarter and end_quarter:
                if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
                    df.loc[:, 'year_quarter'] = pd.to_datetime(df['year_quarter'])

                if period_type == 'ytd':
                    # Convert start_quarter to beginning of the year
                    start_quarter_interm = pd.Timestamp(start_quarter).replace(month=1)
                elif period_type in ['mat', 'yoy_y']:
                    # Subtract 3 quarters from start_quarter
                    start_quarter_interm = pd.Timestamp(start_quarter) - pd.DateOffset(months=9)
                else:
                    start_quarter_interm = start_quarter

                mask &= (df['year_quarter'] >= start_quarter_interm) & (df['year_quarter'] <= end_quarter)

            logger.debug(f"df shape before remaining filters: {df.shape}")

            # Apply remaining filters efficiently
            for col, values in {
                'reinsurance_form': reinsurance_form,
                'reinsurance_geography': reinsurance_geography,
                'reinsurance_type': reinsurance_type,
                'line_type': line_type
            }.items():
                if values and col in df.columns:
                    mask &= df[col].isin(values)

            # Apply the combined mask once
            df = df.loc[mask]
            del mask
            #gc.collect()
            # Get all columns except 'line_type' and 'value' for groupby
            group_cols = [col for col in df.columns if col not in ['line_type', 'value']]
            
            # Aggregate by summing values after dropping line_type
            df = df.groupby(group_cols, observed=True)['value'].sum().reset_index()

            
            logger.debug(f"df shape after remaining filters: {df.shape}")
            logger.debug(f"metrics unique: {df['metric'].unique()}")
            # Process data in chunks

            df = self.filter_by_date_range_and_period_type(
                df,
                period_type=period_type,
                num_periods=num_periods
            )

            number_of_periods_options = len(df['year_quarter'].unique())

            years_to_keep = sorted(df['year'].unique(), reverse=True)[:min(num_periods, number_of_periods_options) + 1]
            df = df[df['year'].isin(years_to_keep)]
            df = df.drop(columns=['year'])
            
            # Initialize options
            insurer_options = []
            compare_options = []
            prev_ranks = []

            # Add calculated metrics
            required_metrics = required_metrics_set - set(df['metric'].unique())
            
            df = self.add_calculated_metrics(df, list(required_metrics))


            logger.debug(f"metrics unique after add_calculated_metrics: {df['metric'].unique()}")

            # Filter by required ratio metrics
            required_ratio_metrics = set(get_required_metrics(
                selected_metrics,
                CALCULATED_RATIOS,
                premium_loss_selection,
                BASE_METRICS
            ))
            logger.debug(f"required_ratio_metrics: {required_ratio_metrics}")
            df = df[df['metric'].isin(required_ratio_metrics)]

            # Handle aggregation
            if (chart_columns and 'linemain' not in chart_columns) or show_data_table:
                group_cols = [col for col in df.columns if col not in {'linemain', 'value'}]
                df = (df.groupby(group_cols, observed=True)['value']
                       .sum()
                       .reset_index()
                       .assign(linemain='all_lines'))

            # Add market share calculations
            if show_data_table or any(metric.endswith(("market_share", "market_share_q_to_q_change"))
                                     for metric in selected_metrics):
                df = self.add_market_share_rows(df, selected_insurers, selected_metrics, show_data_table)

            logger.debug(f"metrics uniqye: {df['metric'].unique() }")
            logger.debug(f"required_metrics : {required_ratio_metrics}")
            # Add averages and ratios if needed
            required_metrics = get_required_metrics(selected_metrics, CALCULATED_RATIOS)
            if set(required_metrics) - BASE_METRICS:
                df = self.add_averages_and_ratios(df, required_metrics)


            end_quarter_df = df[df['year_quarter'] == sorted(df['year_quarter'].unique())[-1]]
            number_of_insurer_options = len(end_quarter_df['insurer'].unique())
            logger.debug(f"number of insurers options: {number_of_insurer_options}")
            logger.debug(f"number of insurers: {number_of_insurers}")
            logger.debug(f"min of insurers: {min(number_of_insurers, number_of_insurer_options)}")

            # Process insurers once
            if show_data_table or selected_insurers:
                df, insurer_options, compare_options, selected_insurers, prev_ranks = self.process_insurers_data(
                    df, selected_insurers, top_n_list, show_data_table,
                    selected_metrics, min(number_of_insurers, number_of_insurer_options), main_insurer
                )
            
            logger.debug(f"metrics unique: {df['metric'].unique() }")
            # Add growth calculations if needed
            if show_data_table or any(metric.endswith("q_to_q_change") for metric in selected_metrics):
                df = self.add_growth_rows_long(df, selected_insurers, show_data_table, num_periods, period_type)

            df = df[df['year_quarter'] >= start_quarter]

            if chart_columns and not show_data_table:
                if 'metric' in chart_columns:
                    df = df[df['metric'].isin(selected_metrics)].copy()
                else:
                    df[df['metric'] == selected_metrics[0] if selected_metrics[0] in df['metric'].unique() else df['metric'].iloc[0]]

            save_df_to_csv(df, "process_dataframe.csv")

            logger.debug(f"process_general_filters returns, Time: {current_time}")
            logger.debug(f"metrics unique: {df['metric'].unique() }")
            return df, insurer_options, compare_options, selected_insurers, prev_ranks, number_of_periods_options, number_of_insurer_options

        finally:
            end_time = time.perf_counter_ns()
            duration_ms = (end_time - start_time) / 1_000_000
            logger.debug(f"process_general_filters actual duration: {duration_ms:.3f}ms")

    #@profile
    def filter_by_date_range_and_period_type(
        self,
        df: pd.DataFrame,
        period_type: str,
        num_periods: int
    ) -> pd.DataFrame:

        """Filter data by date range and period type with optimized performance."""
        df = df.copy()
        df['year'] = df['year_quarter'].dt.year.to_numpy()
        grouping_cols = [col for col in df.columns if col not in {'year_quarter', 'value', 'year', 'quarter'}]
        end_quarter_num = df['year_quarter'].max().quarter
        
        if period_type == 'yoy_q':
            df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
            df = df[df['year_quarter'].dt.quarter == end_quarter_num]
            df = df.drop(columns=['quarter'])

        elif period_type == 'ytd':
            df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
            df = (df[df['year_quarter'].dt.quarter <= end_quarter_num]
                  .assign(year=lambda x: x['year_quarter'].dt.year,
                         ytd_value=lambda x: x.groupby(['year'] + grouping_cols)['value'].cumsum())
                  .assign(value=lambda x: x['ytd_value'])
                  .drop(columns=['ytd_value', 'quarter'])
                  .loc[lambda x: x['year_quarter'].dt.quarter == end_quarter_num]
                  .reset_index(drop=True))

        elif period_type in ['mat', 'yoy_y']:
            df = df.sort_values(grouping_cols + ['year_quarter'])
            df.set_index('year_quarter', inplace=True)
            df['value'] = df.groupby(grouping_cols)['value'].transform(
                lambda x: x.rolling(window='365D', min_periods=1).sum()
            )
            df.reset_index(inplace=True)

            if period_type == 'yoy_y':
                df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
                df = df[df['quarter'] == end_quarter_num]
                df = df.drop(columns=['quarter'])

        elif period_type == 'cumulative_sum':
            df['value'] = df.groupby(grouping_cols)['value'].cumsum()

        return df

    def process_insurers_data(
        self,
        df: pd.DataFrame,
        selected_insurers: List[str],
        top_n_list: List[int],
        show_data_table: bool,
        selected_metrics: List[str],
        number_of_insurers = 200,
        main_insurer: str = None
    ) -> Tuple[pd.DataFrame, List[Dict], List[Dict], List[str], Dict[str, int]]:
        """Process insurers data with improved memory efficiency and previous ranks."""
        benchmark_insurers = {f"top-{n}-benchmark" for n in top_n_list}
        top_n_rows = {f"top-{n}" for n in top_n_list}
        total_rows = {'total'}
        others_rows = {'others'}

        ranking_metric = (selected_metrics[0] if selected_metrics and
                        selected_metrics[0] in df['metric'].unique()
                        else df['metric'].unique()[0])

        benchmark_metric = 'direct_premiums'

        end_quarter_dt = df['year_quarter'].max()

        group_columns = [col for col in df.columns if col not in ['insurer', 'value']]
        dataframes_to_concat = []
        prev_ranks = {}

        if len(df['insurer'].unique()) > 1:
            insurers_to_exclude = top_n_rows | benchmark_insurers | others_rows | total_rows
            ranking_df = df[
                (~df['insurer'].isin(insurers_to_exclude)) &
                (df['metric'] == ranking_metric)
            ]

            # Get current and previous quarter rankings
            quarters = sorted(ranking_df['year_quarter'].unique())
            if len(quarters) >= 2:
                end_quarter_dt = quarters[-1]
                prev_quarter_dt = quarters[-2]
                logger.debug(f"end_quarter_dt: {end_quarter_dt}")
                logger.debug(f"prev_quarter_dt: {prev_quarter_dt}")
                
                # Current quarter rankings
                end_quarter_ranking_df = ranking_df[ranking_df['year_quarter'] == end_quarter_dt]
                end_quarter_ranking_df = end_quarter_ranking_df.sort_values(
                    ['value'], ascending=[False]
                ).reset_index(drop=True)
                logger.debug(f"end_quarter_ranking_df head: {end_quarter_ranking_df.head()}")
                # Previous quarter rankings
                prev_quarter_ranking_df = ranking_df[ranking_df['year_quarter'] == prev_quarter_dt]
                prev_quarter_ranking_df = prev_quarter_ranking_df.sort_values(
                    ['value'], ascending=[False]
                ).reset_index(drop=True)
                logger.debug(f"prev_quarter_ranking_df metric unique: {prev_quarter_ranking_df['metric'].unique()}")
                logger.debug(f"prev_quarter_ranking_df year_quarter unique: {prev_quarter_ranking_df['year_quarter'].unique()}")
                logger.debug(f"prev_quarter_ranking_df linemain unique: {prev_quarter_ranking_df['linemain'].unique()}")
                
                logger.debug(f"prev_quarter_ranking_df head: {prev_quarter_ranking_df.head()}")
                # Store previous ranks for selected insurers
                prev_ranks = {
                    row['insurer']: idx + 1
                    for idx, row in prev_quarter_ranking_df.iterrows()
                }
                logger.debug(f"prev_ranks: {prev_ranks}")
            
            else:
                end_quarter_ranking_df = ranking_df[ranking_df['year_quarter'] == end_quarter_dt]
                end_quarter_ranking_df = end_quarter_ranking_df.sort_values(
                    ['value'], ascending=[False]
                ).reset_index(drop=True)

            top_insurers_options = list(dict.fromkeys(end_quarter_ranking_df['insurer']))
            top5_insurers_options = (end_quarter_ranking_df.groupby('insurer', observed=True)['value']
                                   .sum()
                                   .nlargest(5)
                                   .index
                                   .tolist())

            if show_data_table:
                selected_insurers = (end_quarter_ranking_df.groupby('insurer', observed=True)['value']
                                   .sum()
                                   .nlargest(number_of_insurers)
                                   .index
                                   .tolist())

            # Process top-n rows
            if (selected_insurers and any(insurer in top_n_rows for insurer in selected_insurers)) or show_data_table:
                for n in top_n_list:
                    ranking_df_top_rows = df[~df['insurer'].isin(insurers_to_exclude)]
                    top_n_rows_df = (ranking_df_top_rows.groupby(group_columns)
                                   .apply(lambda x: x.nlargest(n, 'value'))
                                   .reset_index(drop=True)
                                   .groupby(group_columns, observed=True)['value']
                                   .sum()
                                   .reset_index())
                    top_n_rows_df['insurer'] = f'top-{n}'
                    dataframes_to_concat.append(top_n_rows_df)

            # Process benchmark rows
            if any(insurer in benchmark_insurers for insurer in selected_insurers):
                insurers_to_exclude = (set(selected_insurers[0]) | benchmark_insurers |
                                     top_n_rows | total_rows | others_rows)

                end_quarter_benchmark_df = df[
                    (~df['insurer'].isin(insurers_to_exclude)) &
                    (df['year_quarter'] == end_quarter_dt) &
                    (df['metric'] == benchmark_metric)
                ]

                for n in top_n_list:
                    benchmark_insurers_list = (end_quarter_benchmark_df
                                            .groupby('insurer', observed=True)['value']
                                            .sum()
                                            .nlargest(n)
                                            .index
                                            .tolist())
                    benchmark_insurers_df = (df[df['insurer'].isin(benchmark_insurers_list)]
                                          .groupby(group_columns, observed=True)['value']
                                          .sum()
                                          .reset_index())
                    benchmark_insurers_df['insurer'] = f'top-{n}-benchmark'
                    dataframes_to_concat.append(benchmark_insurers_df)

            # Process others rows
            if others_rows.intersection(set(selected_insurers)):
                insurers_to_exclude = (set(selected_insurers) | benchmark_insurers |
                                     top_n_rows | total_rows | others_rows)

                others_df = (df[~df['insurer'].isin(insurers_to_exclude)]
                           .groupby(group_columns, observed=True, sort=False)['value']
                           .sum()
                           .reset_index())
                others_df['insurer'] = 'others'
                dataframes_to_concat.append(others_df)
        else:
            selected_insurers = [df['insurer'].unique()[0]]

        insurers_to_exclude_original_df = benchmark_insurers | top_n_rows | others_rows
        original_df = df[~df['insurer'].isin(insurers_to_exclude_original_df)]
        dataframes_to_concat.insert(0, original_df)

        concat_df = pd.concat(dataframes_to_concat, ignore_index=True)

        if not show_data_table:
            if not any(metric.endswith(("market_share", "market_share_q_to_q_change"))
                      for metric in selected_metrics):
                insurers_to_keep = selected_insurers
            else:
                insurers_to_keep = (selected_insurers or []) + list(total_rows)
        else:
            insurers_to_keep = (selected_insurers or []) + list(top_n_rows) + list(total_rows)

        result_df = concat_df[concat_df['insurer'].isin(insurers_to_keep)]

        # Generate options
        all_insurers_original = list(dict.fromkeys(df['insurer']))
        insurers_not_in_top_insurers_options = [
            insurer for insurer in all_insurers_original
            if insurer not in top_insurers_options
        ]
        insurers_not_in_top5 = [
            insurer for insurer in top_insurers_options
            if insurer not in top5_insurers_options
        ]

        insurer_options = [
            {'label': map_insurer(insurer), 'value': insurer}
            for insurer in (top5_insurers_options + list(total_rows) +
                          list(top_n_rows) + insurers_not_in_top5 +
                          insurers_not_in_top_insurers_options)
        ]

        compare_options = [
            {'label': map_insurer(insurer), 'value': insurer}
            for insurer in (top5_insurers_options + list(total_rows) +
                          list(others_rows) + list(benchmark_insurers) +
                          list(top_n_rows) + insurers_not_in_top5 +
                          insurers_not_in_top_insurers_options)
            if not main_insurer or insurer not in main_insurer
        ]

        # Return previous ranks as additional outpu
        return result_df, insurer_options, compare_options, selected_insurers, prev_ranks

    def add_market_share_rows(
            self,
            df: pd.DataFrame,
            selected_insurers: List[str],
            selected_metrics: List[str],
            show_data_table: bool,
            total_insurer: str = 'total',
            suffix: str = '_market_share'
        ) -> pd.DataFrame:
            """Calculate market share metrics."""
            if df.empty:
                return df

            # Get grouping columns (all columns except 'insurer' and 'value')
            group_cols = [col for col in df.columns if col not in {'insurer', 'value'}]

            # Calculate totals for each group
            totals = (df[df['insurer'] == total_insurer]
                     .groupby(group_cols)['value']
                     .first()
                     .to_dict())

            if not totals:
                return df

            # Calculate market shares
            market_shares = []
            for group_key, group in df.groupby(group_cols):
                if group_key not in totals or totals[group_key] == 0:
                    continue
                group = group.copy()
                group['value'] = (group['value'] / totals[group_key]).fillna(0)
                group['metric'] = group['metric'] + suffix
                market_shares.append(group)

            if not market_shares:
                return df

            result = pd.concat([df] + market_shares, ignore_index=True)

            if not show_data_table:
                result = result[result['insurer'].isin(selected_insurers)]

            return result

    def add_averages_and_ratios(
        self,
        df: pd.DataFrame,
        required_metrics: List[str]
    ) -> pd.DataFrame:
        """Calculate averages and ratios with optimized performance."""
        logger.debug(f"Unique metrics df before averages_and_ratio: {df['metric'].unique().tolist()}")
        logger.debug(f"required_metrics: {required_metrics}")
            
        if 'ceded_premiums_ratio' in required_metrics:
            logger.debug("Checking presence of required metrics:")
            logger.debug(f"'ceded_premiums' in df: {'ceded_premiums' in df['metric'].unique()}")
            logger.debug(f"'total_premiums' in df: {'total_premiums' in df['metric'].unique()}")
            
            # Sample data for both metrics
            logger.debug("\nSample ceded_premiums data:")
            logger.debug(df[df['metric'] == 'ceded_premiums'].head())
            logger.debug("\nSample total_premiums data:")
            logger.debug(df[df['metric'] == 'total_premiums'].head())        
        
        
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
                'average_sum_insured': (
                    ['sums_end', 'contracts_end'],
                    lambda df: df['sums_end'] / df['contracts_end'] / 1_000
                ),
                'average_new_sum_insured': (
                    ['new_sums', 'new_contracts'],
                    lambda df: df['new_sums'] / df['new_contracts'] / 1_000
                ),
                'average_new_premium': (
                    ['new_sums', 'direct_premiums'],
                    lambda df: df['direct_premiums'] / df['new_sums']
                ),

                'average_new_premium': (
                    ['direct_premiums', 'new_contracts'],
                    lambda df: df['direct_premiums'] / df['new_contracts']
                ),
                'average_loss': (
                    ['direct_losses', 'claims_settled'],
                    lambda df: df['direct_losses'] / df['claims_settled']
                )
            },
            'ratios': {
                'ceded_premiums_ratio': (
                    ['ceded_premiums', 'total_premiums'],
                    lambda df: df['ceded_premiums'].fillna(0) / df['total_premiums']
                ),
                'ceded_losses_ratio': (
                    ['ceded_losses', 'total_losses'],
                    lambda df: df['ceded_losses'].fillna(0) / df['total_losses']
                ),
                'ceded_losses_to_ceded_premiums_ratio': (
                    ['ceded_losses', 'ceded_premiums'],
                    lambda df: df['ceded_losses'].fillna(0) / df['ceded_premiums'].fillna(1)
                ),
                'gross_loss_ratio': (
                    ['direct_losses', 'inward_losses', 'direct_premiums', 'inward_premiums'],
                    lambda df: ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0)) /
                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0)))
                ),
                'direct_loss_ratio': (
                    ['direct_losses', 'direct_premiums'],
                    lambda df: df['direct_losses'].fillna(0) / df['direct_premiums'].fillna(1)
                ),
                'inward_loss_ratio': (
                    ['inward_losses', 'inward_premiums'],
                    lambda df: df['inward_losses'].fillna(0) / df['inward_premiums'].fillna(1)
                ),

                'premiums_interm_ratio': (
                    ['direct_premiums', 'premiums_interm'],
                    lambda df: df['premiums_interm'].fillna(0) / df['direct_premiums'].fillna(1)
                ),

                'commissions_rate': (
                    ['premiums_interm', 'commissions_interm'],
                    lambda df: df['commissions_interm'].fillna(0) / df['premiums_interm'].fillna(1)
                ),

                'net_loss_ratio': (
                    ['direct_losses', 'inward_losses', 'ceded_losses',
                     'direct_premiums', 'inward_premiums', 'ceded_premiums'],
                    lambda df: ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0) -
                               df['ceded_losses'].fillna(0)) /
                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0) -
                               df['ceded_premiums'].fillna(0)))
                ),
                'effect_on_loss_ratio': (
                    ['direct_losses', 'inward_losses', 'ceded_losses',
                     'direct_premiums', 'inward_premiums', 'ceded_premiums'],
                    lambda df: ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0)) /
                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0))) -
                             ((df['direct_losses'].fillna(0) + df['inward_losses'].fillna(0) -
                               df['ceded_losses'].fillna(0)) /
                              (df['direct_premiums'].fillna(0) + df['inward_premiums'].fillna(0) -
                               df['ceded_premiums'].fillna(0)))
                ),
                'ceded_ratio_diff': (
                    ['ceded_losses', 'total_losses', 'ceded_premiums', 'total_premiums'],
                    lambda df: (df['ceded_losses'].fillna(0) / df['total_losses']) -
                             (df['ceded_premiums'].fillna(0) / df['total_premiums'])
                )
            }
        }

        def transform_metrics(data: pd.DataFrame) -> pd.DataFrame:
            """Transform metrics using vectorized operations."""
            for metric, transform_func in METRIC_GROUPS['transform'].items():
                if metric in required_metrics:
                    mask = data['metric'] == metric
                    data.loc[mask, 'value'] = transform_func(data.loc[mask, 'value'])
            return data

        def calculate_ratios(pivot_df: pd.DataFrame) -> Dict[str, pd.Series]:
            """Calculate required ratios efficiently."""
            results = {}
            for group in ['averages', 'ratios']:
                for metric, (deps, formula) in METRIC_GROUPS[group].items():
                    if metric in required_metrics:
                        try:
                            if all(dep in pivot_df.columns for dep in deps):
                                results[metric] = formula(pivot_df)
                        except Exception as e:
                            self.logger.error(f"Error calculating {metric}: {str(e)}")
            return results

        try:
            result_df = transform_metrics(df.copy())

            calc_metrics = [m for m in required_metrics if any(
                m in group for group in [METRIC_GROUPS['averages'], METRIC_GROUPS['ratios']]
            )]

            if calc_metrics:
                index_cols = [col for col in df.columns if col not in ['metric', 'value']]
                pivot_df = result_df.pivot_table(
                    values='value',
                    index=index_cols,
                    columns='metric',
                    aggfunc='first'
                ).reset_index()

                if 'ceded_premiums_ratio' in required_metrics:
                    logger.debug("Checking ceded_premiums_ratio components:")
                    logger.debug(f"ceded_premiums values: {pivot_df['ceded_premiums'].head()}")
                    logger.debug(f"total_premiums values: {pivot_df['total_premiums'].head()}")
                    

                
                new_metrics = calculate_ratios(pivot_df)

                # After calculation
                if 'ceded_premiums_ratio' in new_metrics:
                    logger.debug("Resulting ceded_premiums_ratio:")
                    logger.debug(new_metrics['ceded_premiums_ratio'].head())
                
                for metric, values in new_metrics.items():
                    new_rows = pd.DataFrame({
                        **{col: pivot_df[col] for col in index_cols},
                        'metric': metric,
                        'value': values
                    })
                    result_df = pd.concat([result_df, new_rows], ignore_index=True)
            logger.debug(f"Unique metrics df after averages_and_ratio: {result_df['metric'].unique().tolist()}")
            return result_df

        except Exception as e:
            self.logger.error(f"Fatal error in add_averages_and_ratios: {str(e)}")
            raise

    def add_growth_rows_long(
        self,
        df: pd.DataFrame,
        selected_insurers: List[str],
        show_data_table: bool,
        num_periods: int = 2,
        period_type: str = 'qoq'
    ) -> pd.DataFrame:
        """Calculate growth metrics with improved performance."""
        try:
            if df.empty:
                return df

            # Ensure datetime type
            if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
                df['year_quarter'] = pd.to_datetime(df['year_quarter'], errors='coerce')

            group_cols = [col for col in df.columns if col not in ['year_quarter', 'metric', 'value']]
            df_sorted = df.sort_values(by=group_cols + ['year_quarter']).copy()

            # Split processing by metric type
            market_share_mask = df_sorted['metric'].str.endswith('market_share')
            regular_metrics = df_sorted[~market_share_mask].copy()
            market_share_metrics = df_sorted[market_share_mask].copy()

            processed_dfs = []

            # Process regular metrics
            if len(regular_metrics) > 0:
                grouped = regular_metrics.groupby(group_cols + ['metric'], observed=True)
                regular_metrics['previous'] = grouped['value'].shift(1)

                mask = regular_metrics['previous'] > 1e-9
                regular_metrics['growth'] = np.where(
                    mask,
                    (regular_metrics['value'] - regular_metrics['previous']) / regular_metrics['previous'],
                    np.nan
                )

                growth_regular = regular_metrics.copy()
                growth_regular['metric'] += '_q_to_q_change'
                growth_regular['value'] = growth_regular['growth']
                processed_dfs.append(growth_regular.drop(columns=['growth', 'previous']))

            # Process market share metrics
            if len(market_share_metrics) > 0:
                grouped = market_share_metrics.groupby(group_cols + ['metric'], observed=True)
                market_share_metrics['growth'] = grouped['value'].diff().fillna(0)

                growth_market = market_share_metrics.copy()
                growth_market['metric'] += '_q_to_q_change'
                growth_market['value'] = growth_market['growth']
                processed_dfs.append(growth_market.drop(columns=['growth']))

            growth_df = pd.concat(processed_dfs, ignore_index=True) if processed_dfs else pd.DataFrame(columns=df.columns)

            # Filter periods if needed
            if show_data_table:
                num_periods_growth = num_periods - 1

                recent_periods = (df_sorted['year_quarter']
                                .drop_duplicates()
                                .sort_values(ascending=False)
                                .iloc[:num_periods])

                recent_growth_periods = (df_sorted['year_quarter']
                                       .drop_duplicates()
                                       .sort_values(ascending=False)
                                       .iloc[:max(num_periods_growth, 1)])

                df_filtered = df_sorted[df_sorted['year_quarter'].isin(recent_periods)].copy()
                growth_filtered = growth_df[growth_df['year_quarter'].isin(recent_growth_periods)].copy()

                result = pd.concat([df_filtered, growth_filtered], ignore_index=True)
            else:
                result = pd.concat([df_sorted, growth_df], ignore_index=True)

            result.sort_values(by=group_cols + ['year_quarter', 'metric'], inplace=True)
            result.reset_index(drop=True, inplace=True)

            return result

        except Exception as e:
            self.logger.error(f"Error in growth calculation: {str(e)}")
            raise

    #@staticmethod
    def add_calculated_metrics(self, df: pd.DataFrame, required_metrics: List[str]):
        """Add calculated metrics to the DataFrame in-place."""
        grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
        metrics_to_calculate = {
            'net_balance': lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0),

            'total_premiums': lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0),
            'net_premiums': lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0) -
                                     d.get('ceded_premiums', 0)),
            'total_losses': lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0),
            'net_losses': lambda d: (d.get('direct_losses', 0) + d.get('inward_losses', 0) -
                                   d.get('ceded_losses', 0)),
            'gross_result': lambda d: ((d.get('direct_premiums', 0) + d.get('inward_premiums', 0)) -
                                     (d.get('direct_losses', 0) + d.get('inward_losses', 0))),
            'net_result': lambda d: ((d.get('direct_premiums', 0) + d.get('inward_premiums', 0) -
                                    d.get('ceded_premiums', 0)) -
                                   (d.get('direct_losses', 0) + d.get('inward_losses', 0) -
                                    d.get('ceded_losses', 0)))
        }

        # Filter for only required calculations
        active_calculations = {
            metric: calc for metric, calc in metrics_to_calculate.items()
            if metric in required_metrics
        }

        if not active_calculations:
            return df
        logger.debug(f"active_calculations {active_calculations}")

        def calculate_for_group(group):
            try:
                first_row = next(group.itertuples())
                base_dict = {col: getattr(first_row, col) for col in grouping_cols}
                metrics_dict = dict(zip(group['metric'], group['value']))

                result_data = []
                result_data.extend(group.to_dict('records'))

                for metric, calculation in active_calculations.items():
                    result_data.append({
                        'metric': metric,
                        'value': calculation(metrics_dict),
                        **base_dict
                    })

                return pd.DataFrame(result_data)

            except Exception as e:
                logger.error(f"Error in calculate_for_group: {str(e)}")
                return group

        # Process in chunks for memory efficiency
        chunks = []
        for _, group in df.groupby(grouping_cols):
            chunks.append(calculate_for_group(group))

        result_df = pd.concat(chunks, ignore_index=True)

        # Update the input DataFrame in-place
        df.drop(df.index, inplace=True)

        df = pd.concat([df, result_df], ignore_index=True)

        return df