from typing import List, Optional, Dict, Literal, Callable
import time
from functools import wraps

import pandas as pd
import numpy as np

from config.logging_config import get_logger
from data_process.mappings import map_line, map_insurer
from constants.metrics import METRICS

logger = get_logger(__name__)

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'


def timer(func):
    """Decorator to log entry/exit and timing for critical functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.debug(f"Entering function {func.__name__}")
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000
        logger.debug(f"Exiting function {func.__name__} (took {elapsed_ms:.2f}ms)")
        print(f"{func.__name__} took {elapsed_ms:.2f}ms to execute")
        return result
    return wrapper


@timer
def transform_table_data(
    df: pd.DataFrame,
    selected_metrics: List[str],
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    current_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    split_mode: Literal['line', 'insurer'] = 'line'
) -> pd.DataFrame:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    Updates period selection.
    """
    logger.info(f"Starting table transformation: split_mode={split_mode}, rows={len(df)}")
    transformed_dfs = []

    try:
        # Configure grouping based on split_mode.
        if split_mode == 'line':
            group_col, item_col, item_mapper = LINE_COL, INSURER_COL, map_insurer
        else:
            group_col, item_col, item_mapper = INSURER_COL, LINE_COL, map_line

        # Process each group separately.
        groups = df[group_col].unique()
        logger.debug(f"Found {len(groups)} unique groups by '{group_col}'")
        for group in groups:
            group_lower = str(group).lower()
            logger.debug(f"Processing group: '{group}' (normalized: '{group_lower}')")

            # Select group-specific ranking dictionaries when in 'line' mode.
            group_prev_ranks = (prev_ranks.get(group_lower, {}) if (split_mode == 'line' and prev_ranks)
                                else prev_ranks)
            group_current_ranks = (current_ranks.get(group_lower, {}) if (split_mode == 'line' and current_ranks)
                                   else current_ranks)

            group_subset = df[df[group_col] == group].copy()
            logger.debug(f"Group '{group}': {len(group_subset)} rows selected")
            group_df = process_group_data(
                group_subset,
                group_col,
                item_col,
                item_mapper,  # Passed for backwards compatibility (not used in current logic)
                group_prev_ranks,
                group_current_ranks,
                split_mode
            )
            logger.debug(f"Processed group data for '{group}' with {len(group_df)} rows")

            # For 'line' mode, sort regular (non-summary) rows by the first metric column.
            if split_mode == 'line':
                # Use a regex that covers both English and Cyrillic variants.
                summary_mask = group_df[INSURER_COL].str.lower().str.contains(r'^топ|^total|весь рынок', na=False)
                regular_rows = group_df[~summary_mask].copy()
                if not regular_rows.empty:
                    # Identify metric columns by excluding base columns.
                    exclude_cols = {PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}
                    metric_cols = [col for col in group_df.columns if col not in exclude_cols]
                    if metric_cols:
                        sort_col = metric_cols[0]
                        # Convert non-numeric (or '-' placeholders) to numeric; missing values get -inf.
                        regular_rows['_sort_value'] = pd.to_numeric(
                            regular_rows[sort_col].replace('-', float('-inf')), errors='coerce'
                        )
                        regular_rows.sort_values('_sort_value', ascending=False, inplace=True)
                        regular_rows.drop(columns=['_sort_value'], inplace=True)
                        logger.debug(f"Sorted regular rows in group '{group}' by '{sort_col}'")
                    else:
                        logger.debug(f"No metric columns found to sort regular rows in group '{group}'")
                # Recombine: regular rows come first, then summary rows.
                group_df = pd.concat([regular_rows, group_df[summary_mask]], ignore_index=True)
                logger.debug(f"Recombined group '{group}' data: {len(group_df)} rows total")

            transformed_dfs.append(group_df)

        if not transformed_dfs:
            logger.debug("No groups were processed; returning empty DataFrame")
            return pd.DataFrame()

        # Combine all groups into one DataFrame.
        result_df = pd.concat(transformed_dfs, ignore_index=True)
        logger.debug(f"Combined result before dropping extra column: {result_df.shape}")

        # Drop the column not needed in final output.
        drop_col = LINE_COL if split_mode == 'line' else INSURER_COL
        result_df.drop(columns=[drop_col], inplace=True, errors='ignore')

        # Reorder columns according to split_mode.
        if split_mode == 'line':
            base_cols = [PLACE_COL, INSURER_COL]
        else:
            base_cols = [LINE_COL, PLACE_COL]
        other_cols = [col for col in result_df.columns if col not in base_cols]
        logger.info("Table transformation completed successfully")
        return result_df[base_cols + other_cols]

    except Exception as e:
        logger.error(f"Error in table transformation: {e}", exc_info=True)
        raise


