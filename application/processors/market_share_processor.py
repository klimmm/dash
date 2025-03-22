from typing import List
import pandas as pd


class MarketShareProcessor:
    def __init__(self, metrics_for_market_share):
        self.metrics_for_market_share = metrics_for_market_share

    def calculate_market_share(
        self,
        df: pd.DataFrame,
        selected_value_types: List[str],
        logger,
        config
    ) -> pd.DataFrame:
        """Calculate market share metrics for insurance data."""
        if config.value_types.MARKET_SHARE not in selected_value_types or df.empty:
            return df

        # Add value_type for existing records
        df = df.copy()
        if config.columns.VALUE_TYPE not in df.columns:
            df[config.columns.VALUE_TYPE] = config.value_types.BASE

        # Get grouping columns and calculate totals
        group_cols = [col for col in df.columns
                      if col not in {config.columns.INSURER, config.columns.VALUE}]
        totals = (df[df[config.columns.INSURER] == config.special_values.TOTAL_INSURER]
                  .groupby(group_cols)[config.columns.VALUE]
                  .first()
                  .to_dict())

        if not totals:
            return df

        # Calculate market shares for valid metrics
        market_shares = []
        for group_key, group in df.groupby(group_cols):
            metric_name = group[config.columns.METRIC].iloc[0]

            if (metric_name not in self.metrics_for_market_share or
                group_key not in totals or
                    totals[group_key] == 0):
                continue

            # Calculate market share
            share_group = group.copy()
            share_group[config.columns.VALUE] = (share_group[config.columns.VALUE] /
                                          totals[group_key]).fillna(0)
            share_group[config.columns.VALUE_TYPE] = config.value_types.MARKET_SHARE
            market_shares.append(share_group)

        return (pd.concat([df] + market_shares, ignore_index=True)
                if market_shares else df)