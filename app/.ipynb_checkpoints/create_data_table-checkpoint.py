    # create_data_table.py

from typing import Callable, List, Dic
import dash_bootstrap_components as dbc
from dash import html, dcc
import logging
from .dropdown import create_dropdown_componen
from constants.translations import translate

from .font_styles import FILTER_LABEL_STYLE, OPTION_STYLE, TITLE_STYLE, SUBTITLE_STYLE
from constants.filter_options import MARKET_METRIC_DROPDOWN_OPTIONS, ALL_METRICS_OPTIONS

# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)

def create_data_table_tab() -> dbc.Tab:
    """Create the data table tab with optimized layout."""
    return dbc.Tab(
        label=translate("Data Table"),
        children=[
            dbc.Card(
                dbc.CardBody(
                    [
                        # Hidden Toggles for Additional Metrics Columns
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Checklist(
                                        options=[{"label": "", "value": "show"}],
                                        value=["show"],
                                        id="toggle-additional-market-share",
                                        switch=True,
                                        style={'display': 'none'}
                                    ),
                                    width=6
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        options=[{"label": "", "value": "show"}],
                                        value=["show"],
                                        id="toggle-additional-qtoq",
                                        switch=True,
                                        style={'display': 'none'}
                                    ),
                                    width=6
                                ),
                            ],
                            className="mb-3"
                        ),

                        # Title Container on White Background
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        style={
                                            'backgroundColor': '#ffffff',  # White background
                                            'padding': '15px',
                                            'borderRadius': '5px',
                                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                                        },
                                        children=[
                                            html.Div(
                                                [
                                                    html.H5(
                                                        id='table-title-row1',
                                                        style=TITLE_STYLE
                                                    ),
                                                    html.H5(
                                                        id='table-title-row2',
                                                        style=SUBTITLE_STYLE
                                                    ),
                                                ],
                                                id='table-title-container',
                                                className="mb-3"
                                            ),
                                        ]
                                    ),
                                    width=12
                                ),
                            ],
                            className="mb-4"
                        ),

                        # DataTable Container
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        id='data-table',  #
                                        style={'height': 'auto', 'overflow': 'auto'},
                                        children=[],
                                    ),
                                    width=12
                                ),
                            ],
                            className="mb-4"
                        ),

                        # Processing Error Display
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        id='processing-error',
                                        className="text-danger mt-3"
                                    ),
                                    width=12
                                ),
                            ]
                        ),
                    ],
                    style={
                        'backgroundColor': '#f8f9fa',  # Light grey for filter card
                        'padding': '20px'
                    }
                ),
                className="mb-1",
                style={
                    'backgroundColor': '#ffffff',
                    'border': '1px solid #dee2e6'
                }
            ),
        ]
    )
