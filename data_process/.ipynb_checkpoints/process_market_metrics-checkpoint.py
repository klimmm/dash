
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

from data_process.data_utils import save_df_to_csv, log_dataframe_info, category_structure, insurer_name_map

from constants.filter_options import MARKET_METRIC_OPTIONS, METRICS, base_metrics, calculated_metrics, calculated_ratios, REINSURANCE_FIG_TYPES, INSURANCE_FIG_TYPES
from constants.mapping import map_insurer



from logging_config import setup_logging, set_debug_level, DebugLevels, get_logger, debug_log, intensive_debug_log, custom_profile

logger = get_logger(__name__)



#@custom_profile

def process_market_metrics(
    df: pd.DataFrame,
    primary_y_metrics: List[str],
    secondary_y_metrics: List[str],
    period_type: str,
    num_periods: int = 2,
    num_periods_growth: int = 1

) -> pd.DataFrame:


    selected_metrics = (primary_y_metrics or []) + (secondary_y_metrics or [])

    extended_metrics = (selected_metrics or []) + ['total_premiums', 'total_losses']

    df = add_market_share_rows(df)
    df = add_averages_and_ratios(df, extended_metrics)
    df = add_growth_rows_long(df, num_periods, period_type, num_periods_growth)

    return df



def add_market_share_rows(
    df: pd.DataFrame,
    total_insurer: str = 'total',
    exclude_total: bool = False,
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
    exclude_total : bool, default=False
        Whether to exclude total insurer from market share calculations
    suffix : str, default='_market_share'
        Suffix to append to metric names for market share columns

    Returns:
    --------
    pd.DataFrame
        DataFrame with additional market share metrics
    """
    logger = logging.getLogger(__name__)

    def get_group_cols(df: pd.DataFrame) -> List[str]:
        """Efficiently extract grouping columns."""
        return [col for col in df.columns if col not in {'insurer', 'value'}]

    def calculate_market_shares(
        group: pd.DataFrame,
        total_value: float,
        exclude_total: bool
    ) -> Optional[pd.DataFrame]:
        """Calculate market shares for a group efficiently."""
        if exclude_total:
            group = group[group['insurer'] != total_insurer]

        if len(group) == 0:
            return None

        group = group.copy()
        group['value'] = (group['value'] / total_value).fillna(0)
        group['metric'] = group['metric'] + suffix
        return group

    try:
        # Start with basic validation
        if df.empty:
            logger.warning("Empty DataFrame provided")
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
            logger.warning(f"No rows found for total_insurer '{total_insurer}'")
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
                    exclude_total
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

        logger.info(f"Added {len(new_metrics)} new market share metrics")
        logger.debug(f"New metrics: {new_metrics}")

        return resul

    except Exception as e:
        logger.error(f"Error in market share calculation: {str(e)}")
        raise




def add_averages_and_ratios(
    df: pd.DataFrame,
    selected_metrics: List[str]
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
    logger = logging.getLogger(__name__)

    try:
        # Input validation
        if df.empty:
            logger.warning("Empty DataFrame provided")
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
                logger.warning(f"{invalid_dates} year_quarter entries could not be converted to datetime")

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

