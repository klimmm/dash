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
            Output("toggle-sidebar-button", "children"),
            Output("toggle-sidebar-button", "className"),
            Output("toggle-sidebar-button-sidebar", "className")
        ],
        [
            Input("toggle-sidebar-button", "n_clicks"),
            Input("toggle-sidebar-button-sidebar", "n_clicks")
        ],
        [
            State("sidebar-filters", "className")
        ]
    )
    def toggle_sidebar(n_clicks, n_clicks_sidebar, current_class):
        """Toggle sidebar visibility and update all related elements."""
        
        # Determine if we're in collapsed state
        is_collapsed = current_class and "collapsed" in current_class
        
        # Default expanded state classes
        expanded_classes = {
            "sidebar": "sidebar-filters expanded",
            "sidebar_col": "sidebar-col expanded",
            "main_col": "main-col shifted",
            "nav_button": "btn-custom btn-sidebar-toggle",
            "nav_text": "Hide Filters",
            "sidebar_button": "btn-custom btn-period active"
        }
        
        # Default collapsed state classes
        collapsed_classes = {
            "sidebar": "sidebar-filters collapsed",
            "sidebar_col": "sidebar-col",
            "main_col": "main-col",
            "nav_button": "btn-custom btn-sidebar-toggle",
            "nav_text": "Show Filters",
            "sidebar_button": "btn-custom btn-period"
        }
        
        # On first load or when toggling to expanded
        if not n_clicks and not n_clicks_sidebar or is_collapsed:
            return (
                expanded_classes["sidebar"],
                expanded_classes["sidebar_col"],
                expanded_classes["main_col"],
                expanded_classes["nav_text"],
                expanded_classes["nav_button"],
                expanded_classes["sidebar_button"]
            )
        
        # When toggling to collapsed
        return (
            collapsed_classes["sidebar"],
            collapsed_classes["sidebar_col"],
            collapsed_classes["main_col"],
            collapsed_classes["nav_text"],
            collapsed_classes["nav_button"],
            collapsed_classes["sidebar_button"]
        )