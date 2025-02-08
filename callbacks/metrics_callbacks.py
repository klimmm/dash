from typing import Dict, List, Tuple

import dash
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate

from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer
from domain.metrics.options import get_metric_options

logger = get_logger(__name__)


def setup_metric_selection(app: Dash) -> None:
    """Setup callback for multi-value metric selection handling."""
    @app.callback(
        [Output('metrics', 'value'),
         Output('metrics', 'options'),
         Output('metrics-store', 'data')],
        [Input('metrics', 'value'),
         Input('reporting-form-selected', 'data')],
        [State('metrics-store', 'data')]
    )
    @log_callback
    @timer
    @error_handler
    def update_metric_selections(
        selected: List[str],
        reporting_form: str,
        stored: List[str]
    ) -> Tuple[List[str], List[Dict], List[str]]:

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        metric_options, valid_metrics = get_metric_options(
            reporting_form, selected or [])

        updated_values = [v for v in (selected or [])
                          if v is not None and
                          v in valid_metrics] or valid_metrics

        if selected == stored:
            return dash.no_update, metric_options, dash.no_update

        return updated_values, metric_options, updated_values