from typing import Any, Dict, List, Tuple, Optional
import dash_bootstrap_components as dbc
from dash import html

from app.components.checklist import create_btype_checklist
from app.components.button import create_button_components, create_toggle_button
from app.components.dropdown import create_dropdown_components
from app.components.tree import create_tree_dropdown
from core.lines.tree import Tree


def create_filter_row(
    items: List[Tuple[str, Any, int, int, Optional[str]]],
    row_style: Optional[Dict[str, Any]] = None,
    default_class: str = "filter-row",
    extra_classes: str = '',
    label_class: str = "filter-label"
) -> html.Div:
    """
    Create a filter row with column width, label width control and component styling.

    Args:
        items: List of tuples, each containing:
            - label: str - Label text (empty string if no label needed)
            - component: Any - Component to be displayed
            - label_width: int - Width of the label portion
            - col_width: int - Width of the entire column in the grid
            - component_class: Optional[str] - Additional CSS classes for component
        extra_classes: str - Additional CSS classes for the row
        row_style: Optional[Dict[str, Any]] - Inline styles for the row
    """
    cols = []

    for label, component, label_width, col_width, component_class in items:

        content = dbc.Row([
            dbc.Col(
                html.Label(label, className=label_class),
                width=label_width if label else 0
            ),
            dbc.Col(
                html.Div(
                    component,
                    className=component_class
                ),
                width=12 - label_width if label else 12
            )
        ])

        cols.append(
            dbc.Col(
                content,
                width=col_width
            )
        )

    return dbc.Row(
        cols,
        className=f"{default_class} {extra_classes}".strip(),
        style=row_style
    )


def create_buttons_control_row() -> html.Div:
    """Create the period controls row with buttons."""
    buttons = create_button_components()
    return create_filter_row([
        ("", buttons['period_type'], 0, 4, "pe-2 me-2"),
        ("", buttons['periods_data_table'], 0, 3, "ps-2 pe-2"),
        ("", buttons['view_metrics'], 0, 5, "ps-2 ms-2 me-2 pe-2")
    ])


def create_table_pivot_view_buttons() -> html.Div:

    buttons = create_button_components()
    return create_filter_row([
       ("split:", buttons['table_split_mode'], 2, 6,
        "pe-2 me-2"),
       ("pivot:", buttons['pivot_column'], 2, 6,
        "ps-2 ms-2 me-2 pe-2"),
    ])


def create_filter_panel(lines_tree_158: Tree, lines_tree_162: Tree
                        ) -> html.Div:
    """Create the complete filter interface."""
    dropdowns = create_dropdown_components()
    buttons = create_button_components()
    tree_dropdown = create_tree_dropdown('line-tree', lines_tree_158,
                                         lines_tree_162)

    collapsed = html.Div([
        create_filter_row([("Отчетный квартал:", dropdowns['end_quarter'], 6, 5,
                            None),
                          ("Бизнес:", create_btype_checklist(), 3, 7, None)
                           ], row_style={"display": "none"}),

        create_filter_row([("Отчетность:", buttons['reporting_form'], 3, 5,
                            "px-3"),
                           ], extra_classes="px 0"),

        html.Div(style={"marginBottom": "0.5rem"}),

        create_filter_row([("Вид страхования:", tree_dropdown, 3, 12,
                            "pe-4")]),

        create_filter_row([("Показатель:", dropdowns['metric'], 3, 12,
                            "pe-4")]),

        create_filter_row([("Страховщик:", buttons['top_insurers'], 3, 12,
                            "pe-4")]),

        html.Div(style={"marginTop": "-0.5rem"}),

        create_filter_row([(" ", dropdowns['insurer'], 3, 12,
                            "pe-4")])


    ], id='sidebar', className="sidebar")

    button = create_filter_row([("", create_toggle_button(), 0, 12, None)])

    return html.Div(
        [collapsed, button],
        className="filter-panel"
    )