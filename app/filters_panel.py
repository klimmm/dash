from typing import Any, Dict, List, Optional, Tuple, Union

import dash_bootstrap_components as dbc  # type: ignore
from dash import html  # type: ignore

from app.style_constants import StyleConstants
from app.components.checklist import create_btype_checklist
from app.components.button import create_button_group, create_button
from app.components.dropdown import create_dropdown
from app.components.lines_tree import DropdownTree
from config.default_values import (
     DEFAULT_CHECKED_LINES,
     DEFAULT_END_QUARTER, DEFAULT_INSURER,
     DEFAULT_METRICS, DEFAULT_REPORTING_FORM
)
from config.logging_config import get_logger
from constants.translations import translate
from core.lines.tree import Tree
from core.metrics.options import get_metric_options

logger = get_logger(__name__)

ButtonComponents = Dict[str, Any]
DropdownComponents = Dict[str, Union[DropdownTree, Any]]


def _create_button_components() -> ButtonComponents:
    """Create all button group components."""
    return {
        'period_type': create_button_group('period-type'),
        'reporting_form': create_button_group('reporting-form'),
        'table_split_mode': create_button_group('table-split-mode'),
        'top_insurers': create_button_group('top-insurers'),
        'periods_data_table': create_button_group('periods-data-table'),
        'view_metrics': create_button_group('view-metrics')
    }


def _create_dropdown_components(lines_tree_158: Tree, lines_tree_162: Tree
                                ) -> DropdownComponents:
    """Create all dropdown components."""
    tree = (lines_tree_162 if DEFAULT_REPORTING_FORM == '0420162' else
            lines_tree_158)
    # logger.warning(f"DEFAULT_METRICS {DEFAULT_METRICS}")
    metrics_options, metric_value = get_metric_options(
        DEFAULT_REPORTING_FORM, DEFAULT_METRICS)
    logger.debug(f"metrics_options {metrics_options}")
    logger.debug(f"metric_value {metric_value}")
    return {
        'line_tree': DropdownTree(
            tree=tree,
            expansion_state={'states': {}},
            selected=DEFAULT_CHECKED_LINES,
            placeholder="Выберите вид страхования",
            is_open=False
        ),
        'insurer': create_dropdown(
            id='selected-insurers',
            multi=True,
            value=DEFAULT_INSURER,
            searchable=False,
            options=[],
            placeholder="Выберите страховщика",
            disabled=True
        ),
        'metric': create_dropdown(
            id='metrics',
            multi=True,
            value=metric_value,
            options=metrics_options,
            placeholder="Выберите показатель"
        ),
        'end_quarter': create_dropdown(
            id='end-quarter',
            value=DEFAULT_END_QUARTER,
            options=[{'label': translate(DEFAULT_END_QUARTER),
                     'value': DEFAULT_END_QUARTER}],
            placeholder="Select quarter"
        )
    }


def _create_filter_row(label: str, label_width: int,
                       component: Optional[Any] = None,
                       component_className: Optional[str] = None
                       ) -> html.Div:
    """Create a filter row with label and component."""
    return dbc.Row([
        dbc.Col(
            html.Label(label, className=StyleConstants.FILTER["LABEL"]),
            xs=label_width, sm=label_width, md=label_width
        ),
        dbc.Col(
            component,
            xs=12 - label_width, sm=12 - label_width,
            className=component_className or StyleConstants.FLEX["CENTER"]
        )
    ])


def create_row(columns: List[Tuple[Any, int, str, Any]],
               extra_classes: str = '',
               style: Optional[Dict[str, Any]] = None) -> html.Div:
    """Create a row with auto-determined column styles."""
    col_style = {
        1: StyleConstants.FILTER_PANEL["COL"],
        2: StyleConstants.FILTER_PANEL["TWO_COL"]
    }.get(len(columns), StyleConstants.FILTER_PANEL["THIRD_COL"])

    styled_columns = [
        dbc.Col(
            content, xs=width, sm=width, md=width, lg=width,
            className=f"{col_style} {extra_style}".strip(),
            style=style
        )
        for content, width, extra_style, style in columns
    ]

    return dbc.Row(
        styled_columns,
        className=f"{StyleConstants.FILTER_PANEL['ROW']} {extra_classes}"
        .strip(),
        style=style if style else None
    )


