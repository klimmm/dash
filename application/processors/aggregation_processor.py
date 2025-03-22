import pandas as pd


class AggregationProcessor:

    def add_top_n_rows(self, df: pd.DataFrame, logger, config) -> pd.DataFrame:
        """Add aggregated top-N rows to data."""
        df = df.copy()

        # Pre-filter excluded insurers once - use loc for boolean indexing
        group_by_cols = [
            col for col in df.columns if col not in [config.columns.INSURER, config.columns.VALUE]]
        filtered_df = df.loc[df[config.columns.INSURER] != config.special_values.TOTAL_INSURER].copy()

        # Store the original df in the list
        dfs = [df]

        for n in config.special_values.TOP_N_OPTIONS:
            ranked_df = filtered_df.assign(
                rank_temp=lambda x: x.groupby(group_by_cols)[config.columns.VALUE].rank(
                    method='first',
                    ascending=False
                )
            )

            # Filter and aggregate in one step
            top_n_df = (ranked_df[ranked_df['rank_temp'] <= n]
                        .groupby(group_by_cols, observed=True)
                        .agg({config.columns.VALUE: 'sum'})
                        .assign(insurer=f'top-{n}')
                        .reset_index())

            dfs.append(top_n_df)

        return pd.concat(dfs, ignore_index=True)