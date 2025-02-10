from typing import cast, Dict, List, NotRequired, TypedDict, Union

import dash_bootstrap_components as dbc  # type: ignore
from dash import html  # type: ignore
from dash.development.base_component import Component  # type: ignore

from app.style_constants import StyleConstants
from app.ui_configs.button_config import BUTTON_CONFIG
from config.logging_config import get_logger

logger = get_logger(__name__)


class ButtonConfig(TypedDict):
    label: str
    value: Union[str, int]
    hidden: NotRequired[bool]


class ButtonGroupConfig(TypedDict):
    buttons: List[ButtonConfig]
    multi_select: NotRequired[bool]
    default_state: NotRequired[Dict[str, List[str]]]
    default: NotRequired[Union[str, int]]
    class_key: str


def create_button(
    label: str,
    button_id: str,
    className: str = StyleConstants.BTN["DEFAULT"],
    is_active: bool = False,
    hidden: bool = False,
    class_key: str = "DEFAULT"
) -> "dbc.Button":  # Use string literal type for dbc.Button
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


def _check_active_state(button: ButtonConfig, config: ButtonGroupConfig
                        ) -> bool:
    """Determine if a button should be active based on group's default state"""
    if config.get('multi_select', False):
        default_state = config.get('default_state', {})
        return default_state.get(str(button['value']), []) == ['show']

    default_value = config.get('default')
    return default_value is not None and str(
        button['value']) == str(default_value)


def create_button_group(group_id: str) -> "Component":
    """Create a button group with uniform styling"""
    # Cast the config to ButtonGroupConfig to ensure type safety
    config = cast(ButtonGroupConfig, BUTTON_CONFIG[group_id])
    buttons: List["dbc.Button"] = [
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