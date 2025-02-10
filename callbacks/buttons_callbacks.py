from typing import Any, cast, List, Optional, Union

import dash
import pandas as pd
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from app.style_constants import StyleConstants
from app.components.button import (
     ButtonGroupConfig, create_button_group, format_button_id_value)
from app.ui_configs.button_config import BUTTON_CONFIG
from config.callback_logging_config import error_handler, log_callback
from config.logging_config import get_logger, timer
from constants.translations import translate

logger = get_logger(__name__)


def get_button_classes(
    total: int,
    active_indices: Union[int, List[int]],
    class_key: str,
    disabled_indices: Optional[List[int]] = None
) -> List[str]:
    """Generate button classes based on state"""
    base_class = StyleConstants.BTN[class_key]
    classes = {
        'base': base_class,
        'active': f"{base_class} active",
        'disabled': f"{base_class} disabled"
    }

    active_indices = [active_indices] if isinstance(
        active_indices, int) else active_indices
    disabled_indices = disabled_indices or []

    return [
        classes['disabled'] if i in disabled_indices else
        classes['active'] if i in active_indices else
        classes['base']
        for i in range(total)
    ]


def update_button_state(group_id: str, config: ButtonGroupConfig,
                        button_index: int, args: List[Any]
                        ) -> List[Union[str, int, List[str], None]]:
    """Handle button state updates"""
    total_buttons = len(config['buttons'])
    multi_select = config.get('multi_select', False)

    if multi_select:
        current_states = [args[-(len(config['buttons']) - i)] or [
        ] for i in range(len(config['buttons']))]
        new_states = current_states.copy()
        new_states[button_index] = [
        ] if new_states[button_index] == ['show'] else ['show']
        active_indices = [
            i for i, state in enumerate(new_states) if state == ['show']]
        button_classes = get_button_classes(
            total_buttons, active_indices, config['class_key']
        )
        return [*button_classes, *new_states]

    new_value = config['buttons'][button_index]['value']
    button_classes = get_button_classes(
        total_buttons, button_index, config['class_key']
    )
    result: List[Union[
        str, int, List[str], None]] = [*button_classes, new_value]
    if group_id == 'period-type':
        result.append(translate(str(new_value)) if isinstance(
            new_value, int) else translate(new_value))

    return result


def register_callback(app: dash.Dash, group_id: str) -> None:
    """Register callback for button group"""
    if group_id == 'top-insurers':
        return

    config = cast(ButtonGroupConfig, BUTTON_CONFIG[group_id])
    multi_select = config.get('multi_select', False)
    buttons = config['buttons']

    # Build outputs
    outputs = [
        Output(f"btn-{group_id}-{format_button_id_value(btn['value'])}",
               "className")
        for btn in buttons
    ]

    if multi_select:
        outputs.extend(
            Output(f"{group_id}-{format_button_id_value(btn['value'])}", "data")
            for btn in buttons
        )
    else:
        outputs.append(Output(f"{group_id}-selected", "data"))

    if group_id == 'period-type':
        outputs.append(Output(f"{group_id}-text", "children"))

    # Build inputs and states
    inputs = [
        Input(f"btn-{group_id}-{format_button_id_value(btn['value'])}",
              "n_clicks")
        for btn in buttons
    ]

    states = (
        [State(f"{group_id}-{format_button_id_value(btn['value'])}", "data")
         for btn in buttons]
        if multi_select else
        [State(f"{group_id}-selected", "data")]
    )

    @app.callback(outputs, inputs, states, prevent_initial_call=True)
    @log_callback  # Move log_callback to be first after app.callback
    @error_handler
    @timer
    def update_state(*args: Any) -> List[Union[str, int, List[str], None]]:
        logger.debug(f"update_state called with args: {args}")  # Debug log
        ctx = dash.callback_context
        logger.debug(f"callback context triggered: {ctx.triggered}")  # Debug context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        button_index = next(
            (i for i, btn in enumerate(buttons)
             if f"btn-{group_id}-{format_button_id_value(btn['value'])}"
             == triggered_id),
            None
        )

        return (
            update_button_state(group_id, config, button_index, list(args))
            if button_index is not None else
            [dash.no_update] * len(outputs)
        )


def setup_buttons(app: dash.Dash) -> dict[str, html.Div]:
    """Initialize button groups and callbacks"""
    button_groups = {key: create_button_group(key) for key in BUTTON_CONFIG}

    # Period button callback
    group_id = 'periods-data-table'
    config = cast(ButtonGroupConfig, BUTTON_CONFIG[group_id])
    total_buttons = len(config['buttons'])

    @app.callback(
        [Output(f"btn-{group_id}-{format_button_id_value(btn['value'])}",
                "className", allow_duplicate=True)
         for btn in config['buttons']],
        Input("processed-data-store", "data"),
        State(f'{group_id}-selected', 'data'),
        prevent_initial_call=True
    )
    @error_handler
    @log_callback
    @timer
    def update_period_buttons(processed_data: Any, num_periods_selected: int
                              ) -> List[str]:

        df = pd.DataFrame(processed_data['df'])
        if df.empty:
            raise PreventUpdate

        num_periods_available = len(df['year_quarter'].unique())
        '''if num_periods_available >= num_periods_selected:
            raise PreventUpdate'''

        logger.debug(f"Periods selected: {num_periods_selected}")
        logger.debug(f"Periods available: {num_periods_available}")
        active_index = min(num_periods_selected, num_periods_available) - 1
        disabled_indices = (
            list(range(num_periods_available, total_buttons))
            if num_periods_available < num_periods_selected else
            []
        )

        classes = get_button_classes(
            total_buttons, active_index,
            config['class_key'], disabled_indices
        )
        logger.debug(f"Button classes: {classes}")
        return classes

    # Register standard callbacks
    for group_id in BUTTON_CONFIG:
        register_callback(app, group_id)

    return button_groups