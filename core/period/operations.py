from typing import Optional, Set

import pandas as pd

from config.logging import get_logger, monitor_memory, timer
from core.period.options import YearQuarter

logger = get_logger(__name__)


def get_start_quarter(
    end_quarter: YearQuarter,
    period_type: str,
    num_periods: int,
    available_quarters: Set[YearQuarter]
) -> Optional[YearQuarter]:
    """
    Determine the start quarter based on period type and available data.

    Args:
        end_quarter: Target end quarter (format: 'YYYYQN')
        period_type: Analysis period type ('yoy_q', 'ytd', 'yoy_y', 'qoq')
        num_periods: Number of periods to analyze
        available_quarters: Set of available quarter strings

    Returns:
        Start quarter string or None if invalid/insufficient data
    """
    def _to_index(qstr: YearQuarter) -> int:
        year, quarter = int(qstr[:4]), int(qstr[-1])
        return year * 4 + quarter - 1

    def _to_quarter(idx: int) -> YearQuarter:
        year, quarter = divmod(idx, 4)
        return YearQuarter(f"{year}Q{quarter + 1}")

    def _normalize_period_type(period_type: str) -> str:
        """Format button value for ID generation, handling both str and numbers"""
        return str(period_type).replace('-', '_')

    if end_quarter not in available_quarters:
        logger.debug(f"End quarter {end_quarter} not in available quarters")
        return None

    period_type = _normalize_period_type(period_type)
    end_idx = _to_index(end_quarter)
    end_q = int(end_quarter[-1])
    logger.debug(f"end_quarter {end_quarter}")
    logger.debug(f"end_q {end_q}")
    end_year = int(end_quarter[:4])
    logger.debug(f"end_year {end_year}")
    logger.debug(f"num_periods {num_periods}")
    logger.debug(f"period_type {period_type}")
    logger.debug(f"available_quarters {available_quarters}")
    period_handlers = {
        'yoy_q': lambda: (
            # Get all quarters with same quarter number as end_quarter
            sorted(q for q in available_quarters if int(q[-1]) == end_q)
            # Take num_periods + 1 from the end (or all if fewer available)
            [-min(num_periods + 1, len([q for q in available_quarters if int(
                q[-1]) == end_q]))]
        ),
        'ytd': lambda: (
            YearQuarter(f"{int(end_year) - int(num_periods)}Q1") if any(
                all(YearQuarter(f'{year}Q{q}') in available_quarters
                    for q in range(1, end_q + 1))
                for year in range(
                    int(end_year) - int(num_periods), int(end_year) + 1
                )
            ) else None
        ),
        'yoy_y': lambda: next(
            (_to_quarter(start_idx)
             for start_idx in sorted(_to_index(q) for q in available_quarters)
             if start_idx <= end_idx - (num_periods + 1) * 4 + 1
             and all(_to_index(YearQuarter(f"{year}Q{q}"))
                     in map(_to_index, available_quarters) for year in range(
                         int(_to_quarter(start_idx)[:4]), end_year + 1
                     )
                     for q in range(1, 5))), None
        ),
        'qoq': lambda: (
            _to_quarter(target_idx) if target_idx in avail_idx
            and all(i in avail_idx for i in range(target_idx, end_idx + 1))
            else None
        ) if (target_idx := end_idx - num_periods)
        and (avail_idx := set(map(_to_index, available_quarters)))
        else None
    }

    result = period_handlers.get(period_type, lambda: None)()
    logger.debug(f"result {result}")
    return result


@timer
@monitor_memory
def filter_by_period_type(
    df: pd.DataFrame,
    end_quarter: str,
    num_periods_selected: int,
    period_type: str
) -> pd.DataFrame:

    grouping_cols = [col for col in df.columns if col not in {
        'year_quarter', 'value', 'quarter'}]

    end_quarter_num = int(end_quarter[-1])

    if period_type == 'yoy_q':
        df = df.assign(quarter=df['year_quarter'].dt.quarter)
        df = df[df['year_quarter'].dt.quarter == end_quarter_num]
        df = df.drop(columns=['quarter'])

    elif period_type == 'ytd':
        df = (df.assign(quarter=df['year_quarter']
                        .dt.quarter, year=df['year_quarter'].dt.year)
              .pipe(lambda x: x[x['year_quarter']
                    .dt.quarter <= end_quarter_num])
              .assign(ytd_value=lambda x: x
                      .groupby(['year'] + grouping_cols)['value'].cumsum(),)
              .assign(value=lambda x: x['ytd_value'])
              .drop(columns=['ytd_value', 'quarter', 'year'])
              .pipe(lambda x: x[x['year_quarter']
                    .dt.quarter == end_quarter_num])
              .reset_index(drop=True))

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

    logger.debug(
        f"periods after filter_by_period_type "
        f"{set(sorted(df['year_quarter'].tolist()))}"
    )

    return df