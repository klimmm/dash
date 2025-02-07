import pandas as pd

from config.logging_config import timer, get_logger

logger = get_logger(__name__)


@timer
def get_year_quarter_options(df):
    # Get unique and sorted values in one operation
    unique_quarters = pd.Series(df['year_quarter'].unique()).sort_values()

    # Pre-allocate result list
    result_size = len(unique_quarters)
    quarter_options = [None] * result_size

    # Vectorized operations for extracting year and quarter
    years = unique_quarters.dt.year
    quarters = unique_quarters.dt.quarter

    # Build options list
    for i in range(result_size):
        quarter_str = f"{years[i]}Q{quarters[i]}"
        quarter_options[i] = {'label': quarter_str, 'value': quarter_str}

    return quarter_options