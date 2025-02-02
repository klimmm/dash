import json
from typing import List, Optional, Union, Dict, Any

import dash
from dash import Input, Output, State

from config.default_values import (
    DEFAULT_REPORTING_FORM,
    DEFAULT_PERIOD_TYPE,
    DEFAULT_SHOW_MARKET_SHARE,
    DEFAULT_SHOW_CHANGES,
    TOP_N_LIST,
    DEFAULT_NUMBER_OF_PERIODS,
    DEFAULT_SPLIT_MODE
)
from config.callback_logging import log_callback
from config.components_config import BUTTON_CONFIG
from config.logging_config import get_logger
from constants.style_constants import StyleConstants
from constants.translations import translate

logger = get_logger(__name__)


def get_triggered_index(ctx: dash.callback_context,
                        buttons: List[Dict[str, str]],
                        component_id: str) -> Optional[int]:
    """Helper function to get the index of triggered button with validation."""
    logger.debug(f"Entering get_triggered_index for component '{component_id}'")
    if not ctx.triggered:
        logger.debug("No triggers found in context.")
        return None
    try:
        triggered = ctx.triggered[0]["prop_id"].split(".")[0]
        expected_prefix = f"btn-{component_id}-"
        if not triggered.startswith(expected_prefix):
            logger.debug(f"Triggered id '{triggered}' does not start with expected prefix '{expected_prefix}'.")
            return None
        triggered_value = triggered[len(expected_prefix):]
        for i, btn in enumerate(buttons):
            if btn['value'] == triggered_value:
                logger.debug(f"Match found: index {i} for triggered value '{triggered_value}'.")
                return i
        logger.debug("No matching button found for triggered value.")
        return None
    except Exception as e:
        logger.exception("Exception in get_triggered_index")
        raise


def log_button_state(states: Dict[str, List[str]],
                     button_index: Optional[int],
                     config: Dict[str, Any]) -> None:
    """Log the current state of buttons and any state changes."""
    active = [k for k, v in states.items() if v == ['show']]
    logger.debug(
        "Button State Update | "
        f"States: {json.dumps(states)} | "
        f"Triggered Button Index: {button_index} | "
        f"Active Values: {active}"
    )


def create_button_classes(total_buttons: int,
                          active_indices: Optional[Union[int, List[int]]] = None,
                          style_type: str = "GROUP_CONTROL") -> List[str]:
    """Helper function to generate button classes array."""
    logger.debug(f"Creating button classes for {total_buttons} buttons with active indices {active_indices}.")
    classes = [StyleConstants.BTN[style_type]] * total_buttons

    if active_indices is not None:
        if isinstance(active_indices, int):
            if 0 <= active_indices < total_buttons:
                classes[active_indices] = StyleConstants.BTN[f"{style_type}_ACTIVE"]
        else:
            for index in active_indices:
                if 0 <= index < total_buttons:
                    classes[index] = StyleConstants.BTN[f"{style_type}_ACTIVE"]
    logger.debug(f"Button classes generated: {classes}")
    return classes


