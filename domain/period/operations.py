import pandas as pd

from config.logging_config import get_logger, timer, monitor_memory

logger = get_logger(__name__)


@timer
@monitor_memory
def filter_by_period_type(
    df: pd.DataFrame,
    end_quarter: str,
    num_periods_selected: int,
    period_type: str
) -> pd.DataFrame:

    df = df.copy()

    grouping_cols = [col for col in df.columns if col not in {
        'year_quarter', 'value', 'quarter'}]

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

    quarters = sorted(df['year_quarter'].unique(), reverse=True)
    num_periods_available = len(quarters)
    num_periods_to_keep = min(
        num_periods_selected, num_periods_available - 1) + 1
    df = df[df['year_quarter'].isin(quarters[:num_periods_to_keep])]

    logger.debug(
        f"periods after filter_by_period_type {set(sorted(df['year_quarter'].tolist()))}")

    return df