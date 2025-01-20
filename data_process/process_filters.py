# data_process.process_filters

import pandas as pd
import numpy as np
import gc
import logging
import time
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass
from memory_profiler import profile
from data_process.data_utils import save_df_to_csv, map_insurer
from data_process.calculate_metrics import calculate_metrics
from config.logging_config import get_logger
logger = get_logger(__name__)

#@profile
def filter_by_date_range_and_period_type(
    df: pd.DataFrame,
    period_type: str
) -> pd.DataFrame:

    """Filter data by date range and period type with optimized performance."""
    df = df.copy()
    grouping_cols = [col for col in df.columns if col not in {'year_quarter', 'value', 'quarter'}]
    end_quarter_num = df['year_quarter'].max().quarter

    if period_type == 'yoy_q':
        df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
        df = df[df['year_quarter'].dt.quarter == end_quarter_num]
        df = df.drop(columns=['quarter'])

    elif period_type == 'ytd':
        df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
        df['year'] = df['year_quarter'].dt.year.to_numpy()
        df = (df[df['year_quarter'].dt.quarter <= end_quarter_num]
              .assign(year=lambda x: x['year_quarter'].dt.year,
                     ytd_value=lambda x: x.groupby(['year'] + grouping_cols)['value'].cumsum())
              .assign(value=lambda x: x['ytd_value'])
              .drop(columns=['ytd_value', 'quarter'])
              .loc[lambda x: x['year_quarter'].dt.quarter == end_quarter_num]
              .reset_index(drop=True))
        df = df.drop(columns=['year'])
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
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_n_list: List[int],
    show_data_table: bool,
    selected_metrics: List[str],
    number_of_insurers = 200
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]], List[Dict], List[str], Dict[str, int]]:
    """Process insurers data with improved memory efficiency and previous ranks by linemain."""
    top_n_rows = {f"top-{n}" for n in top_n_list}
    total_rows = {'total'}
    ranking_metric = (selected_metrics[0] if selected_metrics and
                    selected_metrics[0] in df['metric'].unique()
                    else df['metric'].unique()[0])
    dataframes_to_concat = []
    prev_ranks = {}
    
    if len(df['insurer'].unique()) > 1:
        insurers_to_exclude = top_n_rows | total_rows
        ranking_df = df[
            (~df['insurer'].isin(insurers_to_exclude)) &
            (df['metric'] == ranking_metric)
        ]
        
        # Get current and previous quarter rankings
        quarters = sorted(ranking_df['year_quarter'].unique())
        end_quarter_dt = quarters[-1]
        end_quarter_ranking_df = ranking_df[ranking_df['year_quarter'] == end_quarter_dt]
        
        if len(quarters) >= 2:
            prev_quarter_dt = quarters[-2]
            prev_quarter_ranking_df = ranking_df[ranking_df['year_quarter'] == prev_quarter_dt]
            
            for line_id in prev_quarter_ranking_df['linemain'].unique():
                line_df = prev_quarter_ranking_df[
                    prev_quarter_ranking_df['linemain'] == line_id
                ].sort_values(['value'], ascending=[False]).reset_index(drop=True)
                
                prev_ranks[line_id] = {
                    str(row['insurer']): idx + 1
                    for idx, row in line_df.iterrows()
                }

        # Process each linemain separately with filtered data
        for line_id in df['linemain'].unique():
            line_end_quarter_df = end_quarter_ranking_df[
                end_quarter_ranking_df['linemain'] == line_id
            ]
            
            if show_data_table:
                top_insurers_for_line = (
                    line_end_quarter_df.groupby('insurer', observed=True)['value']
                    .sum()
                    .nlargest(number_of_insurers)
                    .index
                    .tolist()
                )
                
                # Filter the original data to include only top insurers for this line
                line_df = df[
                    (df['linemain'] == line_id) & 
                    (df['insurer'].isin(top_insurers_for_line + list(insurers_to_exclude)))
                ]
            else:
                line_df = df[df['linemain'] == line_id]

            # Process top-n rows for this linemain
            if show_data_table:  # Modified this condition since we're using top N per line
                group_columns = [col for col in line_end_quarter_df.columns if col not in ['insurer', 'value']]
                
                for n in top_n_list:
                    line_ranking_df_top_rows = df[(~df['insurer'].isin(insurers_to_exclude)) & (df['linemain'] == line_id)]
                    top_n_rows_df = (
                        line_ranking_df_top_rows.groupby(group_columns)
                        .apply(lambda x: x.nlargest(n, 'value'))
                        .reset_index(drop=True)
                        .groupby(group_columns, observed=True)['value']
                        .sum()
                        .reset_index()
                    )
                    top_n_rows_df['insurer'] = f'top-{n}'
                    dataframes_to_concat.append(top_n_rows_df)

            # Add the filtered original data for this linemain
            original_line_df = line_df[~line_df['insurer'].isin(top_n_rows)]
            dataframes_to_concat.append(original_line_df)
    else:
        selected_insurers = [df['insurer'].unique()[0]]
    
    concat_df = pd.concat(dataframes_to_concat, ignore_index=True)
    
    # Modify final filtering to maintain all rows from our concatenated dataframe
    # since we've already filtered per line
    result_df = concat_df
    
    return result_df, prev_ranks

