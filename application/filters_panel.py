import dash_bootstrap_components as dbc
from dash import html

from application.style_constants import StyleConstants
from application.components.checklist import create_btype_checklist
from application.components.button import create_button_group
from application.components.dropdown import create_dropdown
from application.components.lines_tree import DropdownTree
from config.default_values import (
    DEFAULT_CHECKED_LINES, DEFAULT_END_QUARTER, DEFAULT_INSURER,
    DEFAULT_METRICS, DEFAULT_REPORTING_FORM
)
from constants.translations import translate
from domain.lines.tree import lines_tree_158, lines_tree_162


def _create_button_components():
    """Create all button group components."""
    return {
        'period_type': create_button_group('period-type'),
        'reporting_form': create_button_group('reporting-form'),
        'table_split_mode': create_button_group('table-split-mode'),
        'top_insurers': create_button_group('top-insurers'),
        'periods_data_table': create_button_group('periods-data-table'),
        'view_metrics': create_button_group('view-metrics')
    }


def _create_dropdown_components():
    """Create all dropdown components."""
    tree = (lines_tree_162 if DEFAULT_REPORTING_FORM == '0420162' else
            lines_tree_158)

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
            placeholder="Выберите страховщика"
        ),
        'metric': create_dropdown(
            id='metrics',
            multi=True,
            value=DEFAULT_METRICS,
            options=[],
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


def _create_filter_row(label, label_width,
                       component, component_className=None):
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


def create_row(columns, extra_classes=''):
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
        .strip()
    )


def create_filters():
    """Create the complete filter interface."""
    buttons = _create_button_components()
    dropdowns = _create_dropdown_components()

    # Create collapsed section
    collapsed = html.Div(
        create_row([
            (_create_filter_row("Отчетный квартал:", 6,
                                dropdowns['end_quarter']),
             6, "", None),
            (_create_filter_row("Бизнес:", 3,
                                create_btype_checklist(),
                                StyleConstants.FILTER["DROPDOWN"]),
             6, StyleConstants.SPACING["PS_3"], None)
        ]),
        id='sidebar-col',
        className=StyleConstants.SIDEBAR_COLLAPSED
    )

    # Create expanded section
    expanded = [
        html.Div(
            id="period-type-text",
            className=StyleConstants.UTILS["PERIOD_TYPE"],
            style={"display": "none"}
        ),
        create_row([
            (_create_filter_row("Вид данных:", 2,
                                buttons['table_split_mode'],
                                StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None)
        ], StyleConstants.SPACING["MT_3"]),
        create_row([
            (_create_filter_row("Форма отчености:", 4,
                                buttons['reporting_form']),
             12, "", None)
        ]),
        create_row([
            (_create_filter_row("Период:", 1, 
                                buttons['period_type'],
                                StyleConstants.FILTER["BUTTONS_CENTER"]),
             7, "", None),
            (_create_filter_row(" ", 0,
                                buttons['periods_data_table'],
                                StyleConstants.FILTER["BUTTONS_CENTER"]),
             5, "", None)
        ]),
        create_row([
            (_create_filter_row("Вид страхования:", 3,
                                dropdowns['line_tree'],
                                "col-9"),
             12, "", None)
        ]),
        create_row([
            (_create_filter_row("Показатель:", 3,
                                dropdowns['metric']),
             12, "", None),
            (_create_filter_row(" ", 3,
                                buttons['view_metrics'],
                                StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None)
        ]),
        create_row([
            (_create_filter_row("Страховщик:", 3,
                                buttons['top_insurers'],
                                StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None),
            (_create_filter_row(" ", 3,
                                dropdowns['insurer']),
             12, "", None)
        ])
    ]

    return html.Div(dbc.CardBody([collapsed] + expanded))