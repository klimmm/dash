from typing import Dict, List

import pandas as pd
from dash import Input, Output, State, html

from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer

from application.table.data import get_data_table

logger = get_logger(__name__)


def create_data_section(table_data: tuple) -> html.Div:
    """Create a data section with table and hidden headers."""
    return html.Div([
        html.Div(id='click-details'),
        html.H3(table_data[1], className="table-title", style={"display": "none"}),
        html.H4(table_data[2], className="table-subtitle", style={"display": "none"}),
        table_data[0]
    ], className="data-section mb-8")


def setup_ui(app):
    @app.callback(
        Output('tables-container', 'children'),
        [Input('filtered-insurers-data-store', 'data'),
         Input('rankings-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-store', 'data'),
         Input('toggle-selected-market-share', 'data'),
         Input('toggle-selected-qtoq', 'data'),
         Input('table-split-mode', 'data')],
        [State('filter-state-store', 'data'),
         State('period-type', 'data'),
         State('end-quarter', 'value')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    @error_handler
    def process_ui(processed_data: Dict,
                   rankings: Dict,
                   top_n_list: List[int],
                   selected_insurers: str,
                   toggle_show_market_share: bool,
                   toggle_show_change: bool,
                   split_mode: str,
                   filter_state: Dict,
                   period_type: str,
                   end_quarter: str) -> List:

        empty_table = html.Div("No data available for the selected filters",
                               className="text-center p-4")

        if not processed_data:
            return [empty_table]

        if top_n_list == 0 and selected_insurers is None:
            return [empty_table]

        else:
            df = pd.DataFrame.from_records(processed_data).assign(
                year_quarter=lambda x: pd.to_datetime(x['year_quarter']))
            prev_ranks = rankings.get('prev_ranks')
            current_ranks = rankings.get('current_ranks')
            selected_metrics = filter_state['selected_metrics']
            selected_lines = filter_state['selected_lines']

        split_column = 'linemain' if split_mode == 'line' else 'insurer'
        ordered_values = selected_lines if split_mode == 'line' else df['insurer'].unique()

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
                number_of_insurers=top_n_list,
                toggle_show_market_share=toggle_show_market_share,
                toggle_show_change=toggle_show_change,
                prev_ranks=prev_ranks,
                current_ranks=current_ranks,
                insurer=df_filtered['insurer'].unique(),
                line=df_filtered['linemain'].unique()
            )
            tables.append(create_data_section(table_data))

        logger.debug(f"Generated {len(tables)} tables split by {split_mode}")

        return tables