from enum import Enum
from typing import Any, List, Optional, Dict
import time
from functools import wraps

import numpy as np
import pandas as pd
from dash_table.Format import Format, Scheme, Group

# Project-specific imports
from config.logging_config import get_logger
from constants.metrics import METRICS
from constants.translations import translate
from data_process.mappings import map_insurer, map_line

logger = get_logger(__name__)

# ---------------------------- Decorators ----------------------------


def timer(func):
    """Decorator to log entry/exit and timing for critical functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.debug(f"Entering function {func.__name__}")
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000
        logger.debug(f"Exiting function {func.__name__} (took {elapsed_ms:.2f}ms)")
        print(f"{func.__name__} took {elapsed_ms:.2f}ms to execute")
        return result
    return wrapper

# ---------------------------- Enums ----------------------------


class ColumnType(Enum):
    RANK = 'N'
    INSURER = 'insurer'
    CHANGE = 'change'
    LINE = 'linemain'
    DEFAULT = 'default'
    SECTION_HEADER = 'is_section_header'


class RowType(Enum):
    SECTION_HEADER = 'is_section_header'
    TOP = 'топ'
    MARKET_TOTAL = 'весь рынок'
    REGULAR = 'regular'

# ---------------------------- Constants ----------------------------

RANK_COL = 'N'
INSURER_COL = 'insurer'
SECTION_HEADER_COL = 'is_section_header'
LINE_COL = 'linemain'

YTD_FORMATS: Dict[str, str] = {
    '1': '3 мес.',
    '2': '1 пол.',
    '3': '9 мес.',
    '4': '12 мес.'
}

PERCENTAGE_INDICATORS = {'market_share', 'change', 'ratio', 'rate'}

METRIC_TYPE_UNITS = {
    'value': 'млрд. руб.',
    'average_value': 'тыс. руб.',
    'quantity': 'тыс. шт.',
    'ratio': '%',
    'default': 'млрд руб.'
}

COLUMNS = {
    ColumnType.RANK: {
        'width': '3.9rem',
        'min': '3.9rem',
        'max': '4rem',
        'align': 'center',
        'id': RANK_COL
    },
    ColumnType.INSURER: {
        'width': '17rem',
        'min': '17rem',
        'max': '40rem',
        'align': 'left',
        'id': INSURER_COL
    },
    ColumnType.DEFAULT: {
        'width': '6rem',
        'min': '3.5rem',
        'max': '6rem',
        'align': 'right'
    },
    ColumnType.LINE: {
        'width': 'max-content',
        'min': '14rem',
        'max': 'max-content',
        'align': 'left',
        'id': LINE_COL
    },
    ColumnType.CHANGE: {
        'width': '6rem',
        'min': '3.75rem',
        'max': '6rem',
        'align': 'center',
        'id': '_change'
    },
}

# Pre-calculate sorted metric keys for reuse
SORTED_METRICS = sorted(METRICS, key=len, reverse=True)

# ---------------------------- Helper Functions ----------------------------


def get_base_unit(metric: str) -> str:
    """Return the base unit for the metric."""
    logger.debug(f"Getting base unit for metric: {metric}")
    if metric not in METRICS:
        default_unit = METRIC_TYPE_UNITS['default']
        logger.debug(f"Metric not found. Returning default base unit: {default_unit}")
        return default_unit

    metric_type = METRICS[metric][2]
    base_unit = METRIC_TYPE_UNITS.get(metric_type, METRIC_TYPE_UNITS['default'])
    logger.debug(f"Base unit for metric '{metric}': {base_unit}")
    return base_unit


def _process_market_share_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process market share change columns:
      - Replace 0 or '-' with '-'
      - Otherwise, scale values by 100.
    """
    logger.debug("Processing market share change columns.")
    df_modified = df.copy()
    market_share_cols = df_modified.filter(like='market_share_change').columns
    if not market_share_cols.empty:
        logger.debug(f"Found market share change columns: {list(market_share_cols)}")
        df_modified[market_share_cols] = df_modified[market_share_cols].applymap(
            lambda val: '-' if val in (0, '-') else val * 100
        )
    logger.debug("Completed processing market share change columns.")
    return df_modified


