import pandas as pd
from typing import Any, List, Dict, Literal, TypedDict
from enum import Enum
from config.logging_config import get_logger

logger = get_logger(__name__)

# Type definitions for better type safety
StyleDict = Dict[str, Any]
ColumnId = str
RowIndex = int

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

# Dimension constants
DIMENSIONS = {
    'row': {
        'height': '13px',
        'padding': '0.1rem',
        'font_size': '0.75rem',
    },
    'widths': {
        'rank': {'min': '50px', 'max': '60px'},
        'insurer': {'min': '175px', 'max': '200px'},
        'default': {'min': 'none', 'max': 'auto'}
    }
}

# Color constants
COLORS = {
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



# Base styles with consolidated dimensions
BASE_STYLES = {
    'table': {
        'overflowX': 'auto',
        'width': '100%',
        'maxWidth': '100%',
    },
    'cell': {
        'fontFamily': 'Arial, -apple-system, system-ui, sans-serif',
        'fontSize': DIMENSIONS['row']['font_size'],
        'padding': '0',
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'boxSizing': 'border-box',
        'borderSpacing': '0',
        'borderCollapse': 'collapse',
        'borderWidth': '0.2px',
        'width': '100%',
        'maxWidth': '100%',
        'height': DIMENSIONS['row']['height'],
        'minHeight': DIMENSIONS['row']['height'],
        'maxHeight': DIMENSIONS['row']['height'],
        'lineHeight': DIMENSIONS['row']['height'],
    },
    'header': {
        'backgroundColor': COLORS['primary'],
        'color': '#000000',
        'fontWeight': '600',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'padding': DIMENSIONS['row']['padding'],
        'height': DIMENSIONS['row']['height'],
        'minHeight': DIMENSIONS['row']['height'],
        'maxHeight': DIMENSIONS['row']['height'],
        'lineHeight': DIMENSIONS['row']['height'],
    },
}

# Column configurations
COLUMN_CONFIGS = {
    ColumnType.RANK: {
        'width': 'fit-content',
        'minWidth': DIMENSIONS['widths']['rank']['min'],
        'maxWidth': DIMENSIONS['widths']['rank']['max'],
        'textAlign': 'center',
        'column_id': 'N'
    },
    ColumnType.INSURER: {
        'width': 'fit-content',
        'minWidth': DIMENSIONS['widths']['insurer']['min'],
        'maxWidth': DIMENSIONS['widths']['insurer']['max'],
        'textAlign': 'left',
        'column_id': 'insurer'
    },
    ColumnType.CHANGE: {
        'width': 'fit-content',
        'minWidth': DIMENSIONS['widths']['default']['min'],
        'maxWidth': DIMENSIONS['widths']['default']['max'],
        'textAlign': 'center',
        'identifier': '_q_to_q_change'
    },
    ColumnType.DEFAULT: {
        'width': 'fit-content',
        'minWidth': DIMENSIONS['widths']['default']['min'],
        'maxWidth': DIMENSIONS['widths']['default']['max'],
        'textAlign': 'right'
    }
}

# Row configurations
ROW_CONFIGS = {
    RowType.SECTION_HEADER: {
        'backgroundColor': COLORS['section_bg'],
        'fontWeight': 'bold',
        'borderTop': f'2px solid {COLORS["section_bg"]}',
        'borderBottom': f'2px solid {COLORS["section_bg"]}',
        'paddingLeft': '8px',
        'fontSize': DIMENSIONS['row']['font_size'],
        'color': COLORS['section_text'],
        'height': DIMENSIONS['row']['height']
    },
    RowType.TOP: {
        'backgroundColor': COLORS['row_bg'],
        'fontWeight': 'bold'
    },
    RowType.MARKET_TOTAL: {
        'backgroundColor': COLORS['row_bg'],
        'fontWeight': 'bold'
    },
    RowType.REGULAR: {}
}

def _get_column_type(col: str) -> ColumnType:
    """Determine column type based on column name."""
    col_map = {
        COLUMN_CONFIGS[ColumnType.RANK]['column_id']: ColumnType.RANK,
        COLUMN_CONFIGS[ColumnType.INSURER]['column_id']: ColumnType.INSURER
    }
    
    if col in col_map:
        return col_map[col]
    
    if COLUMN_CONFIGS[ColumnType.CHANGE]['identifier'] in col:
        return ColumnType.CHANGE
        
    return ColumnType.DEFAULT

def _get_row_type(row: Dict[str, Any]) -> RowType:
    """Determine row type based on row data."""
    insurer_name = row.get('insurer', '')
    
    if row.get('is_section_header'):
        return RowType.SECTION_HEADER
    if 'top' in insurer_name:
        return RowType.TOP
    if insurer_name == 'total':
        return RowType.MARKET_TOTAL
    return RowType.REGULAR

def _create_style_conditions(df: pd.DataFrame) -> Dict[str, List[StyleDict]]:
    """Generate all conditional styles for the table."""
    styles = {
        'cell': [],
        'data': [],
        'header': []
    }
    
    # Cell styles
    for col in df.columns:
        col_type = _get_column_type(col)
        styles['cell'].append({
            'if': {'column_id': col},
            **{k: v for k, v in COLUMN_CONFIGS[col_type].items() 
               if k not in ['column_id', 'identifier']}
        })
    
    # Data styles
    for col in df.columns:
        col_type = _get_column_type(col)
        
        if col_type == ColumnType.RANK:
            styles['data'].extend([
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
            styles['data'].extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                    'color': color,
                    'fontWeight': 'normal',
                    'backgroundColor': COLORS['row_bg']
                } for op, color in [('>', COLORS['success']), ('<', COLORS['error'])]
            ])
    
    # Row-based styles
    for idx, row in enumerate(df.to_dict('records')):
        row_type = _get_row_type(row)
        if row_type != RowType.REGULAR:
            styles['data'].append({
                'if': {'row_index': idx},
                **ROW_CONFIGS[row_type]
            })
    
    # Header styles
    for col in df.columns:
        col_type = _get_column_type(col)
        
        if col_type in {ColumnType.RANK, ColumnType.INSURER}:
            styles['header'].extend([{
                'if': {'column_id': col, 'header_index': idx},
                'textAlign': 'left' if col_type == ColumnType.INSURER else 'center',
                'verticalAlign': 'middle',
                'height': '100%',
                'backgroundColor': COLORS['row_bg'],
                "borderTop": f"1px solid '#e9ecef'" if idx == 0 else "0px",
                "borderBottom": f"1px solid '#e9ecef'" if idx == 2 else "0px",                
                'color': '#000000' if idx == 1 else 'transparent',
                'fontWeight': 'bold',
            } for idx in range(3)])
        else:
            background = (
                COLORS['row_bg'] if idx == 0 else
                COLORS['header_bg']['market_share'] if any(x in col for x in ['market_share', 'market_share_q_to_q_change']) else
                COLORS['header_bg']['change']
            )
            
            styles['header'].extend([{
                'if': {'column_id': col, 'header_index': idx},
                'fontWeight': 'bold' if idx == 0 else 'normal',
                'textAlign': 'center',
                'backgroundColor': background
            } for idx in range(3)])
    
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
    conditional_styles = _create_style_conditions(df)
    
    # Hidden columns logic
    hidden_columns = [
        col for col in df.columns
        if col == 'is_section_header' or (
            _get_column_type(col) not in {ColumnType.RANK, ColumnType.INSURER} and (
                ('market_share' in col and not show_market_share) or
                (_get_column_type(col) == ColumnType.CHANGE and not show_qtoq)
            )
        )
    ]
    
    dimension_rules = (
        'box-sizing: border-box !important; '
        f'height: {DIMENSIONS["row"]["height"]} !important; '
        f'min-height: {DIMENSIONS["row"]["height"]} !important; '
        f'max-height: {DIMENSIONS["row"]["height"]} !important; '
        f'line-height: {DIMENSIONS["row"]["height"]} !important; '
        'padding: 0 !important; '
        'margin: 0 !important; '
    )

    content_rules = (
        'box-sizing: border-box !important; '
        f'height: {DIMENSIONS["row"]["height"]} !important; '
        f'min-height: {DIMENSIONS["row"]["height"]} !important; '
        f'max-height: {DIMENSIONS["row"]["height"]} !important; '
        f'line-height: {DIMENSIONS["row"]["height"]} !important; '
        'padding: 0 !important; '
        'margin: 0 !important; '
        'overflow: hidden !important; '
        'text-overflow: ellipsis !important; '
        'white-space: nowrap !important;'
    )
    
    css_rules = [
        {'selector': '.dash-table-container', 'rule': 'max-width: 100%; width: 100%; margin: 0; padding: 0; border-spacing: 0 !important;'},
        {'selector': '.dash-spreadsheet', 'rule': 'max-width: 100%; width: 100%; border-collapse: collapse !important;'},
        {'selector': '.dash-spreadsheet tr', 'rule': dimension_rules},
        {'selector': '.dash-cell', 'rule': f'max-width: 100%; width: auto; {dimension_rules}'},
        {'selector': '.dash-header', 'rule': dimension_rules},
        {'selector': '.dash-cell-value', 'rule': content_rules},
        {'selector': '.dash-header-cell-value', 'rule': content_rules},
        {'selector': '.unfocused', 'rule': content_rules},
        {'selector': '.dash-cell div', 'rule': content_rules},
        {'selector': '.dash-header div', 'rule': content_rules},
        {'selector': '.cell-markdown', 'rule': content_rules},
        {'selector': '.dash-cell *', 'rule': content_rules},
        {'selector': 'td.dash-cell', 'rule': dimension_rules},
        {'selector': 'th.dash-header', 'rule': dimension_rules}
    ]
    
    return {
        # Base styles
        'style_table': BASE_STYLES['table'],
        'style_cell': BASE_STYLES['cell'],
        'style_header': BASE_STYLES['header'],
        'style_data': {'backgroundColor': '#ffffff', 'color': COLORS['text']},
        
        # Conditional styles
        'style_cell_conditional': conditional_styles['cell'],
        'style_data_conditional': conditional_styles['data'],
        'style_header_conditional': conditional_styles['header'],
        
        # Column configuration
        'columns': [{
            **col,
            "hideable": False,
            "selectable": False,
            "deletable": False,
            "renamable": False
        } for col in columns],
        'hidden_columns': hidden_columns,
        
        # Additional settings
        'css': css_rules,
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