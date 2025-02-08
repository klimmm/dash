from typing import Any, Dict, Union

import dash_bootstrap_components as dbc
from dash import html

from application.style_constants import StyleConstants
from application.config.button_config import BUTTON_CONFIG
from config.logging_config import get_logger

logger = get_logger(__name__)


def create_button(
    label: str,
    button_id: str,
    className: str = StyleConstants.BTN["DEFAULT"],
    is_active: bool = False,
    hidden: bool = False,
    class_key: str = "DEFAULT"
) -> dbc.Button:
    """Create a button with consistent styling"""
    return dbc.Button(
        label,
        id=button_id,
        className=StyleConstants.BTN[
            f"{class_key}_ACTIVE" if is_active else class_key],
        style={'display': 'none'} if hidden else {}
    )


def format_button_id_value(value: Union[str, int]) -> str:
    """Format button value for ID generation, handling both str and numbers"""
    return str(value).replace('_', '-')


def _check_active_state(button: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Determine if a button should be active based on group's default state"""
    if config.get('multi_select'):
        default_state = config.get('default_state', {})
        return default_state.get(button['value'], []) == ['show']

    default_value = config.get('default')
    return str(button['value']) == str(default_value)


def create_button_group(group_id: str) -> html.Div:
    """Create a button group with uniform styling"""
    config = BUTTON_CONFIG[group_id]
    buttons = [
        create_button(
            label=btn['label'],
            button_id=f"btn-{group_id}-{format_button_id_value(btn['value'])}",
            is_active=_check_active_state(btn, config),
            hidden=btn.get('hidden', False),
            class_key=config['class_key']
        )
        for btn in config['buttons']
    ]
    return html.Div([
        dbc.Row([dbc.ButtonGroup(buttons)], 
                className=StyleConstants.BTN["BUTTON_GROUP_ROW"])
    ])