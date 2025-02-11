from typing import Tuple
import dash  # type: ignore
from dash import Input, Output, State  # type: ignore
from app.style_constants import StyleConstants
from config.logging import log_callback, get_logger, DashDebugHandler

logger = get_logger(__name__)


def setup_sidebar(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""

    SIDEBAR_EXPANDED_CLASS = StyleConstants.SIDEBAR
    SIDEBAR_COLLAPSED_CLASS = StyleConstants.SIDEBAR_COLLAPSED
    BUTTON_SHOW_CLASS = StyleConstants.BTN["SIDEBAR_HIDE"]
    BUTTON_HIDE_CLASS = StyleConstants.BTN["SIDEBAR_SHOW"]

    @app.callback(
        [Output('sidebar', 'className'),
         Output('sidebar-button', 'children'),
         Output('sidebar-button', 'className')],
        [Input('sidebar-button', 'n_clicks')],
        [State('sidebar', 'className')]
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
            if not ctx.triggered or not sidebar_clicks:
                return (
                    SIDEBAR_EXPANDED_CLASS,
                    "Скрыть фильтры",
                    BUTTON_HIDE_CLASS
                )

            is_expanded = current_class and "collapsed" not in current_class

            if is_expanded:
                new_state = (
                    SIDEBAR_COLLAPSED_CLASS,
                    "Показать фильтры",
                    BUTTON_SHOW_CLASS
                )
            else:
                new_state = (
                    SIDEBAR_EXPANDED_CLASS,
                    "Скрыть фильтры",
                    BUTTON_HIDE_CLASS
                )

            logger.debug(f"sidebar_clicks {sidebar_clicks}, cur_class {current_class}")
            logger.debug(f"trigger {ctx.triggered[0]}, new state {new_state}")
            return new_state

        except Exception:
            logger.exception("Error in toggle_sidebar")
            raise


def setup_debug_panel(app: dash.Dash, debug_handler: DashDebugHandler) -> None:
    """Setup callbacks for debug panel functionality."""

    @app.callback(
        Output("debug-collapse", "is_open"),
        Input("debug-toggle", "n_clicks"),
        State("debug-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_debug_button(n_clicks: int, is_open: bool) -> bool:
        return not is_open if n_clicks else is_open

    @app.callback(
        Output("debug-logs", "children"),
        [Input("log-update-interval", "n_intervals"),
         Input("clear-logs-button", "n_clicks")],
        prevent_initial_call=True
    )
    def update_logs(n_intervals, clear_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return ""

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "clear-logs-button":
            debug_handler.log_entries.clear()
            return ""
            
        return "\n".join(list(debug_handler.log_entries))