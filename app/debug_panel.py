import dash_bootstrap_components as dbc  # type: ignore
from dash import dcc, html  # type: ignore

from app.components.dropdown import create_dropdown


def create_debug_panel():
    """Create a collapsible debug panel layout with improved organization."""
    return dbc.Card([

        dbc.Collapse(
            dbc.CardBody([
                dbc.Row([
                    # Log level filter
                    dbc.Col([
                        html.Div("Log Level:", className="filter-label",
                                 style={'fontSize': '0.7rem'}),
                        html.Div(
                            create_dropdown(
                                id='log-level-filter',
                                options=[
                                    {'label': level, 'value': level}
                                    for level in ['DEBUG', 'INFO',
                                                  'WARNING', 'ERROR',
                                                  'CRITICAL']
                                ],
                                value=['DEBUG'],
                                multi=True,
                            ),
                        )
                    ], width=6),

                    # Module filter
                    dbc.Col([
                        html.Div("Module:", className="filter-label",
                                 style={'fontSize': '0.7rem'}),
                        html.Div(
                            create_dropdown(
                                id='module-filter',
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="All modules",
                                clearable=False,
                                searchable=False,
                            ),
                        )
                    ], width=6)
                ], className="mb-3 g-0"),

                html.Div(
                    html.Pre(
                        id='debug-logs',
                        style={
                            'margin': '0',
                            'whiteSpace': 'pre-wrap',
                            'fontSize': '0.7rem'
                        }
                    ),
                    id='debug-logs-container',
                    style={
                        'maxHeight': '400px',
                        'overflowY': 'auto',
                        'backgroundColor': '#f8f9fa',
                        'padding': '5px',
                        'border': '1px solid #dee2e6',
                        'borderRadius': '4px',
                    }
                ),

                # Just the interval for refresh
                dcc.Interval(
                    id='refresh-interval',
                    interval=1000,
                    n_intervals=0
                ),
            ], className="px-0 pt-0"),
            id="debug-collapse",
            is_open=False
        )
    ], className="debug-panel")