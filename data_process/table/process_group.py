from typing import Optional, Dict
import numpy as np
import pandas as pd
from config.logging_config import get_logger
from constants.metrics import METRICS
from data_process.mappings import map_line, map_insurer
from data_process.io import save_df_to_csv
from .formatters import format_ranking_column, format_summary_rows

logger = get_logger(__name__)

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'


import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper
    
@timer
def process_group_data(
    df: pd.DataFrame,
    group_col: str,
    item_col: str,
    item_mapper: callable,
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """
    Process group data with enhanced metric ordering and pivot operations.
    """
    logger.info(f"Starting group data processing: rows={len(df)}, split_mode={split_mode}")
    
    if df.empty:
        logger.warning("Empty DataFrame received")
        return pd.DataFrame()
        
    try:
        # Process year_quarter and create column names
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
        df['column_name'] = df['metric'] + '_' + df['year_quarter']
        
        # Get metrics in original order
        metrics = df['metric'].unique()
        logger.info(f"Processing {len(metrics)} unique metrics")
        
        # Find root for each metric preserving original order
        root_metrics = {}
        root_order = []
        
        sorted_metric_roots = sorted(METRICS, key=len, reverse=True)
        
        # Process metrics in their original order
        for metric in metrics:
            root = next((root for root in sorted_metric_roots 
                        if metric.startswith(root)), metric)
            root_metrics[metric] = root
            if root not in root_order:
                root_order.append(root)
        
        # Create metric groups DataFrame
        metric_groups = pd.DataFrame({
            'metric': metrics,
            'root': [root_metrics[m] for m in metrics]
        })
        
        # Create root order mapping based on appearance in original data
        root_order_map = {root: idx for idx, root in enumerate(root_order)}
        metric_groups['root_order'] = metric_groups['root'].map(root_order_map)
        
        # Sort metrics within each root group
        metric_groups = metric_groups.sort_values(['root_order', 'metric'])
        
        # Get quarters in reverse chronological order
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        
        # Create set of existing combinations for efficient lookup
        existing_combinations = set(df['column_name'].unique())
        
        # Create ordered columns preserving metric grouping
        ordered_cols = []
        for _, group in metric_groups.groupby('root', sort=False):
            for metric in group['metric']:
                for quarter in quarters:
                    col_name = f"{metric}_{quarter}"
                    if col_name in existing_combinations:
                        ordered_cols.append(col_name)
        
        logger.debug(f"Created {len(ordered_cols)} ordered columns")
        logger.debug(f"before pivot {df} s")
        # Set column ordering
        df['column_name'] = pd.Categorical(
            df['column_name'],
            categories=ordered_cols,
            ordered=True
        )
        
        # Prepare line categories
        unique_lines = df[LINE_COL].unique()
        df[LINE_COL] = pd.Categorical(df[LINE_COL], categories=unique_lines, ordered=True)
        
        # Pivot data
        pivot_df = df.pivot_table(
            index=[INSURER_COL, LINE_COL],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True,
            dropna=False
        ).reset_index()
        
        pivot_df[LINE_COL] = pivot_df[LINE_COL].astype(str)
        logger.debug(f"pivot_df  {pivot_df} s")
        # Split and process summary/regular rows
        summary_mask = pivot_df[INSURER_COL].str.lower().str.contains('^top|^total', na=False)
        regular_rows = pivot_df[~summary_mask].copy()
        summary_rows = pivot_df[summary_mask].copy() if summary_mask.any() else None
        
        # Process regular rows with ranking
        processed_regular = format_ranking_column(regular_rows, prev_ranks, current_ranks, split_mode)
        
        # Process summary rows if they exist
        if summary_rows is not None:
            processed_summary = format_summary_rows(summary_rows)
            result_df = pd.concat([processed_regular, processed_summary], ignore_index=True)
        else:
            result_df = processed_regular
        
        # Apply mappings
        result_df[INSURER_COL] = result_df[INSURER_COL].apply(map_insurer)
        result_df[LINE_COL] = result_df[LINE_COL].apply(map_line)
        result_df[SECTION_HEADER_COL] = False
        
        # Organize final columns
        base_cols = {INSURER_COL, LINE_COL}
        metric_cols = [col for col in pivot_df.columns if col not in base_cols]
        final_cols = ([PLACE_COL] if PLACE_COL in result_df.columns else []) + \
                    [INSURER_COL, LINE_COL] + metric_cols + [SECTION_HEADER_COL]
        
        logger.info(f"Successfully processed group data: output_rows={len(result_df)}")
        return result_df[final_cols].replace(0, '-').fillna('-')
        
    except Exception as e:
        logger.error(f"Error in process_group_data: {str(e)}", exc_info=True)
        raise