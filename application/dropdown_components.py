from dash import html, dcc
from typing import Dict, List, Optional, Union, Any

from constants.translations import translate
from constants.filter_options import VALUE_METRICS_OPTIONS
from config.default_values import (
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM,
    DEFAULT_INSURER
)
from data_process.data_utils import (
    category_structure_162,
    category_structure_158,
    get_categories_by_level
)
from application.button_components import ButtonStyleConstants


class StyleConstants:
    """CSS class names for dropdown components"""
    FORM = {
        "DD": "dd-control",
        "CHECKLIST": "checklist",
        "INPUT": "form-control input-short"
    }

def create_base_dropdown(
    id: str,
    options: List[Dict],
    value: Any = None,
    placeholder: str = "",
    clearable: bool = True,
    multi: bool = False
) -> dcc.Dropdown:
    """Create a base dropdown with consistent styling"""
    return dcc.Dropdown(
        id=id,
        options=options,
        value=value,
        multi=multi,
        placeholder=translate(placeholder),
        clearable=clearable,
        className=StyleConstants.FORM["DD"],
        optionHeight=18,
        style={"fontSize": "0.85rem"}
    )

def create_secondary_metric_dropdown() -> dcc.Dropdown:
    """Create secondary metric dropdown component"""
    return create_base_dropdown(
        id='secondary-y-metric',
        options=VALUE_METRICS_OPTIONS,
        value=DEFAULT_SECONDARY_METRICS,
        placeholder="Доп. показатель..."
    )

def create_end_quarter_dropdown() -> dcc.Dropdown:
    """Create end quarter selection dropdown component"""
    return create_base_dropdown(
        id='end-quarter',
        options=[{'label': '2024Q3', 'value': '2024Q3'}],
        value=DEFAULT_END_QUARTER,
        placeholder="Select quarter",
        clearable=False
    )

def create_dynamic_metric_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict] = None
) -> html.Div:
    """Create a dynamic metric dropdown with remove button"""
    if options is None:
        options = VALUE_METRICS_OPTIONS

    return html.Div(
        className="d-flex align-items-center w-100",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    create_base_dropdown(
                        id={'type': 'dynamic-primary-metric', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select primary metric"
                    )
                ]
            ),
            html.Button(
                "✕",
                id={'type': 'remove-primary-metric-btn', 'index': index},
                className=ButtonStyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )


def create_dynamic_metric_dropdown_container() -> html.Div:
    """Create a container specifically for dynamic metric dropdowns"""
    return html.Div([
        html.Div(
            className="d-flex align-items-center w-100",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='primary-metric',
                        options=VALUE_METRICS_OPTIONS,
                        value=DEFAULT_PRIMARY_METRICS,
                        multi=False,
                        placeholder=translate("Доп. показатель..."),
                        clearable=True,
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        style={"fontSize": "0.85rem"}
                    ),
                    className="dash-dropdown flex-grow-1"
                ),
                html.Button(
                    "+",
                    id="primary-metric-add-btn",
                    className=ButtonStyleConstants.BTN["ADD"]
                )
            ]
        ),
        html.Div(
            id="primary-metric-container",
            children=[],
            className="dynamic-dropdowns-container w-100 py-0 pr-1"
        ),
        dcc.Store(id="primary-metric-all-values", data=[])
    ], className="w-100")


def create_dynamic_insurance_line_dropdown_container() -> html.Div:
    """Create a container specifically for dynamic insurance line dropdowns"""
    # Determine the category structure based on reporting form
    category_structure = category_structure_162 if DEFAULT_REPORTING_FORM == '0420162' else category_structure_158

    return html.Div([
        html.Div(
            className="d-flex align-items-center w-100",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='insurance-line-dropdown',
                        options=get_categories_by_level(
                            category_structure,
                            level=2,
                            indent_char="--"
                        ),
                        value=DEFAULT_CHECKED_LINES,
                        multi=False,
                        placeholder=translate("Select insurance line"),
                        clearable=False,
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        style={"fontSize": "0.85rem"}
                    ),
                    className="dash-dropdown flex-grow-1"
                ),
                html.Button(
                    "+",
                    id="insurance-line-add-btn",
                    className=ButtonStyleConstants.BTN["ADD"]
                )
            ]
        ),
        html.Div(
            id="insurance-line-container",
            children=[],
            className="dynamic-dropdowns-container w-100 py-0 pr-1"
        ),
        dcc.Store(id="insurance-line-all-values", data=[])
    ], className="w-100")


