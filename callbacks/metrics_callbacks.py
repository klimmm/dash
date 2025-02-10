from typing import Dict, List, Tuple

import dash  # type: ignore
from dash import Dash, Input, Output, State  # type: ignore

from config.callback_logging_config import error_handler, log_callback
from config.logging_config import get_logger, timer
from core.metrics.options import get_metric_options

logger = get_logger(__name__)


def setup_metric_selection(app: Dash) -> None:
    """Setup callback for multi-value metric selection handling."""
    @app.callback(
        [Output('metrics', 'value'),
         Output('metrics', 'options'),
         Output('metrics-store', 'data')],
        [Input('metrics', 'value'),
         Input('reporting-form-selected', 'data')],
        [State('metrics-store', 'data')],
    )
    @log_callback
    @timer
    @error_handler
    def update_metric_selections(
        selected: List[str],
        reporting_form: str,
        stored: List[str]
    ) -> Tuple[List[str], List[Dict], List[str]]:
        logger.debug(f"selected {selected}")
        logger.debug(f"stored {stored}")
        logger.debug(f"reporting_form {reporting_form}")

        metric_options, valid_metrics = get_metric_options(
            reporting_form, selected or [])
        updated_values = [v for v in (selected or [])
                          if v is not None and
                          v in valid_metrics] or valid_metrics
        logger.debug(f"valid_metrics {valid_metrics}")
        logger.debug(f"updated_values {updated_values}")

        if selected == stored:
            logger.debug("EQUAL - returning no_update")
            return dash.no_update, metric_options, dash.no_update

        logger.debug("NOT EQUAL - returning full update")
        return updated_values, metric_options, updated_values