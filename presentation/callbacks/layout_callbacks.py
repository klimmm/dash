from typing import Dict, List, Any, Union, Optional
import dash
from dash import Input, Output, ALL, html, dcc, ClientsideFunction, State, MATCH
from dash.exceptions import PreventUpdate
from presentation.style_constants import StyleConstants


class LayoutCallbacks:
    def __init__(self, config):
        self.config = config
        self.logger = config.logger
        self.dash_callback = config.dash_callback
        self.memory_handler = config.debug_handler
        self.columns = self.config.columns

    
    def register_callbacks(self, app: dash.Dash, components: Dict[str, Any]) -> None:

        @app.callback(
            Output('filters-summary-second-row', 'style'),
            [Input('filtered-insurers-trigger', 'data'),
             Input('sidebar', 'className')],
            prevent_initial_call=True
        )
        def manage_filters_summary(quarters, sidebar_state):
            # Determine visibility of the second row based on sidebar state
            if sidebar_state == "sidebar collapsed":
                return {'display': 'block'}
            return {'display': 'none'}
    
        self.logger.debug("Registering sidebar callbacks")

        @app.callback(
            Output('sidebar', 'className'),
            Output('sidebar-button', 'children'),
            Input('sidebar-button', 'n_clicks'),
            State('sidebar', 'className'),
            prevent_initial_callback=True
        )
        def toggle_sidebar(n_clicks, current_class):
            if not n_clicks or not current_class:
                raise PreventUpdate

            is_collapsed = StyleConstants.SIDEBAR_COLLAPSED in current_class
            new_class = (StyleConstants.SIDEBAR if is_collapsed 
                         else StyleConstants.SIDEBAR_COLLAPSED)

            return new_class, html.I(className=StyleConstants.SIDEBAR_ICON)

        @app.callback(
            Output({'type': 'collapse-content', 'index': MATCH}, 'style'),
            Output({'type': 'collapse-header', 'index': MATCH}, 'children'),
            Input({'type': 'collapse-header', 'index': MATCH}, 'n_clicks'),
            State({'type': 'collapse-content', 'index': MATCH}, 'style'),
            State({'type': 'collapse-header', 'index': MATCH}, 'children'),
            prevent_initial_callback=True
        )
        def toggle_collapse(n_clicks, style, children):
            if not n_clicks:
                raise PreventUpdate

            new_style = style.copy() if style else {}
            is_visible = new_style.get('display') in (None, 'block')
            new_style['display'] = 'none' if is_visible else 'block'

            icon_class = (StyleConstants.COLLAPSE_ICON_DOWN if is_visible
                          else StyleConstants.COLLAPSE_ICON_UP)
            children[1] = html.I(className=icon_class)

            return new_style, children

        """Register callbacks for debug panel functionality."""
        self.logger.debug("Registering debug panel callbacks")

        # Callback for updating module filter options
        @app.callback(
            Output('module-filter', 'options'),
            Input('refresh-interval', 'n_intervals')
        )
        def update_module_options_callback(n_intervals: Optional[int]) -> List[Dict[str, str]]:
            modules = {log.split(' - ')[1] for log in self.memory_handler.log_entries
                      if len(log.split(' - ')) >= 2}
            return [{'label': module, 'value': module} for module in sorted(modules)]

        # Callback for updating debug logs based on filters
        @app.callback(
            Output('debug-logs', 'children'),
            Input('refresh-interval', 'n_intervals'),
            Input('log-level-filter', 'value'),
            Input('module-filter', 'value')
        )
        def update_debug_logs_callback(
            n_intervals: Optional[int],
            level_filters: Optional[List[str]],
            module_filters: Optional[List[str]]
        ) -> str:
            log_levels = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10}

            # If no levels selected, show all
            if not level_filters:
                level_filters = list(log_levels.keys())

            min_level = min([log_levels[level] for level in level_filters], default=0)

            filtered_logs = []
            for log in self.memory_handler.log_entries:
                parts = log.split(' - ')
                if len(parts) >= 3:
                    log_level = log_levels.get(parts[2].strip(), 0)
                    log_module = parts[1].strip() if len(parts) > 1 else None

                    # Check if log matches filters
                    if (log_level >= min_level and
                        (not module_filters or log_module in module_filters)):
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

        # Callback for toggling debug panel visibility
        @app.callback(
            Output("debug-collapse", "is_open"),
            Output("debug-collapse-button", "children"),
            Input("debug-collapse-button", "n_clicks"),
            State("debug-collapse", "is_open"),
        )
        @self.dash_callback
        def toggle_collapse(n_clicks: Optional[int], is_open: bool) -> tuple[bool, str]:
            if not n_clicks:
                return False, "Show Logs"
            return not is_open, "Hide Logs" if not is_open else "Show Logs"

        @app.callback(
            Output('click-details', 'children'),
            [Input({'type': 'dynamic-table', 'index': ALL}, 'active_cell'),
             Input({'type': 'dynamic-table', 'index': ALL}, 'data')],
            prevent_initial_update=True
        )
        @self.dash_callback
        def display_selected_cell_details(
            active_cells: List[Dict[str, Any]],
            all_table_data: List[List[Dict[str, Any]]]
        ) -> Union[str, html.Div]:
            self.logger.debug(f"Callback triggered with active_cells: {active_cells}")
            ctx = dash.callback_context
            if not ctx.triggered:
                return ""
            if active_cells and any(active_cells):
                clicked_table_index = next(
                    (i for i, cell in enumerate(active_cells) if cell), None
                )
                if clicked_table_index is not None:
                    cell = active_cells[clicked_table_index]
                    data = all_table_data[clicked_table_index]
                    if cell and data:
                        row_data = data[cell['row']]
                        column_id = cell['column_id']
                        self.logger.info(
                            f"Cell clicked - Row: {row_data}, Column: {column_id}")
                        return html.Div([
                            html.H4(f"Selected: {row_data.get(self.columns.INSURER, '')}"),
                            html.Div([
                                html.Div(f"{k}: {v}", className="detail-item")
                                for k, v in row_data.items()
                                if k not in ['is_section_header']
                            ], className="details-grid")
                        ], className="click-details")
            return ""

        # 3. Add viewport detection components and clientside callback
        app.layout.children.append(
            html.Div([
                dcc.Interval(id='viewport-check-interval',
                             interval=1000, n_intervals=0)
            ], style={'display': 'none'})
        )

        # Add clientside JavaScript for viewport detection
        app.clientside_callback(
            ClientsideFunction(
                namespace='clientside',
                function_name='detectViewport'
            ),
            Output('viewport-size', 'data'),
            Input('viewport-check-interval', 'n_intervals'),
            prevent_initial_update=True
        )
    
        # Create button and handle sidebar toggle
        app.clientside_callback(
            """function(n) {
            if (document.getElementById('fixed-button-container')) {
                return window.dash_clientside.no_update;
            }
    
            // Create elements
            const c = document.createElement('div'); // container
            const b = document.createElement('button'); // button
            c.id = 'fixed-button-container';
            b.id = 'fixed-sidebar-button';
            c.appendChild(b);
            document.body.appendChild(c);
    
            // Apply base styles
            c.style.cssText = 'position:fixed;top:25px;z-index:99999;display:block;' + 
                              'transition:left 0.3s ease';
            b.style.cssText = 'position:relative;width:24px;height:24px;' + 
                              'background:#4a6bff;border:none;border-radius:50%;' + 
                              'box-shadow:0 2px 5px rgba(0,0,0,0.2);cursor:pointer;' + 
                              'color:white;transition:all 0.3s ease;display:flex;' + 
                              'align-items:center;justify-content:center';
    
            // Add ripple animation
            const style = document.createElement('style');
            style.textContent = '@keyframes ripple{to{transform:scale(2.5);opacity:0}}';
            document.head.appendChild(style);
    
            // SVG icons
            const m = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" ' + 
                      'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' + 
                      'stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12">' + 
                      '</line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" ' + 
                      'y1="18" x2="21" y2="18"></line></svg>';
            const x = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" ' + 
                      'stroke="currentColor" stroke-width="2" stroke-linecap="round" ' + 
                      'stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18">' + 
                      '</line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    
            // Click handler with ripple
            b.onclick = function() {
                const sb = document.getElementById('sidebar-button');
                if(sb) sb.click();
    
                const r = document.createElement('span'); // ripple
                r.style.cssText = 'position:absolute;border-radius:50%;width:100%;' + 
                                  'height:100%;transform:scale(0);opacity:1;' + 
                                  'background:rgba(255,255,255,0.3);' + 
                                  'animation:ripple 0.6s linear';
                this.appendChild(r);
                setTimeout(() => r.remove(), 700);
            };
    
            // Hover effects
            b.onmouseover = () => {
                b.style.background = '#3451d1';
                b.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                b.style.transform = 'translateY(-2px)';
            };
    
            b.onmouseout = () => {
                b.style.background = '#4a6bff';
                b.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
                b.style.transform = '';
            };
    
            // Update function
            const update = collapsed => {
                b.innerHTML = collapsed ? m : x;
                c.style.left = collapsed ? '0px' : '290px';
            };
    
            // Observe sidebar
            const s = document.getElementById('sidebar');
            if (s) {
                new MutationObserver(m => {
                    if (m[0].attributeName === 'class') {
                        update(s.className.includes('collapsed'));
                    }
                }).observe(s, {attributes:true});
    
                // Initial state
                update(s.className.includes('collapsed'));
            }
    
            return window.dash_clientside.no_update;
        }""",
            Output('_hidden-div-for-clientside', 'children'),
            [Input('_dummy-trigger', 'children')]
        )
    
        # Trigger on page load
        app.clientside_callback(
            "function() { return 'loaded'; }",
            Output('_dummy-trigger', 'children'),
            [Input('_page-load', 'children')]
        )
    
