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
    'colors': {
        'primary': '#3C5A99',
        'border': '#e9ecef',
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
    'dimensions': {
        'height': '15px',
        'padding': '0.4rem',
        'font_size': '0.875rem',
        'section_padding': '8px',
        'border_width': '0.1px',
        'zero': '0px'
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

# Column configurations with enforced width constraints
COLUMN_CONFIGS = {
    ColumnType.RANK: {
        'width': '50px',     # Fixed width instead of fit-content
        'minWidth': '45px',
        'maxWidth': '50px', 
        'textAlign': 'center',
        'identifier': 'N'
    },
    ColumnType.INSURER: {
        'width': '200px',    # Fixed width instead of fit-content
        'minWidth': '175px',
        'maxWidth': '200px', 
        'textAlign': 'left',
        'identifier': 'insurer'
    },
    ColumnType.CHANGE: {
        'width': '80px',    # Fixed width instead of fit-content
        'minWidth': '80px',
        'maxWidth': '80px',
        'textAlign': 'center', 
        'identifier': '_q_to_q_change'
    },
    ColumnType.DEFAULT: {
        'width': '80px',    # Fixed width instead of fit-content
        'minWidth': '80px',
        'maxWidth': '80px',
        'textAlign': 'right'
    }
}

def _get_base_styles() -> Dict[str, Dict[str, Any]]:
    """Generate base styles without width constraints."""
    dims = BASE_STYLES['dimensions']
    colors = BASE_STYLES['colors']
    fonts = BASE_STYLES['fonts']

    return {
        'cell': {
            'fontFamily': fonts['family'],
            'fontSize': dims['font_size'],
            'padding': dims['padding'],
            'boxSizing': 'border-box',
            'borderSpacing': '0',
            'borderCollapse': 'collapse'
        },
        'header': {
            'backgroundColor': colors['primary'],
            'color': colors['black'],
            'fontWeight': fonts['weights']['semibold'],
            'textAlign': 'center',
            'padding': '0rem'
        },
        'data': {
            'backgroundColor': colors['white'],
            'color': colors['text']
        }
    }

def _get_column_css_rules(df: pd.DataFrame) -> Dict[str, str]:
    """Generate CSS rules specifically for column width constraints."""
    width_rules = {}
    
    # Add table-level rules with higher specificity
    width_rules['.dash-table-container table.dash-spreadsheet'] = '''
        table-layout: fixed !important;
        width: 100% !important;
        max-width: 100% !important;
        border-collapse: collapse !important;
    '''
    
    # Add container rules
    width_rules['.dash-table-container .dash-spreadsheet-container'] = '''
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    '''
    
    width_rules['.dash-table-container .dash-spreadsheet-inner'] = '''
        width: 100% !important;
        max-width: 100% !important;
    '''
    
    # Column group rules with higher specificity
    width_rules['.dash-table-container .dash-spreadsheet colgroup'] = '''
        display: table-column-group !important;
        width: auto !important;
    '''
    
    for col in df.columns:
        col_type = _get_column_type(col)
        config = COLUMN_CONFIGS[col_type]
        
        # Base width styles with important flags
        width_styles = f'''
            width: {config.get('width')} !important;
            min-width: {config.get('minWidth')} !important;
            max-width: {config.get('maxWidth')} !important;
            text-align: {config.get('textAlign', 'left')} !important;
        '''
        
        # Column group rule with high specificity
        width_rules[f'.dash-table-container .dash-spreadsheet col[data-column-id="{col}"]'] = width_styles
        
        # Rules for header and data cells with maximum specificity
        for element in ['th', 'td']:
            # Cell container
            selector = f'.dash-table-container .dash-spreadsheet {element}[data-column-id="{col}"]'
            width_rules[selector] = f'''
                {width_styles}
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
            '''
            
            # Cell content
            content_selector = f'.dash-table-container .dash-spreadsheet {element}[data-column-id="{col}"] > div'
            width_rules[content_selector] = f'''
                {width_styles}
                display: block !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
                white-space: nowrap !important;
                box-sizing: border-box !important;
            '''
            
            # Ensure input fields also respect width
            input_selector = f'.dash-table-container .dash-spreadsheet {element}[data-column-id="{col}"] input'
            width_rules[input_selector] = f'''
                width: 100% !important;
                max-width: {config.get('maxWidth')} !important;
                box-sizing: border-box !important;
            '''
    
    return width_rules

def _get_css_rules(df: pd.DataFrame) -> Dict[str, str]:
    """Generate all CSS rules including column width and height constraints."""
    dims = BASE_STYLES['dimensions']
    
    # Core dimension rules with maximum specificity
    dimension_rules = f'''
        height: {dims['height']} !important;
        min-height: {dims['height']} !important;
        max-height: {dims['height']} !important;
        line-height: {dims['height']} !important;
        border-width: {dims['border_width']} !important;
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
        '.dash-table-container': '''
            table-layout: fixed !important;
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            border-spacing: 0 !important;
            overflow-x: auto !important;
        ''',
        '.dash-table-container > div': '''
            width: 100% !important; 
            overflow-x: auto !important;
            max-width: 100% !important;
        ''',
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
        '.dash-table-container .dash-spreadsheet th.dash-header': f'''
            {dimension_rules}
            padding: {dims['padding']} !important;
        ''',
        # Add height constraints for cell content
        '.dash-table-container .dash-cell-value': f'''
            {dimension_rules}
            {text_rules}
        ''',
        '.dash-table-container .dash-header-cell-value': f'''
            {dimension_rules}
            {text_rules}
        ''',
        # Handle all internal cell elements
        '.dash-table-container .dash-cell div': f'''
            {dimension_rules}
            {text_rules}
        ''',
        '.dash-table-container .dash-header div': f'''
            {dimension_rules}
            {text_rules}
        ''',
        '.dash-table-container .cell-markdown': f'''
            {dimension_rules}
            {text_rules}
        ''',
        '.dash-table-container .dash-cell *': f'''
            {dimension_rules}
            {text_rules}
        '''
    }

    # Merge base rules with column-specific width rules
    return {**base_rules, **_get_column_css_rules(df)}

def _get_column_type(col: str) -> ColumnType:
    """Determine column type based on column name."""
    for col_type, config in COLUMN_CONFIGS.items():
        if config.get('identifier') == col or (
            col_type == ColumnType.CHANGE and config['identifier'] in col):
            return col_type
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

def _generate_styles(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generate conditional styles for cells, data, and headers."""
    styles = {'cell': [], 'data': [], 'header': []}
    colors = BASE_STYLES['colors']
    dims = BASE_STYLES['dimensions']
    fonts = BASE_STYLES['fonts']
    
    # Generate cell styles with column constraints
    for col in df.columns:
        col_type = _get_column_type(col)
        config = COLUMN_CONFIGS[col_type]
        styles['cell'].append({
            'if': {'column_id': col},
            'minWidth': config.get('minWidth'),
            'maxWidth': config.get('maxWidth'),
            'width': config.get('width'),
            'textAlign': config.get('textAlign')
        })
    
    # Generate data styles
    for col in df.columns:
        col_type = _get_column_type(col)
        
        if col_type == ColumnType.RANK:
            styles['data'].extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(+"'},
                    'backgroundImage': BASE_STYLES['gradients']['positive']
                },
                *[{
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                    'backgroundImage': BASE_STYLES['gradients']['negative']
                } for i in range(1, 10)]
            ])
        elif col_type == ColumnType.CHANGE:
            styles['data'].extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                    'color': colors['success' if op == '>' else 'error'],
                    'fontWeight': fonts['weights']['normal'],
                    'backgroundColor': colors['row_bg']
                }
                for op in ['>', '<']
            ])
    
    # Add row-based styles
    for idx, row in enumerate(df.to_dict('records')):
        row_type = _get_row_type(row)
        if row_type != RowType.REGULAR:
            base_style = {
                'backgroundColor': colors['row_bg'],
                'fontWeight': fonts['weights']['bold']
            }
            if row_type == RowType.SECTION_HEADER:
                base_style.update({
                    'backgroundColor': colors['section_bg'],
                    'borderTop': f'1px solid {colors["section_bg"]}',
                    'borderBottom': f'1px solid {colors["section_bg"]}',
                    'paddingLeft': dims['section_padding'],
                    'color': colors['section_text']
                })
            styles['data'].append({
                'if': {'row_index': idx},
                **base_style
            })
    
    # Generate header styles
    for col in df.columns:
        col_type = _get_column_type(col)
        base_header = {
            'backgroundColor': colors['row_bg']
        }
        
        if col_type in {ColumnType.RANK, ColumnType.INSURER}:
            for idx in range(3):
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_header,
                    'textAlign': 'left' if col_type == ColumnType.INSURER else 'center',
                    'verticalAlign': 'middle',
                    'borderTop': f"{dims['border_width']} solid {colors['border']}" if idx == 0 else dims['zero'],
                    'borderBottom': f"{dims['border_width']} solid {colors['border']}" if idx == 2 else dims['zero'],
                    'color': colors['black'] if idx == 1 else colors['transparent'],
                    'fontWeight': fonts['weights']['bold']
                })
        else:
            for idx in range(3):
                header_bg = (BASE_STYLES['header_bg']['market_share'] 
                           if any(x in col for x in ['market_share', 'market_share_q_to_q_change'])
                           else BASE_STYLES['header_bg']['change'])
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_header,
                    'fontWeight': fonts['weights']['bold'] if idx == 0 else fonts['weights']['normal'],
                    'backgroundColor': colors['row_bg'] if idx == 0 else header_bg
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

    base_styles = _get_base_styles()
    conditional_styles = _generate_styles(df)
    css_rules = _get_css_rules(df)

    return {
        'style_table': {
            'tableLayout': 'fixed',
            'overflowX': 'auto',
            'width': '100%',
            'maxWidth': '100%'
        },
        'style_cell': base_styles['cell'],
        'style_header': base_styles['header'],
        'style_data': base_styles['data'],
        'style_cell_conditional': conditional_styles['cell'],
        'style_data_conditional': conditional_styles['data'],
        'style_header_conditional': conditional_styles['header'],
        'columns': [{
            **col,
            'hideable': False,
            'selectable': False,
            'deletable': False,
            'renamable': False
        } for col in columns],
        'hidden_columns': hidden_columns,
        'css': [
            {'selector': selector, 'rule': rule.strip()}
            for selector, rule in css_rules.items()
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