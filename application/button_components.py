from dash import html
from typing import Dict, List, Optional, Union
import dash_bootstrap_components as dbc
from config.logging_config import get_logger
from constants.style_config import StyleConstants
logger = get_logger(__name__)


DEFAULT_BUTTON_CONFIGS = {
    'reporting-form': [
        {"label": "0420158", "value": "0420158"},
        {"label": "0420162", "value": "0420162"}
    ],
    'top-insurers': [
        {"label": "Total", "value": "top-999"},
        {"label": "Top5", "value": "top-5"},
        {"label": "Top10", "value": "top-10"},
        {"label": "Top20", "value": "top-20"}
    ],
    'period-type': [
        {"label": "YTD", "value": "ytd"},
        {"label": "YoY-Q", "value": "yoy-q"},
        {"label": "YoY-Y", "value": "yoy-y", "style": {"display": "none"}},
        {"label": "QoQ", "value": "qoq"},
        {"label": "MAT", "value": "mat", "style": {"display": "none"}}
    ],
    'periods-data-table': [
        {"label": str(i), "value": f"period-{i}"} 
        for i in range(1, 6)
    ],
    'metric-toggles': [
        {"label": "Доля рынка", "value": "market-share"},
        {"label": "Динамика", "value": "qtoq"}
    ]
}

def create_button(
    label: str,
    button_id: str,
    className: str = StyleConstants.BTN["GROUP_CONTROL"],
    style: Optional[Dict] = None
) -> dbc.Button:
    """Create a single button with consistent styling"""
    logger.debug(f"Creating button with id: {button_id}")
    return dbc.Button(
        label,
        id=button_id,
        className=className,
        style=style or {}
    )


def create_button_group(
    buttons: Union[List[Dict], Dict],
    className: Optional[str] = StyleConstants.BTN["PERIOD"],
    component_id: Optional[str] = None,
) -> Union[dbc.ButtonGroup, html.Div]:
    """
    Create a button group component with flexible configuration

    Args:
        buttons: List of button configs or dict with 'buttons' and 'className' keys
        className: Default className for the button group
        component_id: Optional component identifier for button IDs
    """
    logger.debug(f"Creating button group for component_id: {component_id}")

    # Handle both dictionary and list configurations
    if isinstance(buttons, dict):
        button_list = buttons.get('buttons', [])
        custom_className = buttons.get('className', className)
    else:
        button_list = buttons
        custom_className = className

    # Create button components
    button_components = []
    for btn in button_list:
        btn_id = (
            f"btn-{component_id}-{btn['value']}"
            if component_id
            else btn.get("id")
        )

        style = btn.get("style", {})

        button = create_button(
            label=btn["label"],
            button_id=btn_id,
            className=custom_className,
            style=style
        )
        button_components.append(button)

    button_group = dbc.ButtonGroup(button_components)

    # Return wrapped ButtonGroup for filter components
    return html.Div([
        dbc.Row([button_group], className=StyleConstants.UTILS["MB_0"])
    ])


def create_button_group_from_config(
    component_id: str,
    config_key: str = None
) -> Union[dbc.ButtonGroup, html.Div]:
    """Create a button group using default configurations"""
    logger.debug(f"Creating button group for {config_key or component_id}")

    buttons = DEFAULT_BUTTON_CONFIGS.get(config_key or component_id, [])

    # Use different classNames based on component type
    if component_id in ['top-insurers', 'periods-data-table', 'metric-toggles']:
        className = StyleConstants.BTN["PERIOD"]
    else:
        className = StyleConstants.BTN["GROUP_CONTROL"]

    return create_button_group(
        buttons=buttons,
        className=className,
        component_id=component_id
    )


# Specific button group creator functions
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
    """Create periods data table button group"""
    return create_button_group_from_config('periods-data-table')

def create_metric_toggles_buttons() -> Union[dbc.ButtonGroup, html.Div]:
    """Create metric toggles button group"""
    return create_button_group_from_config('metric-toggles')