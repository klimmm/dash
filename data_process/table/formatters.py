from typing import List, Optional, Dict

from config.logging_config import get_logger
from dash.dash_table.Format import Format, Scheme, Group

logger = get_logger(__name__)

# Constants
YTD_FORMATS: Dict[str, str] = {
    '1': '3 мес.',
    '2': '1 пол.',
    '3': '9 мес.',
    '4': '12 мес.'
}

PERCENTAGE_INDICATORS = {'market_share', 'change', 'ratio', 'rate'}


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