from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import dash  # type: ignore
from dash import Dash, Input, Output, State, dash_table, html, ALL

from app.table.data import get_data_table
from config.logging import error_handler, log_callback, get_logger, timer

logger = get_logger(__name__)


def create_data_tables_section(
    table_data: Optional[Tuple[dash_table.DataTable, str, str]] = None
) -> html.Div:
    """Create a data section with table and hidden headers."""
    if table_data is None:
        return html.Div("No data available for the selected filters",
                        className="text-start p-4")

    return html.Div([
        html.Div(id='click-details'),
        table_data[0]
    ], className="data-section")


def setup_table(app: Dash) -> None:
    @app.callback(
        Output('tables-container', 'children'),
        [Input('filtered-insurers-data-store', 'data'),
         Input('rankings-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-store', 'data'),
         Input('view-metrics', 'data')],
        [State('table-split-mode-selected', 'data'),
         State('filter-state-store', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    @error_handler
    def generate_data_tables(
        processed_data: Dict,
        rankings: Dict,
        top_n_list: List[int],
        selected_insurers: str,
        view_metrics_state: List[str],
        split_mode: str,
        filter_state: Dict,
    ) -> List[Any]:
        """Process UI updates and generate tables.

        Returns:
            List of table components for the UI
        """
        if not processed_data:
            return [create_data_tables_section()]
        if top_n_list == 0 and selected_insurers is None:
            return [create_data_tables_section()]

        show_market_share = 'market-share' in view_metrics_state
        show_change = 'change' in view_metrics_state
        logger.debug(f"view metrics {view_metrics_state}")
        logger.debug(f"top_n_list {top_n_list}")

        df = pd.DataFrame.from_records(processed_data).assign(
            year_quarter=lambda x: pd.to_datetime(x['year_quarter']))
        prev_ranks = rankings.get('prev_ranks')
        current_ranks = rankings.get('current_ranks')
        selected_metrics = filter_state['selected_metrics']
        selected_lines = filter_state['selected_lines']
        period_type = filter_state['period_type']
        selected_lines = filter_state['selected_lines']

        split_column = 'linemain' if split_mode == 'line' else 'insurer'
        ordered_values = (selected_lines if split_mode == 'line'
                          else df['insurer'].unique())

        tables = []

        for value in ordered_values:
            if split_mode == 'line' and value not in df[split_column].unique():
                continue

            df_filtered = df[df[split_column] == value]
            table_data = get_data_table(
                df=df_filtered,
                split_mode=split_mode,
                selected_metrics=selected_metrics,
                selected_lines=selected_lines,
                period_type=period_type,
                top_n_list=top_n_list,
                show_market_share=show_market_share,
                show_change=show_change,
                prev_ranks=prev_ranks,
                current_ranks=current_ranks,
                insurer=list(df_filtered['insurer'].unique()),
                line=list(df_filtered['linemain'].unique())
            )
            tables.append(create_data_tables_section(table_data))

        logger.debug(
            f"Generated {len(tables)} tables split by {split_mode}. "
            f"Market share: {show_market_share}, Change: {show_change}"
        )

        return tables

    @app.callback(
        Output('click-details', 'children'),
        [Input({'type': 'dynamic-table', 'index': ALL}, 'active_cell'),
         Input({'type': 'dynamic-table', 'index': ALL}, 'data')],
        prevent_initial_call=True
    )
    @error_handler
    @log_callback
    @timer
    def display_selected_cell_details(
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