def create_dynamic_insurer_dropdown_main(
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None  # More specific type hint
) -> html.Div:
    """Create a container specifically for dynamic insurer dropdowns
    
    Args:
        value: Initial selected value
        options: List of dropdown options with 'label' and 'value' keys
        
    Returns:
        html.Div containing the main dropdown and container for additional dropdowns
    """
    options = options or [{'label': 'Весь рынок', 'value': 'total'}]
    value = value or DEFAULT_INSURER
    return html.Div([
        html.Div(
            className="d-flex align-items-center w-100",
            children=[
                html.Div(
                    
                    dcc.Dropdown(
                        id='selected-insurers',
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select insurer",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        searchable=False
                    ), 
                    className="dash-dropdown flex-grow-1"
                ),
                html.Button(
                    children=html.I(className="fas fa-plus"),
                    # children=html.I(cclassName="fas fa-square-plus")
                    id="selected-insurers-add-btn",
                    className=ButtonStyleConstants.BTN["ADD"]
                )
            ]
        ),
        html.Div(
            id="selected-insurers-container",
            children=[],
            className="dynamic-dropdowns-container w-100 py-0 pr-1"
        ),
        dcc.Store(id="selected-insurers-all-values", data=[], storage_type='memory')
    ], className="w-100")


def create_dynamic_insurer_dropdown_additional(
    index: int,
    value: Optional[str] = None,
    options: List[Dict] = None
) -> html.Div:
    if options is None:
        options = [{'label': 'Весь рынок', 'value': 'total'}]

    return html.Div(
        className="d-flex align-items-center w-100",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    dcc.Dropdown(
                        id={'type': 'dynamic-selected-insurers', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select insurer",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        searchable=False
                    )
                ]
            ),
            html.Button(
                children=html.I(className="fas fa-xmark"), 
                # children=html.I(className="fas fa-circle-minus"), 
                # children=html.I(className="fas fa-trash"), 
                id={'type': 'remove-selected-insurers-btn', 'index': index},
                className=ButtonStyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )


def create_insurer_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False
) -> html.Div:
    """Create a unified insurer dropdown
    
    Args:
        index: Index for the dropdown (0 for first, incrementing for additional)
        value: Initial selected value
        options: List of dropdown options with 'label' and 'value' keys
        is_add_button: Whether this dropdown should have an add button (True for last dropdown)
        
    Returns:
        html.Div containing the dropdown and associated button
    """
    options = options or [{'label': 'Весь рынок', 'value': 'total'}]
    
    button_props = {
        'add': {
            'icon_class': "fas fa-plus",
            'button_id': "selected-insurers-add-btn",
            'button_class': ButtonStyleConstants.BTN["ADD"]
        },
        'remove': {
            'icon_class': "fas fa-xmark",
            'button_id': {'type': 'remove-selected-insurers-btn', 'index': index},
            'button_class': ButtonStyleConstants.BTN["REMOVE"]
        }
    }
    
    button_config = button_props['add'] if is_add_button else button_props['remove']
    
    return html.Div(
        className="d-flex align-items-center w-100",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    dcc.Dropdown(
                        id={'type': 'dynamic-selected-insurers', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select insurer",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        searchable=False
                    )
                ]
            ),
            html.Button(
                children=html.I(className=button_config['icon_class']),
                id=button_config['button_id'],
                className=button_config['button_class'],
                n_clicks=0
            )
        ]
    )

def create_dynamic_insurer_container_for_layout(
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None
) -> html.Div:

    if value is None:
        value = 'total'
    if options is None:
        options = options or [{'label': 'Весь рынок', 'value': 'total'}]
    """
    Create the insurer container for the layout system.

    This function serves as a unified implementation to create the insurer container,
    adapting our dropdown system to integrate seamlessly with the existing layout.

    Args:
        value: Initial selected value for the first dropdown.
        options: List of dropdown options, each as a dictionary with 'label' and 'value' keys.

    Returns:
        html.Div: A Div element containing the dropdown container and storage components.
    """
    return html.Div(
        className="w-100",
        children=[
            # Container for all dropdowns (including the first one)
            html.Div(
                id="selected-insurers-container",
                className="dynamic-dropdowns-container w-100 py-0 pr-1",
                children=[
                    create_insurer_dropdown(
                        index=0,
                        value=value,
                        options=options,
                        is_add_button=True
                    )
                ],
            ),
            # Store for all selected insurer values
            dcc.Store(
                id="selected-insurers-all-values",
                data=[],
                storage_type='memory'
            )
        ]
    )