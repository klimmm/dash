# app_layout.py
import dash

from dash import html

import pandas as pd
from dash import dcc, Input, Output, State, ALL, MATCH, dash_table, html
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme, Symbol
import dash_bootstrap_components as dbc
import logging
from typing import List, Dic
from functools import lru_cache
from flask_caching import Cache
from .create_data_table import create_data_table_tab
from .data_utils import default_insurer_options, category_structure
from charting.chart_filter_options import DEFAULT_CHART_TYPE, DEFAULT_SECONDARY_CHART_TYPE, DEFAULT_MARKET_CHART_TYPE, CHART_TYPE_DROPDOWN_OPTIONS, REINSURANCE_GRAPH_SWITCH_OPTIONS, REINSURANCE_FORM_DROPDOWN_OPTIONS, REINSURANCE_TYPE_DROPDOWN_OPTIONS, METRICS_FIG_TYPE_SWITCH

from .filter_options import LINEMAIN_OPTIONS, PREMIUM_LOSS_OPTIONS, MARKET_METRIC_DROPDOWN_OPTIONS, AGGREGATION_TYPES_OPTIONS, PRIMARY_METRICS_OPTIONS, SECONDARY_METRICS_OPTIONS, METRICS_OPTIONS, DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_AGGREGATION_TYPE, DEFAULT_INSURER, DEFAULT_PRIMARY_METRICS, DEFAULT_SECONDARY_METRICS, DEFAULT_MARKET_CHART_METRIC, DEFAULT_TABLE_METRIC, DEFAULT_CHECKED_CATEGORIES, DEFAULT_EXPANDED_CATEGORIES
from translations import translate
from .app_config import TITLE_STYLE, SUBTITLE_STYLE, COLOR_PALETTE_TABLE, FONT_STYLES, FILTER_LABEL_STYLE, OPTION_STYLE, SELECTED_CATEGORIES_HEADER_STYLE

from charting.chart_filter_options import DEFAULT_CHART_TYPE, DEFAULT_SECONDARY_CHART_TYPE, DEFAULT_MARKET_CHART_TYPE, CHART_TYPE_DROPDOWN_OPTIONS, REINSURANCE_GRAPH_SWITCH_OPTIONS, REINSURANCE_FORM_DROPDOWN_OPTIONS, REINSURANCE_TYPE_DROPDOWN_OPTIONS, METRICS_FIG_TYPE_SWITCH, METRICS_FIG_TYPE_SWITCH_CHECKLIST_OPTIONS, REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS

from .category_utils import CategoryChecklis

# Configure logger
from logging_config import get_logger
logger = get_logger(__name__)

