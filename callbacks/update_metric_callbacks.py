from typing import List, Tuple, Dict, Optional, Any
import json
import dash
from dash import Dash, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from callbacks.get_available_metrics import get_available_metrics
from application.dropdown_components import create_dynamic_metric_dropdown
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158
from constants.filter_options import METRICS_OPTIONS
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


FORM_METRICS = {
    '0420158': {'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
                'net_premiums', 'net_losses'
               },
    '0420162': {'direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses', 
                'ceded_premiums', 'ceded_losses',
                'new_sums', 'sums_end',
                'new_contracts', 'contracts_end',
                'premiums_interm', 'commissions_interm', 
                'claims_settled', 'claims_reported'
               }
}


def get_metric_options(
    reporting_form: str,
    selected_primary_metrics: Optional[List[str]] = None,
    selected_secondary_metrics: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    # 1. Initialize and normalize inputs
    allowed_basic_metrics = FORM_METRICS.get(reporting_form, set())
    available_calculated_metrics = set(get_available_metrics(allowed_basic_metrics))  # Convert to set explicitly
    selected_primary_metrics = [selected_primary_metrics] if isinstance(selected_primary_metrics, str) else (selected_primary_metrics or [])
    selected_secondary_metrics = [selected_secondary_metrics] if isinstance(selected_secondary_metrics, str) else (selected_secondary_metrics or [])

    # 2. Determine default metrics sets
    primary_metric_set = allowed_basic_metrics.copy()
    secondary_metric_set = available_calculated_metrics.copy()

    # 3. Handle selected primary metrics that are in secondary set
    for metric in selected_primary_metrics:
        if metric in secondary_metric_set:
            primary_metric_set.add(metric)
            secondary_metric_set.remove(metric)

    # 4. Validate primary metrics
    valid_primary_metrics = [
        metric for metric in selected_primary_metrics 
        if metric in primary_metric_set
    ] or None

    # 5. Handle selected secondary metrics based on primary validation
    if not valid_primary_metrics and selected_secondary_metrics:
        # If no valid primary metrics, collect eligible secondary metrics
        valid_primary_metrics = []
        metrics_to_remove = []

        for metric in selected_secondary_metrics:
            if metric in primary_metric_set or metric in secondary_metric_set:
                valid_primary_metrics.append(metric)
                metrics_to_remove.append(metric)
                primary_metric_set.add(metric)
                secondary_metric_set.discard(metric)

        # Remove processed metrics from selected_secondary_metrics
        for metric in metrics_to_remove:
            selected_secondary_metrics.remove(metric)
    else:
        # If we have valid primary metrics, move appropriate metrics to secondary
        for metric in selected_secondary_metrics:
            if metric in primary_metric_set:
                primary_metric_set.remove(metric)
                secondary_metric_set.add(metric)

    primary_metric_value = valid_primary_metrics if valid_primary_metrics is not None else DEFAULT_PRIMARY_METRICS if reporting_form == '0420162' else DEFAULT_PRIMARY_METRICS_158

    # 6. Validate secondary metrics
    valid_secondary_metrics = [
        metric for metric in selected_secondary_metrics 
        if metric in secondary_metric_set
    ] or None

    secondary_metric_value = valid_secondary_metrics if valid_secondary_metrics is not None else []

    # 7. Create options based on the metric sets
    primary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in primary_metric_set
    ]

    secondary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in secondary_metric_set
    ]

    return primary_metric_options, secondary_metric_options, primary_metric_value, secondary_metric_value


def setup_sync_metrics_callback(app: Dash) -> None:
    """Setup callback for syncing metric values"""

    @app.callback(
        Output('primary-metric-all-values', 'data'),
        [Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value')]
    )
    def sync_metric_values(main_value: str, dynamic_values: List[str]) -> List[str]:
        return [main_value] + [v for v in dynamic_values if v is not None]


def setup_metric_callbacks(app: Dash) -> None:
    """Setup callbacks for managing primary and secondary metric dropdowns"""

    @app.callback(
        [Output('primary-metric', 'options'),
         Output('primary-metric', 'value'),
         Output('primary-metric-container', 'children'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value')],
        [Input('reporting-form', 'data'),
         Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
         Input('primary-metric-add-btn', 'n_clicks'),
         Input({'type': 'remove-primary-metric-btn', 'index': ALL}, 'n_clicks')],
        [State('primary-metric-container', 'children'),
         State('secondary-y-metric', 'value')]
    )
    def update_metric_selections(
        reporting_form: str,
        selected_primary_metric: str,
        selected_dynamic_metrics: List[str],
        add_metric_clicks: int,
        remove_metric_clicks: List[int],
        existing_dropdowns: List,
        secondary_metric: str
    ) -> Tuple:
        """Update metric dropdowns based on user interactions"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:

            # Initialize dropdowns if None
            existing_dropdowns = existing_dropdowns or []
            logger.debug(f"existing_dropdowns {existing_dropdowns}")
            selected_dynamic_metrics = [v for v in (selected_dynamic_metrics or []) if v is not None]
            all_selected_primary_metric = [selected_primary_metric] + selected_dynamic_metrics

            # Get initial metric options
            primary_metric_options, secondary_metric_options, valid_selected_primary_metrics, secondary_metric_value = (
                get_metric_options(reporting_form, all_selected_primary_metric, secondary_metric)
            )
            # Get all selected values
            valid_selected_dynamic_metrics = [v for v in valid_selected_primary_metrics if v != valid_selected_primary_metrics[0]]

            # Handle remove button click
            if '.n_clicks' in ctx.triggered[0]['prop_id'] and '"type":"remove-primary-metric-btn"' in ctx.triggered[0]['prop_id']:
                component_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
                removed_index = component_id['index']

                if ctx.triggered[0]['value'] is not None:
                    valid_selected_dynamic_metrics = [v for i, v in enumerate(valid_selected_dynamic_metrics) if i != removed_index]
                    existing_dropdowns = [
                        d for i, d in enumerate(existing_dropdowns) if i != removed_index
                    ]

            # Handle add button click
            if 'primary-metric-add-btn' in ctx.triggered[0]['prop_id']:
                new_primary_metric_dropdown = create_dynamic_metric_dropdown(
                    index=len(existing_dropdowns),
                    options=[opt for opt in primary_metric_options if opt['value'] not in valid_selected_primary_metrics],
                    value=None
                )
                existing_dropdowns.append(new_primary_metric_dropdown)

            # Update existing dropdowns
            updated_primary_metric_dropdowns = []
            for i, _ in enumerate(existing_dropdowns):
                current_primary_metric = valid_selected_dynamic_metrics[i] if i < len(valid_selected_dynamic_metrics) else None
                other_primary_metric_selected = [v for v in valid_selected_primary_metrics if v != current_primary_metric]

                primary_metric_dropdown_options = [
                    opt for opt in primary_metric_options 
                    if opt['value'] not in other_primary_metric_selected
                ]

                updated_primary_metric_dropdowns.append(create_dynamic_metric_dropdown(
                    index=i,
                    options=primary_metric_dropdown_options,
                    value=current_primary_metric
                ))

            # Filter primary metric options
            filtered_primary_metric_options = [
                opt for opt in primary_metric_options 
                if opt['value'] not in valid_selected_dynamic_metrics
            ]

            return (
                filtered_primary_metric_options,
                valid_selected_primary_metrics[0],
                updated_primary_metric_dropdowns,
                secondary_metric_options,
                secondary_metric_value[0] if secondary_metric_value else []
            )

        except Exception as e:
            logger.error(f"Error in update_metric_dropdowns: {str(e)}", exc_info=True)
            raise