def setup_multi_choice_buttons(app: dash.Dash) -> None:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    Sets up all multi-choice button callbacks with improved error handling and logging.
    """

    @app.callback(
        [Output(f"btn-metric-toggles-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['metric-toggles']['buttons']] +
        [Output('toggle-selected-market-share', 'data'),
         Output('toggle-selected-qtoq', 'data')],
        [Input(f"btn-metric-toggles-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['metric-toggles']['buttons']],
        [State('toggle-selected-market-share', 'data'),
         State('toggle-selected-qtoq', 'data')]
    )
    @log_callback
    def update_ms_change_view_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates metric toggle states with improved state management and logging.
        """
        logger.debug("Entering update_ms_change_view_buttons.")
        try:
            config = BUTTON_CONFIG['metric-toggles']
            # Use defaults if state is None
            states = {
                'market-share': args[-2] if args[-2] is not None else DEFAULT_SHOW_MARKET_SHARE,
                'qtoq': args[-1] if args[-1] is not None else DEFAULT_SHOW_CHANGES
            }
            logger.debug(
                "Initial Button States | "
                f"All States: {json.dumps(states)} | "
                f"Active Buttons: {[k for k, v in states.items() if v == ['show']]}"
            )

            ctx = dash.callback_context
            if not ctx.triggered:
                logger.debug("No trigger detected in update_ms_change_view_buttons.")
                active_indices = [i for i, value in enumerate(config['values'])
                                  if states[value] == ['show']]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    active_indices if active_indices else None,
                    config['style_type']
                )
                result = (*button_classes, dash.no_update, dash.no_update)
                logger.debug(f"Exiting update_ms_change_view_buttons with result: {result}")
                return result

            logger.debug(
                f"Trigger detected in update_ms_change_view_buttons | "
                f"Triggered Props: {ctx.triggered} | "
                f"Input Values: {list(args[:-2])}"
            )
            button_index = get_triggered_index(ctx, config['buttons'], 'metric-toggles')

            if button_index is not None:
                value = config['values'][button_index]
                previous_state = states[value]
                # Toggle the state
                states[value] = [] if states[value] == ['show'] else ['show']
                logger.debug(
                    f"State Change | Button: {value} | "
                    f"Previous State: {previous_state} | New State: {states[value]}"
                )
                active_indices = [i for i, v in enumerate(config['values'])
                                  if (v == value and states[value]) or
                                     (v != value and states[v] == ['show'])]
                logger.debug(f"Active indices after toggle: {active_indices}")
                button_classes = create_button_classes(
                    config['total_buttons'],
                    active_indices if active_indices else None,
                    config['style_type']
                )
                log_button_state(states, button_index, config)
                result = (*button_classes, states['market-share'], states['qtoq'])
                logger.debug(f"Exiting update_ms_change_view_buttons with result: {result}")
                return result

            logger.debug("Button index not found in triggered context; returning no_update.")
            result = [dash.no_update] * 4
            logger.debug(f"Exiting update_ms_change_view_buttons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_ms_change_view_buttons")
            raise

    @app.callback(
        [Output(f"btn-top-insurers-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']] +
        [Output('top-n-rows', 'data')],
        [Input(f"btn-top-insurers-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']],
        State('top-n-rows', 'data'),
        prevent_initial_call=False
    )
    def update_number_insurers_bittons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates insurer selection with improved multi-select support.
        """
        logger.debug("Entering update_number_insurers_bittons.")
        try:
            current_state = args[-1] if args[-1] is not None else TOP_N_LIST
            config = BUTTON_CONFIG['top-insurers']
            logger.debug(f"Current state in update_number_insurers_bittons: {current_state}")

            # Convert current_state values to strings for matching with button['value']
            current_state_str = [str(val) for val in current_state]
            active_indices = [i for i, btn in enumerate(config['buttons'])
                              if btn['value'] in current_state_str]
            button_classes = create_button_classes(
                config['total_buttons'],
                active_indices if active_indices else None,
                config['style_type']
            )
            ctx = dash.callback_context
            if not ctx.triggered:
                logger.debug(f"No trigger detected. Initial state: {current_state}, Classes: {button_classes}")
                result = (*button_classes, dash.no_update)
                logger.debug(f"Exiting update_number_insurers_bittons with result: {result}")
                return result

            # Get triggered button index from button ID
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            triggered_value = triggered_id.split('btn-top-insurers-')[1]
            button_index = next((i for i, btn in enumerate(config['buttons'])
                                 if btn['value'] == triggered_value), None)

            if button_index is not None:
                value = int(config['buttons'][button_index]['value'])  # Convert back to int
                if value in current_state:
                    current_state.remove(value)
                else:
                    current_state.append(value)
                active_indices = [i for i, btn in enumerate(config['buttons'])
                                  if int(btn['value']) in current_state]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    active_indices if active_indices else None,
                    config['style_type']
                )
                current_state.sort()  # Keep state sorted for consistency
                logger.debug(f"Button clicked: {value}. Updated state: {current_state}")
                result = (*button_classes, current_state)
                logger.debug(f"Exiting update_number_insurers_bittons with result: {result}")
                return result

            result = [dash.no_update] * (config['total_buttons'] + 1)
            logger.debug(f"Exiting update_number_insurers_bittons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_number_insurers_bittons")
            raise


def setup_single_choice_buttons(app: dash.Dash) -> None:
    """
    Sets up all single-choice button callbacks with improved error handling and logging.
    Functions marked with @API_STABILITY: BACKWARDS_COMPATIBLE retain their interface.
    """

    @app.callback(
        [Output(f"btn-period-type-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['period-type']['buttons']] +
        [Output('period-type', 'data'),
         Output('period-type-text', 'children')],
        [Input(f"btn-period-type-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['period-type']['buttons']],
        [State('period-type', 'data')]
    )
    @log_callback
    def update_period_type_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period type selection.
        """
        logger.debug("Entering update_period_type_buttons.")
        try:
            ctx = dash.callback_context
            current_state = args[-1] or DEFAULT_PERIOD_TYPE
            config = BUTTON_CONFIG['period-type']
            button_index = get_triggered_index(ctx, config['buttons'], 'period-type')

            if not ctx.triggered:
                button_classes = create_button_classes(
                    config['total_buttons'],
                    config['values'].index(current_state),
                    config['style_type']
                )
                result = (*button_classes, dash.no_update, translate(current_state))
                logger.debug(f"No trigger. Exiting update_period_type_buttons with result: {result}")
                return result

            if button_index is not None:
                new_state = config['values'][button_index]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    button_index,
                    config['style_type']
                )
                result = (*button_classes, new_state, translate(new_state))
                logger.debug(f"Trigger found. Exiting update_period_type_buttons with result: {result}")
                return result

            result = [dash.no_update] * (config['total_buttons'] + 2)
            logger.debug(f"Exiting update_period_type_buttons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_period_type_buttons")
            raise

    @app.callback(
        [Output(f"btn-reporting-form-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['reporting-form']['buttons']] +
        [Output('reporting-form', 'data')],
        [Input(f"btn-reporting-form-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['reporting-form']['buttons']],
        [State('reporting-form', 'data')]
    )
    @log_callback
    def update_reporting_form_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates reporting form selection.
        """
        logger.debug("Entering update_reporting_form_buttons.")
        try:
            ctx = dash.callback_context
            current_state = args[-1] or DEFAULT_REPORTING_FORM
            config = BUTTON_CONFIG['reporting-form']
            button_index = get_triggered_index(ctx, config['buttons'], 'reporting-form')

            if not ctx.triggered:
                button_classes = create_button_classes(
                    config['total_buttons'],
                    config['values'].index(current_state),
                    config['style_type']
                )
                result = (*button_classes, dash.no_update)
                logger.debug(f"No trigger. Exiting update_reporting_form_buttons with result: {result}")
                return result

            if button_index is not None:
                new_state = config['values'][button_index]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    button_index,
                    config['style_type']
                )
                result = (*button_classes, new_state)
                logger.debug(f"Trigger found. Exiting update_reporting_form_buttons with result: {result}")
                return result

            result = [dash.no_update] * (config['total_buttons'] + 1)
            logger.debug(f"Exiting update_reporting_form_buttons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_reporting_form_buttons")
            raise

    @app.callback(
        [Output(f"btn-table-split-mode-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['table-split-mode']['buttons']] +
        [Output('table-split-mode', 'data')],
        [Input(f"btn-table-split-mode-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['table-split-mode']['buttons']],
        [State('table-split-mode', 'data')]
    )
    @log_callback
    def update_table_split_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates table split mode selection.
        """
        logger.debug("Entering update_table_split_buttons.")
        try:
            ctx = dash.callback_context
            current_state = args[-1] or DEFAULT_SPLIT_MODE
            config = BUTTON_CONFIG['table-split-mode']
            button_index = get_triggered_index(ctx, config['buttons'], 'table-split-mode')

            if not ctx.triggered:
                button_classes = create_button_classes(
                    config['total_buttons'],
                    config['values'].index(current_state),
                    config['style_type']
                )
                result = (*button_classes, dash.no_update)
                logger.debug(f"No trigger. Exiting update_table_split_buttons with result: {result}")
                return result

            if button_index is not None:
                new_state = config['values'][button_index]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    button_index,
                    config['style_type']
                )
                result = (*button_classes, new_state)
                logger.debug(f"Trigger found. Exiting update_table_split_buttons with result: {result}")
                return result

            result = [dash.no_update] * (config['total_buttons'] + 1)
            logger.debug(f"Exiting update_table_split_buttons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_table_split_buttons")
            raise

    @app.callback(
        [Output(f"btn-periods-data-table-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['periods-data-table']['buttons']] +
        [Output('number-of-periods-data-table', 'data')],
        [Input(f"btn-periods-data-table-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['periods-data-table']['buttons']],
        State('number-of-periods-data-table', 'data'),
        prevent_initial_call=False
    )
    @log_callback
    def update_number_periods_buttons(*args):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE.
        Updates period selection.
        """
        logger.debug("Entering update_number_periods_buttons.")
        try:
            ctx = dash.callback_context
            current_state = args[-1] or DEFAULT_NUMBER_OF_PERIODS
            config = BUTTON_CONFIG['periods-data-table']
            button_index = get_triggered_index(ctx, config['buttons'], 'periods-data-table')

            if not ctx.triggered:
                button_classes = create_button_classes(
                    config['total_buttons'],
                    config['values'].index(current_state),
                    config['style_type']
                )
                result = (*button_classes, dash.no_update)
                logger.debug(f"No trigger. Exiting update_number_periods_buttons with result: {result}")
                return result

            if button_index is not None:
                new_state = config['values'][button_index]
                button_classes = create_button_classes(
                    config['total_buttons'],
                    button_index,
                    config['style_type']
                )
                result = (*button_classes, new_state)
                logger.debug(f"Trigger found. Exiting update_number_periods_buttons with result: {result}")
                return result

            result = [dash.no_update] * (config['total_buttons'] + 1)
            logger.debug(f"Exiting update_number_periods_buttons with result: {result}")
            return result

        except Exception as e:
            logger.exception("Exception in update_number_periods_buttons")
            raise