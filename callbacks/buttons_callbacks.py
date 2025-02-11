from typing import Any, cast, Dict, List, Optional, Tuple, Union

import dash
import pandas as pd
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate


from app.style_constants import StyleConstants
from app.components.button import create_button_group_from_config
from config.components import BUTTON_GROUP_CONFIG
from config.types import ButtonGroupConfig
from config.logging import log_callback, error_handler, get_logger, timer

logger = get_logger(__name__)


def get_button_classes(total: int,
                       active_indices: Union[int, List[int]],
                       class_key: str,
                       disabled_indices: Optional[List[int]] = None
                       ) -> List[str]:
    """Generate button classes based on state"""
    classes = (
        {k: f"{StyleConstants.BTN[class_key]}{' ' + k if k != 'base' else ''}"
         for k in ['base', 'active', 'disabled']})
    active_indices = [active_indices] if isinstance(
        active_indices, int) else active_indices

    return [classes['disabled'] if i in (disabled_indices or []) else
            classes['active'] if i in active_indices else
            classes['base'] for i in range(total)]


def update_button_state(config: ButtonGroupConfig, button_index: int,
                        current_values: List[str]) -> List[Any]:
    """Handle button state updates"""
    clicked_value = str(config['buttons'][button_index]['value'])
    multi_select = config.get('multi_select', False)

    new_values = ([v for v in current_values if v != clicked_value]
                  if clicked_value in current_values else
                  current_values + [
                      clicked_value]) if multi_select else [clicked_value]

    active_indices = [i for i, btn in enumerate(config['buttons'])
                      if str(btn['value']) in new_values]
    button_classes = get_button_classes(len(config['buttons']), active_indices,
                                        config['class_key'])

    result = [*button_classes, new_values if multi_select else new_values[0]]

    return result


