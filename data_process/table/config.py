from enum import Enum
from typing import Any, List, Optional, Dict

import pandas as pd

from config.logging_config import get_logger
from constants.metrics import METRICS
from constants.translations import translate
from data_process.mappings import map_insurer, map_line
from .formatters import format_period, get_comparison_quarter, get_column_format
from .generator import generate_datatable_config

logger = get_logger(__name__)

PLACE_COL = 'N'
INSURER_COL = 'insurer'
SECTION_HEADER_COL = 'is_section_header'
LINE_COL = 'linemain'

class ColumnType(Enum):
    RANK = 'rank'
    INSURER = 'insurer'
    CHANGE = 'change'
    LINE = 'linemain'
    DEFAULT = 'default'

def get_base_unit(metric: str) -> str:
    """Get the base unit for a metric based on its type."""
    if metric not in METRICS:
        return 'млрд руб.'
        
    metric_type = METRICS[metric][2]  # Get the type (third element in tuple)
    
    return {
        'value': 'млрд. руб.',
        'average_value': 'тыс. руб.',
        'quantity': 'тыс. шт.',
        'ratio': '%'
    }.get(metric_type, 'млрд руб.')

def create_datatable(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    period_type: str,
    toggle_show_market_share: Optional[List[str]] = None,
    toggle_show_change: Optional[List[str]] = None,
    split_mode: str = None,
    line: str = None,
    insurer: str = None

) -> Dict[str, Any]:
    """Generate complete table configuration."""
    logger.debug(f"Starting create_datatable with columns: {df.columns.tolist()}")

    # Process market share changes in a copy of the dataframe
    df_modified = df.copy()
    logger.debug("Processing market share changes")
    df_modified.update(
        df_modified.filter(like='market_share_change').apply(
            lambda x: x.apply(lambda y: '-' if y in (0, '-') else y * 100)
        )
    )

    # Extract metric for column grouping
    logger.debug("Extracting initial metric for column grouping")
    metric = next((m for m in sorted(METRICS, key=len)
                   if any(col.startswith(m) for col in df.columns)), '')
    logger.debug(f"Initial metric extracted: {metric}")

    # Generate column configurations
    columns = []
    logger.debug("Starting column configuration generation")

    # Replace the existing column order list with this conditional one:
    column_order = (
        [PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL] if split_mode == 'line' 
        else [LINE_COL, PLACE_COL, INSURER_COL, SECTION_HEADER_COL]
    )

    # Then use this order in the loop:
    for col in column_order:
        if col not in df.columns:
            continue

        logger.debug(f"Processing column: {col}")
        if col == SECTION_HEADER_COL:
            continue

        if col in [PLACE_COL, INSURER_COL] and split_mode == 'line':

            identifier_config = {
                "id": col,
                "name": [map_line(line[0])] + [translate(col)] * 2
            }

        elif col in [PLACE_COL, LINE_COL] and split_mode == 'insurer':

            identifier_config = {
                "id": col,
                "name": [map_insurer(insurer[0])] + [translate(col)] * 2
            }


        else:
            identifier_config = {
                "id": col,
                "name": [translate(col)] * 3
            }

        logger.debug(f"Generated identifier config for {col}: {identifier_config}")
        columns.append(identifier_config)

    for col in df.columns:
        if col in {PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}:
            logger.debug(f"Skipping already processed column: {col}")
            continue

        # Extract metric and quarter
        curr_metric = next((m for m in sorted(METRICS, key=len, reverse=True)
                            if col.startswith(m)), '')
        parts = col[len(curr_metric)+1:].split('_')
        quarter = parts[-1] if parts else ''

        logger.debug(f"Extracted metric: {curr_metric}, quarter: {quarter}")

        # Determine column type and format
        is_change = 'change' in col
        is_market_share = 'market_share' in col
        logger.debug(f"Column {col} - is_change: {is_change}, is_market_share: {is_market_share}")

        if is_change:
            comparison = get_comparison_quarter(quarter, df.columns)
            header = (f"{format_period(quarter, period_type, True)} vs "
                      f"{format_period(comparison, period_type, True)}"
                      if comparison else format_period(quarter, period_type))
            base = 'Δ(п.п.)' if is_market_share else '%Δ'

        else:
            header = format_period(quarter, period_type)
            base = translate('market_share') if is_market_share else get_base_unit(curr_metric)

        column_config = {
            "id": col,
            "name": [translate(curr_metric), base, header],
            "type": "numeric",
            "format": get_column_format(col)
        }
        logger.debug(f"Generated column config for {col}: {column_config}")
        columns.append(column_config)

    logger.debug("Generating final configuration")

    final_config = {
        **generate_datatable_config(
            df=df,
            columns=columns,
            show_market_share="show" in (toggle_show_market_share or []),
            show_qtoq="show" in (toggle_show_change or [])
        ),
        'data': (df_modified
            .assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer) if 'insurer' in x.columns else '',
                linemain=lambda x: x['linemain'].fillna('').map(map_line) if 'linemain' in x.columns else ''
            )
            .to_dict('records')
        )
    }

    logger.debug("Final configuration generated")
    logger.debug("Column configurations in final output:")
    for col in final_config['columns']:
        logger.debug(f"Column {col['id']}: {col['name']}")

    # Log sample of processed data
    logger.debug("Sample of processed data:")
    if not df_modified.empty:
        logger.debug(df_modified.head().to_dict('records'))

    return final_config