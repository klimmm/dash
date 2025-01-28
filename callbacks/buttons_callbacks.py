import dash
import json
from dash import Input, Output, State
from typing import List, Optional, Union, Dict, Any
from constants.translations import translate
from constants.style_config import StyleConstants
from config.default_values import (
    DEFAULT_REPORTING_FORM,
    DEFAULT_PERIOD_TYPE,
    DEFAULT_SHOW_MARKET_SHARE,
    DEFAULT_SHOW_CHANGES,
    DEFAULT_NUMBER_OF_INSURERS,
    DEFAULT_NUMBER_OF_PERIODS
)
from config.logging_config import get_logger, log_callback, get_triggered_index


logger = get_logger(__name__)

# Centralized button configuration constants
BUTTON_VALUES = {
    'metric_toggles': {
        'values': ['market-share', 'qtoq'],
        'prefix': 'btn-metric-toggles-',
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 2,
        'multi_choice': True,
        'default_state': {'market-share': [], 'qtoq': []}
    },
    'top_insurers': {
        'values': [5, 10, 20, 999],
        'prefix': 'btn-top-insurers-top-',
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 4,
        'multi_choice': True,
        'default_state': []
    },
    'period_type': {
        'values': ['ytd', 'yoy_q', 'yoy_y', 'qoq', 'mat'],
        'prefix': 'btn-period-type-',
        'style_type': 'PERIOD',
        'total_buttons': 5
    },
    'reporting_form': {
        'values': ['0420158', '0420162'],
        'prefix': 'btn-reporting-form-',
        'style_type': 'PERIOD',
        'total_buttons': 2
    },
    'periods_data_table': {
        'values': list(range(1, 6)),
        'prefix': 'btn-periods-data-table-period-',
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 5
    }
}


def log_button_state(states: Dict[str, List[str]], button_index: Optional[int], 
                    config: Dict[str, Any]) -> None:
    """Log the current state of buttons and any state changes."""
    logger.debug(
        "Button State Update | "
        f"States: {json.dumps(states)} | "
        f"Triggered Button Index: {button_index} | "
        f"Active Values: {[v for v, s in states.items() if s == ['show']]}"
    )


def create_button_classes(total_buttons: int, active_indices: Optional[Union[int, List[int]]] = None, 
                         style_type: str = "GROUP_CONTROL") -> List[str]:
    """Helper function to generate button classes array"""
    classes = [StyleConstants.BTN[style_type]] * total_buttons

    if active_indices is not None:
        # Handle single integer
        if isinstance(active_indices, int):
            if 0 <= active_indices < total_buttons:
                classes[active_indices] = StyleConstants.BTN[f"{style_type}_ACTIVE"]
        # Handle list of integers
        else:
            for index in active_indices:
                if 0 <= index < total_buttons:
                    classes[index] = StyleConstants.BTN[f"{style_type}_ACTIVE"]
    return classes


