# app/components/dropdown.py
from typing import Any, cast, Dict, List, Optional, Union

from dash import dcc

from app.style_constants import StyleConstants
from config.components import DROPDOWN_CONFIG
from config.types import DropdownConfig


def create_dropdown(
    id: str,
    className: str = StyleConstants.DROPDOWN,
    clearable: bool = False,
    disabled: bool = False,
    multi: bool = False,
    optionHeight: int = 18,
    options: List[Dict[str, Any]] = [],
    placeholder: Union[str, List[Any]] = "",
    searchable: bool = False,
    style: Optional[Dict[str, Any]] = None,
    value: Any = None
) -> dcc.Dropdown:
    return dcc.Dropdown(
        id=id,
        className=className,
        clearable=clearable,
        disabled=disabled,
        multi=multi,
        optionHeight=optionHeight,
        options=options,
        placeholder=placeholder,  # dcc.Dropdown accepts both str and List
        searchable=searchable,
        style=style,
        value=value
    )


def create_dropdown_from_config(
    key: str
) -> dcc.Dropdown:
    """Create a single dropdown component using configuration."""
    # Cast the configuration dictionaries to our TypedDict
    defaults = cast(DropdownConfig, DROPDOWN_CONFIG['defaults'])
    component_config = cast(DropdownConfig, DROPDOWN_CONFIG['components'][key])

    # Merge configurations with proper typing
    dropdown_config: DropdownConfig = {
        'id': str(component_config.get('id', '')),
        'className': str(component_config.get('className', defaults['className'])),
        'clearable': bool(component_config.get('clearable', defaults['clearable'])),
        'disabled': bool(component_config.get('disabled', defaults['disabled'])),
        'multi': bool(component_config.get('multi', defaults['multi'])),
        'optionHeight': int(component_config.get('optionHeight', defaults['optionHeight'])),
        'options': list(component_config.get('options', defaults['options'])),
        'placeholder': component_config.get('placeholder', defaults['placeholder']),
        'searchable': bool(component_config.get('searchable', defaults['searchable'])),
        'style': component_config.get('style', defaults['style']),
        'value': component_config.get('value', defaults['value'])
    }

    return create_dropdown(**dropdown_config)


def create_dropdown_components() -> Dict[str, dcc.Dropdown]:
    """Create all dropdown components."""
    return {
        'metric': create_dropdown_from_config('metric'),
        'insurer': create_dropdown_from_config('insurer'),
        'end_quarter': create_dropdown_from_config('end_quarter')
    }