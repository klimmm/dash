import dash  # type: ignore
from dash import Input, Output, State  # type: ignore

from config.logging import get_logger, error_handler, DashDebugHandler

logger = get_logger(__name__)


def setup_debug(app: dash.Dash, debug_handler: DashDebugHandler) -> None:
    """Setup callbacks for debug panel functionality."""

    @app.callback(
        Output('module-filter', 'options'),
        Input('refresh-interval', 'n_intervals')
    )
    @error_handler
    def update_module_options(_):
        # Get unique module names from logs
        modules = set()
        for log in debug_handler.log_entries:
            # Extract module name from log entry
            # Assuming format: "timestamp - module - level - message"
            parts = log.split(' - ')
            if len(parts) >= 2:
                modules.add(parts[1])

        return [{'label': module, 'value': module}
                for module in sorted(modules)]
 
    @app.callback(
        Output('debug-logs', 'children'),
        Input('refresh-interval', 'n_intervals'),
        Input('log-level-filter', 'value'),
        Input('module-filter', 'value')
    )
    @error_handler
    def update_debug_logs(n_intervals, level_filters, module_filters):
        filtered_logs = []
        log_levels = {
            'CRITICAL': 50,
            'ERROR': 40,
            'WARNING': 30,
            'INFO': 20,
            'DEBUG': 10
        }

        # If no levels selected, show all
        if not level_filters:
            level_filters = list(log_levels.keys())

        # Find the minimum log level from selected filters
        min_level = min([log_levels[level] for level in level_filters],
                        default=0)

        for log in debug_handler.log_entries:
            parts = log.split(' - ')
            if len(parts) >= 3:
                log_level_name = parts[2].strip()
                log_level = log_levels.get(log_level_name, 0)
                log_module = parts[1].strip() if len(parts) > 1 else None

                # Check if log level is at or above the minimum selected level
                level_match = log_level >= min_level

                # Check if module matches any selected module (or no modul sel)
                module_match = not module_filters or log_module in module_filters

                if level_match and module_match:
                    filtered_logs.append(log)

        return '\n'.join(filtered_logs)

    # Callback for auto-scrolling logs
    app.clientside_callback(
        """
        function(children, is_open) {
            if (is_open) {
                const container = document.getElementById('debug-logs-container');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('debug-logs', 'style'),
        Input('debug-logs', 'children'),
        Input('debug-collapse', 'is_open'),
        prevent_initial_call=True
    )

    # Callback for collapse toggle
    @app.callback(
        Output("debug-collapse", "is_open"),
        Output("debug-collapse-button", "children"),
        Input("debug-collapse-button", "n_clicks"),
        State("debug-collapse", "is_open"),
    )
    def toggle_collapse(n_clicks: int, is_open: bool) -> tuple[bool, str]:
        if not n_clicks:
            return False, "Show Logs"
        return not is_open, "Hide Logs" if not is_open else "Show Logs"