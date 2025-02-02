from typing import List, Optional, Dict, Literal

import pandas as pd

from config.logging_config import get_logger
from data_process.mappings import map_line, map_insurer
from .process_group import process_group_data

logger = get_logger(__name__)


def timer(func):
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'

    
@timer
def transform_table_data(
    df: pd.DataFrame,
    selected_metrics: List[str],
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    current_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    split_mode: Literal['line', 'insurer'] = 'line'
) -> pd.DataFrame:
    """Transform and format table data with enhanced error handling and logging."""
    logger.info(f"Starting table transformation: split_mode={split_mode}, rows={len(df)}")

    try:
        # Configure grouping
        group_configs = {
            'line': (LINE_COL, INSURER_COL, map_line, map_insurer),
            'insurer': (INSURER_COL, LINE_COL, map_insurer, map_line)
        }
        group_col, item_col, group_mapper, item_mapper = group_configs[split_mode]

        transformed_dfs = []
        for group in df[group_col].unique():
            logger.debug(f"Processing group: {group}")

            # Get group-specific ranks
            group_prev_ranks = prev_ranks.get(group.lower(), {}) if split_mode == 'line' and prev_ranks else prev_ranks
            group_current_ranks = current_ranks.get(group.lower(), {}) if split_mode == 'line' and current_ranks else current_ranks

            group_df = process_group_data(
                df[df[group_col] == group].copy(),
                group_col,
                item_col,
                item_mapper,
                group_prev_ranks,
                group_current_ranks,
                split_mode
            )
            logger.debug(f"group_df {group_df}")
            metric_cols = [col for col in group_df.columns 
                         if col not in [PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL]]

            # Sort non-summary rows by first metric
            is_summary = group_df[INSURER_COL].str.lower().str.contains(
                '^топ|^total|весь рынок', 
                na=False
            )
            regular_rows = group_df[~is_summary].copy()
            if split_mode == 'line':
                if not regular_rows.empty:
                    regular_rows['_sort_value'] = pd.to_numeric(
                        regular_rows[metric_cols[0]].replace('-', float('-inf')), 
                        errors='coerce'
                    )
                    regular_rows = regular_rows.sort_values(
                        '_sort_value', 
                        ascending=False
                    ).drop(columns=['_sort_value'])

            group_df = pd.concat([regular_rows, group_df[is_summary]])
            logger.debug(f"group_df {group_df}")
            transformed_dfs.append(group_df)

        if not transformed_dfs:
            logger.debug("No data to transform")
            return pd.DataFrame()

        # Combine and format final output
        result_df = pd.concat(transformed_dfs, ignore_index=True)
        logger.debug(f"result_df {result_df}")
        drop_col = LINE_COL if split_mode == 'line' else INSURER_COL
        result_df = result_df.drop(columns=[drop_col])

        # Reorder columns
        base_cols = ['N', 'insurer'] if split_mode == 'line' else ['linemain', 'N']
        other_cols = [col for col in result_df.columns if col not in base_cols]

        logger.info("Table transformation completed successfully")
        return result_df[base_cols + other_cols]

    except Exception as e:
        logger.error(f"Error in table transformation: {str(e)}", exc_info=True)
        raise