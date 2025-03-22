from enum import Enum
from typing import Dict, List, Optional, Union
import dash
from dash import Input, Output, State


class ButtonState(Enum):
    """Button states enum"""
    ACTIVE = 'active'
    DISABLED = 'disabled'
    DEFAULT = ''


class ButtonStatesCallbacks:
    def __init__(self, config, ui_config):
        self.logger = config.logger
        self.dash_callback = config.dash_callback
        self.ui_config = ui_config

    def register_callbacks(self, app: dash.Dash) -> None:
        """Register callbacks for all button groups"""
        for group_id, config in self.ui_config.get_button_config().items():
            self._register_group_callback(app, group_id, config)

    def _register_group_callback(self, app: dash.Dash, 
                                 group_id: str, config: Dict) -> None:
        """Register callback for a single button group"""
        buttons = config['options']
        outputs = [
            Output(f"{group_id}-{btn['value']}", "className", 
                  allow_duplicate=True) 
            for btn in buttons
        ]
        inputs = [
            Input(group_id, "data"),
            Input('process-data-one-trigger', 'data')
        ]
        states = [
            State(f"{group_id}-{btn['value']}", "className") 
            for btn in buttons
        ]

        @app.callback(outputs, inputs + states, prevent_initial_call=True)
        @self.dash_callback
        def update_buttons(group_data: Union[str, int], 
                         quarters_data: List[str], 
                         *current_states: List[str]) -> List[str]:
            ctx = dash.callback_context
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            trigger = ctx.triggered[0]["prop_id"]
            if 'process-data-one-trigger' in trigger:
                return self._handle_data_trigger(
                    group_id, group_data, buttons, current_states, quarters_data
                )

            return self._get_button_states(
                group_id, group_data, None, current_states
            )

    def _handle_data_trigger(
        self, group_id: str, group_data: Union[str, int],
        buttons: List[Dict], current_states: List[str],
        quarters: List[str]
    ) -> List[str]:
        """Handle processed data trigger updates"""
        if not quarters:
            return self._get_button_states(
                group_id, None, list(range(len(buttons))), current_states
            )

        if group_id == 'number-of-periods':
            disabled_indices = list(range(len(quarters), len(buttons)))
            active_value = min(group_data or 1, len(quarters))
            return self._get_button_states(
                group_id, active_value, disabled_indices, current_states
            )

        return self._get_button_states(
            group_id, group_data, None, current_states
        )

    def _get_button_states(
        self, group_id: str, values: Union[str, int, List],
        disabled_indices: Optional[List[int]] = None,
        current_states: Optional[List[str]] = None
    ) -> List[str]:
        """Generate button states based on current configuration"""
        buttons = self.ui_config.get_button_config(group_id).get(
            'options', []
        )
        if not isinstance(values, list):
            values = [values] if values is not None else []
        values = [str(v) for v in values]

        states = []
        for i, btn in enumerate(buttons):
            base_class = self._get_base_class(
                current_states[i] if current_states and i < len(current_states)
                else None
            )
            if disabled_indices and i in disabled_indices:
                state = ButtonState.DISABLED.value
            elif str(btn.get('value')) in values:
                state = ButtonState.ACTIVE.value
            else:
                state = ButtonState.DEFAULT.value

            states.append(f"{base_class} {state}")

        return states

    def _get_base_class(self, current_class: Optional[str]) -> str:
        """Extract base class name from current class string"""
        if not current_class:
            return "btn"
        return (
            current_class.replace(f" {ButtonState.ACTIVE.value}", "")
            .replace(f" {ButtonState.DISABLED.value}", "")
            .strip()
        )