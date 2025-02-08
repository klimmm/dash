from typing import Dict, List, Any

from dash import dcc

from application.style_constants import StyleConstants


def create_dropdown(
    id: str,
    value: Any = None,
    options: List[Dict] = [],
    multi: bool = False,
    placeholder: str = "",
    clearable: bool = False,
    searchable: bool = False,
    className: str = StyleConstants.DROPDOWN,
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