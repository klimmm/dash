from functools import wraps
import json
import time
from typing import List, Optional, Dict, Literal, Callable

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.main_config import LINES_162_DICTIONARY
from constants.metrics import METRICS
from data_process.mappings import map_insurer, map_line

logger = get_logger(__name__)

PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'
RANK_COL = 'N'


def timer(func):
    """Decorator to log entry/exit and execution time for critical functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.debug(f"Entering {func.__name__}")
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_ms = (time.time() - start) * 1000
            logger.debug(f"Exiting {func.__name__} (took {elapsed_ms:.2f}ms)")
            print(f"{func.__name__} took {elapsed_ms:.2f}ms to execute")
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
    Transforms the table data by grouping, pivoting, and applying ranking.
    """
    logger.info(f"Starting table transformation: split_mode={split_mode}, rows={len(df)}")
    transformed_dfs = []
    try:
        # Determine grouping based on split_mode.
        if split_mode == 'line':
            group_col, item_col = LINE_COL, INSURER_COL
        else:
            group_col, item_col = INSURER_COL, LINE_COL

        groups = df[group_col].unique()
        logger.debug(f"Unique groups by '{group_col}': {groups}")

        for group in groups:
            group_lower = str(group).lower()
            logger.debug(f"Processing group '{group}' (normalized: '{group_lower}')")
            group_prev_ranks = prev_ranks.get(group_lower, {}) if (split_mode == 'line' and prev_ranks) else prev_ranks
            group_current_ranks = current_ranks.get(group_lower, {}) if (split_mode == 'line' and current_ranks) else current_ranks

            group_subset = df[df[group_col] == group].copy()
            logger.debug(f"Group '{group}': selected {len(group_subset)} rows")
            group_df = process_group_data(
                group_subset, group_col, item_col, map_insurer, group_prev_ranks, group_current_ranks, split_mode
            )
            logger.debug(f"Processed group '{group}' with {len(group_df)} rows")

            # For 'line' mode, sort regular (non-summary) rows by the first metric column.
            if split_mode == 'line':
                summary_mask = group_df[INSURER_COL].str.lower().str.contains(r'^топ|^total|весь рынок', na=False)
                regular_rows = group_df[~summary_mask].copy()
                if not regular_rows.empty:
                    exclude_cols = {PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}
                    metric_cols = [col for col in group_df.columns if col not in exclude_cols]
                    if metric_cols:
                        sort_col = metric_cols[0]
                        regular_rows['_sort_value'] = pd.to_numeric(
                            regular_rows[sort_col].replace('-', float('-inf')), errors='coerce'
                        )
                        regular_rows.sort_values('_sort_value', ascending=False, inplace=True)
                        regular_rows.drop(columns=['_sort_value'], inplace=True)
                        logger.debug(f"Sorted regular rows in group '{group}' by '{sort_col}'")
                group_df = pd.concat([regular_rows, group_df[summary_mask]], ignore_index=True)
                logger.debug(f"Recombined group '{group}' with total {len(group_df)} rows")
            transformed_dfs.append(group_df)

        if not transformed_dfs:
            logger.debug("No groups processed; returning empty DataFrame")
            return pd.DataFrame()

        result_df = pd.concat(transformed_dfs, ignore_index=True)
        logger.debug(f"Combined DataFrame shape before dropping extra column: {result_df.shape}")
        drop_col = LINE_COL if split_mode == 'line' else INSURER_COL
        result_df.drop(columns=[drop_col], inplace=True, errors='ignore')

        base_cols = [PLACE_COL, INSURER_COL] if split_mode == 'line' else [LINE_COL, PLACE_COL]
        other_cols = [col for col in result_df.columns if col not in base_cols]
        logger.info("Completed table transformation")
        df = result_df[base_cols + other_cols]

        if split_mode == 'insurer':
            with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as file:
                json_str = file.read()
            logger.debug(f"Unique linemain before sort: {df['linemain'].unique()}")
            df = sort_and_indent_df(df, json_str)

        return df

    except Exception as e:
        logger.error(f"Error in transform_table_data: {e}", exc_info=True)
        raise


