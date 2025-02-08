from typing import Dict, List, Union

import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from application.config.button_config import BUTTON_CONFIG
from application.components.button import (
    create_button_group, format_button_id_value)
from application.style_constants import StyleConstants
from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer
from constants.translations import translate

logger = get_logger(__name__)


def get_button_classes(total: int, active_indices: Union[int,
                       List[int]], class_key: str) -> List[str]:
    """Generate button classes array"""
    base_class = StyleConstants.BTN[class_key]
    active_class = StyleConstants.BTN[f"{class_key}_ACTIVE"]

    if isinstance(active_indices, int):
        active_indices = [active_indices]

    return [
        active_class if i in active_indices else base_class
        for i in range(total)
    ]


def setup_buttons(app: dash.Dash) -> Dict[str, html.Div]:
    """Set up all button callbacks with unified state management"""
    button_groups = {key: create_button_group(key) for key in BUTTON_CONFIG}

    def create_button_callback(group_id: str):
        """Create callback for any button group"""
        if group_id == 'top-insurers':
            return

        config = BUTTON_CONFIG[group_id]
        multi_select = config.get('multi_select', False)
        total_buttons = len(config['buttons'])

        # Define outputs based on button type
        outputs = [
            Output(f"btn-{group_id}-{format_button_id_value(btn['value'])}",
                   "className")
            for btn in config['buttons']
        ]

        if multi_select:
            outputs.extend(
                Output(f"{group_id}-{format_button_id_value(btn['value'])}",
                       "data")
                for btn in config['buttons']
            )
        else:
            outputs.append(Output(f"{group_id}-selected", "data"))

        if group_id == 'period-type':
            outputs.append(Output(f"{group_id}-text", "children"))

        # Define inputs and states
        inputs = [
            Input(f"btn-{group_id}-{format_button_id_value(btn['value'])}", "n_clicks")
            for btn in config['buttons']
        ]

        if multi_select:
            states = [
                State(f"{group_id}-{format_button_id_value(btn['value'])}", "data")
                for btn in config['buttons']
            ]
        else:
            states = [State(f"{group_id}-selected", "data")]

        @app.callback(outputs, inputs, states, prevent_initial_call=True)
        @timer
        @log_callback
        @error_handler
        def update_button_state(*args):
            ctx = dash.callback_context
            if not ctx.triggered:
                raise PreventUpdate

            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            button_index = next(
                (i for i, btn in enumerate(config['buttons'])
                 if f"btn-{group_id}-{format_button_id_value(btn['value'])}" ==
                 triggered),
                None
            )

            if button_index is None:
                return [dash.no_update] * len(outputs)

            if multi_select:
                # Handle multi-select buttons (like view-metrics)
                current_states = [
                    args[-(len(config['buttons']) - i)] or []
                    for i in range(len(config['buttons']))
                ]

                # Update the state of clicked button
                new_states = current_states.copy()
                new_states[button_index] = (
                    [] if new_states[button_index] == ['show'] else ['show']
                )

                # Get indices of all active buttons
                active_indices = [
                    i for i, state in enumerate(new_states)
                    if state == ['show']
                ]

                button_classes = get_button_classes(
                    total_buttons, active_indices, config['class_key']
                )

                return [*button_classes, *new_states]
            else:
                # Handle single-select buttons
                new_value = config['buttons'][button_index]['value']
                button_classes = get_button_classes(
                    total_buttons, button_index, config['class_key']
                )

                result = [*button_classes, new_value]
                if group_id == 'period-type':
                    result.append(translate(new_value))

                return result

    # Set up callbacks for all button groups except top-insurers
    for group_id in BUTTON_CONFIG:
        create_button_callback(group_id)

    return button_groups