def add_market_share_rows(
        df: pd.DataFrame,
        selected_insurers: List[str],
        selected_metrics: List[str],
        show_data_table: bool,
        total_insurer: str = 'total',
        suffix: str = '_market_share'
    ) -> pd.DataFrame:
        """
        Calculate market share metrics, skipping metrics that contain 'ratio', 'average', or 'rate'.
        """
        if df.empty:
            logger.debug("Input DataFrame is empty, returning without calculations")
            return df
            
        logger.debug(f"Initial DataFrame shape: {df.shape}")
        logger.debug(f"Selected insurers: {selected_insurers}")
        logger.debug(f"Selected metrics: {selected_metrics}")
        logger.debug(f"Total insurer value: {total_insurer}")
        logger.debug(f"Input DataFrame head:\n{df.head()}")
        logger.debug(f"Metrics unique before: {df['metric'].unique()}")        
        logger.debug(f"Insurers unique before: {df['insurer'].unique()}")        
    
        # Get grouping columns
        group_cols = [col for col in df.columns if col not in {'insurer', 'value'}]
        logger.debug(f"Grouping columns: {group_cols}")
        
        # Calculate totals for each group
        total_insurer_data = df[df['insurer'] == total_insurer]
        logger.debug(f"Total insurer data shape: {total_insurer_data.shape}")
        logger.debug(f"Total insurer data head:\n{total_insurer_data.head()}")
        
        totals = (total_insurer_data
                 .groupby(group_cols)['value']
                 .first()
                 .to_dict())
                 
        if not totals:
            logger.debug(f"No totals calculated. Total insurer '{total_insurer}' might be missing from data")
            return df
            
        logger.debug(f"Calculated totals: {totals}")        
        
        # Calculate market shares
        market_shares = []
        for group_key, group in df.groupby(group_cols):
            logger.debug(f"Processing group: {group_key}")
            
            # Skip if metric contains ratio, average, or rate
            metric_name = group['metric'].iloc[0].lower()
            if any(word in metric_name for word in ['ratio', 'average', 'rate']):
                logger.debug(f"Skipping market share calculation for metric '{metric_name}' as it contains excluded terms")
                continue
            
            if group_key not in totals:
                logger.debug(f"Group {group_key} not found in totals, skipping")
                continue
                
            if totals[group_key] == 0:
                logger.debug(f"Total for group {group_key} is 0, skipping to avoid division by zero")
                continue
                
            group = group.copy()
            original_values = group['value'].copy()
            group['value'] = (group['value'] / totals[group_key]).fillna(0)
            
            logger.debug(f"Group {group_key} calculation:")
            logger.debug(f"Original values: {original_values.tolist()}")
            logger.debug(f"Total value: {totals[group_key]}")
            logger.debug(f"Calculated market shares: {group['value'].tolist()}")
            
            group['metric'] = group['metric'] + suffix
            market_shares.append(group)
            
        if not market_shares:
            logger.debug("No market shares calculated")
            return df
            
        logger.debug(f"Number of market share groups calculated: {len(market_shares)}")
        
        result = pd.concat([df] + market_shares, ignore_index=True)
        logger.debug(f"Final DataFrame shape after concat: {result.shape}")
        
        if not show_data_table:
            filtered_result = result[result['insurer'].isin(selected_insurers)]
            logger.debug(f"Filtered DataFrame shape: {filtered_result.shape}")
            logger.debug(f"Final insurers: {filtered_result['insurer'].unique()}")
            return filtered_result

        logger.debug(f"Final metrics: {result['metric'].unique()}")
        return result


def add_growth_rows(
    df: pd.DataFrame,
    selected_insurers: List[str],
    show_data_table: bool,
    num_periods_selected: int = 2,
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
            num_periods_growth = num_periods_selected - 1

            recent_periods = (df_sorted['year_quarter']
                            .drop_duplicates()
                            .sort_values(ascending=False)
                            .iloc[:num_periods_selected])

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
        logger.error(f"Error in growth calculation: {str(e)}")
        raise