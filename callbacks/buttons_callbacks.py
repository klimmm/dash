from typing import Any, Dict, List, Optional, Union

import dash
import pandas as pd
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from app.components.button import create_button_group_from_config
from app.style_constants import StyleConstants
from config.components import BUTTON_GROUP_CONFIG
from config.logging import log_callback, error_handler, timer, get_logger

logger = get_logger(__name__)


def get_button_classes(total: int, active_indices: Union[int, List[int]],
                       class_key: str, 
                       disabled_indices: Optional[List[int]] = None
                       ) -> List[str]:
    """Generate button classes based on state, preserving disabled state"""
    active_list = [active_indices] if isinstance(
        active_indices, int) else active_indices
    disabled = disabled_indices or []
    base_class = StyleConstants.BTN[class_key]

    return [
        base_class + " disabled" if i in disabled else  # Keep disabled state regardless
        base_class + " active" if i in active_list and i not in disabled else
        base_class
        for i in range(total)
    ]

class ButtonCallbacks:
    def __init__(self, app: dash.Dash):
        self.app = app
        self._register_callbacks()

    def _register_callbacks(self) -> None:
        """Register button group callbacks"""
        # Set up split mode and pivot column synchronization
        self._setup_split_mode_pivot_sync(
            BUTTON_GROUP_CONFIG['table-split-mode'],
            BUTTON_GROUP_CONFIG['pivot-column']
        )

        # Register standard button group callbacks
        for group_id, config in BUTTON_GROUP_CONFIG.items():
            total_buttons = len(config['buttons'])

            # Define outputs and states
            outputs = [
                Output(f"btn-{group_id}-{btn['value']}", "className",
                       allow_duplicate=True)
                for btn in config['buttons']
            ]
            if group_id == 'top-insurers':
                outputs.append(Output('selected-insurers', 'disabled',
                                      allow_duplicate=True))
            outputs.append(Output(f"{group_id}-selected", "data",
                                  allow_duplicate=True))

            states = [State(f"{group_id}-selected", "data")]

            # Register callbacks
            self._setup_group_callback(group_id, config, total_buttons,
                                       outputs, states)
            if group_id in ['periods-data-table', 'top-insurers',
                            'period-type', 'view-metrics']:
                self._setup_data_store_callback(group_id, config, total_buttons,
                                                outputs, states)

    def _setup_group_callback(self, group_id: str, config: dict,
                                  total_buttons: int, outputs: List,
                                  states: List[State]) -> None:
        """Set up button group interaction callback"""
        inputs = [Input(f"btn-{group_id}-{btn['value']}", "n_clicks")
                  for btn in config['buttons']]
        
        # Add table-split-mode state for pivot-column to track disabled button
        if group_id == 'pivot-column':
            states.append(State("table-split-mode-selected", "data"))
    
        @self.app.callback(outputs, inputs, states, prevent_initial_call=True)
        @log_callback
        @timer
        @error_handler
        def update_button_state(*args: Any) -> List[Any]:
            triggered_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
            current_values = args[-2] if group_id == 'pivot-column' else args[-1]
            split_mode_value = args[-1] if group_id == 'pivot-column' else None
            
            current_values = current_values or []
    
            button_index = next(
                (i for i, btn in enumerate(config['buttons'])
                 if f"btn-{group_id}-{btn['value']}" == triggered_id), None
            )
            if button_index is None:
                return [dash.no_update] * len(outputs)
    
            clicked_value = str(config['buttons'][button_index]['value'])
            new_values = (
                [clicked_value] if not config.get('multi_select') else
                [v for v in current_values if v != clicked_value] + (
                 [clicked_value] if clicked_value not in current_values else []
                )
            )
    
            active_indices = [i for i, btn in enumerate(config['buttons'])
                              if str(btn['value']) in new_values]
                              
            # Get disabled indices for pivot-column based on split-mode value
            disabled_indices = None
            if group_id == 'pivot-column' and split_mode_value:
                disabled_indices = [
                    i for i, btn in enumerate(config['buttons'])
                    if str(btn['value']) == split_mode_value
                ]
                
            button_classes = get_button_classes(
                total_buttons,
                active_indices,
                config['class_key'],
                disabled_indices
            )
    
            result = int(new_values[0]) if group_id in [
                'top-insurers', 'periods-data-table'
            ] else new_values if config.get('multi_select') else new_values[0]
    
            logger.debug(
                f"Button state updated for {group_id}: classes={button_classes}, value={result}")
            return [*button_classes, button_index != total_buttons - 1, result
                   ] if group_id == 'top-insurers' else [
                       *button_classes, result]

    def _setup_data_store_callback(self, group_id: str, config: dict,
                                   total_buttons: int, outputs: List,
                                   states: List[State]) -> None:
        """Set up data store update callback"""
        @self.app.callback(outputs, Input("processed-data-store", "data"), 
                           states, prevent_initial_call=True)
        @log_callback
        @timer
        @error_handler
        def update_from_data_store(processed_data: Any, state: Any = None
                                   ) -> List[Any]:
            if not isinstance(processed_data, dict) or not processed_data:
                raise PreventUpdate

            df = pd.DataFrame(processed_data.get('df', {}))
            if df.empty and group_id == 'top-insurers':
                disabled_indices = list(range(0, total_buttons))
                button_classes = get_button_classes(total_buttons,
                                                    total_buttons - 1,
                                                    config['class_key'],
                                                    disabled_indices)
                return [*button_classes, True, 0]
            elif df.empty:
                disabled_indices = list(range(0, total_buttons))
                button_classes = get_button_classes(total_buttons,
                                                    total_buttons - 1,
                                                    config['class_key'],
                                                    disabled_indices)
                return [*button_classes, dash.no_update]

            if group_id == 'periods-data-table':
                num_available = len(df['year_quarter'].unique())
                active_index = min(state, num_available) - 1
                disabled_indices = list(range(num_available, total_buttons))
                button_classes = get_button_classes(
                    total_buttons, active_index, config['class_key'],
                    disabled_indices if num_available < state else []
                )
                return [*button_classes, active_index + 1]

            if group_id == 'top-insurers':
                active_index = next(
                    (i for i,
                     btn in enumerate(config['buttons']) if str(btn['value'])
                     == str(state)), 0)

                button_classes = get_button_classes(total_buttons,
                                                    active_index,
                                                    config['class_key'])
                is_disabled = active_index != total_buttons - 1
                logger.debug(f"Data store update for {group_id}: classes={button_classes}, is_disabled={is_disabled}, value={state}")
                return [*button_classes, is_disabled, state]

            else:
                active_indices = [i for i, btn in enumerate(config['buttons'])
                                  if str(btn['value']) in state]
                button_classes = get_button_classes(total_buttons,
                                                    active_indices,
                                                    config['class_key'])
                logger.debug(f"Data store update for {group_id}: classes={button_classes}")
                
                return [*button_classes, dash.no_update]
                
            raise PreventUpdate
    
    def _setup_split_mode_pivot_sync(self, split_mode_config: dict, pivot_config: dict) -> None:
        """Set up synchronization between split mode and pivot column button groups"""
        total_buttons = len(pivot_config['buttons'])
        
        # Define outputs for pivot-column buttons
        outputs = [
            Output(f"btn-pivot-column-{btn['value']}", "className", allow_duplicate=True)
            for btn in pivot_config['buttons']
        ]
        outputs.append(Output("pivot-column-selected", "data", allow_duplicate=True))
        
        # Define inputs and states
        inputs = [Input("table-split-mode-selected", "data")]
        states = [State("pivot-column-selected", "data")]

        @self.app.callback(outputs, inputs, states, prevent_initial_call='initial_duplicate')
        @log_callback
        @timer
        @error_handler
        def update_pivot_buttons(split_mode_value: str, pivot_current_value: str) -> List[Any]:
            if not split_mode_value:
                raise PreventUpdate

            # Find button indices
            disabled_index = next(
                (i for i, btn in enumerate(pivot_config['buttons'])
                 if str(btn['value']) == split_mode_value),
                None
            )

            if disabled_index is None:
                raise PreventUpdate

            # If current pivot value matches split mode, we need to change it
            if pivot_current_value == split_mode_value:
                # Select first available value that's not the disabled one
                new_value = next(
                    str(btn['value']) for i, btn in enumerate(pivot_config['buttons'])
                    if i != disabled_index
                )
                active_index = next(
                    i for i, btn in enumerate(pivot_config['buttons'])
                    if str(btn['value']) == new_value
                )
            else:
                # Keep current value
                new_value = pivot_current_value
                active_index = next(
                    i for i, btn in enumerate(pivot_config['buttons'])
                    if str(btn['value']) == pivot_current_value
                )

            # Generate button classes with the disabled button
            button_classes = get_button_classes(
                total_buttons,
                active_index,
                pivot_config['class_key'],
                disabled_indices=[disabled_index]
            )

            logger.debug(
                f"Pivot buttons updated: split_mode={split_mode_value}, "
                f"new_value={new_value}, classes={button_classes}"
            )

            return [*button_classes, new_value]




def setup_buttons(app: dash.Dash) -> Dict[str, html.Div]:
    """Initialize button groups and callbacks"""
    button_groups = {key: create_button_group_from_config(key)
                     for key in BUTTON_GROUP_CONFIG}
    # Register callbacks
    ButtonCallbacks(app)

    return button_groups