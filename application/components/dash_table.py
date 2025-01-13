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
CSS_PATH = Path(__file__).parent.parent.parent / "assets" / "styles" / "01_settings" / "_tokens.css"
css_content = load_css_file(str(CSS_PATH))

# Define base theme structure
THEME = {
    'colors': {
        'header_bg': 'var(--table-surface-header)',
        'header_text': 'var(--table-text-header)',
        'cell_bg': 'var(--table-surface-cell)',
        'cell_text': 'var(--table-text-cell)',
        'border': 'var(--table-border)', 
        'highlight': 'var(--table-surface-highlight)',
        'success': 'var(--color-success-600)',
        'danger': 'var(--color-danger-600)',
        'qtoq_bg': 'var(--table-surface-alternate)'
    },
    'typography': {
        'font_family': 'var(--font-family-sans)',
        'font_size': 'var(--table-font-size)',
        'header_weight': 'var(--font-weight-semibold)',
        'bold_weight': 'bold',
        'normal_weight': 'normal'
    },
    'spacing': {
        'cell_padding': 'var(--space-2)',
        'header_padding': 'var(--space-2) var(--space-3)',
    },
    'layout': {
        'white_space': 'normal',
        'min_width': '100%',
        'overflow_x': 'auto',
        'text_align': {
            'left': 'left',
            'center': 'center',
            'right': 'right'
        },
        'vertical_align': {
            'top': 'top',
            'bottom': 'bottom'
        },
        'border': {
            'width': '1px',
            'style': 'solid',
            'none': 'none'
        }
    },
    'columns': {
        'rank': {
            'width': 'var(--table-col-width-rank)',
            'min_width': 'var(--table-col-min-width-rank)',
            'max_width': 'var(--table-col-max-width-rank)',
            'text_align': 'center'
        },
        'insurer': {
            'width': 'var(--table-col-width-insurer)',
            'min_width': 'var(--table-col-width-insurer)',
            'max_width': 'var(--table-col-width-insurer)',
            'text_align': 'left'
        },
        'value': {
            'width': '120px',
            'min_width': '110px',
            'max_width': '120px',
            'text_align': 'right'
        },
        'change': {
            'width': '120px',
            'min_width': '110px',
            'max_width': '120px',
            'text_align': 'center'
        },
        'market_share': {
            'width': '120px',
            'min_width': '110px',
            'max_width': '120px',
            'text_align': 'right'
        }
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
    
    # Initialize style lists
    style_data_conditional = []
    style_cell_conditional = [
        # Rank column (N)
        {
            'if': {'column_id': 'N'},
            'width': TABLE_THEME['columns']['rank']['width'],
            'min-width': TABLE_THEME['columns']['rank']['min_width'],
            'max-width': TABLE_THEME['columns']['rank']['max_width'],
            'textAlign': TABLE_THEME['columns']['rank']['text_align']
        },
        # Insurer column
        {
            'if': {'column_id': 'insurer'},
            'width': TABLE_THEME['columns']['insurer']['width'],
            'min-width': TABLE_THEME['columns']['insurer']['min_width'],
            'max-width': TABLE_THEME['columns']['insurer']['max_width'],
            'textAlign': TABLE_THEME['columns']['insurer']['text_align']
        }
    ]
    
    # Value columns (premiums)
    value_columns = [col for col in df.columns if 'total_premiums' in col and 'market_share' not in col and 'q_to_q' not in col]
    for col in value_columns:
        style_cell_conditional.append({
            'if': {'column_id': col},
            'width': TABLE_THEME['columns']['value']['width'],
            'min-width': TABLE_THEME['columns']['value']['min_width'],
            'max-width': TABLE_THEME['columns']['value']['max_width'],
            'textAlign': TABLE_THEME['columns']['value']['text_align']
        })
    
    # Change columns (q_to_q)
    change_columns = [col for col in df.columns if 'q_to_q_change' in col]
    for col in change_columns:
        style_cell_conditional.append({
            'if': {'column_id': col},
            'width': TABLE_THEME['columns']['change']['width'],
            'min-width': TABLE_THEME['columns']['change']['min_width'],
            'max-width': TABLE_THEME['columns']['change']['max_width'],
            'textAlign': TABLE_THEME['columns']['change']['text_align']
        })
    
    # Market share columns
    market_share_columns = [col for col in df.columns if 'market_share' in col and 'q_to_q' not in col]
    for col in market_share_columns:
        style_cell_conditional.append({
            'if': {'column_id': col},
            'width': TABLE_THEME['columns']['market_share']['width'],
            'min-width': TABLE_THEME['columns']['market_share']['min_width'],
            'max-width': TABLE_THEME['columns']['market_share']['max_width'],
            'textAlign': TABLE_THEME['columns']['market_share']['text_align']
        })
    
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
            
            metric_label = translate(METRICS.get(metric, {}).get('label', metric))
            if 'market_share' in suffix:
                base = f"{metric_label}, {translate('market_share')}"
                header = translate('q_to_q_change') if 'q_to_q_change' in suffix else \
                        (quarter and f"{quarter.split('Q')[1]} кв. {quarter.split('Q')[0]}")
            else:
                base = f"{metric_label}, {translate('млрд руб.')}"
                header = translate('q_to_q_change') if 'q_to_q_change' in suffix else \
                        (quarter and f"{quarter.split('Q')[1]} кв. {quarter.split('Q')[0]}")
            
            is_qtoq = 'q_to_q_change' in col
            
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
                    group_delimiter=',',
                    sign='+' if is_qtoq else ''  # Only valid signs are '', '-', '+', '(', ' '
                )
            })
        
        columns.append(column_config)

    success_bg = 'rgba(0, 200, 81, 0.15)'  # Полупрозрачный зеленый
    danger_bg = 'rgba(255, 71, 87, 0.15)'  # Полупрозрачный красный
    

    
    # First, add the base background color for all cells
    style_data_conditional.append({
        'if': {'column_id': col for col in df.columns},
        'backgroundColor': TABLE_THEME['colors']['cell_bg'],
    })


    style_data_conditional.append({
        'if': {
            'column_id': 'N',
            'filter_query': '{N} contains "(+"'
        },
        'background': (
            f'linear-gradient(90deg, '
            f'transparent 0%, '
            f'transparent calc(50% - 2ch), '
            f'{success_bg} calc(50% + 1.5ch), '
            f'{success_bg} calc(50% + 2.5ch), '
            f'transparent calc(50% + 3ch), '
            f'transparent 100%)'
        )
    })
    
    # Negative changes - look for (-1 through (-9
    for i in range(1, 10):
        style_data_conditional.append({
            'if': {
                'column_id': 'N',
                'filter_query': f'{{N}} contains "(-{i}"'
            },
            'background': (
                f'linear-gradient(90deg, '
                f'transparent 0%, '
                f'transparent calc(50% - 1ch), '
                f'{danger_bg} calc(50% + 1.5ch), '
                f'{danger_bg} calc(50% + 2.5ch), '
                f'transparent calc(50% + 3ch), '
                f'transparent 100%)'
            )
        })
    
    # Add special insurer styles
    for insurer, style in SPECIAL_INSURERS.items():
        style_data_conditional.append({
            'if': {'filter_query': f'{{insurer}} contains "{insurer}"'},
            'backgroundColor': style['backgroundColor'],
            'fontWeight': style['fontWeight']
        })


    
    # Add special insurer styles (now these will take precedence)
    for insurer, style in SPECIAL_INSURERS.items():
        style_data_conditional.append({
            'if': {'filter_query': f'{{insurer}} contains "{insurer}"'},
            'backgroundColor': style['backgroundColor'],
            'fontWeight': style['fontWeight']
        })
    
    # Add text alignment for identifier columns without background color
    for col in IDENTIFIER_COLS:
        style_data_conditional.append({
            'if': {'column_id': col},
            'textAlign': TABLE_THEME['layout']['text_align']['left'] if col == INSURER_COL 
                        else TABLE_THEME['layout']['text_align']['center']
        })

    for col in df.columns:
        if '_q_to_q_change' in col:
            style_data_conditional.extend([
                # Positive values
                {
                    'if': {
                        'column_id': col,
                        'filter_query': f'{{{col}}} > 0'
                    },
                    'color': TABLE_THEME['colors']['success'],
                    'fontWeight': TABLE_THEME['typography']['normal_weight']
                },
                # Negative values
                {
                    'if': {
                        'column_id': col,
                        'filter_query': f'{{{col}}} < 0'
                    },
                    'color': TABLE_THEME['colors']['danger'],
                    'fontWeight': TABLE_THEME['typography']['normal_weight']
                },
                # Zero values - no special formatting needed
                {
                    'if': {
                        'column_id': col,
                        'filter_query': f'{{{col}}} = 0'
                    },
                    'color': TABLE_THEME['colors']['cell_text'],
                    'fontWeight': TABLE_THEME['typography']['normal_weight']
                },
                # Background for the entire column
                {
                    'if': {'column_id': col},
                    'backgroundColor': TABLE_THEME['colors']['qtoq_bg']
                }
            ])

    # Hidden columns
    hidden_columns = [
        col["id"] for col in columns
        if col["id"] not in IDENTIFIER_COLS and (
            ('market_share' in col["id"] and not show_market_share) or
            ('q_to_q_change' in col["id"] and not show_qtoq)
        )
    ]

    return {
        'style_table': {
            'overflowX': TABLE_THEME['layout']['overflow_x'],
            'width': 'fit-content',  # This makes table take its natural width
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
        'style_cell_conditional': style_cell_conditional,
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
        'columns': [{**col, "hideable": False, "selectable": False, 
                    "deletable": False, "renamable": False} for col in columns],
        'data': df.assign(insurer=lambda x: x['insurer'].map(map_insurer)).to_dict('records'),
        'hidden_columns': hidden_columns,
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
        'dropdown': {},
        'tooltip_conditional': [],
        'tooltip_data': [],
        'tooltip_header': {}
    }