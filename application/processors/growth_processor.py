from typing import List
import numpy as np
import pandas as pd


class GrowthProcessor:
    """Dedicated class for calculating growth metrics."""

    def calculate_growth(self, df: pd.DataFrame, value_types: List[str],
                         num_periods: List[int], config, logger) -> pd.DataFrame:
        """Calculate growth metrics for insurance data with capped changes."""
        if df.empty:
            return df
        if not any(config.value_types.CHANGE_SUFFIX in vt for vt in value_types):
            return df
        num_periods = num_periods[0] if isinstance(num_periods, list) else num_periods
        # Constants for capping
        df = df.copy()
        df.loc[:, config.columns.YEAR_QUARTER] = pd.to_datetime(
            df[config.columns.YEAR_QUARTER], errors='coerce')
        # Ensure value_type exists
        if config.columns.VALUE_TYPE not in df.columns:
            df[config.columns.VALUE_TYPE] = config.value_types.BASE
        # Get grouping columns and sort
        group_cols = [col for col in df.columns if col not in [
            config.columns.YEAR_QUARTER, config.columns.METRIC,
            config.columns.VALUE, config.columns.VALUE_TYPE
        ]]
        df = df.sort_values(by=group_cols + [config.columns.YEAR_QUARTER])
        # Split data based on value_type
        market_share_mask = df[config.columns.VALUE_TYPE] == config.value_types.MARKET_SHARE
        regular_mask = df[config.columns.VALUE_TYPE] == config.value_types.BASE
        results = []
        # Regular metrics
        if regular_mask.any():
            regular = df[regular_mask]
            grouped = regular.groupby(group_cols + [config.columns.METRIC],
                                      observed=True)
            shifted = grouped[config.columns.VALUE].shift(1)
            # Create growth DataFrame
            growth_regular = pd.DataFrame(index=regular.index)
            growth_regular[config.columns.METRIC] = regular[config.columns.METRIC]
            growth_regular[config.columns.VALUE_TYPE] = config.value_types.BASE_CHANGE
            # Calculate change with capping
            uncapped_change = np.where(
                shifted > 1e-9,
                (regular[config.columns.VALUE] - shifted) / shifted,
                np.nan
            )
            growth_regular[config.columns.VALUE] = np.clip(
                uncapped_change,
                -config.special_values.MAX_REGULAR_CHANGE,
                config.special_values.MAX_REGULAR_CHANGE
            )
            # Copy only necessary columns
            for col in group_cols + [config.columns.YEAR_QUARTER]:
                growth_regular[col] = regular[col]
            results.append(growth_regular)
        # Market share metrics
        if market_share_mask.any():
            market_share = df[market_share_mask]

            growth_market = pd.DataFrame(index=market_share.index)
            growth_market[config.columns.METRIC] = market_share[config.columns.METRIC]
            growth_market[config.columns.VALUE_TYPE] = config.value_types.MARKET_SHARE_CHANGE

            uncapped_change = market_share.groupby(
                group_cols + [config.columns.METRIC],
                observed=True
            )[config.columns.VALUE].diff() * 100
            growth_market[config.columns.VALUE] = np.clip(
                uncapped_change,
                -config.special_values.MAX_MARKET_SHARE_CHANGE,
                config.special_values.MAX_MARKET_SHARE_CHANGE
            )

            for col in group_cols + [config.columns.YEAR_QUARTER]:
                growth_market[col] = market_share[col]
            results.append(growth_market)

        if not results:
            growth_df = pd.DataFrame(columns=df.columns)
        else:
            growth_df = pd.concat(results, ignore_index=True)

        unique_periods = df[config.columns.YEAR_QUARTER].unique()
        num_periods = min(num_periods, len(unique_periods))
        recent_periods = pd.Series(unique_periods).nlargest(num_periods)
        growth_periods = recent_periods.iloc[:max(num_periods - 1, 1)]
        # Final concatenation
        result = pd.concat([
            df[df[config.columns.YEAR_QUARTER].isin(recent_periods)],
            growth_df[growth_df[config.columns.YEAR_QUARTER].isin(growth_periods)]
        ], ignore_index=True)

        result = result.sort_values(
            by=group_cols + [config.columns.YEAR_QUARTER]
        ).reset_index(drop=True)

        return result