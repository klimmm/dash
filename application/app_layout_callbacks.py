import dash
from dash import Input, Output, State
from dataclasses import dataclass
from typing import Tuple
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)





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