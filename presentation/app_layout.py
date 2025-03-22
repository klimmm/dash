import traceback
from typing import Union

import dash_bootstrap_components as dbc
from dash import html

from presentation.style_constants import StyleConstants
from infrastructure.logger import logger


def create_navbar() -> dbc.Navbar:
    """Create navigation bar component."""
    return dbc.Navbar([
        dbc.Container(
            children=[
                dbc.Button(
                    "show logs",
                    id="debug-collapse-button",
                    className=StyleConstants.BTN["DEBUG"]
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                dbc.Button(
                    "Data Table",
                    id='data-table-tab',
                    className=StyleConstants.BTN["TABLE_TAB"],
                    style={'display': 'none'}
                )
            ]
        )
    ], color="dark", dark=True, className=StyleConstants.NAV)


def create_app_layout(components, stores) -> Union[dbc.Container, html.Div]:
    """
    Create app layout using organized components and stores dictionaries.

    Args:
        components: Dictionary containing UI components
        stores: Dictionary containing data stores

    Returns:
        The main application container
    """
    try:
        logger.debug("Starting to create app layout")

        return dbc.Container([
            *stores,
            create_navbar(),
            dbc.Row([
                dbc.Col([
                    components['debug_panel']
                ])
            ]),
            html.Div(id='_page-load', children="load",
                     style={'display': 'none'}),
            html.Div(id='_dummy-trigger', children="",
                     style={'display': 'none'}),
            html.Div(id='_hidden-div-for-clientside',
                     style={'display': 'none'}),
            # Keep dbc.Row but add the app-row class
            dbc.Row([
                components['sidebar'],

                # Main content column - with optimized CSS
                dbc.Col([
                    components['filters_summary'],
                    components['view-mode'],
                    html.Div(style={'margin': '10px 0'}),
                    components['vizual_container'],
                ], id='main-content',
                   className=StyleConstants.MAIN_CONTENT,
                   width=12),
            ], className=StyleConstants.APP_ROW),
        ], fluid=True)
    except Exception as e:
        logger.error(f"Error in create_app_layout: {str(e)}")
        traceback.print_exc()
        return html.Div("Error loading layout", style={'color': 'red'})