from typing import Dict, List, Optional, Tuple

import pandas as pd
from dash import dash_table, html  # type: ignore

from app.table.config import create_datatable
from config.logging import get_logger, timer
from constants.translations import translate
from core.lines.mapper import map_line
from core.table.transformer import TableTransformer

logger = get_logger(__name__)


@timer
def get_data_table(
    df: pd.DataFrame,
    split_mode: str,
    selected_metrics: List[str],
    selected_lines: List[str],
    period_type: str,
    top_n_list: int,
    show_market_share: Optional[List[str]],
    show_change: Optional[List[str]],
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    insurer: Optional[List[str]] = None,
    line: Optional[List[str]] = None
) -> Tuple[dash_table.DataTable, str, str]:
    """
    """

    transformer = TableTransformer()
    table_data = transformer.transform_table(
        df,
        selected_metrics,
        prev_ranks,
        current_ranks,
        split_mode
    )

    datatable = create_datatable(
        table_data,
        selected_metrics,
        period_type,
        show_market_share,
        show_change,
        split_mode,
        line,
        insurer
    )

    mapped_lines = map_line(selected_lines)
    lines_str = ', '.join(
        mapped_lines
    ) if isinstance(mapped_lines, list) else mapped_lines

    title = f"Топ-{top_n_list} страховщиков"
    subtitle = f"{translate(selected_metrics[0])}: {lines_str}"

    return dash_table.DataTable(**datatable), title, subtitle


def create_data_section(
    table_data: Optional[Tuple[dash_table.DataTable, str, str]] = None
) -> html.Div:
    """Create a data section with table and hidden headers."""
    if table_data is None:
        return html.Div("No data available for the selected filters",
                        className="text-center p-4")

    return html.Div([
        html.Div(id='click-details'),
        html.H3(table_data[1],
                className="table-title", style={"display": "none"}),
        html.H4(table_data[2],
                className="table-subtitle", style={"display": "none"}),
        table_data[0]
    ], className="data-section")