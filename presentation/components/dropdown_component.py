# presentation/components/dropdown_component.py
from typing import Any, Dict, List, Optional, Union
from dash import dcc


class DropdownComponent:
    """Class for creating dropdown UI components."""

    @staticmethod
    def create_dropdown(
        id: str,
        className: str = 'dd-control',
        clearable: bool = False,
        disabled: bool = False,
        multi: bool = False,
        optionHeight: int = 18,
        options: List[Dict[str, Any]] = None,
        placeholder: Union[str, List[Any]] = "",
        searchable: bool = False,
        style: Optional[Dict[str, Any]] = None,
        value: Any = None
    ) -> dcc.Dropdown:
        """
        Create a dropdown component with specified properties.

        Args:
            id: Component identifier
            className: CSS class for the component
            clearable: Whether the value can be cleared
            disabled: Whether the component is disabled
            multi: Whether multiple selection is allowed
            optionHeight: Height of list items in pixels
            options: List of options to select from
            placeholder: Placeholder text
            searchable: Whether search is enabled
            style: Additional CSS styles
            value: Initial value

        Returns:
            Dash dropdown component
        """

        if options is None:
            options = []

        return dcc.Dropdown(
            id=id,
            className=className,
            clearable=clearable,
            disabled=disabled,
            multi=multi,
            optionHeight=optionHeight,
            options=options,
            placeholder=placeholder,
            searchable=searchable,
            style=style,
            value=value
        )