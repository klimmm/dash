# application/services/pivot_service.py
from typing import Any, Dict, List, Tuple
import pandas as pd


class PivotService:
    """Service class for creating pivot tables from DataFrame."""

    def __init__(self, logger=None, config=None):
        self.logger = logger
        self.config = config

    def create_pivot(
        self,
        df: pd.DataFrame,
        pivot_cols: List[str],
        index_cols: List[str],
        logger,
        config,
        separator: str = '&',
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Create a pivot table from a DataFrame.

        Args:
            df: Source DataFrame
            pivot_cols: Columns to use for pivoting
            index_cols: Columns to use as index in the resulting pivot table
            separator: String to use as separator in the pivot key

        Returns:
            Tuple containing the pivoted DataFrame and ordered column structure
        """
        self.value_types = config.value_types
        self.logger = logger
        self.columns = config.columns


        pivot_cols = [col for col in pivot_cols if col in df.columns]
        index_cols = [col for col in index_cols if col in df.columns]

        df_copy = df.copy()
        self.logger.debug(f"index_cols {index_cols}")

        # Store original column ordering for each index column
        original_orders = self._get_original_column_ordering(df_copy, index_cols)
        self.logger.debug(f"original_orders {original_orders}")

        # Create pivot column hierarchies
        pivot_values = self._get_pivot_values(df_copy, pivot_cols)
        self.logger.debug(f"pivot_values {pivot_values}")

        # Create the combined pivot key column
        df_copy = self._create_pivot_key_column(df_copy, pivot_cols, separator)

        # Create the pivot table
        result_df = self._create_pivot_table(df_copy, index_cols, values_col=self.columns.VALUE)

        # Restore original ordering and sort
        result_df = self._restore_ordering_and_sort(result_df, index_cols, original_orders)

        # Generate ordered column list (preserving hierarchy)
        ordered_col_values = self._generate_ordered_columns(pivot_cols, pivot_values, separator)

        # Create final column list with index columns and ordered pivot columns
        result_df = self._finalize_columns(result_df, index_cols, ordered_col_values)

        # Format the dataframe for display
        result_df = self._format_dataframe(result_df, index_cols)

        # Note: The original function returned a tuple with a second element that wasn't used
        # For compatibility, we'll return an empty list as the second element
        return result_df

    def _get_original_column_ordering(
        self,
        df: pd.DataFrame,
        index_cols: List[str]
    ) -> Dict[str, List[Any]]:
        """Store original column ordering for each index column."""
        return {
            col: pd.Series(df[col].unique()).tolist()
            for col in index_cols
        }

    def _get_pivot_values(
        self,
        df: pd.DataFrame,
        pivot_cols: List[str]

    ) -> Dict[str, List[Any]]:
        """Get unique values for each pivot column with appropriate ordering."""
        pivot_values = {}
        for col in pivot_cols:
            # For consistent ordering, handle 'rank' specially in value_type
            if col == self.columns.YEAR_QUARTER:
                values = sorted(
                    df[col].unique(), reverse=(col == self.columns.YEAR_QUARTER))
            elif col == self.columns.VALUE_TYPE and self.value_types.RANK in df[col].unique():
                values = [self.value_types.RANK] + sorted(
                   v for v in sorted(df[col].unique()) if
                   v != self.value_types.RANK)
            else:
                values = df[col].unique()
            pivot_values[col] = values
        return pivot_values

    def _create_pivot_key_column(
        self,
        df: pd.DataFrame,
        pivot_cols: List[str],
        separator: str
    ) -> pd.DataFrame:
        """Create a combined pivot key column."""
        df['_pivot_key'] = ''
        for col in pivot_cols:
            df['_pivot_key'] += df[col].astype(str) + separator
        df['_pivot_key'] = df['_pivot_key'].str[:-len(separator)]
        return df

    def _create_pivot_table(
        self,
        df: pd.DataFrame,
        index_cols: List[str],
        values_col: str
    ) -> pd.DataFrame:
        """Create the pivot table."""
        return pd.pivot_table(
            data=df,
            values=values_col,
            index=index_cols,
            columns='_pivot_key',
            aggfunc=lambda x: x.iloc[0] if len(x) > 0 else None,
            observed=True,
            dropna=False
        ).reset_index()

    def _restore_ordering_and_sort(
        self,
        df: pd.DataFrame,
        index_cols: List[str],
        original_orders: Dict[str, List[Any]]
    ) -> pd.DataFrame:
        """Restore original ordering to categorical columns and sort."""
        for col in index_cols:
            df[col] = pd.Categorical(
                df[col],
                categories=original_orders[col],
                ordered=True
            )
        # Sort by index columns
        return df.sort_values(index_cols)

    def _generate_ordered_columns(
        self,
        pivot_cols: List[str],
        pivot_values: Dict[str, List[Any]],
        separator: str
    ) -> List[str]:
        """Generate ordered column combinations."""
        ordered_col_values = []

        def generate_combinations(level=0, current_combo=[]):
            """Recursive function to generate all combinations of pivot values."""
            if level == len(pivot_cols):
                ordered_col_values.append(separator.join(current_combo))
                return
            for val in pivot_values[pivot_cols[level]]:
                generate_combinations(level + 1, current_combo + [str(val)])

        # Generate all ordered combinations
        generate_combinations()
        return ordered_col_values

    def _finalize_columns(
        self,
        df: pd.DataFrame,
        index_cols: List[str],
        ordered_col_values: List[str]
    ) -> pd.DataFrame:
        """Create final column list with index columns and ordered pivot columns."""
        final_cols = index_cols.copy()
        for combo in ordered_col_values:
            if combo in df.columns:
                final_cols.append(combo)
        # Select only columns that exist
        return df[final_cols].copy()

    def _format_dataframe(
        self,
        df: pd.DataFrame,
        index_cols: List[str]
    ) -> pd.DataFrame:
        """Format the dataframe for display."""
        # Convert categorical columns to string
        cat_cols = df.select_dtypes(include=['category']).columns
        df[cat_cols] = df[cat_cols].astype(str)

        # Replace empty values with '-'
        df = df.replace([0, ''], '-').fillna('-')

        # Rename columns
        new_columns = []
        for col in df.columns:
            if col in index_cols:
                # Convert index columns to simple strings
                new_columns.append(col)
            else:
                # Keep value columns as is
                new_columns.append(col)
        df.columns = new_columns

        return df