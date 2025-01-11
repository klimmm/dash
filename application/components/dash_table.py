from typing import Dict, Any, List, Optional
import pandas as pd
from dash.dash_table.Format import Format, Scheme, Group
from pathlib import Path
from config.logging_config import get_logger
from constants.translations import translate
from constants.filter_options import METRICS
from data_process.data_utils import map_insurer
from application.components.resolve_variables import load_css_file, resolve_theme_variables

logger = get_logger(__name__)

# Load theme configuration
CSS_PATH = Path(__file__).parent.parent.parent / "assets" / "styles" / "03_components" / "_data-table.css"
css_content = load_css_file(str(CSS_PATH))

# Define base theme structure
THEME = {
    'colors': {
        'header_bg': 'var(--table-header-bg)',
        'header_text': 'var(--table-header-text)',
        'cell_bg': 'var(--table-cell-bg)',
        'cell_text': 'var(--table-cell-text)',
        'border': 'var(--table-border)',
        'highlight': 'var(--table-highlight-bg)',
        'success': 'var(--color-status-success)',
        'danger': 'var(--color-status-danger)',
        'qtoq_bg': 'var(--table-qtoq-bg)',
    },
    'typography': {
        'font_family': 'var(--font-family-base)',
        'font_size': 'var(--table-font-size)',
        'header_weight': 'var(--font-weight-semibold)',
        'bold_weight': 'bold',
        'normal_weight': 'normal'
    },
    'spacing': {
        'cell_padding': 'var(--table-cell-padding-x)',
        'header_padding': 'var(--table-header-padding)',
    },
    'layout': {
        'white_space': 'normal',
        'min_width': '100%',
        'overflow_x': 'auto',
        'text_align': {'left': 'left', 'center': 'center'},
        'vertical_align': {'top': 'top', 'bottom': 'bottom'},
        'border': {'width': '1px', 'style': 'solid', 'none': 'none'}
    }
}

# Resolve theme variables
TABLE_THEME = resolve_theme_variables(THEME, css_content)

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
IDENTIFIER_COLS = {PLACE_COL, INSURER_COL}
SPECIAL_INSURERS = {
    'Топ': {'backgroundColor': TABLE_THEME['colors']['highlight'], 'fontWeight': 'bold'},
    'Весь рынок': {'backgroundColor': TABLE_THEME['colors']['highlight'], 'fontWeight': 'bold'}
}

