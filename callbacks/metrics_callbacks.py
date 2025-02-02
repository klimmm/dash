import json
from typing import List, Dict, Tuple

import dash
from dash import Dash, ALL, Input, Output, State
from dash.exceptions import PreventUpdate
 
from application.components.dropdown import create_dynamic_dropdown
from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.metrics_processor import MetricsProcessor
from constants.translations import translate

logger = get_logger(__name__)


def _create_updated_dropdown(
    index: int, 
    options: List[Dict], 
    value: str, 
    total_dropdowns: int,
    other_selected: List[str] = None
) -> Dict:
    """Create a dropdown with filtered options based on current selections."""
    if other_selected:
        filtered_options = [opt for opt in options if opt['value'] not in other_selected]
        if value and not any(opt['value'] == value for opt in filtered_options):
            filtered_options.append({'label': translate(value), 'value': value})
    else:
        filtered_options = options

    logger.debug(
        f"Creating dropdown | Index: {index} | Value: {value} | "
        f"Total dropdowns: {total_dropdowns} | Other selected: {other_selected} | "
        f"Available options: {[opt['value'] for opt in filtered_options]}"
    )

    return create_dynamic_dropdown(
        dropdown_type='metric',
        index=index,
        options=filtered_options,
        value=value,
        is_add_button=(index == total_dropdowns - 1),
        is_remove_button=(total_dropdowns > 1),
        placeholder="Select metric"
    )


def setup_metric_selection(app: Dash) -> None:
    """Setup callbacks for metric selection handling."""
    @app.callback(
        [Output('metric-container', 'children'),
         Output('metric-all-values', 'data')],
        [Input({'type': 'dynamic-metric', 'index': ALL}, 'value'),
         Input('metric-add-btn', 'n_clicks'),
         Input({'type': 'remove-metric-btn', 'index': ALL}, 'n_clicks'),
         Input('reporting-form', 'data')],
         [State('insurance-lines-all-values', 'data'),
         State('intermediate-data-store', 'data'),
         State('metric-container', 'children'),
         State('metric-all-values', 'data')]
    )
    @log_callback
    def update_metric_selections(
        selected_metrics: List[str],
        add_metric_clicks: int,
        remove_metric_clicks: List[int],
        reporting_form: str,
        lines: List[str],
        intermediate_data: Dict,
        existing_dropdowns: List,
        all_selected_metric: List[str]
    ) -> Tuple[List, List, str, List]:
        """Update  metric selections based on user interactions."""
        ctx = dash.callback_context
        '''if not ctx.triggered:
            logger.debug("No context triggered - preventing update")
            raise PreventUpdate'''

        try:
            trigger = ctx.triggered[0]
            logger.info(
                f"=== Starting metric update ===\n"
                f"Trigger: {trigger['prop_id']}\n"
                f"Form ID: {reporting_form}\n"
                f"Current metrics: {selected_metrics}\n"
                f"Previous metrics: {all_selected_metric}\n"
                f"Total dropdowns: {len(existing_dropdowns) if existing_dropdowns else 0}"
            )


            valid_selected_metrics = MetricsProcessor.validate_metric_values(reporting_form, selected_metrics)

            metric_options = MetricsProcessor.get_metrics_options([reporting_form])
            logger.warning(f"metric_options {metric_options}")
            logger.debug(
                f"Available options:\n"
                f" metrics: {[opt['value'] for opt in metric_options]}\n"
                f"Valid selections: {valid_selected_metrics}"
            )

            # Initialize if no existing dropdowns
            if not existing_dropdowns:
                logger.info("Initializing first dropdown - no existing dropdowns found")
                return ([_create_updated_dropdown(0, metric_options, None, 1)], [])

            initial_dropdowns = existing_dropdowns

            metric = [v for v in (selected_metrics or []) if
                              v is not None and
                              v in valid_selected_metrics
                              ] or valid_selected_metrics

            trigger_id = trigger['prop_id']

            # Handle remove button click
            if 'remove-metric-btn' in trigger_id:
                if len(existing_dropdowns) <= 1:
                    logger.info("Preventing removal of last remaining dropdown")
                    raise PreventUpdate

                removed_index = int(json.loads(trigger_id.split('.')[0])['index'])
                logger.info(f"Processing dropdown removal at index {removed_index}")

                has_value_at_index = removed_index < len(metric) and metric[removed_index] is not None
                other_values = [v for i, v in enumerate(metric) if i != removed_index and v is not None]

                if has_value_at_index and not other_values:
                    value_to_preserve = metric[removed_index]
                    logger.info(
                        f"Preserving sole selected value '{value_to_preserve}' while removing dropdown {removed_index}"
                    )
                    existing_dropdowns.pop(removed_index)
                    return [
                        _create_updated_dropdown(
                            i, metric_options,
                            value_to_preserve if i == 0 else None,
                            len(existing_dropdowns)
                        ) for i in range(len(existing_dropdowns))
                    ], [value_to_preserve]

                existing_dropdowns.pop(removed_index)
                if removed_index < len(metric):
                    removed_value = metric.pop(removed_index)
                    logger.info(f"Removed metric '{removed_value}' at index {removed_index}")

            # Handle add button click
            elif 'metric-add-btn' in trigger_id:
                logger.info(f"Adding new dropdown (current count: {len(existing_dropdowns)})")
                if existing_dropdowns:
                    last_index = len(existing_dropdowns) - 1
                    current_value = metric[last_index] if last_index < len(metric) else None
                    logger.debug(f"Updating last dropdown {last_index} with value: {current_value}")
                    existing_dropdowns[last_index] = _create_updated_dropdown(
                        last_index, metric_options,
                        current_value,
                        len(existing_dropdowns) + 1
                    )
                existing_dropdowns.append(_create_updated_dropdown(
                    len(existing_dropdowns), metric_options, None,
                    len(existing_dropdowns) + 1, metric
                ))

            # Update all dropdowns with current selections
            updated_dropdowns = [
                _create_updated_dropdown(
                    i, metric_options,
                    metric[i] if i < len(metric) else None,
                    len(existing_dropdowns),
                    [v for j, v in enumerate(metric) if j != i and v is not None]
                ) for i in range(len(existing_dropdowns))
            ]
            logger.info(
                f"=== Completed metric update ===\n"
                f"Final metrics: {metric}\n"
                f"Total dropdowns: {len(updated_dropdowns)}\n"
            )

            if metric == all_selected_metric:
                logger.info("No change detected in selected metrics - maintaining current state")

                if updated_dropdowns == initial_dropdowns:
                    return dash.no_update, dash.no_update
                else:
                    return updated_dropdowns, dash.no_update

            return updated_dropdowns, metric

        except Exception as e:
            logger.error(
                f"Error in update_metric_selections:\n"
                f"Trigger: {ctx.triggered[0] if ctx.triggered else 'None'}\n"
                f"Current metrics: {metric}\n"
                f"Error: {str(e)}",
                exc_info=True
            )
            raise