@timer
def format_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Process summary rows with sorting logic for totals and top-N entries."""
    logger.debug("Entering format_summary_rows")
    if df.empty:
        logger.debug("No summary rows to process; returning empty DataFrame")
        return df

    def get_sort_priority(ins: str) -> tuple:
        ins_lower = ins.lower()
        if ins_lower.startswith('total'):
            return (2, 0)
        if ins_lower.startswith('top-'):
            try:
                return (1, int(ins.split('-')[1]))
            except (IndexError, ValueError):
                logger.debug(f"Invalid top-N format: {ins}")
                return (1, 0)
        return (0, 0)

    # Compute sort priorities for each row based on the insurer string.
    sort_priorities = df[INSURER_COL].apply(get_sort_priority)
    df = df.assign(_sort_key=sort_priorities).sort_values('_sort_key').drop(columns=['_sort_key'])

    # Insert placeholder ranking and mark as non-section header.
    df.insert(0, PLACE_COL, np.nan)
    df[SECTION_HEADER_COL] = False

    result = df.replace(0, '-').fillna('-')
    logger.debug(f"Processed {len(result)} summary rows in format_summary_rows")
    logger.debug("Exiting format_summary_rows")
    return result


@timer
def get_rank_change(current: int, previous: Optional[int]) -> str:
    """Calculate and format rank change."""
    if previous is None and current is None:
        return "-"
    if previous is None:
        return str(current)
    diff = previous - current
    if diff == 0:
        return f"{current} (-)"
    sign = '+' if diff > 0 else ''
    return f"{current} ({sign}{diff})"


@timer
def format_ranking_column(
    df: pd.DataFrame,
    prev_ranks: Optional[Dict] = None,
    current_ranks: Optional[Dict] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Format insurance company rankings and annotate rank changes."""
    logger.info(f"Entering format_ranking_column: split_mode={split_mode}, rows={len(df)}")

    if df.empty or not current_ranks:
        df.insert(0, PLACE_COL, '')
        logger.info("Empty DataFrame or no current_ranks provided; skipping ranking format")
        return df

    result_df = df.copy()
    result_df.insert(0, PLACE_COL, '')

    def get_rank_info(row) -> str:
        if split_mode == 'line':
            insurer = row[INSURER_COL]
            curr = current_ranks.get(insurer)
            prev = prev_ranks.get(insurer) if prev_ranks else None
        else:
            line = row[LINE_COL]
            insurer = row[INSURER_COL]
            curr = current_ranks.get(str(line).lower(), {}).get(insurer)
            prev = prev_ranks.get(str(line).lower(), {}).get(insurer) if prev_ranks else None
        return get_rank_change(curr, prev) if curr is not None else '-'

    # Compute ranking for each row.
    result_df[PLACE_COL] = result_df.apply(get_rank_info, axis=1)
    logger.info("Exiting format_ranking_column")
    return result_df.replace(['', 0], '-').fillna('-')


