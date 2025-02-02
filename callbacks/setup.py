from .buttons_callbacks import setup_single_choice_buttons, setup_multi_choice_buttons
from .insurer_callbacks import setup_insurer_selection
from .layout_callbacks import setup_sidebar, setup_debug_panel
from .line_callbacks import setup_line_selection
from .line_tree_view_callbacks import setup_line_tree_view
from .metrics_callbacks import setup_metric_selection
from .prepare_data_callbacks import setup_prepare_data
from .process_data_callbacks import setup_process_data
from .ui_callbacks import setup_ui
import dash
from dash import Output, Input, html, ALL


def data_table_callbacks(app: dash.Dash):

    @app.callback(
        Output('click-details', 'children'),
        [Input({'type': 'dynamic-table', 'index': ALL}, 'active_cell'),
         Input({'type': 'dynamic-table', 'index': ALL}, 'data')],
        prevent_initial_call=True
    )
    def handle_cell_click(active_cells, all_table_data):
        logger.warning(f"Callback triggered with active_cells: {active_cells}")
    
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
                    logger.info(f"Cell clicked - Row: {row_data}, Column: {column_id}")
    
                    return html.Div([
                        html.H4(f"Selected: {row_data.get(INSURER_COL, '')}"),
                        html.Div([
                            html.Div(f"{k}: {v}", className="detail-item") 
                            for k, v in row_data.items()
                            if k not in [SECTION_HEADER_COL]
                        ], className="details-grid")
                    ], className="click-details")
    
        return ""

def setup_all_callbacks(app, lines_tree_162, lines_tree_158, df_162, df_158, end_quarter_options_162, end_quarter_options_158):
    """
    Centralized function to set up all callbacks in the application.
    """
    # Layout and UI setup
    setup_sidebar(app)
    setup_debug_panel(app)
    setup_ui(app)

    # Button callbacks
    setup_single_choice_buttons(app)
    setup_multi_choice_buttons(app)

    # Data selection callbacks
    setup_metric_selection(app)
    setup_line_selection(app, lines_tree_162, lines_tree_158)
    setup_line_tree_view(app, lines_tree_162, lines_tree_158)
    setup_insurer_selection(app)

    # Data processing callbacks
    setup_prepare_data(app, df_162, df_158, end_quarter_options_162, end_quarter_options_158)
    setup_process_data(app)