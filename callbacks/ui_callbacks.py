from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dash import Dash, Input, Output, State, dash_table, html

from app.table.data import get_data_table
from config.logging import error_handler, log_callback, get_logger, timer
from constants.translations import translate
from core.lines.mapper import map_line
from core.insurers.mapper import map_insurer


logger = get_logger(__name__)


def convert_to_quarter_format(date_input, period_type):
    # If input is already a Timestamp or datetime, use it directly
    if isinstance(date_input, (pd.Timestamp, datetime)):
        date = date_input
    else:
        # If it's a string, parse it
        date = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')

    if period_type == 'ytd':
        # Calculate which quarter (in months)
        month = date.month
        quarter_month = ((month - 1) // 3 + 1) * 3
        return f"{quarter_month}M'{date.year}"
    else:
        quarter = (date.month - 1) // 3 + 1
        # Format as 1Q'2023, 2Q'2023, etc.
        return f"{quarter}Q'{date.year}"


def create_title_section(
    df: pd.DataFrame,
    reporting_form: str,
    selected_lines: List[str],
    selected_metrics: List[str],
    selected_insurers: List[str],
    start_quarter: str,
    end_quarter: str,
    period_type: str,
    second_row_displayed: bool = False
) -> html.Div:

    periods = list(df['year_quarter'].unique())
    title_displayed = html.Div([
        f"{translate(reporting_form)} | ",
        f"{', '.join(convert_to_quarter_format(period, period_type) for period in periods)}",
        html.Br()
    ])
    if second_row_displayed:
        title_hidden = html.Div([
            f"Вид страхования: {', '.join(map_line(line) for line in selected_lines)} | ",
            f"Показатель: {', '.join(translate(metric) for metric in selected_metrics)} | ",
            f"Страховщик: {', '.join(map_insurer(insurer) for insurer in selected_insurers)}"
        ], id='table-title-second-row', className="table-title-second-row")
    else:
        title_hidden = html.Div([])

    return html.Div([title_displayed, title_hidden], className="table-title")


def create_data_section(
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


def setup_ui(app: Dash) -> None:
    @app.callback(
        Output('table-title', 'children'),
        Output('tables-container', 'children'),

        [Input('filtered-insurers-data-store', 'data'),
         Input('rankings-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-store', 'data'),
         Input('sidebar', 'className'),
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
        sidebar_classname: str,
        view_metrics_state: List[str],
        split_mode: str,
        filter_state: Dict,
        period_type: str,
        end_quarter: str,
    ) -> List[Any]:
        """Process UI updates and generate tables.

        Returns:
            List of table components for the UI
        """
        if not processed_data:
            return "", [create_data_section()]
        if top_n_list == 0 and selected_insurers is None:
            return "", [create_data_section()]

        show_market_share = 'market-share' in view_metrics_state
        show_change = 'change' in view_metrics_state
        logger.debug(f"view metrics {view_metrics_state}")
        logger.debug(f"top_n_list {top_n_list}")
        logger.warning(f"sidebar_classname {sidebar_classname}")

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

        reporting_form = filter_state['reporting_form']
        end_quarter = filter_state['end_quarter']
        start_quarter = filter_state['start_quarter']   
        second_row_displayed = sidebar_classname == 'sidebar collapsed'
        title_section = create_title_section(df,
            reporting_form, selected_lines, selected_metrics, selected_insurers,
            start_quarter, end_quarter, period_type, second_row_displayed)

        return title_section, tables