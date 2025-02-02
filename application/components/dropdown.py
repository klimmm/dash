from typing import Dict, List, Optional, Any

from dash import html, dcc

from constants.style_constants import StyleConstants


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
    return dcc.Dropdown(
        id=id,
        value=value,
        options=options,
        multi=multi,
        placeholder=placeholder,
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

    if is_detalize_button:
        buttons.append(
            html.Button(
                children=html.I(className=button_props['detalize']['icon_class']),
                id=button_props['detalize']['button_id'],
                className=button_props['detalize']['button_class'],
                n_clicks=0
            )
        )

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


def create_dd_container(
    dropdown_type: str,
    value: Optional[str] = None,
    options: Optional[List[Dict[str, str]]] = None,
    placeholder: str = "",
    show_detalize: bool = False
) -> html.Div:
    """Create a container for dynamic dropdowns with consistent layout"""

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

    return html.Div(
        className=StyleConstants.UTILS['W_100'],
        children=children
    )