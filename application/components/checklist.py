from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import html

from application.style.style_constants import StyleConstants
from domain.metrics.checklist_config import BUSINESS_TYPE_OPTIONS
from config.default_values import DEFAULT_BUSINESS_TYPE



def create_checklist(
    id: str,
    options: List[Dict],
    value: List = None,
    switch: bool = False,
    inline: bool = False,
    readonly: bool = False
) -> dbc.Checklist:
    """
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
    values: List[str] = None
) -> html.Div:
    """Create a business type checklist component
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