def format_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Formats summary rows with sort priorities and placeholder replacements."""
    logger.debug("Formatting summary rows")
    if df.empty:
        logger.debug("Empty DataFrame in format_summary_rows; returning as is")
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

    df = df.assign(_sort_key=df[INSURER_COL].apply(get_sort_priority))
    df.sort_values('_sort_key', inplace=True)
    df.drop(columns=['_sort_key'], inplace=True)
    df.insert(0, PLACE_COL, np.nan)
    df[SECTION_HEADER_COL] = False
    result = df.replace(0, '-').fillna('-')
    logger.debug(f"Formatted {len(result)} summary rows")
    return result


def get_rank_change(current: int, previous: Optional[int]) -> str:
    """Calculates and formats the rank change."""
    if previous is None and current is None:
        return "-"
    if previous is None:
        return str(current)
    diff = previous - current
    sign = '+' if diff > 0 else ''
    return f"{current} ({sign}{diff})" if diff != 0 else f"{current} (-)"


def format_ranking_column(
    df: pd.DataFrame,
    prev_ranks: Optional[Dict] = None,
    current_ranks: Optional[Dict] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Annotates ranking information in the DataFrame."""
    logger.info(f"Formatting ranking column with split_mode={split_mode}, rows={len(df)}")
    if df.empty or not current_ranks:
        df.insert(0, PLACE_COL, '')
        logger.info("Empty DataFrame or missing current_ranks; skipping ranking formatting")
        return df

    result_df = df.copy()
    result_df.insert(0, PLACE_COL, '')

    def get_rank_info(row) -> str:
        if split_mode == 'line':
            curr = current_ranks.get(row[INSURER_COL])
            prev = prev_ranks.get(row[INSURER_COL]) if prev_ranks else None
        else:
            line_lower = str(row[LINE_COL]).lower()
            curr = current_ranks.get(line_lower, {}).get(row[INSURER_COL])
            prev = prev_ranks.get(line_lower, {}).get(row[INSURER_COL]) if prev_ranks else None
        return get_rank_change(curr, prev) if curr is not None else '-'

    result_df[PLACE_COL] = result_df.apply(get_rank_info, axis=1)
    logger.info("Completed ranking column formatting")
    return result_df.replace(['', 0], '-').fillna('-')


