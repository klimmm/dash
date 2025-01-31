import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)


def filter_by_end_quarter(df: pd.DataFrame, end_quarter: str) -> pd.DataFrame:
    """Filter DataFrame to include only dates up to end_quarter."""
    year, quarter = int(end_quarter[:4]), int(end_quarter[-1])
    end_date = pd.Timestamp(f"{year}-{(quarter-1)*3 + 1}-01")
    df = df.copy()
    df['year_quarter'] = pd.to_datetime(df['year_quarter'])
    df = df[df['year_quarter'] <= end_date]
    return df


def quarter_to_index(qstr: str) -> int:
    """Convert quarter string (e.g., '2024Q3') to integer index."""
    year, quarter = int(qstr[:4]), int(qstr[-1])
    return year * 4 + (quarter - 1)


def index_to_quarter(idx: int) -> pd.Timestamp:
    """Convert integer index to timestamp for quarter start."""
    year, quarter_offset = divmod(idx, 4)
    return pd.Timestamp(year=year, month=1 + 3*quarter_offset, day=1)


def get_earliest_valid_date(df: pd.DataFrame, period_type: str, end_quarter: str
                            ) -> pd.Timestamp:
    """Find earliest valid quarter based on period type."""
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


def filter_by_period(df: pd.DataFrame, end_quarter: str, period_type: str, num_periods_selected: int):
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
    return df


def filter_by_period_type(
    df: pd.DataFrame,
    period_type: str
) -> pd.DataFrame:

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

    elif period_type == 'cumulative_sum':
        df['value'] = df.groupby(grouping_cols)['value'].cumsum()

    logger.debug(f"periods after filter_by_period_type {set(sorted(df['year_quarter'].tolist()))}")

    return df