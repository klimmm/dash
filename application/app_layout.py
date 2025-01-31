import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import List

from application.filters_panel import create_filters
from application.components.lines_tree import create_lines_checklist_buttons, initial_state
from constants.style_constants import StyleConstants
from config.default_values import (
     DEFAULT_REPORTING_FORM,
     DEFAULT_NUMBER_OF_PERIODS,
     DEFAULT_NUMBER_OF_INSURERS,
     DEFAULT_PERIOD_TYPE, 
     DEFAULT_SHOW_MARKET_SHARE,
     DEFAULT_SHOW_CHANGES,
     DEFAULT_SPLIT_MODE
    )


def create_stores() -> List[html.Div]:
    """Create store components for app state management."""
    return [
        dcc.Store(id="show-data-table", data=True),
        dcc.Store(id="processed-data-store"),
        dcc.Store(id='intermediate-data-store', storage_type='memory'),
        dcc.Store(id='insurer-options-store', storage_type='memory'),
        dcc.Store(id="filter-state-store"),
        dcc.Store(id='insurance-lines-all-values', data=initial_state, storage_type='memory'),
        dcc.Store(id='expansion-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='period-type', data=DEFAULT_PERIOD_TYPE),
        dcc.Store(id='reporting-form', data=DEFAULT_REPORTING_FORM),
        dcc.Store(id='toggle-selected-market-share', data=DEFAULT_SHOW_MARKET_SHARE),
        dcc.Store(id='toggle-selected-qtoq', data=DEFAULT_SHOW_CHANGES),
        dcc.Store(id='top-n-rows', data=DEFAULT_NUMBER_OF_INSURERS),
        dcc.Store(id='number-of-periods-data-table', data=DEFAULT_NUMBER_OF_PERIODS),
        dcc.Store(id='table-split-mode', data=DEFAULT_SPLIT_MODE),
    ]

def create_navbar() -> dbc.Navbar:
    """Create navigation bar component."""
    return dbc.Navbar(
        [
            dbc.Container(
                # fluid=True,
                children=[
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Button(
                        "Data Table",
                        id="data-table-tab",
                        color="light",
                        className=StyleConstants.BTN["TABLE_TAB"]
                    )
                ]
            )
        ],
        color="dark",
        dark=True,
        className=StyleConstants.NAV
    )


def create_debug_footer() -> html.Div:
    """Create debug footer component."""
    return html.Div(
        id="debug-footer",
        className="debug-footer",
        children=[
            dbc.Button(
                "Toggle Debug Logs",
                id="debug-toggle",
                className=StyleConstants.BTN["DEBUG"]
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Debug Logs", className=StyleConstants.DEBUG["DEBUG_TITLE"]),
                        html.Pre(id="debug-output", className=StyleConstants.DEBUG["DEBUG_OUTPUT"])
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
        return dbc.Container([
            *create_stores(),
            create_navbar(),
            html.Div(id="dummy-output", style={"display": "none"}),
            html.Div(id="dummy-trigger", style={"display": "none"}),
            html.Div(id="tree-container", className=StyleConstants.CONTAINER["TREE"]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Show Additional Filters",
                            id="toggle-sidebar-button-sidebar",
                            className=StyleConstants.BTN["SIDEBAR_SHOW"],
                            style={"display": "none"}
                        ),
                        create_lines_checklist_buttons(),
                        create_filters(),
                        html.Div([
                            dcc.Loading(
                                id="loading-data-tables",
                                type="default",
                                children=html.Div(
                                    id="tables-container",
                                    className=StyleConstants.CONTAINER["DATA_TABLE"]
                                )
                            )
                        ])
                    ], md=12),
                ])
            ], className=StyleConstants.LAYOUT),
            html.Div([
                html.Div([
                    html.H4(id="table-title-chart", className=StyleConstants.TABLE["TITLE"], 
                           style={"display": "none"}),
                    html.H4(id="table-subtitle-chart", className=StyleConstants.TABLE["SUBTITLE"], 
                           style={"display": "none"})
                ], className=StyleConstants.CONTAINER["TITLES_CHART"], style={"display": "none"}),
                html.Div([
                    dcc.Graph(
                        id='graph',
                        style={'height': '100%', 'width': '100%'}
                    ),
                ], className=StyleConstants.CONTAINER["GRAPH"])
            ], id="chart-container", className=StyleConstants.CONTAINER["CHART"], style={"display": "none"}),
            create_debug_footer()
        ], fluid=True)
    except Exception as e:
        print(f"Error in create_app_layout: {str(e)}")
        raise