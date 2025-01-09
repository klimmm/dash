# app_layout_callbacks.py

import dash
from dash import Input, Output, State
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


def setup_tab_state_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for tab state and visibility."""

    @app.callback(
        [
            Output("data-table-content", "style"),
            Output("show-data-table", "data"),
            Output("data-table-tab", "className"),
        ],
        [Input("data-table-tab", "n_clicks")],
        prevent_initial_call=True
    )
    def toggle_visibility(data_table_clicks):
        """Toggle visibility of table content."""
        ctx = dash.callback_context
        start_time = track_callback('app.tab_state_callbacks', 'toggle_visibility', ctx)

        try:
            # Initial load - show table by default
            if not data_table_clicks:
                result = (
                    {"display": "block"},
                    True,
                    "tab-like-button active"
                )
                track_callback_end('app.tab_state_callbacks', 'toggle_visibility', start_time, result=result)
                return result

            # Toggle based on button click
            is_showing = True
            style = {"display": "block"}
            button_class = "tab-like-button active"

            result = (style, is_showing, button_class)
            track_callback_end('app.tab_state_callbacks', 'toggle_visibility', start_time, result=result)
            return result

        except Exception as e:
            logger.exception("Error in toggle_visibility")
            track_callback_end('app.tab_state_callbacks', 'toggle_visibility', start_time, error=str(e))
            raise

    @app.callback(
        Output("debug-collapse", "is_open"),
        Input("debug-toggle", "n_clicks"),
        State("debug-collapse", "is_open"),
    )
    def toggle_debug_collapse(n_clicks: int, is_open: bool) -> bool:
        """Toggle the debug log collapse."""
        ctx = dash.callback_context
        start_time = track_callback('app.tab_state_callbacks', 'toggle_debug_collapse', ctx)

        try:
            if n_clicks:
                result = not is_open
                track_callback_end('app.tab_state_callbacks', 'toggle_debug_collapse', start_time, result="not is_open")
                return result
            track_callback_end('app.tab_state_callbacks', 'toggle_debug_collapse', start_time, result="is_open")
            return is_open

        except Exception as e:
            logger.exception("Error in toggle_debug_collapse")
            track_callback_end('app.tab_state_callbacks', 'toggle_debug_collapse', start_time, error=str(e))
            raise



def setup_sidebar_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""
    
    @app.callback(
        [
            Output("sidebar-filters", "className"),
            Output("sidebar-col", "className"),
            Output("main-content-col", "className"),
            Output("toggle-sidebar-button", "children")
        ],
        [Input("toggle-sidebar-button", "n_clicks")],
        [State("sidebar-filters", "className")]
    )
    def toggle_sidebar(n_clicks, current_class):
        """Toggle sidebar visibility and update button text."""
        if not n_clicks:
            # Initial state - now expanded
            return (
                "sidebar-filters expanded",  # Changed from 'collapsed' to 'expanded'
                "sidebar-col expanded",      # Added 'expanded'
                "main-col shifted",          # Added 'shifted'
                "Hide Filters"               # Changed from 'Show Filters' to 'Hide Filters'
            )
            
        # Toggle based on current state
        if "collapsed" in (current_class or ""):
            return (
                "sidebar-filters expanded",
                "sidebar-col expanded",
                "main-col shifted",
                "Hide Filters"
            )
        else:
            return (
                "sidebar-filters collapsed",
                "sidebar-col",
                "main-col",
                "Show Filters"
            )

    @app.callback(
        Output("sidebar-filters", "style"),
        [Input("navbar-toggler", "n_clicks")],
        [State("sidebar-filters", "style")]
    )
    def handle_mobile_sidebar(n_clicks, current_style):
        """Handle sidebar visibility on mobile."""
        if not n_clicks:
            # Initial state for mobile - visible
            return {"display": "block"}
            
        current_style = current_style or {}
        new_style = current_style.copy()
        
        # Toggle display on mobile
        if new_style.get("display") == "none":
            new_style["display"] = "block"
        else:
            new_style["display"] = "none"
            
        return new_style