from enum import Enum
from typing import Any, List, Optional, Dict
from functools import lru_cache

import pandas as pd
import numpy as np

from config.logging_config import get_logger
from constants.metrics import METRICS
from constants.translations import translate
from data_process.mappings import map_insurer, map_line
from .formatters import format_period, get_comparison_quarter, get_column_format
from .generator import generate_datatable_config

logger = get_logger(__name__)

# Constants
RANK_COL = 'N'
INSURER_COL = 'insurer'
SECTION_HEADER_COL = 'is_section_header'
LINE_COL = 'linemain'

METRIC_TYPE_UNITS = {
    'value': 'млрд. руб.',
    'average_value': 'тыс. руб.',
    'quantity': 'тыс. шт.',
    'ratio': '%',
    'default': 'млрд руб.'
}

class ColumnType(Enum):
    RANK = 'rank'
    INSURER = 'insurer'
    CHANGE = 'change'
    LINE = 'linemain'
    DEFAULT = 'default'

@lru_cache(maxsize=128)
def get_base_unit(metric: str) -> str:
    """
    Get the base unit for a metric based on its type.
    
    Args:
        metric (str): Metric identifier
        
    Returns:
        str: Base unit for the metric
    """
    if metric not in METRICS:
        return METRIC_TYPE_UNITS['default']
    
    metric_type = METRICS[metric][2]
    return METRIC_TYPE_UNITS.get(metric_type, METRIC_TYPE_UNITS['default'])

def _process_market_share_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process market share changes in the dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Processed dataframe
    """
    logger.debug("Processing market share changes")
    df_modified = df.copy()
    market_share_cols = df_modified.filter(like='market_share_change').columns
    
    if not market_share_cols.empty:
        df_modified[market_share_cols] = df_modified[market_share_cols].apply(
            lambda x: x.apply(lambda y: '-' if y in (0, '-') else y * 100)
        )
    
    return df_modified

def _get_identifier_config(col: str, split_mode: str, line: Optional[str] = None, 
                          insurer: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate identifier configuration for a column.
    
    Args:
        col (str): Column name
        split_mode (str): Split mode ('line' or 'insurer')
        line (Optional[str]): Line identifier
        insurer (Optional[str]): Insurer identifier
        
    Returns:
        Dict[str, Any]: Column configuration
    """
    logger.debug(f"Generating identifier config for column: {col}")
    
    if col in [RANK_COL, INSURER_COL] and split_mode == 'line' and line:
        name = [map_line(line[0])] + [translate(col)] * 2
    elif col in [RANK_COL, LINE_COL] and split_mode == 'insurer' and insurer:
        name = [map_insurer(insurer[0])] + [translate(col)] * 2
    else:
        name = [translate(col)] * 3
        
    return {"id": col, "name": name}

def _generate_column_configs(
    df: pd.DataFrame,
    split_mode: str,
    period_type: str,
    line: Optional[str] = None,
    insurer: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate complete column configurations for the datatable.
    
    Args:
        df (pd.DataFrame): Input dataframe
        split_mode (str): Split mode ('line' or 'insurer')
        period_type (str): Period type
        line (Optional[str]): Line identifier
        insurer (Optional[str]): Insurer identifier
        
    Returns:
        List[Dict[str, Any]]: List of column configurations
    """
    logger.debug("Generating column configurations")
    
    # Extract initial metric
    metric = next((m for m in sorted(METRICS, key=len, reverse=True)
                  if any(col.startswith(m) for col in df.columns)), '')
    logger.debug(f"Initial metric extracted: {metric}")

    column_order = ([RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL] 
                   if split_mode == 'line' else 
                   [LINE_COL, RANK_COL, INSURER_COL, SECTION_HEADER_COL])

    columns = []

    # Process identifier columns
    for col in column_order:
        if col in df.columns and col != SECTION_HEADER_COL:
            columns.append(_get_identifier_config(col, split_mode, line, insurer))

    # Process metric columns
    for col in df.columns:
        if col not in {RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}:
            curr_metric = next((m for m in sorted(METRICS, key=len, reverse=True)
                              if col.startswith(m)), '')
            quarter = col[len(curr_metric)+1:].split('_')[-1] if curr_metric else ''
            
            columns.append(_get_metric_column_config(col, curr_metric, quarter, period_type, df.columns.tolist()))
    
    return columns

def _get_metric_column_config(col: str, curr_metric: str, quarter: str, 
                            period_type: str, all_columns: List[str]) -> Dict[str, Any]:
    """
    Generate configuration for metric columns.
    
    Args:
        col (str): Column name
        curr_metric (str): Current metric
        quarter (str): Quarter identifier
        period_type (str): Period type
        all_columns (List[str]): List of all available columns
        
    Returns:
        Dict[str, Any]: Column configuration
    """
    logger.debug(f"Generating metric column config for: {col}")
    
    is_change = 'change' in col
    is_market_share = 'market_share' in col
    
    if is_change:
        comparison = get_comparison_quarter(quarter, all_columns)
        header = (f"{format_period(quarter, period_type, True)} vs "
                 f"{format_period(comparison, period_type, True)}"
                 if comparison else format_period(quarter, period_type))
        base = 'Δ(п.п.)' if is_market_share else '%Δ'
    else:
        header = format_period(quarter, period_type)
        base = translate('market_share') if is_market_share else get_base_unit(curr_metric)
    
    return {
        "id": col,
        "name": [translate(curr_metric), base, header],
        "type": "numeric",
        "format": get_column_format(col)
    }
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
def create_datatable(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    period_type: str,
    toggle_show_market_share: Optional[List[str]] = None,
    toggle_show_change: Optional[List[str]] = None,
    split_mode: str = None,
    line: str = None,
    insurer: str = None
) -> Dict[str, Any]:
    try:
        # Your existing code for processing data and generating columns
        df_modified = _process_market_share_changes(df)
        columns = _generate_column_configs(df, split_mode, period_type, line, insurer)
        
        base_config = generate_datatable_config(
            df=df,
            columns=columns,
            show_market_share="show" in (toggle_show_market_share or []),
            show_qtoq="show" in (toggle_show_change or [])
        )

        clean_line = '-'.join(line) if isinstance(line, (list, np.ndarray)) else str(line)
        clean_insurer = '-'.join(insurer) if isinstance(insurer, (list, np.ndarray)) else str(insurer)
        
        # Clean up special characters
        clean_line = clean_line.replace('\n', '').replace(' ', '')
        clean_insurer = clean_insurer.replace('\n', '').replace(' ', '')

        table_id = {
            'type': 'dynamic-table',
            'index': f"{split_mode}-{clean_line}-{clean_insurer}"
        }

        logger.debug(f"Table config ID: {table_id}")

        final_config = {
            **base_config,
            'id': table_id,
            'style_data': {
                **(base_config.get('style_data', {})),
                'cursor': 'pointer'
            },
            'style_data_conditional': [
                *base_config.get('style_data_conditional', []),
                {
                    'if': {'state': 'active'},
                    'backgroundColor': 'rgba(0, 116, 217, 0.1)',
                }
            ],
            'data': df_modified.assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer) if 'insurer' in x.columns else '',
                linemain=lambda x: x['linemain'].fillna('').map(map_line) if 'linemain' in x.columns else ''
            ).to_dict('records')
        }

        return final_config

    except Exception as e:
        logger.error(f"Error in create_datatable: {str(e)}", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Error in create_datatable: {str(e)}", exc_info=True)
        raise