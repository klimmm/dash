from typing import List
import pandas as pd


class RankProcessor:
    def __init__(self, logger=None, config=None):
        self.config = config
        self.logger = config

    def add_rank_column(self, df: pd.DataFrame, value_types: List[str], num_periods: int, logger, config) -> pd.DataFrame:
        """Add ranks and rank changes for each year_quarter/line/metric combination."""
        self.config = config
        self.logger = logger
        self.columns = config.columns
        self.value_types = config.value_types
        self.special_values = config.special_values


        if self.value_types.RANK not in value_types or df.empty:
            return df

        df = df.copy()

        df[self.columns.VALUE_TYPE] = self.value_types.BASE

        # Create mask for regular insurers
        mask = (df[self.columns.VALUE_TYPE] == self.value_types.BASE) & ~df[
            self.columns.INSURER].isin(self.special_values.NON_INSURERS)

        # Calculate ranks
        df_masked = df[mask].copy()
        df_masked[self.value_types.RANK] = (df_masked.groupby(
            [self.columns.YEAR_QUARTER, self.columns.LINE, self.columns.METRIC])[self.columns.VALUE]
                               .rank(ascending=False, method='min'))

        # Calculate rank changes
        df_masked[self.value_types.RANK_CHANGE] = (
            df_masked.sort_values(self.columns.YEAR_QUARTER).groupby(
                     [self.columns.LINE, self.columns.METRIC, self.columns.INSURER])
                 [self.value_types.RANK].diff() * -1)

        # Prepare rank and rank_change DataFrames
        common_cols = [self.columns.YEAR_QUARTER, self.columns.LINE,
                       self.columns.METRIC, self.columns.INSURER]
        rank_df = df_masked[common_cols + [self.value_types.RANK]].assign(
            value_type=self.value_types.RANK).rename(
            columns={self.value_types.RANK: self.columns.VALUE})


        change_df = df_masked[common_cols + [self.value_types.RANK_CHANGE]].assign(
            value_type=self.value_types.RANK_CHANGE).rename(
            columns={self.value_types.RANK_CHANGE: self.columns.VALUE})

        unique_periods = df[self.columns.YEAR_QUARTER].unique()
        num_periods = min(num_periods, len(unique_periods))
        recent_periods = pd.Series(unique_periods).nlargest(num_periods)
        rank_periods = recent_periods.iloc[:max(num_periods - 1, 1)]

        # Combine results
        result_df = pd.concat([df,
                               rank_df[rank_df[self.columns.YEAR_QUARTER].isin(rank_periods)],
                               change_df[change_df[self.columns.YEAR_QUARTER].isin(rank_periods)],
                              ], ignore_index=True)
        return result_df

    def format_ranks(self, df: pd.DataFrame, logger, config) -> pd.DataFrame:
        """Format rank values for display."""
        self.config = config
        self.columns = config.columns
        self.value_types = config.value_types
        self.special_values = config.special_values
        self.logger = logger


        if self.value_types.RANK not in df[self.columns.VALUE_TYPE].unique() or df.empty:
            return df
        df = df.copy()
        # Handle base_change and market_share_change first
        if self.value_types.BASE_CHANGE in df[self.columns.VALUE_TYPE].unique():
            mask_base_change = df[self.columns.VALUE_TYPE] == self.value_types.BASE_CHANGE
            df.loc[mask_base_change, self.columns.VALUE] = df.loc[
                mask_base_change, self.columns.VALUE].apply(
                lambda x:
                self.special_values.INFINITY_SIGN if pd.to_numeric(x, errors='coerce') >
                    self.special_values.BASE_INFINITY_THRESHOLD
                or pd.to_numeric(x, errors='coerce') <
                    -self.special_values.BASE_INFINITY_THRESHOLD
                else x
            )

        if self.value_types.MARKET_SHARE_CHANGE in df[self.columns.VALUE_TYPE].unique():
            mask_mark_share = df[self.columns.VALUE_TYPE] == self.value_types.MARKET_SHARE_CHANGE
            df.loc[mask_mark_share, self.columns.VALUE] = df.loc[
                mask_mark_share, self.columns.VALUE].apply(
                lambda x:
                self.special_values.INFINITY_SIGN if pd.to_numeric(x, errors='coerce') >
                    self.special_values.MARKET_SHARE_INFINITY_THRESHOLD or
                    pd.to_numeric(x, errors='coerce') <
                    -self.special_values.MARKET_SHARE_INFINITY_THRESHOLD
                else x
            )

        # Check for required value types
        if not {self.value_types.RANK, self.value_types.RANK_CHANGE}.issubset(
                df[self.columns.VALUE_TYPE].unique()):
            mask = df[self.columns.VALUE_TYPE].notna() & ~df[self.columns.VALUE_TYPE].isin(
                [self.value_types.RANK, self.value_types.RANK_CHANGE])
            return df[mask]


        # Get non-value columns for joining
        join_cols = df.columns.difference([self.columns.VALUE, self.columns.VALUE_TYPE]).tolist()
        # Process rank data
        mask_rank = df[self.columns.VALUE_TYPE] == self.value_types.RANK
        mask_change = df[self.columns.VALUE_TYPE] == self.value_types.RANK_CHANGE

        # Convert values to numeric and merge
        merged = pd.merge(
            df[mask_rank][join_cols + [self.columns.VALUE]],
            df[mask_change][join_cols + [self.columns.VALUE]],
            on=join_cols,
            suffixes=(self.value_types.RANK_SUFFIX, self.value_types.CHANGE_SUFFIX)
        )

        def format_rank(row):
            rank_col = f"{self.columns.VALUE}{self.value_types.RANK_SUFFIX}"
            change_col = f"{self.columns.VALUE}{self.value_types.CHANGE_SUFFIX}"

            rank = pd.to_numeric(row[rank_col], errors='coerce')
            change = pd.to_numeric(row[change_col], errors='coerce')

            if pd.isna(rank):
                return '-'
            rank = int(rank)
            if pd.isna(change):
                return str(rank)
            change = int(change)
            change_str = (
                f"({'+' if change > 0 else ''}{change if change else '-'})")
            return f"{rank} {change_str}"

        # Create formatted output
        output = merged[join_cols].copy()
        output[self.columns.VALUE_TYPE] = self.value_types.RANK
        output[self.columns.VALUE] = merged.apply(format_rank, axis=1)
        self.logger.debug(f"Processed {len(output)} ranking rows")

        # Combine with non-rank data
        mask_non_rank = df[self.columns.VALUE_TYPE].notna() & ~df[self.columns.VALUE_TYPE].isin(
            [self.value_types.RANK, self.value_types.RANK_CHANGE])
        df = pd.concat([df[mask_non_rank], output], ignore_index=True)

        return df
