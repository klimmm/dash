from typing import cast, List, NewType, Set, TypedDict

import pandas as pd

from config.logging_config import timer, get_logger

logger = get_logger(__name__)

YearQuarter = NewType('YearQuarter', str)  # Format: "YYYYQN" (e.g., "2024Q1")


class YearQuarterOption(TypedDict):
    label: YearQuarter
    value: YearQuarter


@timer
def get_available_quarters(df: pd.DataFrame) -> Set[YearQuarter]:
    """Get set of available quarters in YYYYQN format."""
    # Cast the string set to YearQuarter set since we know the format is corret
    logger.debug(f" year_quarter unique {df['year_quarter'].unique()}")
    available_quarters = cast(
        Set[YearQuarter],
        {YearQuarter(f"{dt.year}Q{dt.quarter}") for dt in df['year_quarter']}
    )
    logger.debug(f" available_quarters {available_quarters}")
    return available_quarters


@timer
def get_year_quarter_options(df: pd.DataFrame) -> List[YearQuarterOption]:
    # Get unique and sorted values in one operation
    unique_quarters = pd.Series(df['year_quarter'].unique()).sort_values()

    # Pre-allocate result list with proper typing
    result_size = len(unique_quarters)
    quarter_options: List[YearQuarterOption] = []

    # Vectorized operations for extracting year and quarter
    years = unique_quarters.dt.year
    quarters = unique_quarters.dt.quarter

    # Build options list
    for i in range(result_size):
        quarter_str = YearQuarter(f"{years[i]}Q{quarters[i]}")
        quarter_options.append({
            'label': quarter_str,
            'value': quarter_str
        })

    return quarter_options