@timer
def process_group_data(
    df: pd.DataFrame,
    group_col: str,
    item_col: str,
    item_mapper: Callable,  # Provided for backwards compatibility; not used below.
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """
    Process group data with metric ordering and pivot operations.
    """
    logger.info(f"Entering process_group_data: rows={len(df)}, split_mode={split_mode}")
    if df.empty:
        logger.warning("Empty DataFrame received in process_group_data")
        return pd.DataFrame()

    try:
        # Process 'year_quarter' to standard period strings.
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
        df['column_name'] = df['metric'] + '_' + df['year_quarter']
        logger.debug("Created 'column_name' based on metric and year_quarter")

        # Determine ordering based on unique metrics.
        metrics = df['metric'].unique()
        logger.info(f"Processing {len(metrics)} unique metrics")

        sorted_metric_roots = sorted(METRICS, key=len, reverse=True)
        root_metrics = {}
        root_order = []
        for metric in metrics:
            root = next((r for r in sorted_metric_roots if metric.startswith(r)), metric)
            root_metrics[metric] = root
            if root not in root_order:
                root_order.append(root)

        # Build a DataFrame to assist with ordering.
        metric_groups = pd.DataFrame({
            'metric': metrics,
            'root': [root_metrics[m] for m in metrics]
        })
        root_order_map = {root: idx for idx, root in enumerate(root_order)}
        metric_groups['root_order'] = metric_groups['root'].map(root_order_map)
        metric_groups.sort_values(['root_order', 'metric'], inplace=True)
        logger.debug("Ordered metric groups based on root and metric name")

        # Order quarters in reverse chronological order.
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        existing_combinations = set(df['column_name'].unique())
        ordered_cols = [
            f"{metric}_{quarter}"
            for root, group in metric_groups.groupby('root', sort=False)
            for metric in group['metric']
            for quarter in quarters
            if f"{metric}_{quarter}" in existing_combinations
        ]
        logger.debug(f"Ordered pivot columns: {ordered_cols}")

        # Set the ordering for the 'column_name' field.
        df['column_name'] = pd.Categorical(df['column_name'], categories=ordered_cols, ordered=True)

        # Ensure proper ordering for LINE_COL.
        unique_lines = df[LINE_COL].unique()
        df[LINE_COL] = pd.Categorical(df[LINE_COL], categories=unique_lines, ordered=True)

        # Pivot the DataFrame to a wide format.
        pivot_df = df.pivot_table(
            index=[INSURER_COL, LINE_COL],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True,
            dropna=False
        ).reset_index()
        # Convert LINE_COL to string.
        pivot_df[LINE_COL] = pivot_df[LINE_COL].astype(str)
        logger.debug(f"Pivoted DataFrame shape: {pivot_df.shape}")

        # Split pivoted data into regular and summary rows.
        summary_mask = pivot_df[INSURER_COL].str.lower().str.contains(r'^top|^total', na=False)
        regular_rows = pivot_df[~summary_mask].copy()
        summary_rows = pivot_df[summary_mask].copy() if summary_mask.any() else None
        logger.debug(f"Identified {len(regular_rows)} regular rows and "
                     f"{len(summary_rows) if summary_rows is not None else 0} summary rows")

        # Process ranking for regular rows.
        processed_regular = format_ranking_column(regular_rows, prev_ranks, current_ranks, split_mode)

        # Process summary rows if they exist.
        if summary_rows is not None and not summary_rows.empty:
            processed_summary = format_summary_rows(summary_rows)
            result_df = pd.concat([processed_regular, processed_summary], ignore_index=True)
            logger.debug("Combined processed regular and summary rows")
        else:
            result_df = processed_regular

        # Apply mappings to standardize insurer and line names.
        result_df[INSURER_COL] = result_df[INSURER_COL].apply(map_insurer)
        result_df[LINE_COL] = result_df[LINE_COL].apply(map_line)
        result_df[SECTION_HEADER_COL] = False

        # Organize final column order.
        base_cols = {INSURER_COL, LINE_COL}
        metric_cols = [col for col in pivot_df.columns if col not in base_cols]
        final_cols = ( [PLACE_COL] if PLACE_COL in result_df.columns else [] ) + \
                     [INSURER_COL, LINE_COL] + metric_cols + [SECTION_HEADER_COL]

        logger.info(f"Exiting process_group_data: output_rows={len(result_df)}")
        return result_df[final_cols].replace(0, '-').fillna('-')

    except Exception as e:
        logger.error(f"Error in process_group_data: {e}", exc_info=True)
        raise