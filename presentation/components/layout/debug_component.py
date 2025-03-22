
from typing import Dict, Any, Tuple, List, Optional
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc


class DebugComponent:
    """Manages the debug panel with log display and filtering."""

    def __init__(self, config):
        """Initialize the debug callback registrator with required services."""
        self.memory_handler = config.debug_handler
        self.logger = config.logger
        self.dash_callback = config.dash_callback

    def create_debug_panel(self, dropdowns) -> Any:
        """Create debug panel with log level and module dropdowns."""
        return dbc.Card([
            dbc.Collapse(
                dbc.CardBody([
                    dbc.Row([
                        # Log level filter
                        dbc.Col(html.Div([
                            html.Div("Log Level:", className="filter-label", style={'fontSize': '0.7rem'}),
                            dropdowns[0]
                        ]), width=6),
                        # Module filter
                        dbc.Col(html.Div([
                            html.Div("Module:", className="filter-label", style={'fontSize': '0.7rem'}),
                            dropdowns[1]
                        ]), width=6)
                    ], className="mb-3 g-0"),
                    html.Div(
                        html.Pre(
                            id='debug-logs',
                            style={'margin': '0', 'whiteSpace': 'pre-wrap', 'fontSize': '0.7rem'}
                        ),
                        id='debug-logs-container',
                        style={
                            'maxHeight': '400px', 'overflowY': 'auto', 'backgroundColor': '#f8f9fa',
                            'padding': '5px', 'border': '1px solid #dee2e6', 'borderRadius': '4px',
                        }
                    ),
                    dcc.Interval(id='refresh-interval', interval=1000, n_intervals=0),
                ], className="px-0 pt-0"),
                id="debug-collapse",
                is_open=False
            )
        ], className="debug-panel")

    def create_components(self, components, storage_type: str = None
                          ) -> Tuple[Dict[str, Any], List[dcc.Store]]:
        """Create debug panel components without registering callbacks."""
        self.logger.debug("Creating debug panel components")
        debug_panel = self.create_debug_panel([components['log_level'], components['module']])

        # Return the components with their final keys directly
        debug_components = {
            'debug_panel': debug_panel,
            'debug_collapse_button': html.Button(
                "Show Logs",
                id="debug-collapse-button",
                className="btn btn-secondary mb-0",
            )
        }

        return debug_components