from typing import Any, Dict, List, Tuple, Set

import dash  # type: ignore
import pandas as pd
from dash.dependencies import Input, Output, State  # type: ignore
from dash.exceptions import PreventUpdate  # type: ignore

from app.components.checklist import create_btype_checklist
from core.metrics.checklist_config import get_checklist_config
from config.logging import log_callback, error_handler, get_logger, timer, monitor_memory
from core.metrics.operations import (
     get_required_metrics,
     calculate_metrics,
     calculate_growth,
     add_top_n_rows,
     calculate_market_share
)
from core.period.operations import filter_by_period_type, get_start_quarter
from core.period.options import YearQuarter, YearQuarterOption

logger = get_logger(__name__)

# Type aliases for clarity
ProcessedDataDict = Dict[str, List[Dict[str, Any]]]
FilterStateDict = Dict[str, Any]


@timer
@monitor_memory
def filter_by_lines_metrics_and_date_range(
    df: pd.DataFrame,
    selected_lines: List[str],
    required_metrics: List[str],
    start_quarter: str,
    end_quarter: str
) -> pd.DataFrame:
    return df[
        (df['linemain'].isin(selected_lines)) &
        (df['metric'].isin(required_metrics)) &
        (df['year_quarter'] >= start_quarter) &
        (df['year_quarter'] <= end_quarter)
    ]


def setup_process_data(
    app: dash.Dash,
    df_158: pd.DataFrame,
    df_162: pd.DataFrame,
    end_quarter_options_158: List[YearQuarterOption],
    end_quarter_options_162: List[YearQuarterOption],
    available_quarters_158: Set[YearQuarter],
    available_quarters_162: Set[YearQuarter]
) -> None:

    @app.callback(
        [Output('end-quarter', 'options'),
         Output('business-type-checklist-container', 'children'),
         Output('processed-data-store', 'data'),
         Output('filter-state-store', 'data')],
        [Input('metrics-store', 'data'),
         Input('business-type-checklist', 'value'),
         Input('periods-data-table-selected', 'data'),
         Input('end-quarter', 'value'),
         Input('selected-lines-store', 'data'),
         Input('period-type-selected', 'data'),
         Input('reporting-form-selected', 'data')],
        [State('selected-insurers-store', 'data'),
         State('filter-state-store', 'data'),
         State('metrics-store', 'data')]
    )
    @error_handler
    @log_callback
    @timer
    def process_data(
        selected_metrics: List[str],
        curr_btype_selection: List[str],
        num_periods: int,
        end_quarter: str,
        selected_lines: List[str],
        period_type: str,
        reporting_form: str,
        selected_insurers: str,
        current_filter_state: FilterStateDict,
        metrics_state: List[str]
    ) -> Tuple[
     List[YearQuarterOption], List[Any], ProcessedDataDict, FilterStateDict
     ]:

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        checklist_mode, checklist_values = get_checklist_config(
            selected_metrics, reporting_form, curr_btype_selection
        )
        checklist_component = create_btype_checklist(
            checklist_mode, checklist_values
        )
        df = (
            df_162 if reporting_form == '0420162' else df_158
        )
        end_quarter_options = (
            end_quarter_options_162 if reporting_form == '0420162' else
            end_quarter_options_158
        )
        available_quarters = (
            available_quarters_162 if reporting_form == '0420162' else
            available_quarters_158
        )
        start_quarter = get_start_quarter(
            YearQuarter(end_quarter), period_type, num_periods, available_quarters
        )
        logger.debug(f" num_periods {num_periods}")
        logger.debug(f" start_quarter {start_quarter}")

        required_metrics = get_required_metrics(selected_metrics)

        df = (filter_by_lines_metrics_and_date_range(
            df, selected_lines, required_metrics, start_quarter, end_quarter
        )
            .pipe(filter_by_period_type, end_quarter, num_periods, period_type)
            .pipe(add_top_n_rows)
            .pipe(calculate_metrics, selected_metrics, required_metrics)
            .pipe(calculate_market_share, selected_insurers, selected_metrics)
            .pipe(calculate_growth, selected_insurers, num_periods, period_type)
        )

        filter_state: FilterStateDict = {
            **(current_filter_state if current_filter_state else {}),
            'selected_metrics': selected_metrics,
            'selected_lines': selected_lines,
            'reporting_form': reporting_form,
            'start_quarter': start_quarter,
            'end_quarter': end_quarter
        }

        records: List[Dict[str, Any]] = [
            {str(k): v for k, v in record.items()}
            for record in df.to_dict('records')
        ]

        processed_data: ProcessedDataDict = {
            'df': records
        }

        return (
            end_quarter_options,
            [checklist_component],
            processed_data,
            filter_state
        )