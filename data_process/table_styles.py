import pandas as pd
from typing import Any, Dict, List
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

# Base style configurations
BASE_STYLES = {
    'dimensions': {
        'height': '1.2rem',  # 15px
        'padding': '0.3rem',
        'font_size': '0.875rem',
        'section_padding': '0.5rem',  # 8px
        'border_width': '0.0625rem',  # 1px
        'zero': '0rem'
    },
    'colors': {
        'primary': '#3C5A99',
        'border': '#D3D3D3',
        'section_bg': '#E5E7EB',
        'section_text': '#374151',
        'row_bg': '#f8f9fa',
        'text': '#212529',
        'success': '#059669',
        'error': '#dc2626',
        'white': '#ffffff',
        'black': '#000000',
        'transparent': 'transparent'
    },
    'header_bg': {
        'market_share': '#F0FDF4',
        'change': '#EFF6FF',
        'default': 'inherit'
    },
    'fonts': {
        'family': 'Arial, -apple-system, system-ui, sans-serif',
        'weights': {
            'normal': 'normal',
            'bold': 'bold',
            'semibold': '600'
        }
    },
    'gradients': {
        'positive': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)',
        'negative': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'
    }
}

# Simplified style configurations
STYLES = {
    'color': {
        'primary': '#3C5A99',
        'border': '#D3D3D3',
        'section': {'bg': '#E5E7EB', 'text': '#374151'},
        'row_bg': '#f8f9fa',
        'text': '#212529',
        'success': '#059669',
        'error': '#dc2626',
        'white': '#ffffff',
        'black': '#000000'
    },
    'header': {
        'market_share': '#F0FDF4',
        'change': '#EFF6FF'
    },
    'dimension': {
        'height': '1.2rem',
        'padding': '0.3rem',
        'font': '0.875rem',
        'section': '0.8rem',
        'border': '0.1rem'
    },
    'font': {
        'family': 'Arial, -apple-system, system-ui, sans-serif',
        'weight': {'normal': 'normal', 'bold': 'bold', 'semibold': '600'}
    },
    'gradient': {
        'positive': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)',
        'negative': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'
    }
}

# Simplified column configurations
COLUMNS = {
    ColumnType.RANK: {'width': '3.5rem', 'min': '2.8125rem', 'max': '4rem', 'align': 'center', 'id': 'N'},  # 50px, 45px, 50px
    ColumnType.INSURER: {'width': '23rem', 'min': '17rem', 'max': '25rem', 'align': 'left', 'id': 'insurer'},  # 200px, 175px, 200px
    ColumnType.CHANGE: {'width': '6rem', 'min': '3.75rem', 'max': '6rem', 'align': 'center', 'id': '_q_to_q_change'},  # 60px, 60px, 80px
    ColumnType.DEFAULT: {'width': '6rem', 'min': '3.75rem', 'max': '6rem', 'align': 'right'}  # 60px, 60px, 80px
}

def _get_base_style() -> Dict[str, Dict[str, Any]]:
    """Generate base table styles."""
    return {
        'cell': {
            'fontFamily': STYLES['font']['family'],
            'fontSize': STYLES['dimension']['font'],
            'padding': STYLES['dimension']['padding'],
            'boxSizing': 'border-box',
            'borderSpacing': '0',
            'borderCollapse': 'collapse'
        },
        'header': {
            'backgroundColor': STYLES['color']['primary'],
            'color': STYLES['color']['black'],
            'fontWeight': STYLES['font']['weight']['semibold'],
            'textAlign': 'center',
            'padding': '0rem'
        },
        'data': {
            'backgroundColor': STYLES['color']['white'],
            'color': STYLES['color']['text']
        }
    }

def _get_css_rules(df: pd.DataFrame) -> Dict[str, str]:
    """Generate all CSS rules including column width and height constraints."""
    dims = BASE_STYLES['dimensions']
    
    # Core dimension rules with maximum specificity
    dimension_rules = f'''
        height: {dims['height']} !important;
        min-height: {dims['height']} !important;
        max-height: {dims['height']} !important;
        line-height: {dims['height']} !important;
        box-sizing: border-box !important;
    '''
    # Text handling rules
    text_rules = '''
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        box-sizing: border-box !important;
    '''
    # Base rules with increased specificity and height constraints
    base_rules = {
        '.dash-table-container .dash-spreadsheet': '''
            table-layout: fixed !important;
            width: 100% !important;
            max-width: 100% !important;
            border-collapse: collapse !important;
        ''',
        '.dash-table-container .dash-spreadsheet table': '''
            table-layout: fixed !important;
            width: 100% !important;
            max-width: 100% !important;
        ''',
        '.dash-table-container .dash-spreadsheet tr': '''
            width: 100% !important;
            max-width: 100% !important;
        ''',
        '.dash-spreadsheet tr, .dash-header, td.dash-cell, th.dash-header': f'''
            box-sizing: border-box !important;
            {dimension_rules}
            margin: 0 !important;
        ''',
        '.dash-cell-value, .dash-header-cell-value, .unfocused, .dash-cell div, .dash-header div, .cell-markdown, .dash-cell *': f'''
            box-sizing: border-box !important;
            {dimension_rules}
            {text_rules}
        ''',
    }
    # Merge base rules with column-specific width rules
    return {**base_rules}

