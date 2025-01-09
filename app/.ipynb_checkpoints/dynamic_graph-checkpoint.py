from dash import dcc, Input, Output, State, ALL, MATCH, dash_table, html

import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import numpy as np
from .dropdown import create_dropdown_componen
from constants.filter_options import *
from default_values import *
from data_process.data_utils import default_insurer_options

DEFAULT_VALUE_METRICS = list(base_metrics)
DEFAULT_VALUE_INSURERS = ['1208', '1208', 'total', 'total']
from logging_config import get_logger
logger = get_logger(__name__)


opt = ['direct_premiums', 'direct_losses', 'ceded_premiums', 'ceded_losses']

from dash import dcc, html, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc

def create_chart_module(chart_id):
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            dcc.Dropdown(
                                id={'type': 'secondary-y-metrics', 'index': chart_id},
                                options=[opt for opt in opt],
                                value='direct_premiums',  # This will be controlled by the callback
                                multi=False,
                                placeholder=f"Select category for Chart {chart_id + 1}",
                                className="dropdown-hidden",
                                style={'width': '100%'}
                            ),
                        ], className="dropdown-container")
                    ], id={'type': 'secondary-y-metrics-col', 'index': chart_id}, className="col-hidden", width=12),

                    dbc.Col([
                        html.Div([
                            dcc.Dropdown(
                                id={'type': 'compare-insurers-chart', 'index': chart_id},
                                options=[],
                                value='1208',
                                multi=False,
                                placeholder=f"Select Insurer for Chart {chart_id + 1}",
                                className="dropdown-hidden",
                                style={'width': '100%'}
                            ),
                        ], className="dropdown-container")
                    ], id={'type': 'compare-insurers-col', 'index': chart_id}, className="col-hidden", width=12),

                ], className="mb-3"),
                dcc.Loading(
                    id={'type': 'loading', 'index': chart_id},
                    type="default",
                    children=html.Div(id={'type': 'chart', 'index': chart_id})
                )
            ])
        ])
    ],  width=12, md=12, lg=6)

def chart_callbacks(app):
    @app.callback(
        [Output({'type': 'compare-insurers-chart', 'index': MATCH}, 'disabled'),
         Output({'type': 'compare-insurers-chart', 'index': MATCH}, 'className'),
         Output({'type': 'compare-insurers-col', 'index': MATCH}, 'className'),
         Output({'type': 'compare-insurers-chart', 'index': MATCH}, 'value')],  # Reset value when disabled
        [Input('series-column', 'value')]
    )
    def update_compare_insurers_extended(series_column):
        should_display = series_column == 'insurer'

        dropdown_class = 'dropdown-visible' if should_display else 'dropdown-hidden'
        col_class = 'col-visible' if should_display else 'col-hidden'

        # Reset value to [] when disabled
        new_value = [] if not should_display else dash.no_update

        logger.info(f"Insurer dropdown: disabled={not should_display}, class={dropdown_class}, col_class={col_class}")

        return not should_display, dropdown_class, col_class, new_value

    @app.callback(
        [Output({'type': 'secondary-y-metrics', 'index': MATCH}, 'disabled'),
         Output({'type': 'secondary-y-metrics', 'index': MATCH}, 'className'),
         Output({'type': 'secondary-y-metrics-col', 'index': MATCH}, 'className'),
         Output({'type': 'secondary-y-metrics', 'index': MATCH}, 'value')],  # Reset value when disabled
        [Input('series-column', 'value')]
    )
    def update_secondary_y_metrics_extended(series_column):
        should_display = series_column == 'metric'

        dropdown_class = 'dropdown-visible' if should_display else 'dropdown-hidden'
        col_class = 'col-visible' if should_display else 'col-hidden'

        # Reset value to [] when disabled
        new_value = [] if not should_display else dash.no_update

        logger.info(f"Metrics dropdown: disabled={not should_display}, class={dropdown_class}, col_class={col_class}")

        return not should_display, dropdown_class, col_class, new_value
