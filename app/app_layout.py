import traceback
from typing import List, Union

import dash_bootstrap_components as dbc  # type: ignore
from dash import dcc, html  # type: ignore

from app.style_constants import StyleConstants
from app.components.button import create_button
from app.filters import create_filter_panel, create_buttons_control_row
from config.default_values import DEFAULT_BUTTON_VALUES, DEFAULT_CHECKED_LINES
from config.logging import get_logger
from core.lines.tree import Tree


logger = get_logger(__name__)


def _create_navbar() -> dbc.Navbar:
    """Create navigation bar component."""
    return dbc.Navbar(
        [
            dbc.Container(
                children=[
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    create_button(
                        label="Data Table",
                        button_id='data-table-tab',
                        className=StyleConstants
                        .BTN["TABLE_TAB"],
                        hidden=True
                    )
                ]
            )
        ],
        color="dark",
        dark=True,
        className=StyleConstants
        .NAV
    )


def _create_stores() -> List[html.Div]:
    """Create store components for app state management."""
    return [
        dcc.Store(id='filter-state-store', storage_type='memory'),
        dcc.Store(id='filtered-insurers-data-store', storage_type='memory'),
        dcc.Store(id='metrics-store', data=[], storage_type='memory'),
        dcc.Store(id='nodes-expansion-state',
                  data={'states': {}}, storage_type='memory'),
        dcc.Store(id='periods-data-table-selected',
                  data=DEFAULT_BUTTON_VALUES['periods'],
                  storage_type='memory'),
        dcc.Store(id='period-type-selected',
                  data=DEFAULT_BUTTON_VALUES['period_type'],
                  storage_type='memory'),
        dcc.Store(id='processed-data-store', storage_type='memory'),
        dcc.Store(id='rankings-data-store', storage_type='memory'),
        dcc.Store(id='reporting-form-selected',
                  data=DEFAULT_BUTTON_VALUES['reporting_form'],
                  storage_type='memory'),
        dcc.Store(id='selected-insurers-store', storage_type='memory'),
        dcc.Store(id='selected-lines-store',
                  data=DEFAULT_CHECKED_LINES, storage_type='memory'),
        dcc.Store(id='table-split-mode-selected',
                  data=DEFAULT_BUTTON_VALUES['split_mode'],
                  storage_type='memory'),
        dcc.Store(id='view-metrics',
                  data=DEFAULT_BUTTON_VALUES['view_metrics'],
                  storage_type='memory'),
        dcc.Store(id='top-n-rows',
                  data=DEFAULT_BUTTON_VALUES['top_n'],
                  storage_type='memory')
    ]


def create_debug_panel():
    """Create a simple debug panel layout."""
    return html.Div([
        dbc.Button(
            "Show Logs",
            id="debug-toggle",
            className=StyleConstants.BTN["DEFAULT"],
        ),
        dbc.Collapse(
            dbc.Card([
                dbc.Button(
                    "Clear",
                    id="clear-logs-button",
                    className=StyleConstants.BTN["DEFAULT"],
                ),
                dbc.CardBody([
                    html.Pre(
                        id="debug-logs",
                        style={
                            "height": "200px",
                            "overflow-y": "scroll",
                            "white-space": "pre-wrap",
                            "font-family": "monospace",
                            "background-color": "#f8f9fa",
                            "padding": "10px",
                            "border-radius": "4px"
                        }
                    )
                ])
            ]),
            id="debug-collapse",
            is_open=False,
        ),
        dcc.Interval(
            id='log-update-interval',
            interval=1000,  # Update every second
            n_intervals=0
        )
    ])


def create_lines_checklist_buttons() -> dbc.Row:
    """Create hierarchy control buttons."""
    return create_button(label="Показать все", button_id="expand-all-button", className="btn-custom btn-period", hidden=True)


def create_app_layout(lines_tree_158: Tree, lines_tree_162: Tree
                      ) -> Union[dbc.Container, html.Div]:

    try:
        logger.debug("Starting to create app layout")

        return dbc.Container([
            *_create_stores(),
            _create_navbar(),
            create_debug_panel(),

            dbc.CardBody([
                create_lines_checklist_buttons(),
                create_filter_panel(lines_tree_158, lines_tree_162),
                create_buttons_control_row(),
                html.Div(style={"marginBottom": "0.5rem"}),
                html.Div(id='filters-summary'),
                html.Div(style={"marginBottom": "1rem"}),
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