def create_general_filters(
    df: pd.DataFrame,
    year_quarter_options: List[Dict[str, str]]
) -> dbc.Card:
    """Create the general filters section of the layout."""
    try:
        checklist = CategoryChecklist(category_structure, DEFAULT_CHECKED_CATEGORIES, DEFAULT_EXPANDED_CATEGORIES)

        return dbc.Card([
            dbc.CardBody([
                # Row 1: toggle-all-categories + selected-categories-header + category-collapse + premium-loss-checklis
                dbc.Row([
                    dbc.Col([
                        # Inline button and header
                        dbc.Row([
                            dbc.Button(
                                translate("Hide"),
                                id="toggle-all-categories",
                                className="me-2"  # Add margin end for spacing
                            ),
                            html.Div(
                                id="selected-categories-header",
                                className="d-inline"
                            ),
                        ], className="mb-2"),
                        dbc.Collapse(
                            checklist.create_checklist(),
                            id="category-collapse",
                            is_open=True
                        ),
                    ], width=6),

                    # Second Column: Contains three rows
                    dbc.Col([
                        # First Row: "Включая" Checklis
                        dbc.Row([
                            dbc.Col([
                                html.Label(
                                    translate("Включая"),
                                    className="filter-label"
                                ),
                                dbc.Checklist(
                                    id='premium-loss-checklist',
                                    options=PREMIUM_LOSS_OPTIONS,
                                    value=DEFAULT_PREMIUM_LOSS_TYPES,
                                    inline=True,
                                    switch=True,
                                    className="filter-option"
                                ),
                            ])
                        ], className="mb-2"),

                        # Second Row: "Период с:" Dropdown
                        dbc.Row([
                            dbc.Col([
                                html.Label(
                                    translate("Период с:"),
                                    className="filter-label"
                                ),
                                dcc.Dropdown(
                                    id='start-quarter-dropdown',
                                    options=year_quarter_options,
                                    value=year_quarter_options[0]['value'],
                                    clearable=False,
                                    className="filter-option"
                                ),
                            ], width=3),
                            dbc.Col([
                                html.Label(
                                    translate("по:"),
                                    className="filter-label"
                                ),
                                dcc.Dropdown(
                                    id='end-quarter-dropdown',
                                    options=year_quarter_options,
                                    value=year_quarter_options[-1]['value'],
                                    clearable=False,
                                    className="filter-option"
                                ),
                            ], width=3),
                            dbc.Col([
                                html.Label(
                                    translate("Вид данных:"),
                                    className="filter-label"
                                ),
                                dcc.Dropdown(
                                    id='aggregation-type-dropdown',
                                    options=AGGREGATION_TYPES_OPTIONS,
                                    value=DEFAULT_AGGREGATION_TYPE,
                                    clearable=False,
                                    className="filter-option"
                                ),
                            ], width=6),
                        ], className="mb-2"),
                    ], width=6),  # Adjust the width as needed to sum up to 12

                ], className="mb-2"),


                dbc.Row([
                    dbc.Col([
                        html.Label(translate("Select Primary Metrics:"), className="filter-label"),
                        dcc.Dropdown(
                            id='primary-metric-dropdown',
                            options=MARKET_METRIC_DROPDOWN_OPTIONS,
                            value=DEFAULT_PRIMARY_METRICS,
                            clearable=False,
                            className="filter-option"
                        ),
                    ], width=3),
                    dbc.Col([
                        html.Label(
                            translate("Select Secondary Metrics:"),
                            className="filter-label"
                        ),
                        dcc.Dropdown(
                            id='secondary-metric-dropdown',
                            options=MARKET_METRIC_DROPDOWN_OPTIONS,
                            value=DEFAULT_SECONDARY_METRICS,
                            multi=True,
                            className="filter-option"
                        ),
                    ], width=6),

                    # Select Secondary Chart Type
                    # (Add similar structure if needed)
                ], className="mb-2"),

            ], className="p-3")  # Padding for CardBody

        ], className="mb-3")  # Grey background for the card is set via CSS
    except Exception as e:
        logger.error(f"Error in create_general_filters: {str(e)}", exc_info=True)
        return dbc.Card(dbc.CardBody(html.P("Error loading general filters")))