def generate_dash_table_config(
    df: pd.DataFrame,
    period_type: str,
    columns_config: Optional[Dict[str, str]] = None,
    toggle_selected_market_share: Optional[List[str]] = None,
    toggle_selected_qtoq: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate complete table configuration with styling and formatting"""
    
    # Visibility settings
    show_market_share = toggle_selected_market_share and "show" in toggle_selected_market_share
    show_qtoq = toggle_selected_qtoq and "show" in toggle_selected_qtoq
    
    # Format columns and prepare data
    columns = []
    for col in df.columns:
        # Base column config
        column_config = {"id": col}
        
        if col in IDENTIFIER_COLS:
            # Handle identifier columns
            translated_col = translate(col)
            column_config["name"] = [translated_col, translated_col]
        else:
            # Handle metric columns
            metric = next((m for m in sorted(METRICS.keys(), key=len, reverse=True) 
                         if col.startswith(m)), '')
            parts = col[len(metric)+1:].split('_') if metric else col.split('_')
            quarter = parts[0] if parts else ""
            suffix = '_'.join(parts[1:]) if len(parts) > 1 else ""
            
            # Format column name
            metric_label = translate(METRICS.get(metric, {}).get('label', metric))
            if 'market_share' in suffix:
                base = f"{metric_label}, {translate('market_share')}"
                header = translate('q_to_q_change') if 'q_to_q_change' in suffix else \
                        (quarter and f"{quarter.split('Q')[1]} кв. {quarter.split('Q')[0]}")
            else:
                base = f"{metric_label}, {translate('млрд руб.')}"
                header = translate('q_to_q_change') if 'q_to_q_change' in suffix else \
                        (quarter and f"{quarter.split('Q')[1]} кв. {quarter.split('Q')[0]}")
            
            column_config.update({
                "name": [base, header],
                "type": "numeric",
                "format": Format(
                    precision=2 if any(x in col for x in ['market_share', 'q_to_q_change', 'ratio', 'rate']) 
                    else 3,
                    scheme=Scheme.percentage if any(x in col for x in ['market_share', 'q_to_q_change', 'ratio', 'rate'])
                    else Scheme.fixed,
                    group=Group.yes,
                    groups=3,
                    group_delimiter=','
                )
            })
        
        columns.append(column_config)
    
    # Hidden columns
    hidden_columns = [
        col["id"] for col in columns
        if col["id"] not in IDENTIFIER_COLS and (
            ('market_share' in col["id"] and not show_market_share) or
            ('q_to_q_change' in col["id"] and not show_qtoq)
        )
    ]
    
    # Style configuration
    style_data_conditional = []
    
    # Special insurer styles
    for insurer, style in SPECIAL_INSURERS.items():
        style_data_conditional.append({
            'if': {'filter_query': f'{{insurer}} contains "{insurer}"'},
            **style
        })
    
    # Column-specific styles
    for col in df.columns:
        if '_q_to_q_change' in col:
            style_data_conditional.extend([
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} > 0'},
                    'color': TABLE_THEME['colors']['success'],
                    'fontWeight': TABLE_THEME['typography']['normal_weight']
                },
                {
                    'if': {'column_id': col, 'filter_query': f'{{{col}}} < 0'},
                    'color': TABLE_THEME['colors']['danger'],
                    'fontWeight': TABLE_THEME['typography']['normal_weight']
                },
                {
                    'if': {'column_id': col},
                    'backgroundColor': TABLE_THEME['colors']['qtoq_bg']
                }
            ])
        elif col in IDENTIFIER_COLS:
            style_data_conditional.append({
                'if': {'column_id': col},
                'backgroundColor': TABLE_THEME['colors']['cell_bg'],
                'textAlign': TABLE_THEME['layout']['text_align']['left'] if col == INSURER_COL 
                            else TABLE_THEME['layout']['text_align']['center']
            })
    
    return {
        # Base styles
        'style_table': {
            'overflowX': TABLE_THEME['layout']['overflow_x'],
            'minWidth': TABLE_THEME['layout']['min_width']
        },
        'style_cell': {
            'fontFamily': TABLE_THEME['typography']['font_family'],
            'fontSize': TABLE_THEME['typography']['font_size'],
            'padding': TABLE_THEME['spacing']['cell_padding'],
            'whiteSpace': TABLE_THEME['layout']['white_space'],
            'border': f"{TABLE_THEME['layout']['border']['width']} "
                     f"{TABLE_THEME['layout']['border']['style']} "
                     f"{TABLE_THEME['colors']['border']}"
        },
        'style_header': {
            'backgroundColor': TABLE_THEME['colors']['header_bg'],
            'color': TABLE_THEME['colors']['header_text'],
            'fontWeight': TABLE_THEME['typography']['header_weight'],
            'textAlign': TABLE_THEME['layout']['text_align']['center'],
            'whiteSpace': TABLE_THEME['layout']['white_space'],
            'padding': TABLE_THEME['spacing']['header_padding']
        },
        'style_data': {
            'backgroundColor': TABLE_THEME['colors']['cell_bg'],
            'color': TABLE_THEME['colors']['cell_text']
        },
        
        # Data and columns
        'columns': [{**col, "hideable": False, "selectable": False, 
                    "deletable": False, "renamable": False} for col in columns],
        'data': df.assign(insurer=lambda x: x['insurer'].map(map_insurer)).to_dict('records'),
        'hidden_columns': hidden_columns,
        
        # Conditional styles
        'style_data_conditional': style_data_conditional,
        'style_header_conditional': [
            {
                'if': {'column_id': col, 'header_index': idx},
                'textAlign': 'left' if col == INSURER_COL else 'center',
                'verticalAlign': 'bottom',
                'borderBottom': TABLE_THEME['layout']['border']['none'] if idx == 0 else None,
                'borderTop': TABLE_THEME['layout']['border']['none'] if idx == 1 else None,
                'paddingBottom': '0',
                'paddingTop': '0',
                'color': 'transparent' if idx == 1 else TABLE_THEME['colors']['header_text']
            }
            for col in IDENTIFIER_COLS
            for idx in [0, 1]
        ],
        
        # Table behavior
        'sort_action': 'none',
        'sort_mode': None,
        'filter_action': 'none',
        'merge_duplicate_headers': True,
        'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
        'column_selectable': False,
        'row_selectable': False,
        'cell_selectable': False,
        'page_action': 'none',
        'editable': False,
        
        # Additional settings
        'dropdown': {},
        'tooltip_conditional': [],
        'tooltip_data': [],
        'tooltip_header': {}
    }