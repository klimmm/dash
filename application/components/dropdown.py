from typing import Dict, List, Optional, Any

from dash import html, dcc

from constants.metrics import VALUE_METRICS_OPTIONS, METRICS_OPTIONS
from constants.translations import translate
from config.default_values import (
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM,
    DEFAULT_INSURER
    )
from constants.style_constants import StyleConstants
from data_process.mappings import map_insurer
from data_process.options import get_insurance_line_options


def create_secondary_metric_dropdown() -> dcc.Dropdown:
    """Create secondary metric dropdown component"""
    return create_base_dropdown(
        id='secondary-y-metric',
        value=DEFAULT_SECONDARY_METRICS,
        options=VALUE_METRICS_OPTIONS,
        placeholder="Доп. показатель..."
    )


def create_end_quarter_dropdown() -> dcc.Dropdown:
    """Create end quarter selection dropdown component"""
    return create_base_dropdown(
        id='end-quarter',
        value=DEFAULT_END_QUARTER,
        options=[{'label': translate(DEFAULT_END_QUARTER), 'value': DEFAULT_END_QUARTER}],
        placeholder="Select quarter"
    )


def create_base_dropdown(
    id: str,
    value: Any = None,
    options: List[Dict] = [],
    multi: bool = False,
    placeholder: str = "",
    clearable: bool = False,
    searchable: bool = False,
    className: str = StyleConstants.FORM["DD"],
    optionHeight: int = 18
) -> dcc.Dropdown:
    """Create a base dropdown with consistent styling"""
    return dcc.Dropdown(
        id=id,
        value=value,
        options=options,
        multi=multi,
        placeholder=translate(placeholder),
        clearable=clearable,
        searchable=searchable,
        className=className,
        optionHeight=optionHeight
    )


def create_dynamic_dropdown(
    dropdown_type: str,
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = False,
    is_detalize_button: bool = False,
    placeholder: str = ""
) -> html.Div:
    """
    Create a dynamic dropdown with optional buttons
    """
    button_props = {
        'add': {
            'icon_class': "fas fa-plus",
            'button_id': f"{dropdown_type}-add-btn",
            'button_class': StyleConstants.BTN["ADD"]
        },
        'remove': {
            'icon_class': "fas fa-xmark",
            'button_id': {'type': f'remove-{dropdown_type}-btn', 'index': str(index)},
            'button_class': StyleConstants.BTN["REMOVE"]
        },
        'detalize': {
            'icon_class': "fas fa-list",
            'button_id': {'type': f'dropdown-detalize-btn', 'index': index},
            'button_class': StyleConstants.BTN["SECONDARY"]
        }
    }

    buttons = []

    # Add detalize button if enabled
    if is_detalize_button:
        buttons.append(
            html.Button(
                children=html.I(className=button_props['detalize']['icon_class']),
                id=button_props['detalize']['button_id'],
                className=button_props['detalize']['button_class'],
                n_clicks=0
            )
        )

    # Add remove button or placeholder
    if is_remove_button:
        buttons.append(
            html.Button(
                children=html.I(className=button_props['remove']['icon_class']),
                id=button_props['remove']['button_id'],
                className=button_props['remove']['button_class'],
                n_clicks=0
            )
        )
    else:
        buttons.append(
            html.Div(
                className=button_props['remove']['button_class'],
                style={'visibility': 'hidden'}
            )
        )

    # Add add button or placeholder
    if is_add_button:
        buttons.append(
            html.Button(
                children=html.I(className=button_props['add']['icon_class']),
                id=button_props['add']['button_id'],
                className=button_props['add']['button_class'],
                n_clicks=0
            )
        )
    else:
        buttons.append(
            html.Div(
                className=button_props['add']['button_class'],
                style={'visibility': 'hidden'}
            )
        )

    return html.Div(
        className=f"{StyleConstants.FLEX['CENTER']} {StyleConstants.UTILS['W_100']}",
        children=[
            html.Div(
                className=f"{StyleConstants.DROPDOWN['CONTAINER']} {StyleConstants.UTILS['FLEX_GROW_1']}",
                children=[
                    create_base_dropdown(
                        id={'type': f'dynamic-{dropdown_type}', 'index': index},
                        value=value,
                        options=options,
                        placeholder=placeholder
                    )
                ]
            ),
            *buttons
        ]
    )


