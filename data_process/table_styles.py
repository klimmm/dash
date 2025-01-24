import pandas as pd
from typing import Any, Dict, List, TypedDict
from enum import Enum
from config.logging_config import get_logger

logger = get_logger(__name__)

class ColumnType(Enum):
    RANK = 'rank'
    INSURER = 'insurer'
    CHANGE = 'change'
    DEFAULT = 'default'

class RowType(Enum):
    SECTION_HEADER = 'section_header'
    TOP = 'top'
    MARKET_TOTAL = 'market_total'
    REGULAR = 'regular'

# Consolidated style constants
STYLES = {
    'dimensions': {
        'row': {
            'height': '15px',
            'padding': '0.4rem',
            'font_size': '0.875rem'
        },
        'column': {
            'rank': {'min': '50px', 'max': '50px'},
            'insurer': {'min': '175px', 'max': '200px'},
            'default': {'min': 'none', 'max': 'auto'}
        }
    },
    'colors': {
        'primary': '#3C5A99',
        'border': '#e9ecef',
        'section_bg': '#E5E7EB',
        'section_text': '#374151',
        'row_bg': '#f8f9fa',
        'text': '#212529',
        'success': '#059669',
        'error': '#dc2626',
        'header_bg': {
            'market_share': '#F0FDF4',
            'change': '#EFF6FF',
            'default': 'inherit'
        }
    }
}

# Column type configurations
COLUMN_CONFIGS = {
    ColumnType.RANK: {'width': 'fit-content', 'minWidth': '45px', 'maxWidth': '50px', 
                     'textAlign': 'center', 'column_id': 'N'},
    ColumnType.INSURER: {'width': 'fit-content', 'minWidth': '175px', 'maxWidth': '200px', 
                        'textAlign': 'left', 'column_id': 'insurer'},
    ColumnType.CHANGE: {'width': 'fit-content', 'minWidth': 'none', 'maxWidth': 'auto', 
                       'textAlign': 'center', 'identifier': '_q_to_q_change'},
    ColumnType.DEFAULT: {'width': 'fit-content', 'minWidth': 'none', 'maxWidth': 'auto', 
                        'textAlign': 'right'}
}

# Row type configurations
ROW_CONFIGS = {
    RowType.SECTION_HEADER: {
        'backgroundColor': STYLES['colors']['section_bg'],
        'fontWeight': 'bold',
        'borderTop': f'1px solid {STYLES["colors"]["section_bg"]}',
        'borderBottom': f'1px solid {STYLES["colors"]["section_bg"]}',
        'paddingLeft': '8px',
        'fontSize': STYLES['dimensions']['row']['font_size'],
        'color': STYLES['colors']['section_text'],
        'height': STYLES['dimensions']['row']['height']
    },
    RowType.TOP: {'backgroundColor': STYLES['colors']['row_bg'], 'fontWeight': 'bold'},
    RowType.MARKET_TOTAL: {'backgroundColor': STYLES['colors']['row_bg'], 'fontWeight': 'bold'},
    RowType.REGULAR: {}
}

def _get_dimension_rules() -> str:
    """Generate common dimension CSS rules."""
    height = STYLES['dimensions']['row']['height']
    return (
        'box-sizing: border-box !important; '
        f'height: {height} !important; '
        f'min-height: {height} !important; '
        f'max-height: {height} !important; '
        f'line-height: {height} !important; '
        'margin: 0 !important; '
        'borderWidth: 0.1px !important;'
    )

def _get_content_rules() -> str:
    """Generate common content CSS rules."""
    height = STYLES['dimensions']['row']['height']
    return (
        'box-sizing: border-box !important; '
        f'height: {height} !important; '
        f'min-height: {height} !important; '
        f'max-height: {height} !important; '
        f'line-height: {height} !important; '
        'overflow: hidden !important; '
        'text-overflow: ellipsis !important; '
        'white-space: nowrap !important;'
    )

def _get_column_type(col: str) -> ColumnType:
    """Determine column type based on column name."""
    if col == COLUMN_CONFIGS[ColumnType.RANK]['column_id']:
        return ColumnType.RANK
    if col == COLUMN_CONFIGS[ColumnType.INSURER]['column_id']:
        return ColumnType.INSURER
    if COLUMN_CONFIGS[ColumnType.CHANGE]['identifier'] in col:
        return ColumnType.CHANGE
    return ColumnType.DEFAULT

def _get_row_type(row: Dict[str, Any]) -> RowType:
    """Determine row type based on row data."""
    if row.get('is_section_header'):
        return RowType.SECTION_HEADER
    insurer = row.get('insurer', '')
    if 'top' in insurer:
        return RowType.TOP
    if insurer == 'total':
        return RowType.MARKET_TOTAL
    return RowType.REGULAR

