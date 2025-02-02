from typing import List, Optional, Dict

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from dash.dash_table.Format import Format, Scheme, Group
from config.logging_config import get_logger
from constants.metrics import METRICS

logger = get_logger(__name__)

# Constants
YTD_FORMATS: Dict[str, str] = {
    '1': '3 мес.',
    '2': '1 пол.',
    '3': '9 мес.',
    '4': '12 мес.'
}

PERCENTAGE_INDICATORS = {'market_share', 'change', 'ratio', 'rate'}

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'


def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """
    Format quarter string into readable period format.

    Args:
        quarter_str: Quarter string in format 'YYYYQN'
        period_type: Type of period ('ytd', 'yoy_y', 'yoy_q', etc.)
        comparison: Whether this is a comparison period

    Returns:
        Formatted period string
    """
    logger.debug(f"Formatting period: quarter_str={quarter_str}, type={period_type}, comparison={comparison}")

    if not quarter_str or len(quarter_str) != 6:
        logger.debug(f"Invalid quarter string format: {quarter_str}")
        return quarter_str

    try:
        year_short = quarter_str[2:4]
        quarter = quarter_str[5]

        if period_type == 'ytd':
            if comparison:
                return year_short
            return f"{YTD_FORMATS[quarter]} {year_short}"

        if comparison and period_type in ['yoy_y', 'yoy_q']:
            return year_short

        return f"{quarter}кв." if comparison else f"{quarter} кв. {year_short}"

    except Exception as e:
        logger.error(f"Error formatting period: {e}", exc_info=True)
        return quarter_str


def get_comparison_quarter(current_quarter: str, columns: List[str]) -> Optional[str]:
    """
    Get the comparison quarter for a given quarter.

    Args:
        current_quarter: Current quarter string in format 'YYYYQN'
        columns: List of column names

    Returns:
        Comparison quarter string or None if not found
    """
    logger.debug(f"Getting comparison quarter for: {current_quarter}")

    if not current_quarter:
        return None

    try:
        year, q_num = current_quarter[:4], current_quarter[5]

        candidates = [
            f"{int(year)-1}Q{q_num}",  # year ago
            f"{year}Q{str(int(q_num)-1)}" if q_num != '1' else f"{int(year)-1}Q4"  # previous quarter
        ]

        base_columns = [col for col in columns if '_change' not in col]

        for candidate in candidates:
            if any(candidate in col for col in base_columns):
                logger.info(f"Found comparison quarter: {candidate}")
                return candidate

        logger.debug(f"No comparison quarter found for {current_quarter}")
        return None

    except Exception as e:
        logger.error(f"Error getting comparison quarter: {e}", exc_info=True)
        return None


def get_column_format(col_name: str) -> Format:
    """
    Get format configuration for a column.

    Args:
        col_name: Column name

    Returns:
        Format configuration for the column
    """
    logger.debug(f"Getting format for column: {col_name}")

    try:
        is_market_share_qtoq = 'market_share_change' in col_name
        is_percentage = any(indicator in col_name for indicator in PERCENTAGE_INDICATORS)

        format_config = Format(
            precision=2 if is_percentage or is_market_share_qtoq else 3,
            scheme=Scheme.fixed if is_market_share_qtoq else 
                   Scheme.percentage if is_percentage else Scheme.fixed,
            group=Group.yes,
            groups=3,
            group_delimiter=',',
            sign='+' if 'change' in col_name else ''
        )

        logger.debug(f"Created format config: {format_config}")
        return format_config

    except Exception as e:
        logger.error(f"Error creating column format: {e}", exc_info=True)
        # Return a safe default format
        return Format(
            precision=3,
            scheme=Scheme.fixed,
            group=Group.yes,
            groups=3,
            group_delimiter=','
        )

def format_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Process summary data rows with sorting logic for totals and top-N entries."""
    logger.debug("Processing summary rows")
    if df.empty:
        return df

    # Simplified sort key function
    def get_sort_priority(ins: str) -> tuple:
        ins_lower = ins.lower()
        if ins_lower.startswith('total'): return (2, 0)
        if ins_lower.startswith('top-'):
            try:
                return (1, int(ins.split('-')[1]))
            except (IndexError, ValueError):
                logger.debug(f"Invalid top-N format: {ins}")
                return (1, 0)
        return (0, 0)

    df = df.sort_values(
        by=INSURER_COL, 
        key=lambda x: pd.Series([get_sort_priority(ins) for ins in x])
    )
    
    # Initialize new columns efficiently
    df.insert(0, PLACE_COL, np.nan)
    df[SECTION_HEADER_COL] = False
    
    logger.debug(f"Processed {len(df)} summary rows")
    return df.replace(0, '-').fillna('-')

def get_rank_change(current: int, previous: Optional[int]) -> str:
    """Calculate and format rank change."""
    if previous is None and current is None:
        return f"-"
    if previous is None:
        return str(current)
    diff = previous - current
    if diff == 0:
        return f"{current} (-)"
    return f"{current} ({'+' if diff > 0 else ''}{diff})"

def format_ranking_column(
    df: pd.DataFrame,
    prev_ranks: Optional[Dict] = None,
    current_ranks: Optional[Dict] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Process insurance company rankings and format rank changes."""
    logger.info(f"Formatting ranking column: split_mode={split_mode}, rows={len(df)}")
    
    if df.empty or not current_ranks:
        df.insert(0, PLACE_COL, '')
        return df

    result_df = df.copy()
    result_df.insert(0, PLACE_COL, '')

    def get_rank_info(row):
        if split_mode == 'line':
            insurer = row[INSURER_COL]
            curr = current_ranks.get(insurer)
            prev = prev_ranks.get(insurer) if prev_ranks else None
        else:  # split_mode == 'insurer'
            line, insurer = row[LINE_COL], row[INSURER_COL]
            line_ranks = current_ranks.get(line.lower(), {})
            curr = line_ranks.get(insurer)
            prev = prev_ranks.get(line.lower(), {}).get(insurer) if prev_ranks else None
        
        return get_rank_change(curr, prev) if curr is not None else '-'  # Changed to '-'

    result_df[PLACE_COL] = result_df.apply(get_rank_info, axis=1)
    logger.info(f"Completed ranking column formatting")
    return result_df.replace(['', 0], '-').fillna('-') 
