from dash import html
import dash_bootstrap_components as dbc
from application.style.style_constants import StyleConstants
from application.components.checklist import create_btype_checklist
from application.components.button import (
    create_reporting_form_buttons,
    create_top_insurers_buttons,
    create_period_type_buttons,
    create_periods_data_table_buttons,
    create_metric_toggles_buttons,
    create_table_split_buttons
)
from application.components.dropdown import (
    create_insurer_dropdown,
    create_metric_dropdown,
    create_end_quarter_dropdown
)
from application.components.lines_tree import create_dropdown_tree


def create_filter(label: str, label_width: int, component_func, component_className: str = None):
    """Create a filter row with a label and a component."""
    return dbc.Row([
        dbc.Col(
            html.Label(label, className=StyleConstants.FILTER["LABEL"]),
            xs=label_width,
            sm=label_width,
            md=label_width
        ),
        dbc.Col(
            component_func(),
            xs=12 - label_width,
            sm=12 - label_width,
            className=component_className or StyleConstants.FLEX["CENTER"]
        )
    ])


def get_col_style(cols_count: int) -> str:
    """
    Determine the appropriate column style based on the number of columns in the row.
    """
    if cols_count == 1:
        return StyleConstants.FILTER_PANEL["COL"]
    elif cols_count == 2:
        return StyleConstants.FILTER_PANEL["TWO_COL"]
    else:
        return StyleConstants.FILTER_PANEL["THIRD_COL"]


def create_row(columns, extra_classes=''):
    """
    Create a row with automatically determined column styles.

    Args:
        columns: List of tuples (content, width, extra_style, style)
        extra_classes: Additional classes to add to the row
    """
    cols_count = len(columns)
    col_style = get_col_style(cols_count)

    styled_columns = [
        dbc.Col(
            content,
            xs=width, sm=width, md=width, lg=width,
            className=f"{col_style} {extra_style}".strip(),
            style=style
        )
        for content, width, extra_style, style in columns
    ]

    row_className = f"{StyleConstants.FILTER_PANEL['ROW']} {extra_classes}".strip()
    return dbc.Row(styled_columns, className=row_className)


def create_filters() -> html.Div:
    """Create the complete filter interface with responsive rows."""
    # Create collapsed section
    collapsed_section = html.Div(
        create_row([
            (create_filter("Отчетный квартал:", 6, create_end_quarter_dropdown),
             6, "", None),
            (create_filter("Бизнес:", 3, create_btype_checklist, StyleConstants.FILTER["DROPDOWN"]),
             6, StyleConstants.SPACING["PS_3"], None)
        ]),
        id='sidebar-col',
        className=StyleConstants.SIDEBAR_COLLAPSED
    )

    # Create expanded section
    expanded_section = [
        # Period indicator
        html.Div(
            id="period-type-text",
            className=StyleConstants.UTILS["PERIOD_TYPE"],
            style={"display": "none"}
        ),
        # Row 2
        create_row([
            (create_filter("Вид данных:", 2, create_table_split_buttons, StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None)
        ], StyleConstants.SPACING["MT_3"]),
        create_row([
            (create_filter("Форма отчености:", 4, create_reporting_form_buttons),
             12, "", None),
        ]),
        # Row 3
        create_row([
            (create_filter("Период:", 1, create_period_type_buttons, StyleConstants.FILTER["BUTTONS_CENTER"]),
             7, "", None),
            (create_filter(" ", 0, create_periods_data_table_buttons, StyleConstants.FILTER["BUTTONS_CENTER"]),
             5, "", None)
        ]),

        # Row 4
        create_row([
            (create_filter("Вид страхования:", 3, create_dropdown_tree, "col-9"),
             12, "", None)
        ]),

        # Row 5
        create_row([
            (create_filter("Показатель:", 3, create_metric_dropdown),
             12, "", None),
            (create_filter(" ", 3, create_metric_toggles_buttons, StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None)
        ]),

        # Row 6
        create_row([
            (create_filter("Страховщик:", 3, create_top_insurers_buttons, StyleConstants.FILTER["BUTTONS_START"]),
             12, "", None),
            (create_filter(" ", 3, create_insurer_dropdown),
             12, "", None)
        ])


    ]

    return html.Div(dbc.CardBody([collapsed_section] + expanded_section))