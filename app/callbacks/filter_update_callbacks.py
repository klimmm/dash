import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import dash
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate
from data_process.data_utils import category_structure_162, category_structure_158, get_categories_by_level
from config.logging_config import get_logger, track_callback, track_callback_end
from constants.filter_options import METRICS_OPTIONS
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PREMIUM_LOSS_TYPES
from app.app_layout import create_component

logger = get_logger(__name__)

# Simplified metric mappings
FORM_METRICS = {
    '0420158': {'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
                'net_premiums', 'net_losses', 'ceded_premiums_ratio', 'ceded_losses_ratio'
               'ceded_losses_to_ceded_premiums_ratio', 'net_loss_ratio'
               },
    '0420162': {'total_premiums', 'total_losses', 'direct_premiums', 'direct_losses',
                'inward_premiums', 'inward_losses', 'ceded_premiums', 'ceded_losses',
                'net_premiums', 'net_losses', 'new_sums', 'sums_end', 'premiums_interm',
                'ceded_premiums_ratio', 'gross_loss_ratio', 'ceded_losses_ratio', 'new_contracts',
                'average_new_premium', 'direct_loss_ratio', 'premiums_interm_ratio', 'commissions_interm',
                'claims_settled', 'average_loss', 'inward_loss_ratio', 'ceded_losses_to_ceded_premiums_ratio',
                'net_loss_ratio', 'average_new_sum_insured', 'average_rate', 'average_sum_insured',
                'commissions_rate'
               }
}

PRIMARY_TO_SECONDARY_METRICS_MAP = {
    'total_premiums': {'total_losses', 'inward_premiums', 'direct_premiums', 
                      'ceded_premiums', 'net_premiums', 'ceded_premiums_ratio', 
                      'gross_loss_ratio'},
    'total_losses': {'direct_losses', 'inward_losses', 'ceded_losses', 
                    'net_losses', 'ceded_losses_ratio'},
    'direct_premiums': {'new_contracts', 'average_new_premium', 'direct_losses',
                       'direct_loss_ratio', 'premiums_interm', 
                       'premiums_interm_ratio', 'commissions_interm'},
    'direct_losses': {'claims_settled', 'average_loss'},
    'inward_premiums': {'inward_losses', 'inward_loss_ratio'},
    'ceded_premiums': {'ceded_losses', 'ceded_premiums_ratio', 'ceded_losses_ratio', 
                      'ceded_losses_to_ceded_premiums_ratio'},
    'ceded_losses': {'ceded_premiums', 'ceded_losses_ratio',
                    'ceded_losses_to_ceded_premiums_ratio'},
    'net_premiums': {'net_losses', 'net_loss_ratio'},
    'net_losses': {'net_premiums', 'net_loss_ratio'},
    'new_sums': {'new_contracts', 'average_new_sum_insured', 'average_rate'},
    'sums_end': {'contracts_end', 'average_sum_insured'},
    'premiums_interm': {'direct_premiums', 'commissions_interm', 'commissions_rate'}
}


@dataclass
class FilterState:
    primary_y_metric: List[str]
    secondary_y_metric: List[str]
    selected_metrics: List[str]
    premium_loss_checklist: List[str]
    selected_lines: List[str]
    show_data_table: bool = False
    clear_filters_btn: int = 0
    reporting_form: str = ''

    @staticmethod
    def normalize(value: Any) -> List[Any]:
        if not value:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return [value]
        return [value] if not isinstance(value, list) else value


def get_premium_loss_state(metric: str, reporting_form: str) -> Tuple[bool, Optional[List[str]]]:
    if not metric:
        return True, ['direct']

    is_form_158 = reporting_form == '0420158'

    states = {
        ('total_premiums', 'total_losses'): 
            (True, ['direct', 'inward']) if is_form_158 else (False, None),
        ('ceded_premiums', 'ceded_losses', 'ceded_premiums_ratio',
         'ceded_losses_to_ceded_premiums_ratio', 'net_premiums', 'net_losses'):
            (True, ['direct', 'inward']),
        ('inward_premiums', 'inward_losses'): 
            (True, ['inward'])
    }

    for metrics, state in states.items():
        if metric in metrics:
            return state
    return True, ['direct']


def get_metric_options(reporting_form: str, primary_metric: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:

    allowed_metrics = FORM_METRICS.get(reporting_form, set())

    primary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in PRIMARY_TO_SECONDARY_METRICS_MAP.keys() and opt['value'] in allowed_metrics
    ]

    secondary_options = []

    if primary_metric:
        # Get the intersection of secondary metrics allowed by both:
        # 1. The primary metric relationships
        # 2. The reporting form's allowed metrics
        potential_secondary = PRIMARY_TO_SECONDARY_METRICS_MAP.get(primary_metric, set())
        allowed_secondary = potential_secondary.intersection(allowed_metrics)
        secondary_options = [opt for opt in METRICS_OPTIONS if opt['value'] in allowed_secondary]

    # logger.debug(f"primary_metric {primary_metric}")
    # logger.debug(f"secondary_options {secondary_options}")

    return {
        'primary_y_metric_options': primary_options,
        'secondary_y_metric_options': secondary_options
    }


