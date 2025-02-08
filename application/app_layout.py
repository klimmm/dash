import traceback
from typing import List

import dash_bootstrap_components as dbc
from dash import dcc, html

from application.style_constants import StyleConstants
from application.components.button import create_button
from application.components.lines_tree import create_lines_checklist_buttons
from application.filters_panel import create_filters
from config.default_values import DEFAULT_BUTTON_VALUES, DEFAULT_CHECKED_LINES
from config.logging_config import get_logger

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
        dcc.Store(id='filter-state-store'),
        dcc.Store(id='filtered-insurers-data-store'),
        dcc.Store(id='metrics-store'),
        dcc.Store(id='nodes-expansion-state',
                  data={'states': {}}),
        dcc.Store(id='periods-data-table-selected',
                  data=DEFAULT_BUTTON_VALUES['periods']),
        dcc.Store(id='period-type-selected',
                  data=DEFAULT_BUTTON_VALUES['period_type']),
        dcc.Store(id='processed-data-store'),
        dcc.Store(id='rankings-data-store'),
        dcc.Store(id='reporting-form-selected',
                  data=DEFAULT_BUTTON_VALUES['reporting_form']),
        dcc.Store(id='selected-insurers-store'),
        dcc.Store(id='selected-lines-store',
                  data=DEFAULT_CHECKED_LINES),
        dcc.Store(id='table-split-mode-selected',
                  data=DEFAULT_BUTTON_VALUES['split_mode']),
        dcc.Store(id='view-metrics-market-share',
                  data=DEFAULT_BUTTON_VALUES['market_share']),
        dcc.Store(id='view-metrics-qtoq',
                  data=DEFAULT_BUTTON_VALUES['qtoq']),
        dcc.Store(id='top-n-rows',
                  data=DEFAULT_BUTTON_VALUES['top_n'])
    ]


def _create_debug_footer() -> html.Div:
    """Create debug footer component."""
    return html.Div(
        id="debug-footer",
        className="debug-footer",
        children=[
            dbc.Button(
                "Toggle Debug Logs",
                id="debug-toggle",
                className=StyleConstants
                .BTN["DEBUG"]
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Debug Logs",
                                className=StyleConstants
                                .DEBUG["DEBUG_TITLE"]),
                        html.Pre(id="debug-output",
                                 className=StyleConstants
                                 .DEBUG["DEBUG_OUTPUT"])
                    ]),
                    className="debug-card"
                ),
                id="debug-collapse",
                is_open=False
            )
        ], style={"display": "none"},
    )


def create_app_layout():

    try:
        logger.warning("Starting to create app layout")

        return dbc.Container([
            *_create_stores(),
            _create_navbar(),

            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_button(
                            label="Show Additional Filters",
                            button_id='toggle-sidebar-button-sidebar',
                            className=StyleConstants
                            .BTN["SIDEBAR_SHOW"],
                            hidden=True
                        ),
                        create_lines_checklist_buttons(),
                        create_filters(),
                        html.Div([
                            dcc.Loading(
                                id="loading-data-tables",
                                type="default",
                                children=html.Div(
                                    id="tables-container",
                                    className=StyleConstants
                                    .CONTAINER["DATA_TABLE"]
                                )
                            )
                        ])
                    ], md=12),
                ])
            ], className=StyleConstants
                         .LAYOUT),
            _create_debug_footer()
        ], fluid=True)
    except Exception as e:
        logger.error(f"Error in create_app_layout: {str(e)}")
        traceback.print_exc()
        return html.Div("Error loading layout", style={'color': 'red'})