def _get_cell_styles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate cell-specific styles."""
    return [
        {
            'if': {'column_id': col},
            **{k: v for k, v in COLUMN_CONFIGS[_get_column_type(col)].items() 
               if k not in ['column_id', 'identifier']}
        }
        for col in df.columns
    ]

def _get_data_styles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate data-specific styles."""
    styles = []
    
    # Column-based styles
    for col in df.columns:
        col_type = _get_column_type(col)
        
        if col_type == ColumnType.RANK:
            styles.extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(+"'},
                    'backgroundImage': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'
                },
                *[{
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                    'backgroundImage': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'
                } for i in range(1, 10)]
            ])
        elif col_type == ColumnType.CHANGE:
            styles.extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                    'color': STYLES['colors']['success' if op == '>' else 'error'],
                    'fontWeight': 'normal',
                    'backgroundColor': STYLES['colors']['row_bg']
                }
                for op in ['>', '<']
            ])
    
    # Row-based styles
    styles.extend([
        {
            'if': {'row_index': idx},
            **ROW_CONFIGS[_get_row_type(row)]
        }
        for idx, row in enumerate(df.to_dict('records'))
        if _get_row_type(row) != RowType.REGULAR
    ])
    
    return styles

def _get_header_styles(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate header-specific styles."""
    styles = []
    
    for col in df.columns:
        col_type = _get_column_type(col)
        
        if col_type in {ColumnType.RANK, ColumnType.INSURER}:
            styles.extend([
                {
                    'if': {'column_id': col, 'header_index': idx},
                    'textAlign': 'left' if col_type == ColumnType.INSURER else 'center',
                    'verticalAlign': 'middle',
                    'backgroundColor': STYLES['colors']['row_bg'],
                    'borderTop': f"0.1px solid {STYLES['colors']['border']}" if idx == 0 else "0px",
                    'borderBottom': f"0.1px solid {STYLES['colors']['border']}" if idx == 2 else "0px",
                    'color': '#000000' if idx == 1 else 'transparent',
                    'fontWeight': 'bold',
                }
                for idx in range(3)
            ])
        else:
            styles.extend([
                {
                    'if': {'column_id': col, 'header_index': idx},
                    'fontWeight': 'bold' if idx == 0 else 'normal',
                    'textAlign': 'center',
                    'backgroundColor': (
                        STYLES['colors']['row_bg'] if idx == 0
                        else STYLES['colors']['header_bg']['market_share'] if any(x in col for x in ['market_share', 'market_share_q_to_q_change'])
                        else STYLES['colors']['header_bg']['change']
                    )
                }
                for idx in range(3)
            ])
    
    return styles

def generate_table_config(
    df: pd.DataFrame,
    columns: List[Dict[str, Any]],
    show_market_share: bool,
    show_qtoq: bool
) -> Dict[str, Any]:
    """
    Generate table configuration with styles and formatting.
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    hidden_columns = [
        col for col in df.columns
        if col == 'is_section_header' or (
            _get_column_type(col) not in {ColumnType.RANK, ColumnType.INSURER} and (
                ('market_share' in col and not show_market_share) or
                (_get_column_type(col) == ColumnType.CHANGE and not show_qtoq)
            )
        )
    ]
    
    base_cell_style = {
        'fontFamily': 'Arial, -apple-system, system-ui, sans-serif',
        'fontSize': STYLES['dimensions']['row']['font_size'],
        'padding': STYLES['dimensions']['row']['padding'],
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'boxSizing': 'border-box',
        'borderSpacing': '0',
        'borderCollapse': 'collapse',
        'borderWidth': '0.1px',
        'height': STYLES['dimensions']['row']['height'],
        'minHeight': STYLES['dimensions']['row']['height'],
        'maxHeight': STYLES['dimensions']['row']['height'],
        'lineHeight': STYLES['dimensions']['row']['height'],
    }
    
    dimension_rules = _get_dimension_rules()
    content_rules = _get_content_rules()
    
    return {
        'style_table': {'overflowX': 'auto', 'width': '100%', 'maxWidth': '100%'},
        'style_cell': base_cell_style,
        'style_header': {
            'backgroundColor': STYLES['colors']['primary'],
            'color': '#000000',
            'fontWeight': '600',
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'padding': '0rem',
            **{k: v for k, v in base_cell_style.items() if k.startswith(('height', 'min', 'max', 'line'))}
        },
        'style_data': {'backgroundColor': '#ffffff', 'color': STYLES['colors']['text']},
        'style_cell_conditional': _get_cell_styles(df),
        'style_data_conditional': _get_data_styles(df),
        'style_header_conditional': _get_header_styles(df),
        'columns': [{**col, 'hideable': False, 'selectable': False, 
                    'deletable': False, 'renamable': False} for col in columns],
        'hidden_columns': hidden_columns,
        'css': [
            {'selector': '.dash-table-container', 
             'rule': 'max-width: 100%; width: fit-content; margin: 0; padding: 0; border-spacing: 0 !important;'},
            {'selector': '.dash-spreadsheet', 
             'rule': 'max-width: 100%; width: 100%; border-collapse: collapse !important;'},
            {'selector': '.dash-spreadsheet tr', 'rule': dimension_rules},
            *[{'selector': selector, 'rule': dimension_rules} 
              for selector in ['.dash-header', 'td.dash-cell', 'th.dash-header']],
            *[{'selector': selector, 'rule': content_rules} 
              for selector in ['.dash-cell-value', '.dash-header-cell-value', '.unfocused',
                             '.dash-cell div', '.dash-header div', '.cell-markdown', '.dash-cell *']],
        ],
        'sort_action': 'none',
        'sort_mode': None,
        'filter_action': 'none',
        'merge_duplicate_headers': True,
        'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
        'column_selectable': False,
        'row_selectable': False,
        'cell_selectable': False,
        'page_action': 'none',
        'editable': False
    }