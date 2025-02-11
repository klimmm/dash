from dataclasses import dataclass
from typing import Tuple
import dash  # type: ignore
from dash import Input, Output, State  # type: ignore
from app.style_constants import StyleConstants
from config.logging import log_callback, get_logger

logger = get_logger(__name__)


@dataclass
class SidebarState:
    """Manages sidebar-related classes and states."""
    sidebar_col_class: str
    inner_btn_text: str
    inner_btn_class: str

    @classmethod
    def expanded(cls) -> 'SidebarState':
        """Create expanded sidebar state."""
        return cls(
            sidebar_col_class=StyleConstants.SIDEBAR,
            inner_btn_text="Скрыть фильтры",
            inner_btn_class=StyleConstants.BTN["SIDEBAR_HIDE"]
        )

    @classmethod
    def collapsed(cls) -> 'SidebarState':
        """Create collapsed sidebar state."""
        return cls(
            sidebar_col_class=StyleConstants.SIDEBAR_COLLAPSED,
            inner_btn_text="Показать фильтры",
            inner_btn_class=StyleConstants.BTN["SIDEBAR_SHOW"]
        )

    def to_tuple(self) -> Tuple[str, str, str]:
        """Convert state to callback output tuple."""
        return (
            self.sidebar_col_class,
            self.inner_btn_text,
            self.inner_btn_class
        )

def setup_sidebar(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""
    @app.callback(
        [Output('sidebar', 'className'),
         Output('sidebar-button', 'children'),
         Output('sidebar-button', 'className')],
        [Input('sidebar-button', 'n_clicks')],
        [State('sidebar', 'className')]
        # Remove prevent_initial_call=True
    )
    @log_callback
    def toggle_sidebar_button(
        sidebar_clicks: int,
        current_class: str
    ) -> Tuple[str, str, str]:
        """
        Toggle sidebar visibility and update related elements.
        """
        ctx = dash.callback_context
        try:
            # If no button was clicked (initial load) or no clicks yet, return expanded state
            if not ctx.triggered or not sidebar_clicks:
                return SidebarState.expanded().to_tuple()

            # Determine current state
            is_expanded = current_class and "collapsed" not in current_class
            # Return opposite state
            new_state = SidebarState.collapsed() if is_expanded else SidebarState.expanded()

            logger.debug(f"sidebar_clicks {sidebar_clicks}, cur_class {current_class}")
            logger.debug(f"trigger {ctx.triggered[0]}, new state {new_state.to_tuple()}")

            return new_state.to_tuple()
        except Exception:
            logger.exception("Error in toggle_sidebar")
            raise

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
        try:
            result = not is_open if n_clicks else is_open
            return result
        except Exception:
            logger.exception("Error in toggle_debug")
            raise