def create_dynamic_container_for_layout(
    dropdown_type: str,
    default_value: Any,
    default_options: Optional[List[Dict[str, str]]] = None,
    value: Optional[Any] = None,
    options: Optional[List[Dict[str, str]]] = None,
    placeholder: str = "",
    show_detalize: bool = False
) -> html.Div:
    """Create a container for dynamic dropdowns with consistent layout"""
    if value is None:
        value = default_value

    if options is None:
        if default_options is None:
            label = (
                translate(default_value) 
                if dropdown_type == 'primary-metric' 
                else map_insurer(default_value)
            )
            options = [{'label': label, 'value': default_value}]
        else:
            options = default_options

    # Create container children
    children = [
        html.Div(
            id=f"{dropdown_type}-container",
            className=f"{StyleConstants.DROPDOWN['DYNAMIC_CONTAINER']} {StyleConstants.UTILS['W_100']} {StyleConstants.UTILS['PY_0']} {StyleConstants.UTILS['PR_1']}",
            children=[
                create_dynamic_dropdown(
                    dropdown_type=dropdown_type,
                    index=0,
                    value=value,
                    options=options,
                    is_add_button=True,
                    is_detalize_button=show_detalize,
                    placeholder=placeholder
                )
            ]
        )
    ]

    # Add stores
    stores = []

    # Add main store with standard ID format
    stores.append(
        dcc.Store(
            id=f"{dropdown_type}-all-values",
            data=[value] if value is not None else [],
            storage_type='memory'
        )
    )

    children.extend(stores)

    return html.Div(
        className=StyleConstants.UTILS['W_100'],
        children=children
    )


def create_insurance_line_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = True,
    show_detalize: bool = True
) -> html.Div:
    """Create a single insurance line dropdown with optional buttons"""
    if options is None:
        options = get_insurance_line_options(
            DEFAULT_REPORTING_FORM,
            level=2
        )

    return create_dynamic_dropdown(
        dropdown_type='insurance-line',
        index=index,
        value=value,
        options=options,
        is_add_button=is_add_button,
        is_remove_button=is_remove_button,
        is_detalize_button=show_detalize,
        placeholder="Select insurance line"
    )


def create_primary_metric_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = False
) -> html.Div:
    """Create a primary metric dropdown"""
    return create_dynamic_dropdown(
        dropdown_type='primary-metric',
        index=index,
        value=value,
        options=options,
        is_add_button=is_add_button,
        is_remove_button=is_remove_button,
        placeholder="Select primary metric"
    )


def create_insurer_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = True
) -> html.Div:
    """Create an insurer dropdown"""
    return create_dynamic_dropdown(
        dropdown_type='selected-insurers',
        index=index,
        value=value,
        options=options,
        is_add_button=is_add_button,
        is_remove_button=is_remove_button,
        placeholder="Select insurer"
    )


def create_dynamic_insurance_line_container_for_layout(
    value: Optional[str] = None,
    options: Optional[List[Dict[str, str]]] = None,
) -> html.Div:
    """Create a container specifically for dynamic insurance line dropdowns"""
    if options is None:
        options = get_insurance_line_options(
            DEFAULT_REPORTING_FORM,
            level=2
        )
    return create_dynamic_container_for_layout(
        dropdown_type='insurance-line',
        default_value=DEFAULT_CHECKED_LINES[0] if isinstance(DEFAULT_CHECKED_LINES, list) else DEFAULT_CHECKED_LINES,
        value=value,
        options=options,
        placeholder="Select insurance line",
        show_detalize=True
    )


def create_dynamic_primary_metric_container_for_layout(
    value: Optional[str] = None,
    options: Optional[List[Dict[str, str]]] = None,
) -> html.Div:
    """Create a container specifically for primary metric dropdowns"""

    # Create with both standard and specific store IDs
    return create_dynamic_container_for_layout(
        dropdown_type='primary-metric',
        default_value=DEFAULT_PRIMARY_METRICS,
        value=value,
        options=METRICS_OPTIONS,
        placeholder="Select primary metric",
    )


def create_dynamic_insurer_container_for_layout(
    value: Optional[str] = None,
    options: Optional[List[Dict[str, str]]] = None
) -> html.Div:
    """Create a container specifically for insurer dropdowns"""
    if options is None:
        options = [{'label': map_insurer(DEFAULT_INSURER), 'value': DEFAULT_INSURER}]    

    return create_dynamic_container_for_layout(
        dropdown_type='selected-insurers',
        default_value=DEFAULT_INSURER,
        value=value,
        options=options,
        placeholder="Select insurer"
    )