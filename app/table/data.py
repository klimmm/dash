from typing import List, Optional, Tuple

import pandas as pd
from dash import dash_table  # type: ignore

from app.table.config import create_datatable
from config.logging import get_logger, timer
from core.table.transformer import TableTransformer
from core.table.two_level_headers import create_two_level_headers
from core.io import save_df_to_csv

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
    show_rank: Optional[List[str]],
    insurer: Optional[List[str]] = None,
    line: Optional[List[str]] = None,
    metric: Optional[List[str]] = None,
    pivot_column: str = None
) -> Tuple[dash_table.DataTable, str, str]:
    """
    """
    split_mode_value=line if split_mode == 'line' else insurer if split_mode == 'insurer' else metric
    logger.debug(f"df: {type(df)}")
    save_df_to_csv(df, f"{split_mode}_{insurer[0]}_before_transform.csv")
    transformer = TableTransformer()
    table_data = transformer.transform_table(df, split_mode, pivot_column)
    logger.debug(f"table_datalt: {type(table_data)}")
    save_df_to_csv(table_data, f"{split_mode}_{insurer[0]}_table_data1.csv")

    table_data = create_two_level_headers(table_data, pivot_column)
    logger.debug(f"table_datalt: {type(table_data)}")
    logger.debug(f"table_datalt: {table_data}")
    
    save_df_to_csv(table_data, f"{split_mode}_{insurer[0]}_table_data2.csv")
    logger.debug(f"split_mode: {split_mode}")
    logger.debug(f"columns: {table_data.columns}")
    columns_to_drop = {'insurer': 'insurer', 'line': 'line', 'metric_base': 'metric_base'}
    table_data = table_data.drop(columns=[columns_to_drop[split_mode]]) if split_mode in columns_to_drop and columns_to_drop[split_mode] in table_data.columns else df
    logger.debug(f"columns after: {table_data.columns}")
    

    save_df_to_csv(table_data, "table_data_after_drop.csv")    
    datatable = create_datatable(
        table_data,
        selected_metrics,
        period_type,
        show_market_share,
        show_change,
        show_rank,
        split_mode,
        line,
        insurer,
        metric,
        pivot_column
    )

    return dash_table.DataTable(**datatable)