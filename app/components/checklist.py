from typing import Dict, List, Optional

import dash_bootstrap_components as dbc  # type: ignore
from dash import html  # type: ignore

from app.style_constants import StyleConstants
from config.default_values import DEFAULT_BUSINESS_TYPE
from core.metrics.checklist_config import BUSINESS_TYPE_OPTIONS


def create_checklist(
    id: str,
    options: List[Dict[str, str]],
    value: Optional[List[str]] = None,
    switch: bool = False,
    inline: bool = False,
    readonly: bool = False
) -> dbc.Checklist:
    """Create a checklist component with configurable options

    Args:
        id: Unique identifier for the checklist
        options: List of option dictionaries
        value: Optional list of selected values
        switch: Whether to use switch style
        inline: Whether to display inline
        readonly: Whether the checklist is readonly

    Returns:
        A dbc.Checklist component
    """
    style = {}
    if readonly:
        style.update({'pointerEvents': 'none', 'opacity': 0.5})

    return dbc.Checklist(
        id=id,
        options=options,
        value=value or [],
        switch=switch,
        inline=inline,
        style=style,
        className=StyleConstants.CHECKLIST
    )


def create_btype_checklist(
    readonly: bool = False,
    values: Optional[List[str]] = None
) -> html.Div:
    """Create a business type checklist component

    Args:
        readonly: Whether the checklist is readonly
        values: Optional list of selected business types

    Returns:
        A div containing the business type checklist
    """
    checklist = create_checklist(
        id='business-type-checklist',
        options=BUSINESS_TYPE_OPTIONS,
        value=values or DEFAULT_BUSINESS_TYPE,
        switch=True,
        inline=True,
        readonly=readonly
    )

    return html.Div(
        id='business-type-checklist-container',
        children=[checklist]
    )