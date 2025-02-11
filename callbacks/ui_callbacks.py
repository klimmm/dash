from typing import Any, Dict, List

import pandas as pd
from dash import Dash, Input, Output, State  # type: ignore

from app.table.data import create_data_section, get_data_table
from config.logging import error_handler, log_callback, get_logger, timer

logger = get_logger(__name__)


def setup_ui(app: Dash) -> None:
    @app.callback(
        Output('tables-container', 'children'),
        [Input('filtered-insurers-data-store', 'data'),
         Input('rankings-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-store', 'data'),
         Input('view-metrics', 'data')],
        [State('table-split-mode-selected', 'data'),
         State('filter-state-store', 'data'),
         State('period-type-selected', 'data'),
         State('end-quarter', 'value')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    @error_handler
    def process_ui(
        processed_data: Dict,
        rankings: Dict,
        top_n_list: List[int],
        selected_insurers: str,
        view_metrics_state: List[str],
        split_mode: str,
        filter_state: Dict,
        period_type: str,
        end_quarter: str
    ) -> List[Any]:
        """Process UI updates and generate tables.

        Returns:
            List of table components for the UI
        """
        if not processed_data:
            return [create_data_section()]
        if top_n_list == 0 and selected_insurers is None:
            return [create_data_section()]

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
            tables.append(create_data_section(table_data))

        logger.debug(
            f"Generated {len(tables)} tables split by {split_mode}. "
            f"Market share: {show_market_share}, Change: {show_change}"
        )
        return tables