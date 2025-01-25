# data_process.filter_period_type

import pandas as pd
import numpy as np
from memory_profiler import profile
from config.logging_config import get_logger
logger = get_logger(__name__)

#@profile
def filter_by_period_type(
    df: pd.DataFrame,
    period_type: str
) -> pd.DataFrame:

    """Filter data by date range and period type with optimized performance."""
    df = df.copy()
    grouping_cols = [col for col in df.columns if col not in {'year_quarter', 'value', 'quarter'}]
    end_quarter_num = df['year_quarter'].max().quarter

    if period_type == 'yoy_q':
        df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
        df = df[df['year_quarter'].dt.quarter == end_quarter_num]
        df = df.drop(columns=['quarter'])

    elif period_type == 'ytd':
        df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
        df['year'] = df['year_quarter'].dt.year.to_numpy()

        complete_years = (df[df['quarter'] == 1]
                 .groupby('year')
                 .size()
                 .index)

        # Filter to keep only those years
        df = df[df['year'].isin(complete_years)]


        df = (df[df['year_quarter'].dt.quarter <= end_quarter_num]
              .assign(year=lambda x: x['year_quarter'].dt.year,
                     ytd_value=lambda x: x.groupby(['year'] + grouping_cols)['value'].cumsum())
              .assign(value=lambda x: x['ytd_value'])
              .drop(columns=['ytd_value', 'quarter'])
              .loc[lambda x: x['year_quarter'].dt.quarter == end_quarter_num]
              .reset_index(drop=True))
        df = df.drop(columns=['year'])
    elif period_type in ['mat', 'yoy_y']:
        df = df.sort_values(grouping_cols + ['year_quarter'])
        df['quarter_end'] = df['year_quarter'] + pd.offsets.QuarterEnd() 
        start_date = df.groupby(grouping_cols)['year_quarter'].transform('min')
        df['days_history'] = (df['quarter_end'] - start_date).dt.total_seconds() / (24 * 60 * 60)
        df = df.drop(columns=['quarter_end'])
        df.set_index('year_quarter', inplace=True)
        df['value'] = df.groupby(grouping_cols)['value'].transform(
            lambda x: x.rolling(window='365D', min_periods=1).sum()
        )
        df.reset_index(inplace=True)
        df = df[df['days_history'] >= 364].drop(columns=['days_history'])
        if period_type == 'yoy_y':
            df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
            df = df[df['quarter'] == end_quarter_num]
            df = df.drop(columns=['quarter'])

    elif period_type == 'cumulative_sum':
        df['value'] = df.groupby(grouping_cols)['value'].cumsum()

    logger.debug(f"periods after filter_by_period_type {set(sorted(df['year_quarter'].tolist()))}")
    return df
