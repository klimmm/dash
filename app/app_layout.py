import traceback
from typing import Union

import dash_bootstrap_components as dbc  # type: ignore
from dash import dcc, html  # type: ignore

from app.style_constants import StyleConstants
from app.debug_panel import create_debug_panel
from app.filters import create_filter_panel, create_buttons_control_row, create_table_pivot_view_buttons
from app.navbar import create_navbar
from app.stores import create_stores
from config.logging import get_logger
from core.lines.tree import Tree

logger = get_logger(__name__)


def create_app_layout(lines_tree_158: Tree, lines_tree_162: Tree
                      ) -> Union[dbc.Container, html.Div]:
    try:
        logger.debug("Starting to create app layout")
        html.Div(id='main-content'),
        return dbc.Container([
            *create_stores(),
            create_navbar(),
            create_debug_panel(),

            dbc.CardBody([
                create_filter_panel(lines_tree_158, lines_tree_162),
                html.Div(style={"marginBottom": "-0.5rem"}),
                create_buttons_control_row(),
                html.Div(style={"marginBottom": "-0.5rem"}),
                create_table_pivot_view_buttons(),
                html.Div(style={"marginBottom": "2rem"}),
                html.Div(id='filters-summary'),
                html.Div(style={"marginBottom": "2rem"}),
                html.Div([
                    dcc.Loading(
                        id="loading-data-tables",
                        type="default",
                        children=html.Div(
                            id="tables-container",
                            className=StyleConstants.TABLES_CONTAINER
                        )
                    )
                ])
            ], className=StyleConstants
                         .LAYOUT),
            html.Div(style={"marginBottom": "1rem"}),

        ], fluid=True)
    except Exception as e:
        logger.error(f"Error in create_app_layout: {str(e)}")
        traceback.print_exc()
        return html.Div("Error loading layout", style={'color': 'red'})