def create_app_layout(
    df: pd.DataFrame,
    year_quarter_options: List[Dict[str, str]],
) -> html.Div:
    """Create the main application layout."""
    try:
        layout = dbc.Container([
            # Inject Custom CSS
            # Removed html.Style(get_custom_css())

            # Store components
            dcc.Store(id='category-expand-states', data={}),
            dcc.Store(id='all-expanded', data=False),
            dcc.Store(id='selected-linemain-store'),
            dcc.Store(id='selected-labels'),

            # Navbar
            dbc.NavbarSimple(
                brand=translate("Insurance Data Dashboard"),
                brand_href="#",
                color="primary",
                dark=True,
                className="mb-4"
            ),

            # General Filters
            create_general_filters(df, year_quarter_options),

            # Selected Categories Outpu
            html.Div(id="selected-categories-output", className="mb-3"),

            # Main Content Tabs
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        dbc.Tab([
                            #Insurance Card
                            dbc.Card([
                                dbc.CardBody([
                                    # Switch Controls (Checklist and Combined Metrics Options)
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Checklist(
                                                id='metrics-switch',
                                                options=METRICS_FIG_TYPE_SWITCH_CHECKLIST_OPTIONS,
                                                value=["combined"],  # default selected
                                                inline=True,
                                                className="filter-option"
                                            )
                                        ], width=2),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                id='insurer-radio',
                                                options=default_insurer_options,
                                                value=DEFAULT_INSURER,
                                                clearable=False,
                                                className="filter-option"
                                            ),
                                        ], width=2),
                                        dbc.Col([
                                            html.Div([
                                                dbc.Row([
                                                    dbc.Col([
                                                        dcc.Dropdown(
                                                            id='compare-to-dropdown',
                                                            options=MARKET_METRIC_DROPDOWN_OPTIONS,
                                                            value=None,
                                                            multi=True,
                                                            placeholder=translate("Select to Compare"),
                                                            className="filter-option"
                                                        ),
                                                    ], width=6),
                                                    dbc.Col([
                                                        dcc.Dropdown(
                                                            id='compare-to-benchmark',
                                                            options=MARKET_METRIC_DROPDOWN_OPTIONS,
                                                            value=None,
                                                            multi=True,
                                                            placeholder=translate("Select Benchmark"),
                                                            className="filter-option"
                                                        ),
                                                    ], width=6),
                                                ], className="g-0"),
                                            ], id='combined-metrics-options', style={'display': 'none'}),
                                        ], width=8),
                                    ], className="g-0 mb-3"),

                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Row([
                                                dbc.Col(html.Label(translate("Y:"), className="filter-label"), width="auto"),
                                                dbc.Col(dcc.Dropdown(
                                                    id='primary-chart-type',
                                                    options=CHART_TYPE_DROPDOWN_OPTIONS,
                                                    value=DEFAULT_CHART_TYPE,
                                                    clearable=False,
                                                    className="filter-option"
                                                ), width=6)
                                            ], align="center", className="g-0"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Row([
                                                dbc.Col(html.Label(translate("Y2:"), className="filter-label"), width="auto"),
                                                dbc.Col(dcc.Dropdown(
                                                    id='secondary-chart-type',
                                                    options=CHART_TYPE_DROPDOWN_OPTIONS,
                                                    value=DEFAULT_SECONDARY_CHART_TYPE,
                                                    clearable=False,
                                                    className="filter-option"
                                                ), width=6)
                                            ], align="center", className="g-0"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='stacking-metrics-toggle',
                                                label=translate("Stack metrics"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='stacking-entities-toggle',
                                                label=translate("Stack entity"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='show-percentage-toggle',
                                                label=translate("Show percent"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='show-100-percent-toggle',
                                                label=translate("Show 100% bars"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                            )
                                        ], width=2, className="d-flex align-items-center")
                                    ], className="mb-3"),

                                    # Container for Dynamic Graphs
                                    html.Div(id='dynamic-graphs', children=[], style={'height': 'auto'})

                                ], className="card-body")
                            ], className="mb-2"),

                            # Reinsurance Graphs Card
                            dbc.Card([
                                dbc.CardBody([
                                    # Graph Switch
                                    dbc.Row([

                                        dbc.Col([
                                            html.Label(translate("Select Graph Type"), className="filter-label"),
                                            dbc.Checklist(
                                                id='reinsurance-graph-switch',
                                                options=REINSURANCE_GRAPH_SWITCH_OPTIONS,
                                                value=[],  # Empty list means no option is selected by defaul
                                                inline=True,
                                                className="filter-option"
                                            ),
                                        ], width=6),

                                        dbc.Col([
                                            dcc.Dropdown(
                                                id='reinsurance-metric-dropdown',
                                                options=MARKET_METRIC_DROPDOWN_OPTIONS,
                                                value=['ceded_premiums'],
                                                multi=True,
                                                placeholder=translate("Показатель"),
                                            ),
                                        ], width=6),
                                    ], className="mb-3"),

                                    # Reinsurance Dropdowns
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Dropdown(
                                                id='reinsurance-form-dropdown',
                                                options=REINSURANCE_FORM_DROPDOWN_OPTIONS,
                                                className="filter-option",
                                                value=None,
                                                multi=True,
                                                placeholder=translate("Reinsurance Form"),
                                            ),
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                id='reinsurance-type-dropdown',
                                                options=REINSURANCE_TYPE_DROPDOWN_OPTIONS,
                                                className="filter-option",
                                                value=None,
                                                multi=True,
                                                placeholder=translate("Reinsurance Type"),
                                            ),
                                        ], width=4),
                                        dbc.Col([
                                            dcc.Dropdown(
                                                id='reinsurance-geography-dropdown',
                                                options=REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS,
                                                className="filter-option",
                                                value=None,
                                                multi=True,
                                                placeholder=translate("Reinsurance Geography"),
                                            ),
                                        ], width=4),
                                    ], className="mb-3"),

                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Row([
                                                dbc.Col(html.Label(translate("Y:"), className="filter-label"), width="auto"),
                                                dbc.Col(dcc.Dropdown(
                                                    id='primary-chart-type-reinsurance',
                                                    options=CHART_TYPE_DROPDOWN_OPTIONS,
                                                    value=DEFAULT_CHART_TYPE,
                                                    clearable=False,
                                                    className="filter-option"
                                                ), width=6)
                                            ], align="center", className="g-0"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Row([
                                                dbc.Col(html.Label(translate("Y2:"), className="filter-label"), width="auto"),
                                                dbc.Col(dcc.Dropdown(
                                                    id='secondary-chart-type-reinsurance',
                                                    options=CHART_TYPE_DROPDOWN_OPTIONS,
                                                    value=DEFAULT_SECONDARY_CHART_TYPE,
                                                    clearable=False,
                                                    className="filter-option"
                                                ), width=6)
                                            ], align="center", className="g-0"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='stacking-metrics-toggle-reinsurance',
                                                label=translate("Stack metrics"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                                # Removed inline styles for font size
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='stacking-entities-toggle-reinsurance',
                                                label=translate("Stack entity"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                                # Removed inline styles for font size
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='show-percentage-toggle-reinsurance',
                                                label=translate("Show percent"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                                # Removed inline styles for font size
                                            )
                                        ], width=2, className="d-flex align-items-center"),
                                        dbc.Col([
                                            dbc.Switch(
                                                id='show-100-percent-toggle-reinsurance',
                                                label=translate("Show 100% bars"),
                                                value=False,  # Default to stacked
                                                className="ms-2",
                                                # Removed inline styles for font size
                                            )
                                        ], width=2, className="d-flex align-items-center")
                                    ], className="mb-3"),
                                    # Container for Reinsurance Graphs
                                    html.Div(id='reinsurance-graphs', children=[], style={'height': 'auto'})

                                ], className="card-body")
                            ])
                        ], label=translate("Reinsurance")),

                        # Data Table Tab
                        dbc.Tab(
                            create_data_table_tab(
                                translate,
                                MARKET_METRIC_DROPDOWN_OPTIONS,
                                DEFAULT_TABLE_METRIC
                            ),
                            label=translate("Data Table")
                        ),
                    ], className="custom-tabs")
                ], width=12)
            ]),

            # Debug Logs Section
            dbc.Row([
                dbc.Col([
                    dbc.Collapse(
                        dbc.Card(
                            dbc.CardBody([
                                html.H4(translate("Debug Logs"), className="card-title"),
                                html.Pre(
                                    id='debug-output',
                                    style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-all'}
                                )
                            ])
                        ),
                        id="debug-collapse",
                        is_open=False,
                    ),
                    dbc.Button(
                        translate("Toggle Debug Logs"),
                        id="debug-toggle",
                        className="mt-3",
                        color="secondary",
                        # Removed inline styles for font size
                    )
                ], width=12)
            ], className="mt-4")
        ], fluid=True)  # Background and font are set via CSS

        return layou
    except Exception as e:
        logging.error(f"Error in create_app_layout: {str(e)}", exc_info=True)
        return html.Div([
            html.H1("Error"),
            html.P(f"An error occurred while creating the layout: {str(e)}")
        ])

__all__ = ['create_app_layout', 'get_custom_css']
