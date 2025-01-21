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
            (True, ['inward'])
    }
    
    result_bool = True
    result_states = set()
    
    # Check each metric in the input list
    for metric in metrics:
        found = False
        for metrics_group, (bool_state, state_list) in states.items():
            if metric in metrics_group:
                found = True
                # Update the boolean state
                result_bool = result_bool and bool_state
                # Always add states to the result set if they exist
                if state_list:
                    result_states.update(state_list)
                break
        if not found:
            result_states.add('direct')
    
    # If no states were collected, use default
    if not result_states:
        result_states.add('direct')
    
    return result_bool, sorted(list(result_states))


def get_metric_options(reporting_form: str, primary_metric: Optional[List[str]] = None, secondary_metric: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    allowed_metrics = FORM_METRICS.get(reporting_form, set())
    availabale_metrics = get_available_metrics(allowed_metrics)
    
    # Include metrics from allowed_metrics
    primary_metrics = allowed_metrics.copy()
    
    # Add primary metrics if they exist in available metrics
    if primary_metric:
        primary_metrics.update(metric for metric in primary_metric if metric in availabale_metrics)
    
    # Create primary options first
    primary_options = [opt for opt in METRICS_OPTIONS if opt['value'] in primary_metrics]
    primary_option_values = {opt['value'] for opt in primary_options}
    
    # Initialize list for valid primary metrics
    valid_primary = []
    if primary_metric:
        valid_primary.extend(metric for metric in primary_metric if metric in primary_option_values)
    
    # Move secondary metrics that appear in primary options to primary metrics
    secondary_metrics_to_move = set()
    if secondary_metric:
        for metric in secondary_metric:
            if metric in primary_option_values:
                primary_metrics.add(metric)
                secondary_metrics_to_move.add(metric)
                valid_primary.append(metric)  # Add moved metrics to valid primary metrics
    
    # Update secondary metrics list by removing moved metrics
    final_secondary_metrics = set(secondary_metric or []) - secondary_metrics_to_move
    
    # Set valid primary metrics if we have any
    valid_primary_metrics = valid_primary if valid_primary else None
    
    # Recalculate primary and secondary options
    primary_options = [opt for opt in METRICS_OPTIONS if opt['value'] in primary_metrics]
    secondary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in availabale_metrics 
        and opt['value'] not in primary_metrics
        and (not secondary_metric or opt['value'] in final_secondary_metrics)
    ]
    
    # Validate secondary_metric against available secondary options
    valid_secondary_metrics = None
    if secondary_metric:
        available_secondary_values = {opt['value'] for opt in secondary_options}
        valid_secondary = [metric for metric in final_secondary_metrics if metric in available_secondary_values]
        valid_secondary_metrics = valid_secondary if valid_secondary else None
    
    logger.warning(f"primary_metric {primary_metric}")
    logger.debug(f"availabale_metrics {availabale_metrics}")
    logger.debug(f"primary_options {primary_options}")
    logger.debug(f"secondary_options {secondary_options}")
    logger.debug(f"METRICS_OPTIONS {METRICS_OPTIONS}")
    logger.warning(f"valid_primary_metrics {valid_primary_metrics}")
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
        [Input('reporting-form', 'value'),
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
            
            end_quarter_options = quarter_options_162 if reporting_form == '0420162' else quarter_options_158
            insurance_line_dropdown_options = get_categories_by_level(
                category_structure_162 if reporting_form == '0420162' else category_structure_158, 
                level=2, 
                indent_char="--"
            )

            # Use validated metrics for selected_metrics
            selected_metrics = (primary_metric_value or []) + (secondary_metric_value or [])
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
            
            output = (
                metric_options['primary_y_metric_options'],
                primary_metric_value[0],
                metric_options['secondary_y_metric_options'],
                secondary_metric_value,
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