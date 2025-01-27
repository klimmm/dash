from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import List
from application.insurance_lines_tree import initial_state
from application.style_config import StyleConstants
from config.default_values import DEFAULT_REPORTING_FORM, DEFAULT_NUMBER_OF_PERIODS, DEFAULT_NUMBER_OF_INSURERS, DEFAULT_PERIOD_TYPE, DEFAULT_SHOW_MARKET_SHARE, DEFAULT_SHOW_CHANGES


def create_stores() -> List[html.Div]:
    """Create store components for app state management."""
    return [
        html.Div(id="_hidden-init-trigger", style={"display": "none"}),
        dcc.Store(id='grouped-df-store', storage_type='memory'),
        dcc.Store(id="show-data-table", data=True),
        dcc.Store(id="processed-data-store"),
        dcc.Store(id='intermediate-data-store', storage_type='memory'),
        dcc.Store(id='reporting-form-inter', storage_type='memory'),
        dcc.Store(id='insurance-lines-inter', storage_type='memory'),
        dcc.Store(id='insurer-options-store', storage_type='memory'),
        dcc.Store(id="filter-state-store"),
        dcc.Store(id="top-insurers-store"),

        dcc.Store(id='insurance-lines-state', data=initial_state),
        dcc.Store(id='expansion-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='tree-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='period-type', data=DEFAULT_PERIOD_TYPE),
        dcc.Store(id='reporting-form', data=DEFAULT_REPORTING_FORM),
        dcc.Store(id='toggle-selected-market-share', data=DEFAULT_SHOW_MARKET_SHARE),
        dcc.Store(id='toggle-selected-qtoq', data=DEFAULT_SHOW_CHANGES),
        dcc.Store(id='number-of-insurers', data=DEFAULT_NUMBER_OF_INSURERS),
        dcc.Store(id='number-of-periods-data-table', data=DEFAULT_NUMBER_OF_PERIODS)

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