def _get_identifier_config(col: str, split_mode: str, line: Optional[str] = None,
                             insurer: Optional[str] = None) -> Dict[str, Any]:
    """Generate configuration for identifier columns."""
    logger.debug(f"Generating identifier config for column '{col}' with split_mode '{split_mode}'")
    if col in [RANK_COL, INSURER_COL] and split_mode == 'line' and line:
        name = [map_line(line[0])] + [translate(col)] * 2
    elif col in [RANK_COL, LINE_COL] and split_mode == 'insurer' and insurer:
        name = [map_insurer(insurer[0])] + [translate(col)] * 2
    else:
        name = [translate(col)] * 3
    config = {"id": col, "name": name}
    logger.debug(f"Identifier config for '{col}': {config}")
    return config


def _get_metric_column_config(col: str, curr_metric: str, quarter: str,
                              period_type: str, all_columns: List[str]) -> Dict[str, Any]:
    """Generate configuration for metric columns with header and format."""
    logger.debug(f"Generating metric config for column '{col}'")
    is_change = 'change' in col
    is_market_share = 'market_share' in col

    if is_change:
        comparison = get_comparison_quarter(quarter, all_columns)
        if comparison:
            header = f"{format_period(quarter, period_type, True)} vs {format_period(comparison, period_type, True)}"
        else:
            header = format_period(quarter, period_type)
        base = 'Δ(п.п.)' if is_market_share else '%Δ'
    else:
        header = format_period(quarter, period_type)
        base = translate('market_share') if is_market_share else get_base_unit(curr_metric)

    config = {
        "id": col,
        "name": [translate(curr_metric), base, header],
        "type": "numeric",
        "format": get_column_format(col)
    }
    logger.debug(f"Metric column config for '{col}': {config}")
    return config