def _get_column_type(col: str) -> ColumnType:
    """Determine column type efficiently."""
    for col_type, config in COLUMNS.items():
        if config.get('id') == col or (col_type == ColumnType.CHANGE and config['id'] in col):
            return col_type
    return ColumnType.DEFAULT

def _get_row_type(row: Dict[str, Any]) -> RowType:
    """Determine row type with simplified logic."""
    if row.get('is_section_header'):
        return RowType.SECTION_HEADER
    insurer = row.get('insurer', '')
    if 'top' in insurer:
        return RowType.TOP
    return RowType.MARKET_TOTAL if insurer == 'total' else RowType.REGULAR

def _generate_styles(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generate optimized conditional styles."""
    styles = {'cell': [], 'data': [], 'header': []}
    
    # Column-based styles
    for col in df.columns:
        col_type = _get_column_type(col)
        config = COLUMNS[col_type]
        styles['cell'].append({
            'if': {'column_id': col},
            'minWidth': config['min'],
            'maxWidth': config['max'],
            'width': config['width'],
            'textAlign': config['align']
        })
        
        # Special column styling
        if col_type == ColumnType.RANK:
            styles['data'].extend([
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(+"'},
                 'backgroundImage': STYLES['gradient']['positive']},
                *[{'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                  'backgroundImage': STYLES['gradient']['negative']} for i in range(1, 10)]
            ])
        elif col_type == ColumnType.CHANGE:
            styles['data'].extend([
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                 'color': STYLES['color']['success' if op == '>' else 'error'],
                 'fontWeight': STYLES['font']['weight']['normal'],
                 'backgroundColor': STYLES['color']['row_bg']}
                for op in ['>', '<']
            ])
    
    # Row-based styles
    for idx, row in enumerate(df.to_dict('records')):
        row_type = _get_row_type(row)
        if row_type != RowType.REGULAR:
            style = {
                'backgroundColor': STYLES['color']['row_bg'],
                'fontWeight': STYLES['font']['weight']['bold']
            }
            if row_type == RowType.SECTION_HEADER:
                style.update({
                    'backgroundColor': STYLES['color']['section']['bg'],
                    'borderTop': f"1px solid {STYLES['color']['section']['bg']}",
                    'borderBottom': f"1px solid {STYLES['color']['section']['bg']}",
                    'paddingLeft': STYLES['dimension']['section'],
                    'color': STYLES['color']['section']['text']
                })
            styles['data'].append({'if': {'row_index': idx}, **style})
    
    # Header styles
    for col in df.columns:
        col_type = _get_column_type(col)
        base_style = {'backgroundColor': STYLES['color']['row_bg']}
        
        if col_type in {ColumnType.RANK, ColumnType.INSURER}:
            for idx in range(3):
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_style,
                    'textAlign': 'left' if col_type == ColumnType.INSURER else 'center',
                    'verticalAlign': 'middle',
                    'borderTop': f"{STYLES['dimension']['border']} solid {STYLES['color']['border']}" if idx == 0 else '0px',
                    'borderBottom': f"{STYLES['dimension']['border']} solid {STYLES['color']['border']}" if idx == 2 else '0px',
                    'color': STYLES['color']['black'] if idx == 1 else 'transparent',
                    'fontWeight': STYLES['font']['weight']['bold']
                })
        else:
            header_bg = (STYLES['header']['market_share'] 
                        if any(x in col for x in ['market_share', 'market_share_q_to_q_change'])
                        else STYLES['header']['change'])
            for idx in range(3):
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_style,
                    'fontWeight': STYLES['font']['weight']['bold' if idx == 0 else 'normal'],
                    'backgroundColor': STYLES['color']['row_bg'] if idx == 0 else header_bg
                })
    
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

    base_styles = _get_base_style()
    conditional_styles = _generate_styles(df)
    css_rules = _get_css_rules(df)

    return {
        'style_cell': base_styles['cell'],
        'style_header': base_styles['header'],
        'style_data': base_styles['data'],
        'style_cell_conditional': conditional_styles['cell'],
        'style_data_conditional': conditional_styles['data'],
        'style_header_conditional': conditional_styles['header'],
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
        'cell_selectable': False,
        'page_action': 'none',
        'editable': False
    }