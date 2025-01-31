import numpy as np
import pandas as pd
from typing import List
from config.logging_config import get_logger
from data_process.io import save_df_to_csv

logger = get_logger(__name__)


def calculate_growth(
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
        save_df_to_csv(df_sorted, "df_sorted_growth.csv")
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

        save_df_to_csv(result, "result_growth_before_sort.csv")
        
        result.sort_values(by=group_cols + ['year_quarter'], inplace=True)
        save_df_to_csv(result, "result_growth_after_sort.csv")

        
        result.reset_index(drop=True, inplace=True)

        return result

    except Exception as e:
        logger.error(f"Error in growth calculation: {str(e)}")
        raise