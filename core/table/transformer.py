import json
from typing import Any, Dict, Generator, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd

from config.app_config import LINES_162_DICTIONARY
from config.logging import get_logger, timer
from core.insurers.mapper import map_insurer
from core.lines.mapper import map_line
from core.metrics.definitions import METRICS

logger = get_logger(__name__)


class TableTransformer:
    """Handles table data transformation and ranking operations."""

    def __init__(self) -> None:
        self.PLACE_COL = 'N'
        self.INSURER_COL = 'insurer'
        self.LINE_COL = 'linemain'

    @staticmethod
    def _get_rank_change(current: Optional[int], previous: Optional[int]
                         ) -> str:
        """Calculate rank change with formatting."""
        # Handle cases where either value is None
        if current is None:
            logger.debug(f"current is none - previous {previous} ")

        if previous is None and current is None:
            return "-"
        if previous is None:
            return str(current)
        if current is None:
            return "-"

        # Now we know both values are integers
        diff = previous - current
        return (
            f"{current} ({'+' if diff > 0 else ''}{diff})"
            if diff != 0 else f"{current} (-)"
        )

    def _get_ordered_metrics(self, metrics: np.ndarray) -> pd.DataFrame:
        """Order metrics by root and within root groups."""
        sorted_metric_roots = sorted(METRICS, key=len, reverse=True)
        root_metrics = {m: next((r for r in sorted_metric_roots if m.
                                 startswith(r)), m) for m in metrics}

        root_order = []
        for root in root_metrics.values():
            if root not in root_order:
                root_order.append(root)

        metric_groups = pd.DataFrame({
            'metric': metrics,
            'root': [root_metrics[m] for m in metrics]
        })
        root_order_map = {root: idx for idx, root in enumerate(root_order)}
        metric_groups['root_order'] = metric_groups['root'].map(root_order_map)

        result_df = metric_groups.sort_values(['root_order', 'metric'])

        return result_df

    def _process_group(self, df: pd.DataFrame,
                       prev_ranks: Optional[Dict] = None,
                       current_ranks: Optional[Dict] = None,
                       split_mode: str = 'line') -> pd.DataFrame:
        """Process a single group of data."""
        if df.empty:
            return pd.DataFrame()

        # Create period-metric columns
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period(
            'Q').astype(str)
        df['column_name'] = df['metric'] + '_' + df['year_quarter']

        # Order metrics
        metric_groups = self._get_ordered_metrics(df['metric'].unique())
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        existing_combinations = set(df['column_name'].unique())

        ordered_cols = [
            f"{metric}_{quarter}"
            for _, group in metric_groups.groupby('root', sort=False)
            for metric in group['metric']
            for quarter in quarters
            if f"{metric}_{quarter}" in existing_combinations
        ]

        # Pivot and process
        pivot_df = df.pivot_table(
            index=[self.INSURER_COL, self.LINE_COL],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True,
            dropna=False
        ).reset_index()

        # Handle regular and summary rows
        summary_mask = pivot_df[
            self.INSURER_COL
        ].str.lower().str.contains(r'^top|^total', na=False)
        regular_rows = pivot_df[~summary_mask].copy()
        summary_rows = pivot_df[summary_mask].copy() if summary_mask.any(
        ) else None

        # Process regular rows with rankings
        if current_ranks:
            regular_rows[self.PLACE_COL] = regular_rows.apply(
                lambda row: self._get_rank_change(
                    current_ranks.get(row[self.INSURER_COL]),
                    prev_ranks.get(row[self.INSURER_COL])
                    if prev_ranks else None
                ) if split_mode == 'line' else self._get_rank_change(
                    current_ranks.get(str(row[self.LINE_COL]).lower(),
                                      {}).get(row[self.INSURER_COL]
                                              ),
                    prev_ranks.get(str(row[self.LINE_COL]).lower(),
                                   {}).get(row[self.INSURER_COL])
                    if prev_ranks else None
                ),
                axis=1
            )

        # Process summary rows
        if summary_rows is not None and not summary_rows.empty:
            summary_rows[self.PLACE_COL] = np.nan
            result_df = pd.concat(
                [regular_rows, summary_rows], ignore_index=True
            )
        else:
            result_df = regular_rows

        # Clean and format
        result_df[self.INSURER_COL] = result_df[
            self.INSURER_COL
        ].apply(map_insurer)
        result_df[self.LINE_COL] = result_df[self.LINE_COL].apply(map_line)

        # Reorder columns
        metric_cols = [col for col in ordered_cols if col in result_df.columns]
        base_cols = [self.PLACE_COL, self.INSURER_COL, self.LINE_COL]
        result_df = result_df[base_cols + metric_cols]

        return result_df.replace([0, ''], '-').fillna('-')

    def _sort_by_hierarchy(self, df: pd.DataFrame,
                           hierarchy: Dict[str, Any]) -> pd.DataFrame:
        """Sort DataFrame based on insurance line hierarchy."""
        def get_node_info(key: str, depth: int = 0) -> Generator[Tuple[str, int], None, None]:
            if key in hierarchy:
                yield (hierarchy[key]['label'], depth)
                for child in hierarchy[key].get('children', []):
                    yield from get_node_info(child, depth + 1)

        # Build sorting order
        order_map = {label: (i, depth) for i, (label, depth) in
                     enumerate(get_node_info('все линии'))}

        # Apply sort and indent
        df = df.copy()
        df['_sort'] = df['linemain'].map(
            lambda x: order_map.get(x, (float('inf'), 0))
        )
        df.sort_values('_sort', inplace=True)
        min_depth = min(
            depth for _, depth in df['_sort'] if depth != float('inf')
        )
        df['linemain'] = df.apply(
            lambda row:
            "---" * (
                row['_sort'][1] - min_depth
                if row['_sort'][1] != float('inf') else 0
            ) + row['linemain'], axis=1
        )
        return df.drop('_sort', axis=1)

    @timer
    def transform_table(
        self,
        df: pd.DataFrame,
        selected_metrics: List[str],
        prev_ranks: Optional[Dict[str, Dict[str, int]]] = None,
        current_ranks: Optional[Dict[str, Dict[str, int]]] = None,
        split_mode: Literal['line', 'insurer'] = 'line'
    ) -> pd.DataFrame:
        """Transform table data with rankings and formatting."""
        if df.empty:
            return pd.DataFrame()

        # Set grouping columns based on split mode
        group_col, item_col = (
            self.LINE_COL, self.INSURER_COL
        ) if split_mode == 'line' else (
            self.INSURER_COL, self.LINE_COL
        )

        # Process each group
        transformed = []
        for group in df[group_col].unique():
            group_lower = str(group).lower()
            group_prev_ranks = prev_ranks.get(group_lower, {}) if (
                split_mode == 'line' and prev_ranks
            ) else prev_ranks
            group_current_ranks = current_ranks.get(group_lower, {}) if (
                split_mode == 'line' and current_ranks
            ) else current_ranks

            group_df = self._process_group(
                df[df[group_col] == group],
                group_prev_ranks,
                group_current_ranks,
                split_mode
            )
            transformed.append(group_df)

        if not transformed:
            return pd.DataFrame()

        # Combine results
        result = pd.concat(transformed, ignore_index=True)

        # Sort by first metric column for line mode
        if split_mode == 'line':
            # Get first metric column (excluding base and header columns)
            exclude_cols = {self.PLACE_COL, self.INSURER_COL, self.LINE_COL}
            metric_cols = [
                col for col in result.columns if col not in exclude_cols
            ]
            if metric_cols:
                # Identify and exclude summary rows from sorting
                summary_mask = result[
                    self.INSURER_COL
                ].str.lower().str.contains(r'^топ|^total|весь рынок', na=False)
                regular_rows = result[~summary_mask].copy()
                summary_rows = result[summary_mask]

                if not regular_rows.empty:
                    sort_col = metric_cols[0]
                    # Convert values to numeric, treating '-' as negative inf
                    regular_rows['_sort_value'] = pd.to_numeric(
                        regular_rows[sort_col].mask(
                            regular_rows[sort_col] == '-', float('-inf')
                        ),
                        errors='coerce'
                    )
                    regular_rows.sort_values(
                        '_sort_value', ascending=False, inplace=True
                    )
                    regular_rows.drop(columns=['_sort_value'], inplace=True)
                    # Recombine sorted regular rows with summary rows
                    result = pd.concat(
                        [regular_rows, summary_rows], ignore_index=True
                    )

        # Drop appropriate column based on split mode
        drop_col = self.LINE_COL if split_mode == 'line' else self.INSURER_COL
        result.drop(columns=[drop_col], inplace=True, errors='ignore')

        # Sort by hierarchy if needed
        if split_mode == 'insurer':
            with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
                hierarchy = json.load(f)
            result = self._sort_by_hierarchy(result, hierarchy)

        return result.replace([0, ''], '-').fillna('-')