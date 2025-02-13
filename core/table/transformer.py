from typing import Any, Dict, Generator, Tuple

import json
import pandas as pd
from config.app_config import LINES_162_DICTIONARY
from config.logging import get_logger
from core.lines.mapper import map_line
from core.io import save_df_to_csv

logger = get_logger(__name__)


def sort_by_hierarchy(df: pd.DataFrame,
                     hierarchy: Dict[str, Any]) -> pd.DataFrame:
    """Sort DataFrame based on insurance line hierarchy."""
    logger.warning(f"Input df lines: {df['line'].unique()}")
    logger.warning(f" df: {df}")
    
    if df.empty:
        return df
        
    df = df.copy().reset_index(drop=True)  # Reset index to ensure stable sort
    
    def get_node_info(key: str, depth: int = 0) -> Generator[Tuple[str, int], None, None]:
        if key in hierarchy:
            yield (hierarchy[key]['label'], depth)
            for child in hierarchy[key].get('children', []):
                yield from get_node_info(child, depth + 1)
                
    # Build sorting order
    order_map = {label: (i, depth) for i, (label, depth) in
                enumerate(get_node_info('все линии'))}
    
    # Add original index as secondary sort key for stability
    df['_original_idx'] = range(len(df))
    
    # Apply sort and indent
    df['_sort'] = df['line'].map(
        lambda x: order_map.get(x, (float('inf'), 0))
    )
    
    df.sort_values(['_sort', '_original_idx'], inplace=True)
    logger.warning(f" df: {df}")
    
    # Handle case when all depths are inf
    sort_values = [depth for _, depth in df['_sort'] if depth != float('inf')]
    if not sort_values:
        min_depth = 0
    else:
        min_depth = min(sort_values)
    logger.warning(f" sort_values: {sort_values}")
    
    df['line'] = df.apply(
        lambda row:
        "---" * (
            row['_sort'][1] - min_depth
            if row['_sort'][1] != float('inf') else 0
        ) + row['line'], axis=1
    )
    logger.warning(f" df: {df}")
    
    return df.drop(['_sort', '_original_idx'], axis=1)


