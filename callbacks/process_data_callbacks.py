from typing import Dict, List, Tuple

import dash
import pandas as pd
from dash.dependencies import Input, Output, State

from application.components.checklist import create_btype_checklist
from domain.metrics.checklist_config import get_checklist_config
from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer, monitor_memory

from domain.metrics.operations import (
    get_required_metrics,
    calculate_metrics,
    calculate_growth,
    add_top_n_rows,
    calculate_market_share
)

from domain.period.operations import filter_by_period_type


logger = get_logger(__name__)


@timer
@monitor_memory
def filter_lines_and_metrics(
    df: pd.DataFrame,
    selected_lines: List[str],
    required_metrics: List[str]
) -> pd.DataFrame:
    return df[df['linemain'].isin(
        selected_lines) & df['metric'].isin(required_metrics)]


def setup_process_data(
    app: dash.Dash,
    df_162: pd.DataFrame,
    df_158: pd.DataFrame,
    end_quarter_options_162: List[Dict],
    end_quarter_options_158: List[Dict]
) -> None:

    @app.callback(
        [Output('end-quarter', 'options'),
         Output('business-type-checklist-container', 'children'),
         Output('processed-data-store', 'data'),
         Output('filter-state-store', 'data')],
        [Input('metrics-store', 'data'),
         Input('business-type-checklist', 'value'),
         Input('number-of-periods-data-table', 'data'),
         Input('end-quarter', 'value'),
         Input('selected-lines-store', 'data'),
         Input('period-type', 'data'),
         Input('reporting-form', 'data')],
        [State('selected-insurers-store', 'data'),
         State('filter-state-store', 'data')]
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
        current_filter_state: Dict
    ) -> Tuple:

        df = (df_162 if reporting_form == '0420162' else
              df_158)

        end_quarter_options = (
            end_quarter_options_162 if reporting_form == '0420162' else
            end_quarter_options_158)
        logger.warning(f" current checklist values {curr_btype_selection}")
        checklist_mode, checklist_values = get_checklist_config(selected_metrics, reporting_form, curr_btype_selection)
        logger.warning(f" new checklist values  {checklist_values}")
        checklist_component = create_btype_checklist(checklist_mode, checklist_values)

        required_metrics = get_required_metrics(selected_metrics)

        df = (filter_lines_and_metrics(df, selected_lines, required_metrics)
              .pipe(filter_by_period_type, end_quarter, num_periods, period_type)
              .pipe(add_top_n_rows)
              .pipe(calculate_metrics, selected_metrics, required_metrics)
              .pipe(calculate_market_share, selected_insurers, selected_metrics)
              .pipe(calculate_growth, selected_insurers, num_periods, period_type)
              )

        filter_state = {
            **(current_filter_state if current_filter_state else {}),
            'selected_metrics': selected_metrics,
            'selected_lines': selected_lines
        }

        processed_data = {
            'df': df.to_dict('records')
        }

        return end_quarter_options, [checklist_component], processed_data, filter_state