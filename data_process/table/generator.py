from enum import Enum
from typing import Any, Dict, List
import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)

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


def get_column_type(col: str) -> ColumnType:
    """Determine column type efficiently."""
    logger.debug(f"Determining column type for column: {col}")

    for col_type, config in COLUMNS.items():
        logger.debug(f"Checking against column type: {col_type}")

        if config.get('id') == col:
            logger.debug(f"Found exact match for column {col}: {col_type}")
            return col_type
        elif col_type == ColumnType.CHANGE and config['id'] in col:
            logger.debug(f"Found change type match for column {col}: {col_type}")
            return col_type

    logger.info(f"No specific type found for column {col}, returning DEFAULT")
    return ColumnType.DEFAULT

def get_row_type(row: Dict[str, Any]) -> RowType:
    """
    Determine row type based on row data.
    """
    logger.debug(f"Determining row type for row: {row}")

    if row.get(ColumnType.SECTION_HEADER.value):
        logger.debug("Found SECTION_HEADER row")
        return RowType.SECTION_HEADER

    insurer_value = str(row.get(ColumnType.INSURER.value, '')).lower()
    logger.debug(f"Insurer value: {insurer_value}")

    if RowType.TOP.value in insurer_value:
        logger.debug("Found TOP row")
        return RowType.TOP

    if insurer_value == RowType.MARKET_TOTAL.value:
        logger.debug("Found MARKET_TOTAL row")
        return RowType.MARKET_TOTAL

    logger.debug("No special row type found, returning REGULAR")
    return RowType.REGULAR


COLUMNS = {
    ColumnType.RANK: {
        'width': '3.8rem',
        'min': '3.8rem',
        'max': '4rem',
        'align': 'center',
        'id': 'N'
    }, 
    ColumnType.INSURER: {
        'width': '17rem',
        'min': '17rem',
        'max': 'none',  # Remove max width constraint
        'align': 'left',
        'id': 'insurer'
    },
    ColumnType.DEFAULT: {
        'width': '6rem',
        'min': '3.5rem',
        'max': '6rem',
        'align': 'right'
    },    
    ColumnType.LINE: {
        'width': '14rem',
        'min': '14rem',
        'max': 'none',  # Remove max width constraint
        'align': 'left',
        'id': 'linemain'
    },
    ColumnType.CHANGE: {
        'width': '6rem',
        'min': '3.75rem',
        'max': '6rem',
        'align': 'center',
        'id': '_change'
    },

}

def get_base_style() -> Dict[str, Dict[str, Any]]:
    """Generate base table styles."""
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
    """Generate all CSS rules including column width and height constraints."""

    dimension_rules = '''
        height: auto !important;
        min-height: 1.2rem;
        max-height: none !important;
        line-height: 1.4;
        box-sizing: border-box !important;
    '''
    text_rules = '''
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        box-sizing: border-box !important;
    '''
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
        'th.dash-header.column-2': '''
            border-bottom-width: 0 !important;
        ''',
        '.dash-header.column-2.cell--right-last': '''
            border-bottom-width: 0.1rem !important;
            background-color: '#FFFFFF' !important;
        ''',
        'th.dash-header.column-0': '''
            border-top-width: 0 !important;
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
        '''
    }
    return {**base_rules}



def generate_styles(df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generate optimized conditional styles with inline values."""
    styles = {'cell': [], 'data': [], 'header': []}

    # Column-based styles
    for col in df.columns:
        col_type = get_column_type(col)
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
                 'backgroundImage': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'},
                *[{'if': {'column_id': col, 'filter_query': f'{{{col}}} contains "(-{i}"'},
                  'backgroundImage': 'linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'} for i in range(1, 10)]
            ])
        
        elif col_type == ColumnType.CHANGE:
            styles['data'].extend([
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
                 'color': '#059669' if op == '>' else '#dc2626',
                 'fontWeight': 'normal',
                 'backgroundColor': '#f8f9fa'}
                for op in ['>', '<']
            ])

    for idx, row in enumerate(df.to_dict('records')):
        row_type = get_row_type(row)
        if row_type != RowType.REGULAR:
            style = {
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold'
            }
            if row_type == RowType.SECTION_HEADER:
                style.update({
                    'backgroundColor': '#E5E7EB',
                    'borderTop': '1px solid #E5E7EB',
                    'borderBottom': '1px solid #E5E7EB',
                    'paddingLeft': '0.8rem',
                    'color': '#374151'
                })
            styles['data'].append({'if': {'row_index': idx}, **style})

    # Header styles
    for col in df.columns:
        col_type = get_column_type(col)
        base_style = {'backgroundColor': '#f8f9fa'}

        if col_type in {ColumnType.INSURER, ColumnType.LINE, ColumnType.RANK}:
            for idx in range(3):
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_style,
                    'textAlign': 'center' if idx == 1 and col_type == ColumnType.RANK else 'left',
                    'verticalAlign': 'bottom' if idx == 0 else 'bottom',
                    'paddingLeft': '15px' if idx == 0 else '0px',
                    'marginBottom': '-10px' if idx == 1 else '3px',
                    'paddingBottom': '-10px' if idx == 1 else '6px',
                    'paddingTop': '3px' if idx == 1 else '3px',
                    'min-height': 'auto',  # Changed from fixed height
                    'height': 'auto',      # Allow content to determine height
                    'whiteSpace': 'normal',  # Allow text wrapping
                    'overflow': 'visible',   # Show overflow content
                    'paddingBottom': '6px' if idx == 0 else '0px',
                    'marginLeft': '6px' if idx == 0 else '0px',
                    'borderTop': '0.1rem solid #D3D3D3' if idx == 1 else '0px',
                    'borderBottom': '0.1rem solid #D3D3D3' if idx == 0 or idx == 2 else '0px',
                    'borderLeft': '0.1rem solid #D3D3D3' if idx == 2 or idx == 1 else '0px',
                    'color': '#000000' if idx == 0 or idx == 1 else 'transparent',
                    'fontWeight': 'bold' if idx == 0 else 'normal',
                    'backgroundColor': '#FFFFFF' if idx == 0 else '#f8f9fa'
                })


        else:
            header_bg = '#F0FDF4' if any(x in col for x in ['market_share', 'market_share_change']) else '#EFF6FF'
            for idx in range(3):
                styles['header'].append({
                    'if': {'column_id': col, 'header_index': idx},
                    **base_style,
                    'borderTop': '0.1rem solid #D3D3D3 !importa' if idx == 1 else '0px',
                    
                    'borderBottom': '0.1rem solid #D3D3D3' if idx == 2 or idx == 0 else '0px',
                    'fontWeight': 'bold' if idx == 0 else 'normal',
                    'paddingBottom': '6px' if idx == 0 else '0px',
                    'borderRight': '0.1rem solid #D3D3D3' if idx == 2 or idx == 1 else '0px',
                    'borderLeft': '0.1rem solid #D3D3D3' if idx == 2 or idx == 1 else '0px',
                    'backgroundColor': '#FFFFFF' if idx == 0 else header_bg
                })

    return styles


def generate_datatable_config(
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
            get_column_type(col) not in {ColumnType.RANK, ColumnType.INSURER, ColumnType.LINE} and (
                ('market_share' in col and not show_market_share) or
                (get_column_type(col) == ColumnType.CHANGE and not show_qtoq)
            )
        )
    ]

    base_styles = get_base_style()
    conditional_styles = generate_styles(df)
    css_rules = get_css_rules(df)

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