class TableTransformer:
    """Handles table data transformation and ranking operations."""

    COLS = {
        'insurer': 'insurer',
        'line': 'line',
        'metric_base': 'metric_base'
    }

    def _format_rank(self, rank: int, change: int) -> str:
        """Format rank with change indicator."""
        if rank == '-' or change == '-':
            return '-'
        return f"{rank} ({'+' if change > 0 else ''}{change})" if change else f"{rank} (-)"

    def _process_rankings(self, df: pd.DataFrame, split_mode) -> pd.DataFrame:
        """Process and format rankings for each quarter."""

        save_df_to_csv(df, f"{split_mode}_before_ranks.csv")
        df = df[df['metric'] == df['metric_base']].copy()
        #logger.debug(f"Rankings data shape: {df.shape}")
        save_df_to_csv(df, f"{split_mode}_ranks_1.csv")
        # Convert ranks to integers
        for col in ['rank', 'rank_change']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        save_df_to_csv(df, f"{split_mode}_ranks_2.csv")
        df['formatted_rank'] = df.apply(
            lambda row: self._format_rank(row['rank'], row['rank_change']), axis=1
        )
        save_df_to_csv(df, f"{split_mode}_ranks_3.csv")
        return df[['insurer', 'line', 'metric_base', 'year_quarter', 'formatted_rank']]

    def _flatten_multiindex(self, df: pd.DataFrame) -> pd.DataFrame:
        """Safely flatten any MultiIndex in columns or index."""
        #logger.debug("Flattening MultiIndex")
        #logger.debug(f"Input df info: {df.info()}")

        # First reset any MultiIndex in the index
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
            #logger.debug("Reset MultiIndex index")

        # Then handle MultiIndex columns if they exist
        if isinstance(df.columns, pd.MultiIndex):
            # Convert tuples to strings
            df.columns = [
                col[0] if isinstance(col, tuple) else col 
                for col in df.columns
            ]
            #logger.debug("Flattened MultiIndex columns")

        #logger.debug(f"Output columns: {df.columns.tolist()}")
        return df

    def transform_table(self, df: pd.DataFrame, split_mode: str = None, pivot_column: str = None) -> pd.DataFrame:
        """Transform table data with rankings and formatting."""
        try:
            df = df.copy()
            df['line'] = df['line'].apply(map_line)

            # Store original data orders
            original_orders = {
                col: df[col].unique() 
                for col in self.COLS.values()
            }
            save_df_to_csv(df, f"{split_mode}_before_trans.csv")
            # Process rankings
            rank_df = self._process_rankings(df, split_mode)
            save_df_to_csv(rank_df, f"{split_mode}rank_df.csv")
            rank_df['value_type'] = 'rank'
            rank_df['value'] = rank_df['formatted_rank']
            # Combine data
            metric_data = df[df['value_type'].notna()].copy()

            combined_df = pd.concat([metric_data, rank_df], ignore_index=True)
            combined_df['year_quarter'] = pd.to_datetime(
                combined_df['year_quarter']
            ).dt.to_period('Q').astype(str)
            combined_df['column_name'] = (
                combined_df['value_type'] + '_' + combined_df['year_quarter']
            )
            save_df_to_csv(combined_df, f"{split_mode}_before_pivot.csv")
            # Get ordered columns
            quarters = sorted(combined_df['year_quarter'].unique(), reverse=True)
            # Remove 'rank' from the list and add it back at the beginning
            value_types = sorted([vt for vt in combined_df['value_type'].unique() if vt != 'rank'])
            value_types = ['rank'] + value_types
            
            # Now your ordered_cols will have rank columns first
            ordered_cols = [
                f"{vt}_{q}" for vt in value_types for q in quarters
            ]
            logger.warning(f"ordered_cols {ordered_cols}")
            logger.warning(f"value_types {value_types}")
            # Store original orders before pivot - removing nulls but preserving order
            original_metric_order = pd.Series(combined_df['metric_base'].unique()).dropna().tolist()
            original_insurer_order = pd.Series(combined_df['insurer'].unique()).dropna().tolist()
            # Create pivot table and immediately flatten it
            pivot_df = pd.pivot_table(
                combined_df,
                index=list(self.COLS.values()),
                columns='column_name',
                values='value',
                aggfunc='first',
                observed=True,
                dropna=False
            )
            # Flatten the pivot table structure
            pivot_df = self._flatten_multiindex(pivot_df)

            oldest_quarter = min(quarters)
            rank_col_to_remove = f"rank_{oldest_quarter}"
            if rank_col_to_remove in pivot_df.columns:
                pivot_df = pivot_df.drop(columns=[rank_col_to_remove])
                ordered_cols.remove(rank_col_to_remove)            
            # Set up categorical ordering for both insurer and metric
            pivot_df = pivot_df.set_index(list(self.COLS.values()))

            # Get level indices
            metric_level_idx = pivot_df.index.names.index('metric_base')
            insurer_level_idx = pivot_df.index.names.index('insurer')
            def safe_categorical(x, categories):
                # Convert Index to Series if needed
                if isinstance(x, pd.Index):
                    x = pd.Series(x)

                # Handle nulls while preserving order
                valid_mask = x.notna()
                valid_values = x[valid_mask]
                valid_categories = [cat for cat in categories if pd.notna(cat)]

                if x.name == 'insurer':
                    # Special handling for insurers to preserve top/total ordering
                    special_mask = valid_values.str.lower().str.contains(r'^топ|^top|^total|весь рынок', na=False)
                    special_insurers = valid_values[special_mask].unique()
                    regular_insurers = [ins for ins in valid_categories if ins not in special_insurers]
                    final_categories = regular_insurers + list(special_insurers)
                else:
                    final_categories = valid_categories

                # Create categorical directly for all values
                result = pd.Categorical(
                    x,
                    categories=final_categories,
                    ordered=True
                )

                return result

            # Use in sort_index
            pivot_df = pivot_df.reorder_levels(
                order=[i for i in range(len(pivot_df.index.names))],
                axis=0
            ).sort_index(
                level=[metric_level_idx, insurer_level_idx],
                key=lambda x: safe_categorical(x, 
                    original_metric_order if x.name == 'metric_base' else original_insurer_order
                )
            )

            pivot_df = pivot_df.reset_index()
            save_df_to_csv(pivot_df, f"{split_mode}_after_pivot.csv")
            # Process metric groups
            metric_groups = {}
            for metric in original_orders['metric_base']:
                group_df = pivot_df[pivot_df['metric_base'] == metric].copy()

                # Identify summary rows
                summary_mask = group_df['insurer'].str.lower().str.contains(
                    r'^топ|^top|^total|весь рынок', na=False
                )
                regular_df = group_df[~summary_mask].copy()
                summary_df = group_df[summary_mask].copy()
                logger.warning(f"  summary_df  {summary_df}")

                if not regular_df.empty:
                    regular_df = self._flatten_multiindex(regular_df)
                    save_df_to_csv(regular_df, f"{split_mode}before hiearchy sorted_df.csv")
                    with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
                        hierarchy_dict = json.load(f)
                    if split_mode != 'line':
                        regular_df = sort_by_hierarchy(regular_df, hierarchy_dict)
                        save_df_to_csv(regular_df, f"{split_mode}after_hierarchy.csv")

                    if pivot_column != 'line' and ordered_cols and not (pivot_column == 'insurer' and split_mode == 'metric_base'):
                        first_value_col = next(
                            (col for col in ordered_cols if col in regular_df.columns),
                            None
                        )
                        logger.warning(f" first value col {first_value_col}")
                        if first_value_col:
                            #regular_df = self._sort_within_lines(regular_df, first_value_col)
                            regular_df['_sort_value'] = pd.to_numeric(
                            regular_df[first_value_col].mask(regular_df[first_value_col] == '-', float('-inf')),
                                errors='coerce'
                            )
                            regular_df.sort_values('_sort_value', ascending=False, inplace=True)
                            regular_df.drop('_sort_value', axis=1, inplace=True)

                    if not summary_df.empty:
                        summary_df = sort_by_hierarchy(summary_df, hierarchy_dict)
                        logger.warning(f"  summary_df  {summary_df}")
                        rank_cols = [col for col in summary_df.columns if col.startswith('rank_')]
                        summary_df[rank_cols] = pd.NA
                        regular_df = pd.concat([regular_df, summary_df], ignore_index=True)
                        logger.warning(f"  sorted_df  {regular_df}")
                else:
                    sorted_df = summary_df
                    with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
                        hierarchy_dict = json.load(f)
                    regular_df = sort_by_hierarchy(sorted_df, hierarchy_dict)

                metric_groups[metric] = regular_df

            # Combine results
            result_df = pd.concat(
                [metric_groups[metric] for metric in original_orders['metric_base']],
                ignore_index=True
            )

            # Select and order columns
            result_cols = list(self.COLS.values()) + [
                col for col in ordered_cols if col in result_df.columns
            ]

            return result_df[result_cols].replace([0, ''], '-').fillna('-')

        except Exception as e:
            raise

    def _sort_within_lines(self, df: pd.DataFrame, sort_col: str) -> pd.DataFrame:
        """Sort data within each line group."""
        line_groups = []
        for line in df[self.COLS['line']].unique():
            line_df = df[df[self.COLS['line']] == line].copy()
            line_df['_sort_value'] = pd.to_numeric(
                line_df[sort_col].mask(line_df[sort_col] == '-', float('-inf')),
                errors='coerce'
            )
            line_df.sort_values('_sort_value', ascending=False, inplace=True)
            line_df.drop('_sort_value', axis=1, inplace=True)
            line_groups.append(line_df)

        return pd.concat(line_groups, ignore_index=True)