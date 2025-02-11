from typing import List, Dict, Any, Union

import dash  # type: ignore
from dash import Output, Input, html, ALL  # type: ignore

from config.logging import log_callback, error_handler, get_logger, timer

logger = get_logger(__name__)


def setup_data_table(app: dash.Dash) -> None:
    @app.callback(
        Output('click-details', 'children'),
        [Input({'type': 'dynamic-table', 'index': ALL}, 'active_cell'),
         Input({'type': 'dynamic-table', 'index': ALL}, 'data')],
        prevent_initial_call=True
    )
    @error_handler
    @log_callback
    @timer
    def handle_cell_click(
        active_cells: List[Dict[str, Any]], 
        all_table_data: List[List[Dict[str, Any]]]
    ) -> Union[str, html.Div]:
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
                    logger.info(
                        f"Cell clicked - Row: {row_data}, Column: {column_id}")
                    return html.Div([
                        html.H4(f"Selected: {row_data.get('insurer', '')}"),
                        html.Div([
                            html.Div(f"{k}: {v}", className="detail-item")
                            for k, v in row_data.items()
                            if k not in ['is_section_header']
                        ], className="details-grid")
                    ], className="click-details")
        return ""