def _generate_column_configs(
    df: pd.DataFrame,
    split_mode: str,
    period_type: str,
    line: Optional[str] = None,
    insurer: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Generate full column configurations for the datatable."""
    logger.debug("Generating column configurations for datatable.")
    metric = next((m for m in SORTED_METRICS if any(col.startswith(m) for col in df.columns)), '')
    logger.debug(f"Extracted metric key: '{metric}'")
    if split_mode == 'line':
        column_order = [RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL]
    else:
        column_order = [LINE_COL, RANK_COL, INSURER_COL, SECTION_HEADER_COL]

    configs: List[Dict[str, Any]] = []
    # Process identifier columns
    for col in column_order:
        if col in df.columns and col != SECTION_HEADER_COL:
            configs.append(_get_identifier_config(col, split_mode, line, insurer))
    # Process metric columns
    for col in df.columns:
        if col not in {RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}:
            curr_metric = next((m for m in SORTED_METRICS if col.startswith(m)), '')
            quarter = col[len(curr_metric) + 1:].split('_')[-1] if curr_metric else ''
            configs.append(_get_metric_column_config(col, curr_metric, quarter, period_type, df.columns.tolist()))
    logger.debug("Completed generating column configurations.")
    return configs


def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """Format a quarter string into a human-readable period format."""
    logger.debug(f"Formatting period: quarter_str='{quarter_str}', period_type='{period_type}', comparison={comparison}")
    if not quarter_str or len(quarter_str) != 6:
        logger.debug(f"Invalid quarter format '{quarter_str}', returning as is.")
        return quarter_str
    try:
        year_short = quarter_str[2:4]
        quarter = quarter_str[5]
        if period_type == 'ytd':
            return year_short if comparison else f"{YTD_FORMATS.get(quarter, quarter)} {year_short}"
        if comparison and period_type in ['yoy_y', 'yoy_q']:
            return year_short
        return f"{quarter}кв." if comparison else f"{quarter} кв. {year_short}"
    except Exception as e:
        logger.error(f"Error in format_period: {e}", exc_info=True)
        return quarter_str


def get_comparison_quarter(current_quarter: str, columns: List[str]) -> Optional[str]:
    """Return a candidate comparison quarter for the given quarter."""
    logger.debug(f"Getting comparison quarter for '{current_quarter}'")
    if not current_quarter or len(current_quarter) < 6:
        logger.debug("No valid current quarter provided.")
        return None
    try:
        year, q_num = current_quarter[:4], current_quarter[5]
        candidates = [
            f"{int(year) - 1}Q{q_num}",  # Same quarter last year
            f"{year}Q{str(int(q_num) - 1)}" if q_num != '1' else f"{int(year) - 1}Q4"  # Previous quarter
        ]
        base_columns = [col for col in columns if '_change' not in col]
        for candidate in candidates:
            if any(candidate in col for col in base_columns):
                logger.info(f"Comparison quarter found: '{candidate}'")
                return candidate
        logger.debug(f"No comparison quarter found for '{current_quarter}'")
        return None
    except Exception as e:
        logger.error(f"Error in get_comparison_quarter: {e}", exc_info=True)
        return None


def get_column_format(col_name: str) -> Format:
    """Return the dash_table.Format configuration for the given column."""
    logger.debug(f"Getting column format for '{col_name}'")
    try:
        is_market_share_qtoq = 'market_share_change' in col_name
        is_percentage = any(ind in col_name for ind in PERCENTAGE_INDICATORS)
        fmt = Format(
            precision=2 if (is_percentage or is_market_share_qtoq) else 3,
            scheme=Scheme.fixed if (not is_percentage or is_market_share_qtoq) else Scheme.percentage,
            group=Group.yes,
            groups=3,
            group_delimiter=',',
            sign='+' if 'change' in col_name else ''
        )
        logger.debug(f"Format for '{col_name}': {fmt}")
        return fmt
    except Exception as e:
        logger.error(f"Error in get_column_format for '{col_name}': {e}", exc_info=True)
        return Format(
            precision=3,
            scheme=Scheme.fixed,
            group=Group.yes,
            groups=3,
            group_delimiter=','
        )


def get_column_type(col: str) -> ColumnType:
    """Determine and return the ColumnType for the given column identifier."""
    logger.debug(f"Determining column type for '{col}'")
    for col_type, config in COLUMNS.items():
        if config.get('id') == col:
            logger.debug(f"Exact match for column '{col}': {col_type}")
            return col_type
        elif col_type == ColumnType.CHANGE and config.get('id') in col:
            logger.debug(f"Matched change column for '{col}': {col_type}")
            return col_type
    logger.info(f"No specific type for column '{col}', defaulting to {ColumnType.DEFAULT}")
    return ColumnType.DEFAULT


def get_row_type(row: Dict[str, Any]) -> RowType:
    """Determine the row type based on its content."""
    logger.debug(f"Determining row type for row: {row}")
    if row.get(SECTION_HEADER_COL):
        logger.debug("Row identified as SECTION_HEADER")
        return RowType.SECTION_HEADER

    insurer_value = str(row.get(INSURER_COL, '')).lower()
    if RowType.TOP.value in insurer_value:
        logger.debug("Row identified as TOP")
        return RowType.TOP
    if insurer_value == RowType.MARKET_TOTAL.value:
        logger.debug("Row identified as MARKET_TOTAL")
        return RowType.MARKET_TOTAL

    logger.debug("Row identified as REGULAR")
    return RowType.REGULAR


def get_base_style() -> Dict[str, Dict[str, Any]]:
    """Return the base style configuration for the datatable."""
    return {
        'cell': {
            'fontFamily': 'Arial, -apple-system, system-ui, sans-serif',
            'fontSize': '0.85rem',
            'padding': '0.3rem',
            'boxSizing': 'border-box',
            'borderSpacing': '0',
            'borderCollapse': 'collapse'
        },
        'header': {
            'backgroundColor': '#3C5A99',
            'color': '#000000',
            'fontWeight': '600',
            'textAlign': 'center',
            'padding': '0rem'
        },
        'data': {
            'backgroundColor': '#ffffff',
            'color': '#212529'
        }
    }


def get_css_rules(df: pd.DataFrame) -> Dict[str, str]:
    """Return the CSS rules for the datatable layout and styling."""
    logger.debug("Generating CSS rules")
    dimension_rules = (
        "height: auto !important; "
        "min-height: 1.2rem; "
        "max-height: none !important; "
        "line-height: 1.4; "
        "box-sizing: border-box !important;"
    )
    text_rules = (
        "overflow: visible !important; "
        "text-overflow: clip !important; "
        "white-space: normal !important; "
        "word-wrap: break-word !important; "
        "box-sizing: border-box !important;"
    )
    rules = {
        '.dash-table-container .dash-spreadsheet': (
            "table-layout: fixed !important; width: 100% !important; "
            "max-width: 100% !important; border-collapse: collapse !important;"
        ),
        '.dash-table-container .dash-spreadsheet table': (
            "table-layout: fixed !important; width: 100% !important; max-width: 100% !important;"
        ),
        '.dash-table-container .dash-spreadsheet tr': (
            "width: 100% !important; max-width: 100% !important;"
        ),
        'th.dash-header.column-2': "border-bottom-width: 0 !important;",
        '.dash-header.column-2.cell--right-last': (
            "border-bottom-width: 0.05rem !important; background-color: '#FFFFFF' !important;"
        ),
        'th.dash-header.column-0': "border-top-width: 0 !important;",
        '.dash-spreadsheet tr, .dash-header, td.dash-cell, th.dash-header': (
            f"box-sizing: border-box !important; {dimension_rules} margin: 0 !important;"
        ),
        ('.dash-cell-value, .dash-header-cell-value, .unfocused, .dash-cell div, '
         '.dash-header div, .cell-markdown, .dash-cell *'): (
            f"box-sizing: border-box !important; {dimension_rules} {text_rules}"
        )
    }
    return rules


def _generate_header_styles_for_col(col: str, col_type: ColumnType) -> List[Dict[str, Any]]:
    """
    Generate header styling rules for a given column based on its type.
    This helper factors out the two header style variants.
    """
    base_style = {'backgroundColor': '#f8f9fa'}
    header_styles = []
    if col_type in {ColumnType.INSURER, ColumnType.LINE, ColumnType.RANK}:
        for idx in range(3):
            header_styles.append({
                'if': {'column_id': col, 'header_index': idx},
                **base_style,
                'textAlign': 'center' if (idx == 1 and col_type == ColumnType.RANK) else 'left',
                'verticalAlign': 'bottom',
                'paddingLeft': '15px' if idx == 0 else '3px',
                'marginBottom': '-10px' if idx == 1 else '3px',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'paddingTop': '3px',
                'min-height': 'auto',
                'height': 'auto',
                'whiteSpace': 'normal',
                'overflow': 'visible',
                'marginLeft': '6px',
                'borderTop': '0.5rem solid #D3D3D3' if idx == 1 else '0px',
                'borderBottom': '0.05rem solid #D3D3D3' if idx in (0, 2) else '0px',
                'borderLeft': '0.05rem solid #D3D3D3' if idx in (1, 2) else '0px',
                'color': '#000000' if idx in (0, 1) else 'transparent',
                'fontWeight': 'bold' if idx == 0 else 'normal',
                'backgroundColor': '#FFFFFF' if idx == 0 else '#f8f9fa',
                'borderRight': '0.05rem solid #D3D3D3'
            })
    else:
        header_bg = '#F0FDF4' if any(x in col for x in ['market_share', 'market_share_change']) else '#EFF6FF'
        for idx in range(3):
            header_styles.append({
                'if': {'column_id': col, 'header_index': idx},
                **base_style,
                'borderTop': '0.05rem solid #D3D3D3 !importa' if idx == 1 else '0px',
                'borderBottom': '0.05rem solid #D3D3D3' if idx in (0, 2) else '0px',
                'fontWeight': 'bold' if idx == 0 else 'normal',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderRight': '0.05rem solid #D3D3D3',
                'borderLeft': '0.05rem solid #D3D3D3',
                'backgroundColor': '#FFFFFF' if idx == 0 else header_bg
            })
    return header_styles


def generate_styles(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generate conditional styling rules for cells, headers, and data rows."""
    logger.debug("Entering generate_styles")
    styles = {'cell': [], 'data': [], 'header': []}

    # Generate cell and data styles based on each column's type
    for col in df.columns:
        col_type = get_column_type(col)
        config = COLUMNS.get(col_type, {})
        styles['cell'].append({
            'if': {'column_id': col},
            'minWidth': config.get('min'),
            'maxWidth': config.get('max'),
            'width': config.get('width'),
            'textAlign': config.get('align')
        })
        if col_type == ColumnType.RANK:
            # Positive gradient style
            styles['data'].append({
                'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(+"'},
                'backgroundImage': (
                    "linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), "
                    "rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), "
                    "transparent calc(50% + 3ch), transparent 100%)"
                )
            })
            # Negative gradient styles for various substring matches
            neg_styles = [
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                    'backgroundImage': (
                        "linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), "
                        "rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), "
                        "transparent calc(50% + 3ch), transparent 100%)"
                    )
                } for i in range(1, 10)
            ]
            styles['data'].extend(neg_styles)
        elif col_type == ColumnType.CHANGE:
            # Color-code positive and negative changes
            for op in ['>', '<']:
                styles['data'].append({
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                    'color': '#059669' if op == '>' else '#dc2626',
                    'fontWeight': 'normal',
                    'backgroundColor': '#f8f9fa'
                })

    # Row-based styling (e.g., for section headers or special rows)
    for idx, row in enumerate(df.to_dict('records')):
        row_type = get_row_type(row)
        if row_type != RowType.REGULAR:
            style = {'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
            if row_type == RowType.SECTION_HEADER:
                style.update({
                    'backgroundColor': '#E5E7EB',
                    'borderTop': '1px solid #E5E7EB',
                    'borderBottom': '1px solid #E5E7EB',
                    'paddingLeft': '0.8rem',
                    'color': '#374151'
                })
            styles['data'].append({'if': {'row_index': idx}, **style})

    # Header styles using the helper for clarity
    for col in df.columns:
        col_type = get_column_type(col)
        header_styles = _generate_header_styles_for_col(col, col_type)
        styles['header'].extend(header_styles)

    logger.debug("Exiting generate_styles")
    return styles


def generate_styles_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Helper to combine base style, conditional styles, and CSS rules."""
    base_styles = get_base_style()
    conditional_styles = generate_styles(df)
    css_rules = get_css_rules(df)
    return {
        'base': base_styles,
        'conditional': conditional_styles,
        'css': css_rules
    }

# ---------------------------- Datatable Configuration ----------------------------

@timer
def generate_datatable_config(
    df: pd.DataFrame,
    columns: List[Dict[str, Any]],
    show_market_share: bool,
    show_qtoq: bool
) -> Dict[str, Any]:
    """Generate the complete configuration for the datatable."""
    logger.debug("Entering generate_datatable_config")
    hidden_columns = [
        col for col in df.columns
        if col == SECTION_HEADER_COL or (
            get_column_type(col) not in {ColumnType.RANK, ColumnType.INSURER, ColumnType.LINE} and (
                ('market_share' in col and not show_market_share) or
                (get_column_type(col) == ColumnType.CHANGE and not show_qtoq)
            )
        )
    ]
    styles_config = generate_styles(df)
    base_styles = get_base_style()
    css_rules = get_css_rules(df)

    config = {
        'style_cell': base_styles['cell'],
        'style_header': base_styles['header'],
        'style_data': base_styles['data'],
        'style_cell_conditional': styles_config['cell'],
        'style_data_conditional': styles_config['data'],
        'style_header_conditional': styles_config['header'],
        'columns': [{**col, 'hideable': False, 'selectable': False,
                     'deletable': False, 'renamable': False} for col in columns],
        'hidden_columns': hidden_columns,
        'css': [{'selector': s, 'rule': r.strip()} for s, r in css_rules.items()],
        'sort_action': 'none',
        'sort_mode': None,
        'filter_action': 'none',
        'merge_duplicate_headers': True,
        'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
        'column_selectable': False,
        'row_selectable': False,
        'cell_selectable': True,
        'page_action': 'none',
        'editable': False
    }
    logger.debug("Exiting generate_datatable_config")
    return config

# ---------------------------- API (Backwards Compatible) ----------------------------

@timer
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
    """
    Create the datatable configuration.
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    logger.debug("Entering create_datatable")
    try:
        # Process market share change columns and generate column configs
        df_modified = _process_market_share_changes(df)
        columns = _generate_column_configs(df, split_mode, period_type, line, insurer)

        base_config = generate_datatable_config(
            df=df,
            columns=columns,
            show_market_share="show" in (toggle_show_market_share or []),
            show_qtoq="show" in (toggle_show_change or [])
        )

        # Inline helper to clean identifiers (supports lists/arrays)
        def clean_identifier(val):
            if isinstance(val, (list, np.ndarray)):
                val = '-'.join(val)
            return str(val).replace('\n', '').replace(' ', '')

        clean_line = clean_identifier(line)
        clean_insurer = clean_identifier(insurer)

        table_id = {
            'type': 'dynamic-table',
            'index': f"{split_mode}-{clean_line}-{clean_insurer}"
        }
        logger.debug(f"Generated table ID: {table_id}")

        final_config = {
            **base_config,
            'id': table_id,
            'style_data': {**base_config.get('style_data', {}), 'cursor': 'pointer'},
            'style_data_conditional': [
                *base_config.get('style_data_conditional', []),
                {
                    'if': {'state': 'active'},
                    'backgroundColor': 'rgba(0, 116, 217, 0.1)',
                }
            ],
            'data': df_modified.assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer) if 'insurer' in x.columns else '',
                linemain=lambda x: x['linemain'].fillna('').map(map_line) if 'linemain' in x.columns else ''
            ).to_dict('records')
        }
        logger.debug("Exiting create_datatable")
        return final_config

    except Exception as e:
        logger.error(f"Error in create_datatable: {e}", exc_info=True)
        raise