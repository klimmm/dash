from enum import Enum
from functools import wraps
import time
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List

from dash_table.Format import Format, Scheme, Group

from config.logging_config import get_logger
from constants.translations import translate
from data_process.mappings import map_insurer, map_line
from constants.metrics import METRICS

logger = get_logger(__name__)

# --- Constants & Enumerations ---

PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'
RANK_COL = 'N'


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

# --- Decorator ---

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


def get_base_unit(metric: str) -> str:
    """Returns the base unit for the specified metric."""
    logger.debug(f"Getting base unit for metric: {metric}")
    if metric not in METRICS:
        default_unit = METRIC_TYPE_UNITS['default']
        logger.debug(f"Metric '{metric}' not found; using default unit: {default_unit}")
        return default_unit
    metric_type = METRICS[metric][2]
    base_unit = METRIC_TYPE_UNITS.get(metric_type, METRIC_TYPE_UNITS['default'])
    logger.debug(f"Base unit for metric '{metric}': {base_unit}")
    return base_unit


def _process_market_share_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes market share change columns:
      - Replaces 0 or '-' with '-'
      - Otherwise scales values by 100.
    """
    logger.debug("Processing market share change columns")
    df_modified = df.copy()
    market_share_cols = df_modified.filter(like='market_share_change').columns
    if not market_share_cols.empty:
        for col in market_share_cols:
            df_modified[col] = df_modified[col].map(
                lambda val: '-' if val in (0, '-') else val * 100
            )
    logger.debug("Completed market share change processing")
    return df_modified


def _get_identifier_config(col: str, split_mode: str, line: Optional[str] = None, insurer: Optional[str] = None) -> Dict[str, Any]:
    """Generates configuration for identifier columns."""
    if col in [RANK_COL, INSURER_COL] and split_mode == 'line' and line:
        name = [map_line(line[0]), translate(col), translate(col)]
    elif col in [RANK_COL, LINE_COL] and split_mode == 'insurer' and insurer:
        name = [map_insurer(insurer[0]), translate(col), translate(col)]
    else:
        name = [translate(col)] * 3
    config = {"id": col, "name": name}
    logger.debug(f"Identifier config for '{col}': {config}")
    return config


def _get_metric_column_config(col: str, curr_metric: str, quarter: str, period_type: str, all_columns: List[str]) -> Dict[str, Any]:
    """Generates configuration for metric columns with header and format."""
    is_change = 'change' in col
    is_market_share = 'market_share' in col
    if is_change:
        comparison = get_comparison_quarter(quarter, all_columns)
        header = f"{format_period(quarter, period_type, True)} vs {format_period(comparison, period_type, True)}" if comparison else format_period(quarter, period_type)
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
    """Generates full column configurations for the datatable."""
    logger.debug("Generating column configurations")
    metric = next((m for m in SORTED_METRICS if any(col.startswith(m) for col in df.columns)), '')
    column_order = [RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL] if split_mode == 'line' else [LINE_COL, RANK_COL, INSURER_COL, SECTION_HEADER_COL]
    configs: List[Dict[str, Any]] = []
    for col in column_order:
        if col in df.columns and col != SECTION_HEADER_COL:
            configs.append(_get_identifier_config(col, split_mode, line, insurer))
    for col in df.columns:
        if col not in {RANK_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL}:
            curr_metric = next((m for m in SORTED_METRICS if col.startswith(m)), '')
            quarter = col[len(curr_metric)+1:].split('_')[-1] if curr_metric else ''
            configs.append(_get_metric_column_config(col, curr_metric, quarter, period_type, list(df.columns)))
    logger.debug("Completed column configuration generation")
    return configs


def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """Formats a quarter string into a human-readable period."""
    logger.debug(f"Formatting period: {quarter_str}, type: {period_type}, comparison: {comparison}")
    if not quarter_str or len(quarter_str) != 6:
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
    """Returns a candidate comparison quarter for the given quarter."""
    logger.debug(f"Getting comparison quarter for {current_quarter}")
    if not current_quarter or len(current_quarter) < 6:
        return None
    try:
        year, q_num = current_quarter[:4], current_quarter[5]
        candidates = [
            f"{int(year)-1}Q{q_num}",
            f"{year}Q{str(int(q_num)-1)}" if q_num != '1' else f"{int(year)-1}Q4"
        ]
        base_columns = [col for col in columns if '_change' not in col]
        for candidate in candidates:
            if any(candidate in col for col in base_columns):
                logger.info(f"Found comparison quarter: {candidate}")
                return candidate
        return None
    except Exception as e:
        logger.error(f"Error in get_comparison_quarter: {e}", exc_info=True)
        return None


def get_column_format(col_name: str) -> Format:
    """Returns the dash_table.Format configuration for the given column."""
    logger.debug(f"Getting column format for {col_name}")
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
        return fmt
    except Exception as e:
        logger.error(f"Error in get_column_format for '{col_name}': {e}", exc_info=True)
        return Format(precision=3, scheme=Scheme.fixed, group=Group.yes, groups=3, group_delimiter=',')


def get_column_type(col: str) -> ColumnType:
    """Determines and returns the ColumnType for the given column identifier."""
    logger.debug(f"Determining column type for {col}")
    for col_type, config in COLUMNS.items():
        if config.get('id') == col:
            return col_type
        elif col_type == ColumnType.CHANGE and config.get('id') in col:
            return col_type
    return ColumnType.DEFAULT


def get_row_type(row: Dict[str, Any]) -> RowType:
    """Determines the row type based on its content."""
    if row.get(SECTION_HEADER_COL):
        return RowType.SECTION_HEADER
    insurer_value = str(row.get(INSURER_COL, '')).lower()
    if RowType.TOP.value in insurer_value:
        return RowType.TOP
    if insurer_value == RowType.MARKET_TOTAL.value:
        return RowType.MARKET_TOTAL
    return RowType.REGULAR


def get_base_style() -> Dict[str, Dict[str, Any]]:
    """Returns the base style configuration for the datatable."""
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
    """Returns the CSS rules for the datatable layout."""
    dimension_rules = (
        "height: auto !important; min-height: 1.2rem; max-height: none !important; "
        "line-height: 1.4; box-sizing: border-box !important;"
    )
    text_rules = (
        "overflow: visible !important; text-overflow: clip !important; white-space: normal !important; "
        "word-wrap: break-word !important; box-sizing: border-box !important;"
    )
    return {
        '.dash-table-container .dash-spreadsheet': (
            "table-layout: fixed !important; width: 100% !important; max-width: 100% !important; "
            "border-collapse: collapse !important;"
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
        '.dash-cell-value, .dash-header-cell-value, .unfocused, .dash-cell div, '
        '.dash-header div, .cell-markdown, .dash-cell *': (
            f"box-sizing: border-box !important; {dimension_rules} {text_rules}"
        )
    }


def _generate_header_styles_for_col(col: str, col_type: ColumnType) -> List[Dict[str, Any]]:
    """
    Generates header styling rules for a given column based on its type.
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
                'borderTop': '0.05rem solid #D3D3D3' if idx == 1 else '0px',
                'borderBottom': '0.05rem solid #D3D3D3' if idx in (0, 2) else '0px',
                'fontWeight': 'bold' if idx == 0 else 'normal',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderRight': '0.05rem solid #D3D3D3',
                'borderLeft': '0.05rem solid #D3D3D3',
                'backgroundColor': '#FFFFFF' if idx == 0 else header_bg
            })
    return header_styles