def create_period_controls_row() -> html.Div:
    buttons = {
        'period_type': create_button_group('period-type'),
        'periods_data_table': create_button_group('periods-data-table'),
        'view_metrics': create_button_group('view-metrics')
    }

    return create_row([
        (_create_filter_row("", 0, 
                            buttons['period_type'],
                            StyleConstants.FILTER["BUTTONS_START"]),
         4, "", None),
        (_create_filter_row(" ", 0,
                            buttons['periods_data_table'],
                            StyleConstants.FILTER["BUTTONS_CENTER"]),
         4, "", None),
        (_create_filter_row(" ", 0,
                            buttons['view_metrics'],
                            StyleConstants.FILTER["BUTTONS_END"]),
         4, "", None)
    ], StyleConstants.SPACING["MB_5"])


# Create collapsed section
def create_filters(lines_tree_158: Tree, lines_tree_162: Tree) -> html.Div:
    """Create the complete filter interface."""
    buttons = _create_button_components()
    dropdowns = _create_dropdown_components(lines_tree_158, lines_tree_162)

    # Create the collapsed section separately
    collapsed = html.Div([
        create_row([
            (_create_filter_row("Отчетный квартал:", 6,
                                dropdowns['end_quarter']),
             6, "", None),
            (_create_filter_row("Бизнес:", 3,
                                create_btype_checklist(),
                                StyleConstants.FILTER["DROPDOWN"]),
             6, StyleConstants.SPACING["PS_3"], None)
        ], style={"display": "none"}),
        html.Div(
            id="period-type-text",
            className=StyleConstants.UTILS["PERIOD_TYPE"],
            style={"display": "none"}
        ),
        create_row([
            (_create_filter_row("Отчетность:", 3,
                                buttons['reporting_form'],
                                StyleConstants.FILTER["BUTTONS_CENTER"]),
             5, "", None),
            (_create_filter_row("В разрезе:", 3,
                                buttons['table_split_mode'],
                                StyleConstants.FILTER["BUTTONS_START"]),
             7, "", None),
        ], StyleConstants.SPACING["MT_3"]),
        html.Div(style={"margin-bottom": "0.5rem"}),

        create_row([
            (_create_filter_row("Вид страхования:", 3,
                                dropdowns['line_tree'],
                                "col-9"),
             12, "", None),
            (_create_filter_row(" ", 3),
             0, "", None)
        ]),
        create_row([
            (_create_filter_row("Показатель:", 3,
                                dropdowns['metric']),
             12, "", None),
            (_create_filter_row(" ", 3),
             0, "", None)
        ]),
        create_row([
            (_create_filter_row("Страховщик:", 3,
                                buttons['top_insurers'],
                                StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None),
            (_create_filter_row(" ", 3),
             0, "", None)
        ]),
        html.Div(style={"margin-top": "-0.5rem"}),
        create_row([
            (_create_filter_row(" ", 3,
                                dropdowns['insurer']),
             12, "", None),
            (_create_filter_row(" ", 3),
             0, "", None)
        ])
    ],
     id='sidebar-col',
     className=StyleConstants.SIDEBAR_COLLAPSED)

    # Create the expanded section separately
    expanded = html.Div([
        create_button(
            label="Скрыть фильтры",
            button_id='toggle-sidebar-button-sidebar',
            className=StyleConstants.BTN["SIDEBAR_HIDE"],
            hidden=False
        )
    ])

    # Return both sections wrapped in a CardBody
    return html.Div(
        dbc.CardBody([
            collapsed,
            expanded  # Now expanded is a sibling to collapsed, not a child
        ]),
        className="filter-panel"
    )