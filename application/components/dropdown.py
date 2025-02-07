from typing import Dict, List, Any

from dash import dcc

from application.style.style_constants import StyleConstants
from config.default_values import DEFAULT_METRICS, DEFAULT_END_QUARTER, DEFAULT_INSURER
from constants.translations import translate


def create_base_dropdown(
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


def create_insurer_dropdown():
    return create_base_dropdown(
        id='selected-insurers',
        multi=True,
        value=DEFAULT_INSURER,
        searchable=False,
        options=[],
        placeholder="Выберите страховщика"
    )


def create_metric_dropdown():
    return create_base_dropdown(
        id='metrics',
        multi=True,
        value=DEFAULT_METRICS,
        options=[],
        placeholder="Выберите показатель"
    )


def create_end_quarter_dropdown():
    return create_base_dropdown(
        id='end-quarter',
        value=DEFAULT_END_QUARTER,
        options=[
            {'label': translate(DEFAULT_END_QUARTER),
             'value': DEFAULT_END_QUARTER}
        ],
        placeholder="Select quarter"
    )