import pandas as pd
import time
from functools import wraps
from config.logging_config import get_logger

logger = get_logger(__name__)

# You can keep your timer decorator as is
def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


class PeriodProcessor:
    def __init__(self, df: pd.DataFrame):
        # Store a copy of the dataframe
        self.df = df.copy()

    @timer
    def get_year_quarter_options(self, df: pd.DataFrame = None):
        """
        Return a list of quarter options based on the 'year_quarter' column.
        If no DataFrame is provided, use the stored self.df.
        """
        # Allow passing in a dataframe or use the one on the instance
        df = df if df is not None else self.df

        # Get unique and sorted values in one operation
        unique_quarters = pd.Series(df['year_quarter'].unique()).sort_values()
        result_size = len(unique_quarters)
        quarter_options = [None] * result_size

        # Use vectorized operations to extract year and quarter
        years = unique_quarters.dt.year
        quarters = unique_quarters.dt.quarter

        # Build the options list
        for i in range(result_size):
            quarter_str = f"{years[i]}Q{quarters[i]}"
            quarter_options[i] = {'label': quarter_str, 'value': quarter_str}

        return quarter_options

    @timer
    def filter_by_period_type(
        self,
        end_quarter: str, 
        num_periods_selected: int,
        period_type: str
    ) -> pd.DataFrame:
        """
        Filter self.df based on the provided period_type, end_quarter, and number
        of periods. Returns a new DataFrame.
        """
        df = self.df.copy()
        grouping_cols = [col for col in df.columns if col not in {'year_quarter', 'value', 'quarter'}]
        end_quarter_num = int(end_quarter[-1])

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

            df = df[df['year'].isin(complete_years)]

            df = (df[df['year_quarter'].dt.quarter <= end_quarter_num]
                  .assign(year=lambda x: x['year_quarter'].dt.year,
                          ytd_value=lambda x: x.groupby(['year'] + grouping_cols)
                          ['value'].cumsum())
                  .assign(value=lambda x: x['ytd_value'])
                  .drop(columns=['ytd_value', 'quarter'])
                  .loc[lambda x: x['year_quarter'].dt.quarter == end_quarter_num]
                  .reset_index(drop=True))

            df = df.drop(columns=['year'])
            df = df[df['year_quarter'].dt.quarter == end_quarter_num]

        elif period_type in ['mat', 'yoy_y']:
            df = df.sort_values(grouping_cols + ['year_quarter'])
            df['quarter_end'] = df['year_quarter'] + pd.offsets.QuarterEnd()
            start_date = df.groupby(grouping_cols)['year_quarter'].transform('min')
            df['days_history'] = (
                df['quarter_end'] - start_date).dt.total_seconds() / (24 * 60 * 60)

            df = df.drop(columns=['quarter_end'])
            df.set_index('year_quarter', inplace=True)
            df['value'] = df.groupby(grouping_cols)['value'].transform(
                lambda x: x.rolling(window='365D', min_periods=1).sum())
            df.reset_index(inplace=True)
            df = df[df['days_history'] >= 364].drop(columns=['days_history'])
            if period_type == 'yoy_y':
                df.loc[:, 'quarter'] = df['year_quarter'].dt.quarter
                df = df[df['quarter'] == end_quarter_num]
                df = df.drop(columns=['quarter'])
            df = df[df['year_quarter'].dt.quarter == end_quarter_num]

        elif period_type == 'cumulative_sum':
            df['value'] = df.groupby(grouping_cols)['value'].cumsum()

        # Limit the periods kept
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        num_periods_available = len(quarters)
        num_periods_to_keep = min(num_periods_selected, num_periods_available - 1) + 1
        df = df[df['year_quarter'].isin(quarters[:num_periods_to_keep])]    

        logger.debug(f"periods after filter_by_period_type: {set(sorted(df['year_quarter'].tolist()))}")

        return df

    @timer
    def process(self, end_quarter: str, num_periods_selected: int, period_type: str):
        """
        Combined method that first filters the DataFrame based on period_type
        and then generates quarter options.
        Returns a tuple of (filtered DataFrame, quarter options).
        """
        filtered_df = self.filter_by_period_type(end_quarter, num_periods_selected, period_type)
        # Optionally, you can generate quarter options from the filtered DataFrame
        quarter_options = self.get_year_quarter_options(filtered_df)
        return filtered_df, quarter_options
