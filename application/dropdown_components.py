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
from data_process.insurance_line_options import get_insurance_line_options
from application.button_components import ButtonStyleConstants
from data_process.data_utils import map_insurer
from callbacks.update_metric_callbacks import create_primary_metric_dropdown
from constants.translations import translate



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









def create_dynamic_primary_metric_container_for_layout(
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None
) -> html.Div:

    if value is None:
        value = DEFAULT_PRIMARY_METRICS

    if options is None:
        options = [
            {'label': translate(DEFAULT_PRIMARY_METRICS), 'value': DEFAULT_PRIMARY_METRICS} 
        ]

    return html.Div(
        className="w-100",
        children=[
            # Container for all dropdowns (including the first one)
            html.Div(
                id="primary-metric-container",
                className="dynamic-dropdowns-container w-100 py-0 pr-1",
                children=[
                    create_primary_metric_dropdown(
                        index=0,
                        value=value,
                        options=options,
                        is_add_button=True
                    )
                ],
            ),
            # Store for all selected insurer values
            dcc.Store(
                id="primary-metric-all-values",
                data=[],
                storage_type='memory'
            )
        ]
    )








def create_dynamic_insurance_line_dropdown_container() -> html.Div:
    """Create a container specifically for dynamic insurance line dropdowns"""
    # Determine the category structure based on reporting form

    return html.Div([
        html.Div(
            className="d-flex align-items-center w-100",
            children=[
                html.Div(
                    dcc.Dropdown(
                        id='insurance-line-dropdown',
                        options=get_insurance_line_options(
                            DEFAULT_REPORTING_FORM,
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
                    " ",
                    id="insurance-line-add-btn",
                    className=ButtonStyleConstants.BTN["ADD"]
                ),
                html.Button(
                    " ",
                    id="insurance-line-remove-btn",
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


def create_insurer_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = True
) -> html.Div:

    button_props = {
        'add': {
            'icon_class': "fas fa-plus",
            'button_id': "selected-insurers-add-btn",
            'button_class': ButtonStyleConstants.BTN["ADD"]
        },
        'remove': {
            'icon_class': "fas fa-xmark",
            'button_id': {'type': 'remove-selected-insurers-btn', 'index': str(index)},
            'button_class': ButtonStyleConstants.BTN["REMOVE"]
        }
    }

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
                children=html.I(className=button_props['remove']['icon_class']), 
                id=button_props['remove']['button_id'],
                className=button_props['remove']['button_class'],
                n_clicks=0
            ) if is_remove_button else html.Div(
                className=button_props['remove']['button_class'],
                style={'visibility': 'hidden'}
            ),
            html.Button(
                children=html.I(className=button_props['add']['icon_class']),
                id=button_props['add']['button_id'],
                className=button_props['add']['button_class'],
                n_clicks=0
            ) if is_add_button else html.Div(
                className=button_props['add']['button_class'],
                style={'visibility': 'hidden'}
            ),
        ]
    )


def create_dynamic_insurer_container_for_layout(
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None
) -> html.Div:

    if value is None:
        value = DEFAULT_INSURER

    if options is None:
        options = [
            {'label': map_insurer(DEFAULT_INSURER), 'value': DEFAULT_INSURER} 
        ]

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