def generate_styles(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generates conditional styling rules for cells, headers, and data rows."""
    logger.debug("Generating conditional styles")
    styles = {'cell': [], 'data': [], 'header': []}

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
            styles['data'].append({
                'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(+"'},
                'backgroundImage': (
                    "linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), "
                    "rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), "
                    "transparent calc(50% + 3ch), transparent 100%)"
                )
            })
            neg_styles = [{
                'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                'backgroundImage': (
                    "linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), "
                    "rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), "
                    "transparent calc(50% + 3ch), transparent 100%)"
                )
            } for i in range(1, 10)]
            styles['data'].extend(neg_styles)
        elif col_type == ColumnType.CHANGE:
            for op in ['>', '<']:
                styles['data'].append({
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                    'color': '#059669' if op == '>' else '#dc2626',
                    'fontWeight': 'normal',
                    'backgroundColor': '#f8f9fa'
                })

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

    for col in df.columns:
        col_type = get_column_type(col)
        header_styles = _generate_header_styles_for_col(col, col_type)
        styles['header'].extend(header_styles)

    logger.debug("Conditional styles generation complete")
    return styles

def generate_styles_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Combines base style, conditional styles, and CSS rules into one configuration."""
    base_styles = get_base_style()
    conditional_styles = generate_styles(df)
    css_rules = get_css_rules(df)
    return {
        'base': base_styles,
        'conditional': conditional_styles,
        'css': css_rules
    }


@timer
def generate_datatable_config(
    df: pd.DataFrame,
    columns: List[Dict[str, Any]],
    show_market_share: bool,
    show_qtoq: bool
) -> Dict[str, Any]:
    """Generates the complete configuration for the datatable."""
    logger.debug("Generating datatable configuration")
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
        'columns': [{**col, 'hideable': False, 'selectable': False, 'deletable': False, 'renamable': False} for col in columns],
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
    logger.debug("Datatable configuration generated")
    return config


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
    Creates the datatable configuration.
    """
    logger.debug("Creating datatable")
    try:
        df_modified = _process_market_share_changes(df)
        columns = _generate_column_configs(df, split_mode, period_type, line, insurer)
        base_config = generate_datatable_config(
            df=df,
            columns=columns,
            show_market_share="show" in (toggle_show_market_share or []),
            show_qtoq="show" in (toggle_show_change or [])
        )
        # Clean identifier helper.
        def clean_identifier(val):
            if isinstance(val, (list, np.ndarray)):
                return '-'.join(val)
            return str(val).replace('\n', '').replace(' ', '')
        clean_line = clean_identifier(line)
        clean_insurer = clean_identifier(insurer)
        table_id = {'type': 'dynamic-table', 'index': f"{split_mode}-{clean_line}-{clean_insurer}"}
        final_config = {
            **base_config,
            'id': table_id,
            'style_data': {**base_config.get('style_data', {}), 'cursor': 'pointer'},
            'style_data_conditional': [
                *base_config.get('style_data_conditional', []),
                {'if': {'state': 'active'}, 'backgroundColor': 'rgba(0, 116, 217, 0.1)'}
            ],
            'data': df_modified.assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer) if 'insurer' in x.columns else '',
                linemain=lambda x: x['linemain'].fillna('').map(map_line) if 'linemain' in x.columns else ''
            ).to_dict('records')
        }
        logger.debug("Datatable created")
        return final_config
    except Exception as e:
        logger.error(f"Error in create_datatable: {e}", exc_info=True)
        raise