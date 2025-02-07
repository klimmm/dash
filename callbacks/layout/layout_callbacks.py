from dataclasses import dataclass
from typing import Tuple

import dash
from dash import Input, Output, State

from config.logging_config import get_logger
from config.callback_logging import log_callback
from application.style.style_constants import StyleConstants
logger = get_logger(__name__)


def setup_debug_panel(app: dash.Dash) -> None:
    """Setup callbacks for debug panel functionality."""

    @app.callback(
        Output("debug-collapse", "is_open"),
        Input("debug-toggle", "n_clicks"),
        State("debug-collapse", "is_open"),
        prevent_initial_call=True
    )
    @log_callback
    def toggle_debug_button(n_clicks: int, is_open: bool) -> bool:
        ctx = dash.callback_context

        try:
            result = not is_open if n_clicks else is_open
            return result

        except Exception as e:
            logger.exception("Error in toggle_debug")
            raise


@dataclass
class SidebarState:
    """Manages sidebar-related classes and states."""
    chart_cont_class: str
    sidebar_col_class: str
    inner_btn_text: str
    inner_btn_class: str

    @classmethod
    def expanded(cls) -> 'SidebarState':
        """Create expanded sidebar state."""
        return cls(
            chart_cont_class=StyleConstants.CONTAINER["CHART"],
            sidebar_col_class=StyleConstants.SIDEBAR,
            inner_btn_text="Hide Filters",
            inner_btn_class=StyleConstants.BTN["SIDEBAR_HIDE"]
        )

    @classmethod
    def collapsed(cls) -> 'SidebarState':
        """Create collapsed sidebar state."""
        return cls(
            chart_cont_class=StyleConstants.CONTAINER["CHART_COLLAPSED"],
            sidebar_col_class=StyleConstants.SIDEBAR_COLLAPSED,
            inner_btn_text="Show Filters",
            inner_btn_class=StyleConstants.BTN["SIDEBAR_SHOW"]
        )

    def to_tuple(self) -> Tuple[str, str, str, str, str]:
        """Convert state to callback output tuple."""
        return (
            self.chart_cont_class,
            self.sidebar_col_class,
            self.inner_btn_text,
            self.inner_btn_class
        )


def setup_sidebar(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""

    @app.callback(
        [
            Output("chart-container", "className"),
            Output("sidebar-col", "className"),
            Output("toggle-sidebar-button-sidebar", "children"),
            Output("toggle-sidebar-button-sidebar", "className")
        ],
        [
            Input("toggle-sidebar-button-sidebar", "n_clicks")
        ],
        [
            State("sidebar-col", "className")
        ],
        prevent_initial_call=True  # Prevent callback from firing on initial load
    )
    @log_callback
    def toggle_sidebar_button(
        sidebar_clicks: int,
        current_class: str
    ) -> Tuple[str, str, str, str, str]:
        """
        Toggle sidebar visibility and update related elements.
        """
        ctx = dash.callback_context

        try:
            # If no button was clicked (initial load), return expanded state
            if not ctx.triggered:
                return SidebarState.expanded().to_tuple()

            # Determine current state
            is_expanded = current_class and "collapsed" not in current_class

            # Return opposite state
            new_state = SidebarState.collapsed() if is_expanded else SidebarState.expanded()

            logger.debug(f"sidebar_clicks {sidebar_clicks}, current_class {current_class},trigger {ctx.triggered[0]}, new state {new_state.to_tuple()} ")

            return new_state.to_tuple()

        except Exception as e:
            logger.exception("Error in toggle_sidebar")
            raise