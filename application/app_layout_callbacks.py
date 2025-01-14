import dash
from dash import Input, Output, State
from dataclasses import dataclass
from typing import Tuple
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


@dataclass
class SidebarState:
    """Manages sidebar-related classes and states."""
    chart_cont_class: str
    main_class: str
    sidebar_col_class: str
    inner_btn_text: str
    inner_btn_class: str

    @classmethod
    def expanded(cls) -> 'SidebarState':
        """Create expanded sidebar state."""
        return cls(
            chart_cont_class="chart-container",
            main_class="sidebar-filters",
            sidebar_col_class="sidebar-col",
            inner_btn_text="Hide Filters",
            inner_btn_class="btn-custom btn-sidebar-toggle-nav"
        )

    @classmethod
    def collapsed(cls) -> 'SidebarState':
        """Create collapsed sidebar state."""
        return cls(
            chart_cont_class="chart-container collapsed",
            main_class="sidebar-filters collapsed",
            sidebar_col_class="sidebar-col collapsed",
            inner_btn_text="Show Filters",
            inner_btn_class="btn-custom btn-sidebar-toggle-nav",
        )

    def to_tuple(self) -> Tuple[str, str, str, str, str]:
        """Convert state to callback output tuple."""
        return (
            self.chart_cont_class,
            self.main_class,
            self.sidebar_col_class,
            self.inner_btn_text,
            self.inner_btn_class
        )


def setup_sidebar_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""
    
    @app.callback(
        [
            Output("chart-container", "className"),
            Output("sidebar-filters", "className"),
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
    def toggle_sidebar(
        sidebar_clicks: int,
        current_class: str
    ) -> Tuple[str, str, str, str, str]:
        """
        Toggle sidebar visibility and update related elements.
        """
        ctx = dash.callback_context
        start_time = track_callback('app.sidebar_callbacks', 'toggle_sidebar', ctx)

        try:
            # If no button was clicked (initial load), return expanded state
            if not ctx.triggered:
                return SidebarState.expanded().to_tuple()

            # Determine current state
            is_expanded = current_class and "collapsed" not in current_class

            # Return opposite state
            new_state = SidebarState.collapsed() if is_expanded else SidebarState.expanded()

            track_callback_end('app.sidebar_callbacks', 'toggle_sidebar', start_time, 
                             result=f"toggled_to_{'collapsed' if is_expanded else 'expanded'}")

            logger.warning(f"sidebar_clicks {sidebar_clicks}, current_class {current_class},trigger {ctx.triggered[0]}, new state {new_state.to_tuple()} ")

            return new_state.to_tuple()

        except Exception as e:
            logger.exception("Error in toggle_sidebar")
            track_callback_end('app.sidebar_callbacks', 'toggle_sidebar', start_time, error=str(e))
            raise


def setup_debug_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for debug panel functionality."""

    @app.callback(
        Output("debug-collapse", "is_open"),
        Input("debug-toggle", "n_clicks"),
        State("debug-collapse", "is_open"),
    )
    def toggle_debug_collapse(n_clicks: int, is_open: bool) -> bool:
        ctx = dash.callback_context
        start_time = track_callback('app.tab_state_callbacks', 'toggle_debug_collapse', ctx)

        try:
            result = not is_open if n_clicks else is_open
            track_callback_end(
                'app.tab_state_callbacks',
                'toggle_debug_collapse',
                start_time,
                result="not is_open" if n_clicks else "is_open"
            )
            return result

        except Exception as e:
            logger.exception("Error in toggle_debug_collapse")
            track_callback_end(
                'app.tab_state_callbacks',
                'toggle_debug_collapse',
                start_time,
                error=str(e)
            )
            raise