def setup_buttons_callbacks_multichoice(app: dash.Dash) -> None:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    Sets up all button callbacks with improved error handling and logging.
    """
    @app.callback(
        [Output(f"{BUTTON_VALUES['metric_toggles']['prefix']}{toggle}", "className")
         for toggle in BUTTON_VALUES['metric_toggles']['values']] +
        [Output('toggle-selected-market-share', 'data'),
         Output('toggle-selected-qtoq', 'data')],
        [Input(f"{BUTTON_VALUES['metric_toggles']['prefix']}{toggle}", "n_clicks")
         for toggle in BUTTON_VALUES['metric_toggles']['values']],
        [State('toggle-selected-market-share', 'data'),
         State('toggle-selected-qtoq', 'data')]
    )
    @log_callback
    def update_ms_dynamic_toggles(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates metric toggle states with improved state management and logging.
        """
        config = BUTTON_VALUES['metric_toggles']
        states = {
            'market-share': args[-2] if args[-2] is not None else DEFAULT_SHOW_MARKET_SHARE,
            'qtoq': args[-1] if args[-1] is not None else DEFAULT_SHOW_CHANGES
        }

        # Log initial state of all buttons before any changes
        logger.debug(
            f"Initial Button States | "
            f"All States: {json.dumps(states)} | "
            f"Active Buttons: {[k for k, v in states.items() if v == ['show']]}"
        )

        ctx = dash.callback_context
        if not ctx.triggered:
            logger.debug("No trigger detected - returning initial state")
            active_indices = [i for i, value in enumerate(config['values']) 
                            if states[value] == ['show']]
            button_classes = create_button_classes(
                config['total_buttons'],
                active_indices if active_indices else None,
                config['style_type']
            )
            return (*button_classes, dash.no_update, dash.no_update)

        # Log trigger information
        logger.debug(
            f"Trigger detected | "
            f"Triggered Props: {ctx.triggered} | "
            f"Input Values: {[arg for arg in args[:-2]]}"
        )

        button_index = get_triggered_index(ctx, config['values'], config['prefix'])

        if button_index is not None:
            value = config['values'][button_index]
            previous_state = states[value]

            # Toggle the state
            states[value] = [] if states[value] == ['show'] else ['show']

            # Log state change
            logger.debug(
                f"State Change | "
                f"Button: {value} | "
                f"Previous State: {previous_state} | "
                f"New State: {states[value]}"
            )

            active_indices = [i for i, v in enumerate(config['values']) 
                            if (v == value and states[value]) or 
                               (v != value and states[v] == ['show'])]

            # Log active buttons
            logger.debug(f"Active Indices: {active_indices}")

            button_classes = create_button_classes(
                config['total_buttons'],
                active_indices if active_indices else None,
                config['style_type']
            )

            # Log final state before return
            log_button_state(states, button_index, config)

            return (*button_classes, states['market-share'], states['qtoq'])

        logger.warning("Button index not found in triggered context")
        return [dash.no_update] * 4

    @app.callback(
        [Output(f"{BUTTON_VALUES['top_insurers']['prefix']}{n}", "className")
         for n in BUTTON_VALUES['top_insurers']['values']] +
        [Output('top-n-rows', 'data')],
        [Input(f"{BUTTON_VALUES['top_insurers']['prefix']}{n}", "n_clicks")
         for n in BUTTON_VALUES['top_insurers']['values']],
        State('top-n-rows', 'data'),
        prevent_initial_call=False
    )
    @log_callback
    def update_number_insurers(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates insurer selection with improved multi-select support.
        """
        current_state = args[-1] if args[-1] is not None else DEFAULT_NUMBER_OF_INSURERS
        config = BUTTON_VALUES['top_insurers']
        ctx = dash.callback_context

        logger.debug(f" current_state {current_state}")

        active_indices = [i for i, value in enumerate(config['values']) 
                            if value in current_state]

        button_classes = create_button_classes(
            config['total_buttons'],
            active_indices if active_indices else None,
            config['style_type']
        )

        if not ctx.triggered:
            logger.debug(f"Initial state: {current_state}, Classes: {button_classes}")
            return (*button_classes, dash.no_update)

        button_index = get_triggered_index(ctx, config['values'], config['prefix'])

        if button_index is not None:
            value = config['values'][button_index]
            # Toggle selection
            if value in current_state:
                current_state.remove(value)
            else:
                current_state.append(value)

            active_indices = [i for i, v in enumerate(config['values']) 
                            if v in current_state]
            button_classes = create_button_classes(
                config['total_buttons'],
                active_indices if active_indices else None,
                config['style_type']
            )

            current_state.sort()  # Keep state sorted for consistency
            logger.debug(f"Updated state: {current_state}, Button clicked: {value}")
            return (*button_classes, current_state)

        return [dash.no_update] * (config['total_buttons'] + 1)


def setup_buttons_callbacks_singlechoice(app: dash.Dash) -> None:
    @app.callback(
        [Output(f"{BUTTON_VALUES['period_type']['prefix']}{pt.replace('_', '-')}", "className") 
         for pt in BUTTON_VALUES['period_type']['values']] +
        [Output('period-type', 'data'),
         Output('period-type-text', 'children')],
        [Input(f"{BUTTON_VALUES['period_type']['prefix']}{pt.replace('_', '-')}", "n_clicks") 
         for pt in BUTTON_VALUES['period_type']['values']],
        [State('period-type', 'data')]
    )
    @log_callback
    def update_period_type(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period type selection.
        """
        ctx = dash.callback_context

        current_state = args[-1] or DEFAULT_PERIOD_TYPE
        config = BUTTON_VALUES['period_type']

        button_index = get_triggered_index(ctx, 
                                         [v.replace('_', '-') for v in config['values']],
                                         config['prefix'])

        if not ctx.triggered:
            button_classes = create_button_classes(
                config['total_buttons'],
                config['values'].index(current_state),
                config['style_type']
            )
            return (*button_classes, dash.no_update, translate(current_state))

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index, 
                config['style_type']
            )
            return (*button_classes, new_state, translate(new_state))

        return [dash.no_update] * (config['total_buttons'] + 2)


    @app.callback(
        [Output(f"{BUTTON_VALUES['reporting_form']['prefix']}{form}", "className") 
         for form in BUTTON_VALUES['reporting_form']['values']] +
        [Output('reporting-form', 'data')],
        [Input(f"{BUTTON_VALUES['reporting_form']['prefix']}{form}", "n_clicks") 
         for form in BUTTON_VALUES['reporting_form']['values']],
        [State('reporting-form', 'data')]
    )
    @log_callback
    def update_reporting_form(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates reporting form selection.
        """

        ctx = dash.callback_context

        current_state = args[-1] or DEFAULT_REPORTING_FORM
        config = BUTTON_VALUES['reporting_form']
        button_index = get_triggered_index(ctx, config['values'], config['prefix'])

        if not ctx.triggered:
            button_classes = create_button_classes(
                config['total_buttons'],
                config['values'].index(current_state), 
                config['style_type']
            )
            return (*button_classes, dash.no_update)

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index, 
                config['style_type']
            )
            return (*button_classes, new_state)

        return [dash.no_update] * (config['total_buttons'] + 1)

    @app.callback(
        [Output(f"{BUTTON_VALUES['periods_data_table']['prefix']}{i}", "className") 
         for i in BUTTON_VALUES['periods_data_table']['values']] +
        [Output('number-of-periods-data-table', 'data')],
        [Input(f"{BUTTON_VALUES['periods_data_table']['prefix']}{i}", "n_clicks") 
         for i in BUTTON_VALUES['periods_data_table']['values']],
        State('number-of-periods-data-table', 'data'),
        prevent_initial_call=False
    )
    @log_callback
    def update_number_periods(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period selection.
        """
        ctx = dash.callback_context
        current_state = args[-1] or DEFAULT_NUMBER_OF_PERIODS
        config = BUTTON_VALUES['periods_data_table']
        button_index = get_triggered_index(ctx, config['values'], config['prefix'])

        if not ctx.triggered:
            button_classes = create_button_classes(
                config['total_buttons'],
                config['values'].index(current_state), 
                config['style_type']
            )
            return (*button_classes, dash.no_update)

        if button_index is not None:
            new_state = config['values'][button_index]
            button_classes = create_button_classes(
                config['total_buttons'],
                button_index,
                config['style_type']
            )
            return (*button_classes, new_state)

        return [dash.no_update] * (config['total_buttons'] + 1)