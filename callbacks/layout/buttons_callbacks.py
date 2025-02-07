from typing import List, Optional, Union, Dict

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from application.config.components_config import BUTTON_CONFIG
from application.style.style_constants import StyleConstants
from config.callback_logging import log_callback
from config.logging_config import get_logger
from constants.translations import translate

logger = get_logger(__name__)


def get_triggered_index(ctx: dash.callback_context, 
                        buttons: List[Dict[str, str]], 
                        component_id: str) -> Optional[int]:
    """Helper function to get the index of triggered button with validation"""
    if not ctx.triggered:
        return None
    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    expected_prefix = f"btn-{component_id}-"

    # Extract the value part from the triggered ID
    if not triggered.startswith(expected_prefix):
        return None
    triggered_value = triggered[len(expected_prefix):]

    # Find matching button index
    for i, btn in enumerate(buttons):
        if btn['value'] == triggered_value:
            return i
    return None


def create_button_classes(total_buttons: int, active_indices: Optional[Union[int, List[int]]] = None, 
                         class_key: str = "GROUP_CONTROL") -> List[str]:
    """Helper function to generate button classes array"""
    classes = [StyleConstants.BTN[class_key]] * total_buttons

    if active_indices is not None:
        # Handle single integer
        if isinstance(active_indices, int):
            if 0 <= active_indices < total_buttons:
                classes[active_indices] = StyleConstants.BTN[f"{class_key}_ACTIVE"]
        # Handle list of integers
        else:
            for index in active_indices:
                if 0 <= index < total_buttons:
                    classes[index] = StyleConstants.BTN[f"{class_key}_ACTIVE"]
    return classes


def setup_buttons(app: dash.Dash) -> None:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    Sets up all button callbacks with improved error handling and logging.
    """
    @app.callback(
        [Output(f"btn-metric-toggles-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['metric-toggles']['buttons']] +
        [Output('toggle-selected-market-share', 'data'),
         Output('toggle-selected-qtoq', 'data')],
        [Input(f"btn-metric-toggles-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['metric-toggles']['buttons']],
        [State('toggle-selected-market-share', 'data'),
         State('toggle-selected-qtoq', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    def update_ms_change_view_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates metric toggle states with improved state management and logging.
        """
        config = BUTTON_CONFIG['metric-toggles']
        states = {
            'market-share': args[-2] if args[-2] is not None else [],
            'qtoq': args[-1] if args[-1] is not None else []
        }

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        button_index = get_triggered_index(ctx, config['buttons'], 'metric-toggles')

        if button_index is not None:
            value = config['values'][button_index]
            previous_state = states[value]

            # Toggle the state
            states[value] = [] if states[value] == ['show'] else ['show']

            active_indices = [i for i, v in enumerate(config['values']) 
                              if (v == value and states[value]) or 
                              (v != value and states[v] == ['show'])]

            button_classes = create_button_classes(
                config['total_buttons'],
                active_indices if active_indices else None,
                config['class_key']
            )

            return (*button_classes, states['market-share'], states['qtoq'])

        logger.debug("Button index not found in triggered context")
        return [dash.no_update] * 4

    @app.callback(
        [Output(f"btn-period-type-{btn['value']}", "className") 
         for btn in BUTTON_CONFIG['period-type']['buttons']] +
        [Output('period-type', 'data'),
         Output('period-type-text', 'children')],
        [Input(f"btn-period-type-{btn['value']}", "n_clicks") 
         for btn in BUTTON_CONFIG['period-type']['buttons']],
        [State('period-type', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    def update_period_type_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period type selection.
        """
        ctx = dash.callback_context

        config = BUTTON_CONFIG['period-type']
        button_index = get_triggered_index(ctx, config['buttons'], 'period-type')

        if not ctx.triggered:
            raise PreventUpdate

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index, 
                config['class_key']
            )
            return (*button_classes, new_state, translate(new_state))

        return [dash.no_update] * (config['total_buttons'] + 2)

    @app.callback(
        [Output(f"btn-reporting-form-{btn['value']}", "className") 
         for btn in BUTTON_CONFIG['reporting-form']['buttons']] +
        [Output('reporting-form', 'data')],
        [Input(f"btn-reporting-form-{btn['value']}", "n_clicks") 
         for btn in BUTTON_CONFIG['reporting-form']['buttons']],
        [State('reporting-form', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    def update_reporting_form_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates reporting form selection.
        """

        ctx = dash.callback_context

        config = BUTTON_CONFIG['reporting-form']
        button_index = get_triggered_index(ctx, config['buttons'], 'reporting-form')

        if not ctx.triggered:
            raise PreventUpdate

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index, 
                config['class_key']
            )
            return (*button_classes, new_state)

        return [dash.no_update] * (config['total_buttons'] + 1)

    @app.callback(
        [Output(f"btn-table-split-mode-{btn['value']}", "className") 
         for btn in BUTTON_CONFIG['table-split-mode']['buttons']] +
        [Output('table-split-mode', 'data')],
        [Input(f"btn-table-split-mode-{btn['value']}", "n_clicks") 
         for btn in BUTTON_CONFIG['table-split-mode']['buttons']],
        [State('table-split-mode', 'data')],
        prevent_initial_call=True
    )

    @log_callback
    def update_table_split_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates reporting form selection.
        """

        ctx = dash.callback_context

        config = BUTTON_CONFIG['table-split-mode']
        button_index = get_triggered_index(ctx, config['buttons'], 'table-split-mode')

        if not ctx.triggered:
            raise PreventUpdate

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index, 
                config['class_key']
            )
            return (*button_classes, new_state)

        return [dash.no_update] * (config['total_buttons'] + 1)

    @app.callback(
        [Output(f"btn-periods-data-table-{btn['value']}", "className") 
         for btn in BUTTON_CONFIG['periods-data-table']['buttons']] +
        [Output('number-of-periods-data-table', 'data')],
        [Input(f"btn-periods-data-table-{btn['value']}", "n_clicks") 
         for btn in BUTTON_CONFIG['periods-data-table']['buttons']],
        State('number-of-periods-data-table', 'data'),
        prevent_initial_call=True
    )
    @log_callback
    def update_number_periods_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period selection.
        """
        ctx = dash.callback_context
        config = BUTTON_CONFIG['periods-data-table']
        button_index = get_triggered_index(ctx, config['buttons'], 'periods-data-table')

        if not ctx.triggered:
            raise PreventUpdate

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index,
                config['class_key']
            )
            return (*button_classes, new_state)

        return [dash.no_update] * (config['total_buttons'] + 1)