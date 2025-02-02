from functools import wraps
import time
from typing import List, Tuple, Optional, Dict

from dash import dash_table
import pandas as pd

from config.logging_config import get_logger
from constants.translations import translate
from data_process.mappings import map_line
from data_process.table.config import create_datatable
from data_process.table.transformers import transform_table_data

logger = get_logger(__name__)


def timer(func):
    """Decorator to log entry/exit and execution time for critical functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.debug(f"Entering {func.__name__}")
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_ms = (time.time() - start) * 1000
            logger.debug(f"Exiting {func.__name__} (took {elapsed_ms:.2f}ms)")
            print(f"{func.__name__} took {elapsed_ms:.2f}ms to execute")
    return wrapper


@timer
def get_data_table(
    df: pd.DataFrame,
    split_mode: str,
    table_selected_metric: List[str],
    selected_linemains: List[str],
    period_type: str,
    number_of_insurers: int,
    toggle_show_market_share: Optional[List[str]],
    toggle_show_change: Optional[List[str]],
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None
) -> Tuple[dash_table.DataTable, str, str]:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    df.loc[:, 'metric'] = df['metric'].str.replace('_q_to_q', '')
    insurer = df['insurer'].unique()
    line = df['linemain'].unique()

    table_data = transform_table_data(df, table_selected_metric, prev_ranks, current_ranks, split_mode)

    datatable = create_datatable(
        table_data,
        table_selected_metric,
        period_type,
        toggle_show_market_share,
        toggle_show_change,
        split_mode,
        line,
        insurer
    )

    mapped_lines = map_line(selected_linemains)
    lines_str = ', '.join(mapped_lines) if isinstance(mapped_lines, list) else mapped_lines

    title = f"Топ-{number_of_insurers} страховщиков"
    subtitle = f"{translate(table_selected_metric[0])}: {lines_str}"
    return dash_table.DataTable(**datatable), title, subtitle