@timer
def process_group_data(
    df: pd.DataFrame,
    group_col: str,
    item_col: str,
    item_mapper: Callable,
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """
    Processes group data by pivoting, ordering metrics, and combining summary and regular rows.
    """
    logger.info(f"Processing group data with {len(df)} rows, split_mode={split_mode}")
    if df.empty:
        logger.warning("Received empty DataFrame in process_group_data")
        return pd.DataFrame()
    try:
        # Standardize period strings and create composite column names.
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
        df['column_name'] = df['metric'] + '_' + df['year_quarter']
        logger.debug("Created 'column_name' from metric and year_quarter")

        # Determine metric ordering.
        metrics = df['metric'].unique()
        sorted_metric_roots = sorted(METRICS, key=len, reverse=True)
        root_metrics = {metric: next((r for r in sorted_metric_roots if metric.startswith(r)), metric) for metric in metrics}
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
        metric_groups.sort_values(['root_order', 'metric'], inplace=True)
        logger.debug("Ordered metric groups")

        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        existing_combinations = set(df['column_name'].unique())
        ordered_cols = [
            f"{metric}_{quarter}"
            for root, group in metric_groups.groupby('root', sort=False)
            for metric in group['metric']
            for quarter in quarters
            if f"{metric}_{quarter}" in existing_combinations
        ]
        logger.debug(f"Pivot columns order: {ordered_cols}")
        df['column_name'] = pd.Categorical(df['column_name'], categories=ordered_cols, ordered=True)

        unique_lines = df[LINE_COL].unique()
        df[LINE_COL] = pd.Categorical(df[LINE_COL], categories=unique_lines, ordered=True)

        pivot_df = df.pivot_table(
            index=[INSURER_COL, LINE_COL],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True,
            dropna=False
        ).reset_index()
        pivot_df[LINE_COL] = pivot_df[LINE_COL].astype(str)
        logger.debug(f"Pivoted DataFrame shape: {pivot_df.shape}")

        summary_mask = pivot_df[INSURER_COL].str.lower().str.contains(r'^top|^total', na=False)
        regular_rows = pivot_df[~summary_mask].copy()
        summary_rows = pivot_df[summary_mask].copy() if summary_mask.any() else None
        logger.debug(f"Regular rows: {len(regular_rows)}, Summary rows: {len(summary_rows) if summary_rows is not None else 0}")

        processed_regular = format_ranking_column(regular_rows, prev_ranks, current_ranks, split_mode)
        if summary_rows is not None and not summary_rows.empty:
            processed_summary = format_summary_rows(summary_rows)
            result_df = pd.concat([processed_regular, processed_summary], ignore_index=True)
            logger.debug("Combined regular and summary rows")
        else:
            result_df = processed_regular

        # Map insurer and line names.
        result_df[INSURER_COL] = result_df[INSURER_COL].apply(map_insurer)
        result_df[LINE_COL] = result_df[LINE_COL].apply(map_line)
        result_df[SECTION_HEADER_COL] = False

        base_cols = {INSURER_COL, LINE_COL}
        metric_cols = [col for col in pivot_df.columns if col not in base_cols]
        final_cols = ([PLACE_COL] if PLACE_COL in result_df.columns else []) + [INSURER_COL, LINE_COL] + metric_cols + [SECTION_HEADER_COL]
        logger.info(f"Processed group data; final rows: {len(result_df)}")
        return result_df[final_cols].replace(0, '-').fillna('-')
    except Exception as e:
        logger.error(f"Error in process_group_data: {e}", exc_info=True)
        raise


def build_label_to_key_map(data: Dict) -> Dict[str, str]:
    """Creates a mapping from labels to keys based on a hierarchical dictionary."""
    label_map = {}
    for key, value in data.items():
        if isinstance(value, dict) and 'label' in value:
            label_map[value['label']] = key
    return label_map


def get_path_depth(data: Dict, key: str) -> int:
    """Calculates the depth of a key in the given hierarchy."""
    depth = 0
    current = key
    while True:
        parent = None
        for potential_parent, node_data in data.items():
            if 'children' in node_data and current in node_data['children']:
                parent = potential_parent
                depth += 1
                break
        if not parent:
            break
        current = parent
    return depth


def sort_and_indent_df(df: pd.DataFrame, json_str: str) -> pd.DataFrame:
    """
    Sorts DataFrame rows based on an insurance hierarchy (provided as JSON)
    and adds indentation to the 'linemain' column.
    """
    data = json.loads(json_str)
    label_order = {}
    order_idx = 0

    def process_node(key, depth=0):
        nonlocal order_idx
        if key in data:
            label = data[key]['label']
            label_order[label] = (order_idx, depth)
            order_idx += 1
            for child in data[key].get('children', []):
                process_node(child, depth + 1)

    process_node('все линии')

    def get_sort_key(label):
        return label_order.get(label, (float('inf'), 0))

    df = df.copy()
    df['sort_key'] = df['linemain'].apply(get_sort_key)
    df.sort_values(by='sort_key', inplace=True)
    min_depth = min(row[1] for row in df['sort_key'] if row[1] != float('inf'))
    df['linemain'] = df.apply(
        lambda row: "---" * (row['sort_key'][1] - min_depth if row['sort_key'][1] != float('inf') else 0) + row['linemain'],
        axis=1
    )
    df.drop(columns=['sort_key'], inplace=True)
    return df
