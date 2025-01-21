import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import dash
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate
from data_process.data_utils import category_structure_162, category_structure_158, get_categories_by_level
from config.logging_config import get_logger, track_callback, track_callback_end
from constants.filter_options import METRICS_OPTIONS
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158, DEFAULT_PREMIUM_LOSS_TYPES
from application.app_layout import FilterComponents
from application.callbacks.get_available_metrics import get_available_metrics

logger = get_logger(__name__)

# Simplified metric mappings
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


def get_premium_loss_state(metrics: List[str], reporting_form: str) -> Tuple[bool, Optional[List[str]]]:
    if not metrics:
        return True, ['direct']

    is_form_158 = reporting_form == '0420158'
    states = {
        ('total_premiums', 'total_losses'): 
            (True, ['direct', 'inward']) if is_form_158 else (False, ['direct', 'inward']),
        ('ceded_premiums', 'ceded_losses', 'ceded_premiums_ratio',
         'ceded_losses_to_ceded_premiums_ratio', 'net_premiums', 'net_losses'):
            (True, ['direct', 'inward']),
        ('inward_premiums', 'inward_losses'): 
            (True, ['inward']),
        ('direct_premiums', 'direct_losses'): (True, ['direct'])
    }
    
    result_bool = False  # Change initial value to False
    result_states = set()
    
    # Check each metric in the input list
    for metric in metrics:
        found = False
        for metrics_group, (bool_state, state_list) in states.items():
            if metric in metrics_group:
                found = True
                # Update the boolean state
                result_bool = result_bool or bool_state
                # Always add states to the result set if they exist
                if state_list:
                    result_states.update(state_list)
                break
        if not found:
            result_states.add('direct')
    
    # If no states were collected, use default
    if not result_states:
        result_states.add('direct')

    logger.warning(f"metric: {metric}")
    logger.warning(f"readonly: {result_bool}")
    logger.warning(f"values: {sorted(list(result_states))}")
    return result_bool, sorted(list(result_states))


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

    # 6. Validate secondary metrics
    valid_secondary_metrics = [
        metric for metric in selected_secondary_metrics 
        if metric in secondary_metric_set
    ] or None

    # 7. Create options based on the metric sets
    primary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in primary_metric_set
    ]

    secondary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in secondary_metric_set
    ]

    return {
        'primary_y_metric_options': primary_options,
        'secondary_y_metric_options': secondary_options,
        'primary_metric': valid_primary_metrics,
        'secondary_metric': valid_secondary_metrics
    }

def setup_filter_update_callbacks(app: Dash, quarter_options_162, quarter_options_158) -> None:
    @app.callback(
        [Output('primary-y-metric', 'options'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value'),
         Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('premium-loss-checklist-container', 'children'),

         
         Output('filter-state-store', 'data')],  # Add filter state store output
        [Input('reporting-form', 'data'),
         Input('primary-y-metric', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('premium-loss-checklist', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data'),
        ],
        [
         State('show-data-table', 'data'),   
         State('filter-state-store', 'data')],  # Add filter state store state
        prevent_initial_call=True
    )
    def update_options(reporting_form, primary_metric, secondary_metric, current_values, lines, period_type, show_table, current_filter_state):
        ctx = dash.callback_context
        start_time = track_callback('app.callbacks.filter_update_callbacks', 'update_options', ctx)
        if not ctx.triggered:
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time)
            raise PreventUpdate
        try:

            metric_options = get_metric_options(reporting_form, primary_metric, secondary_metric)
            # primary_metric = (primary_metric or []) if isinstance(primary_metric, list) else []
            # secondary_metric = (secondary_metric or []) if isinstance(secondary_metric, list) else []

            # Get validated metrics from the return value
            validated_primary = metric_options.get('primary_metric')
            validated_secondary = metric_options.get('secondary_metric')
            # Use validated metrics or empty list if None
            primary_metric_value = validated_primary if validated_primary is not None else DEFAULT_PRIMARY_METRICS if reporting_form == '0420162' else DEFAULT_PRIMARY_METRICS_158
            secondary_metric_value = validated_secondary if validated_secondary is not None else []
            selected_metrics = (primary_metric_value or []) + (secondary_metric_value or [])
            end_quarter_options = quarter_options_162 if reporting_form == '0420162' else quarter_options_158
            insurance_line_dropdown_options = get_categories_by_level(
                category_structure_162 if reporting_form == '0420162' else category_structure_158, 
                level=2, 
                indent_char="--"
            )

            # Use validated metrics for selected_metrics
            readonly, enforced_values = get_premium_loss_state(selected_metrics, reporting_form)
            values = enforced_values if enforced_values is not None else current_values
            
            component = FilterComponents.create_component(
                'checklist',
                id='premium-loss-checklist',
                readonly=readonly,
                value=values
            )
    
            # Update filter state with new values
            filter_state = current_filter_state or {}
            updated_filter_state = {
                **filter_state,
                'primary_y_metric': primary_metric_value,
                'secondary_y_metric': secondary_metric_value,
                'selected_metrics': selected_metrics,
                'premium_loss_checklist': values or [],
                'selected_lines': lines,
                'show_data_table': bool(show_table),
                'reporting_form': reporting_form,
                'period_type': period_type,
            }
            logger.warning(f"component: {[component]}")
            
            
            output = (
                metric_options['primary_y_metric_options'],
                primary_metric_value[0],
                metric_options['secondary_y_metric_options'],
                secondary_metric_value[0] if secondary_metric_value else [],
                end_quarter_options,
                insurance_line_dropdown_options,
                [component],
                updated_filter_state  # Include updated filter state in output
            )
            
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, result=output)
            return output
            
        except Exception as e:
            logger.error(f"Error in update_options: {str(e)}", exc_info=True)
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, error=str(e))
            raise