class ButtonCallbackManager:
    """Manages button callbacks"""

    def __init__(self, app: dash.Dash):
        self.app = app
        self._register_callbacks()
        self._setup_top_insurers_callback()

    def _get_io_components(self, group_id: str,
                           config: ButtonGroupConfig
                           ) -> Tuple[List[Output], List[Input], List[State]]:
        """Get outputs, inputs and states for a button group"""
        multi_select = config.get('multi_select', False)
        store_id = group_id if multi_select else f"{group_id}-selected"

        outputs = [Output(f"btn-{group_id}-{btn['value']}", "className")
                   for btn in config['buttons']]
        outputs.append(Output(store_id, "data"))

        inputs = [Input(f"btn-{group_id}-{btn['value']}", "n_clicks")
                  for btn in config['buttons']]
        states = [State(store_id, "data")]

        return outputs, inputs, states

    def _setup_period_data_callback(self, group_id: str,
                                    config: ButtonGroupConfig) -> None:
        """Setup period data specific callback"""
        total_buttons = len(config['buttons'])
        outputs = [Output(f"btn-{group_id}-{btn['value']}", "className",
                          allow_duplicate=True) for btn in config['buttons']]

        @self.app.callback(
            outputs,
            Input("processed-data-store", "data"),
            State(f'{group_id}-selected', 'data'),
            prevent_initial_call=True
        )
        @log_callback
        @timer
        @error_handler
        def update_period_buttons(processed_data: Any,
                                  num_periods_selected: int) -> List[str]:
            if not processed_data or not isinstance(processed_data, dict):
                raise PreventUpdate

            df = pd.DataFrame(processed_data.get('df', {}))
            if df.empty:
                raise PreventUpdate

            num_available = len(df['year_quarter'].unique())
            active_index = min(num_periods_selected or 1, num_available) - 1
            disabled_indices = (list(range(num_available, total_buttons))
                                if num_available < num_periods_selected
                                else [])

            return get_button_classes(total_buttons, active_index,
                                      config['class_key'], disabled_indices)

    def _setup_top_insurers_callback(self) -> None:
        """Setup top insurers callback"""
        config = cast(ButtonGroupConfig, BUTTON_GROUP_CONFIG['top-insurers'])
        buttons = config['buttons']
        total_buttons = len(buttons)

        outputs = [
            Output(f"btn-top-insurers-{btn['value']}", "className")
            for btn in buttons
        ] + [
            Output('top-n-rows', 'data'),
            Output('selected-insurers', 'disabled')
        ]

        inputs = [
            Input(f"btn-top-insurers-{btn['value']}", "n_clicks")
            for btn in buttons
        ] + [Input('processed-data-store', 'data')]

        @self.app.callback(
            outputs,
            inputs,
            State('top-n-rows', 'data'),
            prevent_initial_call=True
        )
        @log_callback
        @timer
        @error_handler
        def update_top_insurers(*args: Any
                                ) -> Tuple[Union[str, int, bool], ...]:
            ctx = dash.callback_context
            if not ctx.triggered:
                raise PreventUpdate

            processed_data = args[-2]  # -2 because -1 is top-n-rows data
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"trigger {triggered}")

            df = pd.DataFrame(
                processed_data.get('df', {})
            ) if processed_data else pd.DataFrame()

            logger.debug(f"df is empty {df.empty}")
            if df.empty:
                current_idx = total_buttons - 1
                button_classes = get_button_classes(total_buttons, current_idx,
                                                    config['class_key'])
                return (*button_classes, 0, True)

            if triggered == 'processed-data-store':
                if not processed_data or 'df' not in processed_data:
                    current_idx = total_buttons - 1
                    button_classes = get_button_classes(total_buttons,
                                                        current_idx,
                                                        config['class_key'])
                    return (*button_classes, 0, True)
                logger.debug(f"prevent update trigger {triggered}")
                raise PreventUpdate

            current_value = args[-1] if args[-1] is not None else config.get(
                'default', 0)  # Added default value

            button_index = next(
                (i for i, btn in enumerate(buttons)
                 if f"btn-top-insurers-{btn['value']}" == triggered),
                -1  # Changed None to -1
            )
            if button_index >= 0:  # Changed condition
                current_value = buttons[button_index]['value']

            current_idx = next(
                (i for i, btn in enumerate(buttons)
                 if str(btn['value']) == str(current_value)),
                total_buttons - 1  # Changed None to default index
            )

            button_classes = get_button_classes(total_buttons, current_idx,
                                                config['class_key'])
            logger.debug(f"button_classes {button_classes}")

            try:
                val_int = int(str(
                    current_value)) if current_value is not None else 0
                is_valid_top_n = val_int in [5, 10, 20]
            except (ValueError, TypeError):
                val_int = 0
                is_valid_top_n = False
            output_value = val_int if is_valid_top_n else 0
            logger.debug(f"output_value {output_value}")
            return (*button_classes, output_value, is_valid_top_n)

    def _register_callbacks(self) -> None:
        """Register all button callbacks"""
        for group_id, config in BUTTON_GROUP_CONFIG.items():
            if group_id == 'top-insurers':
                continue

            outputs, inputs, states = self._get_io_components(group_id, config)
            
            @self.app.callback(outputs, inputs, states,
                               prevent_initial_call=True)
            @log_callback
            @timer
            @error_handler
            def update_state(*args: Any, _group_id: str = group_id,
                             _config: ButtonGroupConfig = config,
                             _outputs: List[Output] = outputs) -> List[Any]:
                ctx = dash.callback_context
                if not ctx.triggered:
                    raise PreventUpdate

                triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
                button_index = next(
                    (i for i, btn in enumerate(_config['buttons']) if
                     f"btn-{_group_id}-{btn['value']}" == triggered_id), None)

                if button_index is None:
                    return [dash.no_update] * len(_outputs)

                result = update_button_state(
                    _config, button_index, args[-1] or [])

                # Handle period data conversion
                if _group_id == 'periods-data-table':
                    data_idx = next(
                        i for i, output in enumerate(_outputs)
                        if output.component_property != 'className')
                    try:
                        result[data_idx] = int(result[data_idx])
                    except (ValueError, TypeError):
                        logger.debug(
                            f"Invalid period value: {result[data_idx]}")

                # Ensure result length matches outputs
                if len(result) < len(_outputs):
                    result.extend([None] * (len(_outputs) - len(result)))
                logger.debug(f"result {result}")

                return result

            if group_id == 'periods-data-table':
                self._setup_period_data_callback(group_id, config)


def setup_buttons(app: dash.Dash) -> Dict[str, html.Div]:
    """Initialize button groups and callbacks"""
    button_groups = {key: create_button_group_from_config(key)
                     for key in BUTTON_GROUP_CONFIG}
    ButtonCallbackManager(app)
    return button_groups