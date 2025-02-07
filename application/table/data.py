from typing import Dict, List, Optional, Tuple

import pandas as pd
from dash import dash_table

from application.table.config import create_datatable
from config.logging_config import get_logger, timer
from constants.translations import translate
from domain.lines.mapper import map_line
from domain.table.transformer import TableTransformer

logger = get_logger(__name__)


@timer
def get_data_table(
    df: pd.DataFrame,
    split_mode: str,
    selected_metrics: List[str],
    selected_lines: List[str],
    period_type: str,
    number_of_insurers: int,
    toggle_show_market_share: Optional[List[str]],
    toggle_show_change: Optional[List[str]],
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    insurer: List[str] = None,
    line: List[str] = None
) -> Tuple[dash_table.DataTable, str, str]:
    """
    """

    transformer = TableTransformer()
    table_data = transformer.transform_table(
        df,
        selected_metrics,
        prev_ranks,
        current_ranks,
        split_mode)

    datatable = create_datatable(
        table_data,
        selected_metrics,
        period_type,
        toggle_show_market_share,
        toggle_show_change,
        split_mode,
        line,
        insurer
    )

    mapped_lines = map_line(selected_lines)
    lines_str = ', '.join(
        mapped_lines) if isinstance(mapped_lines, list) else mapped_lines

    title = f"Топ-{number_of_insurers} страховщиков"
    subtitle = f"{translate(selected_metrics[0])}: {lines_str}"

    return dash_table.DataTable(**datatable), title, subtitle


__all__ = ['get_data_table']