import pandas as pd
from config.logging_config import get_logger
logger = get_logger(__name__)


def quarter_to_index(qstr: str) -> int:
    """Convert quarter string (e.g., '2024Q3') to integer index."""
    year, quarter = int(qstr[:4]), int(qstr[-1])
    return year * 4 + (quarter - 1)

def index_to_quarter(idx: int) -> pd.Timestamp:
    """Convert integer index to timestamp for quarter start."""
    year, quarter_offset = divmod(idx, 4)
    return pd.Timestamp(year=year, month=1 + 3*quarter_offset, day=1)

def filter_by_end_quarter(df: pd.DataFrame, end_quarter: str) -> pd.DataFrame:
    """Filter DataFrame to include only dates up to end_quarter."""
    year, quarter = int(end_quarter[:4]), int(end_quarter[-1])
    end_date = pd.Timestamp(f"{year}-{(quarter-1)*3 + 1}-01")
    #print(f"end_date: {end_date}")
    df = df.copy()
    df['year_quarter'] = pd.to_datetime(df['year_quarter'])
    #print(f"dates available: {sorted(df['year_quarter'].tolist())}")
    df = df[df['year_quarter'] <= end_date]
    #print(f"dates after filtering for end date: {sorted(df['year_quarter'].tolist())}")

    return df

def get_earliest_valid_date(df: pd.DataFrame, period_type: str, end_quarter: str) -> pd.Timestamp:
    """Find earliest valid quarter based on period type."""
    end_year = int(end_quarter[:4])
    end_quarter_num = int(end_quarter[-1])

    if period_type == 'yoy_q':
        return df[df['year_quarter'].dt.quarter == end_quarter_num]['year_quarter'].min()

    if period_type == 'ytd':
        logger.debug(f"period_type {period_type}")
        df_quarters = (df[df['year_quarter'].dt.quarter <= end_quarter_num]
                      .groupby(df['year_quarter'].dt.year)['year_quarter'].nunique())

        logger.debug(f"df_quarters {df_quarters}")
        complete_years = df_quarters[df_quarters == end_quarter_num].index
        logger.debug(f"complete_years {complete_years}")
        return pd.Timestamp(f"{min(complete_years)}-01-01") if len(complete_years) > 0 else None

    if period_type == 'yoy_y':
        end_index = quarter_to_index(end_quarter)
        quarter_indices = sorted({quarter_to_index(f"{dt.year}Q{dt.quarter}") 
                                for dt in df['year_quarter']})

        if end_index not in quarter_indices:
            return None

        for start_idx in quarter_indices:
            if start_idx > end_index:
                continue
            length = end_index - start_idx + 1
            if length % 4 == 0 and all(idx in quarter_indices 
                                     for idx in range(start_idx, end_index + 1)):
                return index_to_quarter(start_idx)

    if period_type == 'qoq':
        return df['year_quarter'].min()

    return None

def filter_by_num_periods(df: pd.DataFrame, period_type: str, num_periods_selected: int) -> pd.DataFrame:
    """Filter DataFrame based on number of periods to show."""
    df = df.copy()

    if period_type == 'yoy_q':
        end_quarter = df['year_quarter'].dt.quarter.iloc[-1]
        logger.debug(f"end_quarter {end_quarter}")
        quarters = df[df['year_quarter'].dt.quarter == end_quarter]['year_quarter']
        num_periods_available = len(quarters.unique())
        num_periods_to_keep = min(num_periods_selected, num_periods_available - 1) + 1
        logger.debug(f"num_periods_available {num_periods_available}")
        logger.debug(f"num_periods_to_keep {num_periods_to_keep}")
        logger.debug(f"periods before filter {set(sorted(df['year_quarter'].tolist()))}")
        df = df[df['year_quarter'].isin(pd.Series(quarters.unique()).nlargest(num_periods_to_keep))]

    if period_type == 'ytd':
        years = df['year_quarter'].dt.year.unique()
        num_periods_available = len(years)
        num_periods_to_keep = min(num_periods_selected, num_periods_available - 1) + 1
        df = df[df['year_quarter'].dt.year.isin(sorted(years)[-num_periods_to_keep:])]

    if period_type == 'yoy_y':
        periods = sorted(df['year_quarter'].unique())
        num_periods_available = len(periods) / 4
        num_periods_to_keep = min(num_periods_selected, num_periods_available - 1) + 1
        df = df[df['year_quarter'].isin(periods[-int(num_periods_to_keep * 4):])] 


    if period_type == 'qoq':
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        num_periods_available = len(quarters)
        num_periods_to_keep = min(num_periods_selected, num_periods_available - 1) + 1
        df = df[df['year_quarter'].isin(quarters[:num_periods_to_keep])]

    return df, num_periods_available


