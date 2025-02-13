from typing import cast, Any, Dict, List

import dash_bootstrap_components as dbc  # type: ignore
from dash import html  # type: ignore
from dash.development.base_component import Component  # type: ignore

from app.style_constants import StyleConstants
from config.components import BUTTON_GROUP_CONFIG
from config.logging import get_logger
from config.types import ButtonConfig, ButtonGroupConfig

logger = get_logger(__name__)


def create_button(
    label: str,
    button_id: str,
    className: str = StyleConstants.BTN["DEFAULT"],
    disabled: bool = False,
    is_active: bool = False,
    hidden: bool = False,
    title: str = "Description",
    class_key: str = "DEFAULT",
    draggable: str = ""
) -> "dbc.Button":  # Use string literal type for dbc.Button
    """Create a button with consistent styling"""
    return dbc.Button(
        label,
        id=button_id,
        className=StyleConstants.BTN[
            f"{class_key}_ACTIVE" if is_active else class_key],
        style={'display': 'none'} if hidden else {},
        title=title
    )


def _check_active_state(button: ButtonConfig, config: ButtonGroupConfig
                        ) -> bool:
    """Check if button should be in active state based on config."""
    default_val = config.get('default', [])
    # Convert to list if single value
    default_list = default_val if isinstance(
        default_val, list) else [default_val]
    # Convert all values to strings for comparison
    return str(button['value']) in [str(val) for val in default_list]


def create_button_group(
    buttons: List["dbc.Button"],
    className: str = StyleConstants.BTN["BUTTON_GROUP_ROW"]
) -> "Component":
    """Create a button group with uniform styling"""
    return html.Div([
        dbc.Row([dbc.ButtonGroup(buttons)], className=className)
    ])


def create_button_group_from_config(group_id: str) -> "Component":
    """Create a button group based on configuration"""
    config = cast(ButtonGroupConfig, BUTTON_GROUP_CONFIG[group_id])
    buttons = [
        create_button(
            label=btn['label'],
            button_id=f"btn-{group_id}-{btn['value']}",
            is_active=_check_active_state(btn, config),
            hidden=btn.get('hidden', False),
            class_key=config['class_key']
        )
        for btn in config['buttons']
    ]
    return create_button_group(buttons)


def create_button_components() -> Dict[str, Any]:
    """Create button group components for filter panel."""
    return {
        'period_type': create_button_group_from_config('period-type'),
        'reporting_form': create_button_group_from_config('reporting-form'),
        'table_split_mode': create_button_group_from_config('table-split-mode'),
        'top_insurers': create_button_group_from_config('top-insurers'),
        'periods_data_table': create_button_group_from_config('periods-data-table'),
        'view_metrics': create_button_group_from_config('view-metrics'),
        'pivot_column': create_button_group_from_config('pivot-column'),
    }


def create_toggle_button() -> html.Button:
    """Create the sidebar toggle button."""
    return create_button(
        label="Скрыть фильтры",
        button_id='sidebar-button',
        class_key="SIDEBAR_HIDE"
    )