from typing import Any, Dict, List, Optional

from dash import dcc  # type: ignore

from app.style_constants import StyleConstants


def create_dropdown(
    id: str,
    value: Any = None,
    options: List[Dict] = [],
    multi: bool = False,
    placeholder: str = "",
    clearable: bool = False,
    searchable: bool = False,
    className: str = StyleConstants.DROPDOWN,
    optionHeight: int = 18,
    style: Optional[Dict[str, Any]] = None,
    disabled: bool = False
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
        optionHeight=optionHeight,
        style=style,
        disabled=disabled
    )