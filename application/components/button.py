from typing import Dict, List, Optional, Union

import dash_bootstrap_components as dbc
from dash import html

from application.style.style_constants import StyleConstants
from application.config.components_config import BUTTON_CONFIG
from config.logging_config import get_logger


logger = get_logger(__name__)


def create_button(
    label: str,
    button_id: str,
    style: Optional[Dict] = None,
    is_active: bool = False,
    class_key: str = "DEFAULT"
) -> dbc.Button:
    """Create a single button with consistent styling"""
    logger.debug(f"Creating button with id: {button_id}, active: {is_active}")

    button_class = (
        StyleConstants.BTN[f"{class_key}_ACTIVE"] if is_active
        else StyleConstants.BTN[class_key]
    )

    return dbc.Button(
        label,
        id=button_id,
        className=button_class,
        style=style or {}
    )


def create_button_group(
    buttons: Union[List[Dict], Dict],
    component_id: Optional[str] = None,
    default_state: Optional[Union[str, Dict, int]] = None,
    class_key: str = "PERIOD"
) -> Union[dbc.ButtonGroup, html.Div]:
    """
    """
    logger.debug(f"Creating button group for component_id: {component_id}")

    # Handle both dictionary and list configurations
    if isinstance(buttons, dict):
        button_list = buttons.get('buttons', [])
    else:
        button_list = buttons

    # Create button components
    button_components = []
    for btn in button_list:
        btn_id = (
            f"btn-{component_id}-{btn['value']}"
            if component_id
            else btn.get("id")
        )

        style = btn.get("style", {})

        # Determine if button should be active
        is_active = False
        if default_state is not None:
            if isinstance(default_state, dict):
                # For multi-choice buttons (like metric-toggles)
                is_active = default_state.get(btn['value'], False)
            else:
                # For single-choice buttons
                is_active = str(default_state) == str(btn['value'])

        button = create_button(
            label=btn["label"],
            button_id=btn_id,
            style=style,
            is_active=is_active,
            class_key=class_key
        )
        button_components.append(button)

    button_group = dbc.ButtonGroup(button_components)

    return html.Div([
        dbc.Row([button_group], className=StyleConstants.BTN["BUTTON_GROUP_ROW"])
    ])


def create_button_group_from_config(
    component_id: str,
    config_key: str = None
) -> Union[dbc.ButtonGroup, html.Div]:
    """Create a button group using default configurations"""

    config = BUTTON_CONFIG.get(config_key or component_id, {})
    buttons = config.get('buttons', [])
    default_state = config.get('default_state')
    class_key = config.get('class_key', 'GROUP_CONTROL')

    return create_button_group(
        buttons=buttons,
        component_id=component_id,
        default_state=default_state,
        class_key=class_key
    )


def create_table_split_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create reporting form button group"""
    return create_button_group_from_config('table-split-mode')


def create_reporting_form_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create reporting form button group"""
    return create_button_group_from_config('reporting-form')


def create_top_insurers_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create top insurers button group"""
    return create_button_group_from_config('top-insurers')


def create_period_type_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create period type button group"""
    return create_button_group_from_config('period-type')


def create_periods_data_table_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    return create_button_group_from_config('periods-data-table')


def create_metric_toggles_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create metric toggles button group"""
    return create_button_group_from_config('metric-toggles')