from typing import List, NewType, TypedDict, Optional
import pandas as pd
import numpy as np


YearQuarter = NewType('YearQuarter', str)  # Format: "YYYYQN" (e.g., "2024Q1")


class YearQuarterOption(TypedDict):
    label: YearQuarter
    value: YearQuarter


class PeriodProcessor:
    def __init__(self, logger=None, config=None):
        self.config = config
        self.logger = logger

    def get_start_quarter(
        self,
        available_quarters: List[str],
        end_quarter: YearQuarter,
        period_type: str,
        num_periods: int,
        logger,
        config
    ) -> Optional[YearQuarter]:
        """
        Determine the start quarter based on period type and available data.

        Args:
            end_quarter: Target end quarter (format: 'YYYYQN')
            period_type: Analysis period type ('yoy_q', 'ytd', 'yoy_y', 'qoq')
            num_periods: Number of periods to analyze
            reporting_form: Form identifier to determine available quarters

        Returns:
            Start quarter string or None if invalid/insufficient data
        """
        self.config = self.config
        self.columns = self.config.columns
        self.logger = logger

        self.logger.debug(f"available_quarters {available_quarters}")
        '''self.available_quarters = self.domain_service.get_available_quarters_from_form(self.reporting_form)
        self.start_q = self.period_processor.get_start_quarter(
            self.available_quarters, self.end_q, self.period_type, self.num_periods)
        self.logger.debug(f"start q {self.start_q}")
        .pipe(self.domain_service.filter_by_column,
            self.columns.YEAR_QUARTER, self.start_q, 'gte')'''

        def _to_index(qstr: YearQuarter) -> int:
            year, quarter = int(qstr[:4]), int(qstr[-1])
            return year * 4 + quarter - 1

        def _to_quarter(idx: int) -> YearQuarter:
            year, quarter = divmod(idx, 4)
            return YearQuarter(f"{year}Q{quarter + 1}")

        if end_quarter not in available_quarters:
            self.logger.debug(f"End quarter {end_quarter} not in available quarters")
            return None

        period_type = str(period_type).replace('-', '_')
        end_idx = _to_index(end_quarter)
        end_q = int(end_quarter[-1])
        end_year = int(end_quarter[:4])

        self.logger.debug(f"end_quarter {end_quarter}")
        self.logger.debug(f"end_q {end_q}")
        self.logger.debug(f"end_year {end_year}")
        self.logger.debug(f"num_periods {num_periods}")
        self.logger.debug(f"period_type {period_type}")

        # Dictionary of period type handlers for extensibility
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
                 for start_idx in sorted(
                     (_to_index(q) for q in available_quarters), reverse=True)
                 if start_idx <= end_idx - num_periods * 4
                 and all(YearQuarter(f"{year}Q{end_q}") in available_quarters
                         for year in range(int(_to_quarter(start_idx)[:4]),
                                           end_year + 1))), None),
            'qoq': lambda: (
                _to_quarter(target_idx) if target_idx in avail_idx
                and all(i in avail_idx for i in range(target_idx, end_idx + 1))
                else None
            ) if (target_idx := end_idx - num_periods)
            and (avail_idx := set(map(_to_index, available_quarters)))
            else None
        }

        # Get result from appropriate handler or default to first available quarter
        result = period_handlers.get(period_type, lambda: None)()
        if result is None:
            result = available_quarters[0]

        self.logger.debug(f"start_quarter result: {result}")
        return result

    def calculate_period_type(
        self,
        df: pd.DataFrame,
        end_quarter: str,
        period_type: str,
        logger,
        config
    ) -> pd.DataFrame:
        """Transform data based on selected period type."""
        self.config = config
        self.columns = self.config.columns
        self.logger = logger
        grouping_cols = [col for col in df.columns if col not in {
            self.columns.YEAR_QUARTER, self.columns.VALUE, 'quarter'}]

        end_quarter_num = int(end_quarter[-1])
        period_type = str(period_type).replace('-', '_')

        if period_type == 'yoy_q':
            df = df.assign(quarter=df[self.columns.YEAR_QUARTER].dt.quarter)
            df = df[df[self.columns.YEAR_QUARTER].dt.quarter == end_quarter_num]
            df = df.drop(columns=['quarter'])

        elif period_type == 'ytd':
            df = (df.assign(quarter=df[self.columns.YEAR_QUARTER]
                            .dt.quarter, year=df[self.columns.YEAR_QUARTER].dt.year)
                  .pipe(lambda x: x[x[self.columns.YEAR_QUARTER]
                        .dt.quarter <= end_quarter_num])
                  .assign(ytd_value=lambda x: x
                          .groupby(['year'] + grouping_cols)[self.columns.VALUE].cumsum(),)
                  .assign(value=lambda x: x['ytd_value'])
                  .drop(columns=['ytd_value', 'quarter', 'year'])
                  .pipe(lambda x: x[x[self.columns.YEAR_QUARTER]
                        .dt.quarter == end_quarter_num])
                  .reset_index(drop=True))

        elif period_type in ['mat', 'yoy_y']:
            df = df.sort_values(grouping_cols + [self.columns.YEAR_QUARTER])
            df['quarter_end'] = df[self.columns.YEAR_QUARTER] + pd.offsets.QuarterEnd()
            start_date = df.groupby(
                grouping_cols)[self.columns.YEAR_QUARTER].transform('min')
            df['days_history'] = (
                df['quarter_end'] - start_date).dt.total_seconds() / (24 * 60 * 60)

            df = df.drop(columns=['quarter_end'])
            df.set_index(self.columns.YEAR_QUARTER, inplace=True)
            df[self.columns.VALUE] = df.groupby(
                grouping_cols)[self.columns.VALUE].transform(
                lambda x: x.rolling(window='365D', min_periods=1).sum())
            df.reset_index(inplace=True)
            df = df[df['days_history'] >= 364].drop(columns=['days_history'])
            if period_type == 'yoy_y':
                df.loc[:, 'quarter'] = df[self.columns.YEAR_QUARTER].dt.quarter
                df = df[df['quarter'] == end_quarter_num]
                df = df.drop(columns=['quarter'])
            df = df[df[self.columns.YEAR_QUARTER].dt.quarter == end_quarter_num]

        elif period_type == 'cumulative_sum':
            df[self.columns.VALUE] = df.groupby(grouping_cols)[self.columns.VALUE].cumsum()

        self.logger.debug(
            f"periods after filter_by_period_type "
            f"{set(sorted(df[self.columns.YEAR_QUARTER].tolist()))}"
        )
        return df

    def filter_by_num_periods(self, df: pd.DataFrame, num_periods: int) -> pd.DataFrame:
        """Filter data to include only the most recent periods."""
        return (df[df[self.columns.YEAR_QUARTER]
                .isin(np.sort(df[self.columns.YEAR_QUARTER].unique())[::-1]
                      [:num_periods])].copy())