def filter_year_quarter(df: pd.DataFrame, end_quarter: str, period_type: str, num_periods_selected: int):
    df = filter_by_end_quarter(df, end_quarter)
    logger.debug(f"period_type {period_type}")
    logger.debug(f"num_periods_selected {num_periods_selected}")
    logger.debug(f"end_quarter {end_quarter}")
    earliest_date = get_earliest_valid_date(df, period_type, end_quarter)
    logger.debug(f"earliest_date {earliest_date}")
    if earliest_date is not None:
        df = df[df['year_quarter'] >= earliest_date]
    logger.debug(f"periods after earliest date {set(sorted(df['year_quarter'].tolist()))}")
    df, num_periods_available = filter_by_num_periods(df, period_type, num_periods_selected)
    logger.debug(f"periods after filter_by_num_periods_selected {set(sorted(df['year_quarter'].tolist()))}")
    return df #, round(num_periods_available)


'''# Example usage
if __name__ == '__main__':
    dates = [
        '2019-04-01 00:00:00', '2019-07-01 00:00:00',
        '2019-10-01 00:00:00', '2020-01-01 00:00:00', '2020-04-01 00:00:00',
        '2020-07-01 00:00:00', '2020-10-01 00:00:00', '2021-01-01 00:00:00',
        '2021-04-01 00:00:00', '2021-07-01 00:00:00', '2021-10-01 00:00:00',
        '2022-01-01 00:00:00', '2022-04-01 00:00:00', '2022-07-01 00:00:00',
        '2022-10-01 00:00:00', '2023-01-01 00:00:00', '2023-04-01 00:00:00',
        '2023-07-01 00:00:00', '2023-10-01 00:00:00', '2024-01-01 00:00:00',
        '2024-04-01 00:00:00', '2024-07-01 00:00:00'
    ]
    df = pd.DataFrame({'year_quarter': dates})
    print(f"dates in df: {sorted(df['year_quarter'].tolist())}")
    period_types = ['ytd', 'yoy_q', 'yoy_y', 'qoq']
    end_quarter_options = ['2023Q3', '2024Q1', '2024Q2', '2024Q3']
    num_periods_selected = 6


    for end_quarter in end_quarter_options:
        print(f"\n{end_quarter}:")
        for period_type in period_types:
            print(f"\n{period_type}:")
            df_filtered, num_periods_available = filter_year_quarter(df, end_quarter, period_type, num_periods_selected)
            print(f"num_periods_available: {num_periods_available}")
            print(f"Filtered dates: {sorted(df_filtered['year_quarter'].tolist())}")

           earliest_date = get_earliest_valid_date(df_filtered, period_type, end_quarter)
            print(f"\n{period_type}:")
            print(f"Earliest valid date: {earliest_date}")
            
            if earliest_date is not None:
                df_filtered = df_filtered[df_filtered['year_quarter'] >= earliest_date]
                
                df_filtered, num_periods_available = filter_by_num_periods(df_filtered, period_type, num_periods_selected)

                print(f"Number of rows: {len(df_filtered)}")
                print(f"num_periods_available: {num_periods_available}")  
                print(f"Filtered dates: {sorted(df_filtered['year_quarter'].tolist())}")'''