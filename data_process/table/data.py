from typing import List, Tuple, Optional, Dict

from dash import dash_table
import pandas as pd

from config.logging_config import get_logger
from constants.translations import translate
from data_process.io import save_df_to_csv
from data_process.mappings import map_line
from .config import create_datatable
from .transformers import transform_table_data
from .sort_lines import sort_and_indent_df
from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY


logger = get_logger(__name__)
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
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
    """Generate table configuration with styles and formatting."""
    df.loc[:, 'metric'] = df['metric'].str.replace('_q_to_q', '')
    insurer = df['insurer'].unique()
    # save_df_to_csv(df, "df_before_pivot.csv")
    # save_df_to_csv(df,f"{insurer[0]}df_before_pivot.csv")
    line = df['linemain'].unique()

    table_data = transform_table_data(
        df, 
        table_selected_metric, 
        prev_ranks, 
        current_ranks,
        split_mode
    )
    #save_df_to_csv(table_data, "df_after_pivot.csv")

    if split_mode == 'insurer':

        with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as file:
            json_str = file.read()
        logger.debug(f" line uniquw {table_data['linemain'].unique()} ")
        table_data = sort_and_indent_df(table_data, json_str)

    # save_df_to_csv(table_data, "df_after_pivot_aftersort.csv")
    # save_df_to_csv(table_data,f"{insurer[0]}df_after_pivot.csv")
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

    return (
        dash_table.DataTable(**datatable),
        f"Топ-{number_of_insurers} страховщиков",
        f"{translate(table_selected_metric[0])}: {lines_str}"
    )