def setup_filter_update_callbacks(app: Dash, quarter_options_162, quarter_options_158) -> None:
    @app.callback(
        [Output('primary-y-metric', 'options'),
         Output('secondary-y-metric', 'options'),
         Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('premium-loss-checklist-container', 'children')],
        [Input('reporting-form', 'value'),
         Input('primary-y-metric', 'value')],
         State('premium-loss-checklist', 'value'),
        prevent_initial_call=True
    )
    def update_options(reporting_form, primary_metric, current_values):
        ctx = dash.callback_context
        start_time = track_callback('app.callbacks.filter_update_callbacks', 'update_options', ctx)

        if not ctx.triggered:
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time)
            raise PreventUpdate

        try:
            metric_options = get_metric_options(reporting_form, primary_metric)

            end_quarter_options = quarter_options_162 if reporting_form == '0420162' else quarter_options_158

            insurance_line_dropdown_options = get_categories_by_level(category_structure_162 if reporting_form == '0420162' else category_structure_158, level=2, indent_char="--")

            metric = primary_metric[0] if isinstance(primary_metric, list) and primary_metric else primary_metric
            readonly, enforced_values = get_premium_loss_state(metric, reporting_form)
            values = enforced_values if enforced_values is not None else current_values
            component = create_component('checklist', id='premium-loss-checklist', readonly=readonly, value=values)

            output = metric_options['primary_y_metric_options'], metric_options['secondary_y_metric_options'], end_quarter_options, insurance_line_dropdown_options, [component]

            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, result=output)
            # logger.debug(f"secondary_y_metric_options {metric_options['secondary_y_metric_options']}")

            return output

        except Exception as e:
            logger.error(f"Error in update_options: {str(e)}", exc_info=True)
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, error=str(e))
            raise

    @app.callback(
        [Output('filter-state-store', 'data'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'value')],
        [Input('clear-filters-button', 'n_clicks'),
         Input('primary-y-metric', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('reporting-form', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('premium-loss-checklist', 'value')],
        [State('show-data-table', 'data')]
    )
    def update_values(clear_btn, primary_metric, secondary_metric, 
                     reporting_form, lines, premium_loss, show_table):
        ctx = dash.callback_context
        start_time = track_callback('app.callbacks.filter_update_callbacks', 'update_values', ctx)

        if not ctx.triggered:
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_values', start_time)
            raise PreventUpdate

        try:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Initialize state
            primary = FilterState.normalize(primary_metric)
            secondary = FilterState.normalize(secondary_metric)
            selected_metrics = primary.copy()
            if secondary:
                selected_metrics.extend(secondary)

            state = FilterState(
                primary_y_metric=primary,
                secondary_y_metric=secondary,
                selected_metrics=selected_metrics,
                premium_loss_checklist=FilterState.normalize(premium_loss),
                selected_lines=FilterState.normalize(lines),
                show_data_table=bool(show_table),
                clear_filters_btn=clear_btn or 0,
                reporting_form=reporting_form
            )

            # Update state based on trigger
            if trigger_id == 'clear-filters-button':
                state.primary_y_metric = DEFAULT_PRIMARY_METRICS
                state.secondary_y_metric = []
                state.premium_loss_checklist = DEFAULT_PREMIUM_LOSS_TYPES

            if state.secondary_y_metric:
                allowed_secondary = PRIMARY_TO_SECONDARY_METRICS_MAP.get(state.primary_y_metric[0], set())
                if state.secondary_y_metric[0] not in allowed_secondary:
                    state.secondary_y_metric = []
                    state.selected_metrics = state.primary_y_metric

            # Validate form 158 metrics
            if reporting_form == '0420158' and state.primary_y_metric:
                if state.primary_y_metric[0] not in FORM_METRICS['0420158']:
                    state.primary_y_metric = DEFAULT_PRIMARY_METRICS
                    state.secondary_y_metric = []
                    state.selected_metrics = DEFAULT_PRIMARY_METRICS

            result = (
                vars(state),
                state.primary_y_metric[0] if state.primary_y_metric else None,
                state.secondary_y_metric[0] if state.secondary_y_metric else None
            )

            track_callback_end('app.callbacks.filter_update_callbacks', 'update_values',
                             start_time, result=result)
            return result

        except Exception as e:
            logger.exception("Error in update_values")
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_values', 
                             start_time, error=str(e))
            raise