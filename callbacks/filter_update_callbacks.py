import dash
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate
from data_process.data_utils import category_structure_162, category_structure_158, get_categories_by_level
from config.logging_config import get_logger, track_callback, track_callback_end
from application.app_layout import FilterComponents
from callbacks.get_available_metrics import get_metric_options, get_premium_loss_state

logger = get_logger(__name__)


def setup_filter_update_callbacks(app: Dash, quarter_options_162, quarter_options_158) -> None:
    @app.callback(
        [Output('primary-y-metric', 'options'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value'),
         Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('premium-loss-checklist-container', 'children'),
         Output('filter-state-store', 'data')],
        [Input('reporting-form', 'data'),
         Input('primary-y-metric', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('premium-loss-checklist', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data')],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')],  # Add filter state store state
        prevent_initial_call=True
    )
    def update_options(reporting_form, primary_metric, secondary_metric, current_values, lines, period_type, show_table, current_filter_state):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE
        """
        ctx = dash.callback_context
        start_time = track_callback('app.callbacks.filter_update_callbacks', 'update_options', ctx)
        if not ctx.triggered:
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time)
            raise PreventUpdate
        try:

            metric_options = get_metric_options(reporting_form, primary_metric, secondary_metric)

            # Get validated metrics from the return value
            primary_metric_value = metric_options.get('primary_metric')
            secondary_metric_value = metric_options.get('secondary_metric')
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
            logger.debug(f"component: {[component]}")
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