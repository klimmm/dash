from typing import Dict, Any, List, Optional
import pandas as pd
from dash.dash_table.Format import Format, Scheme, Group
from pathlib import Path
from config.logging_config import get_logger
from constants.translations import translate
from constants.filter_options import METRICS
from data_process.data_utils import map_insurer, format_period, get_comparison_quarters
from application.components.resolve_variables import load_css_file, resolve_theme_variables

logger = get_logger(__name__)

# Load theme configuration
CSS_PATH = Path(__file__).parent.parent.parent / "assets" / "styles" / "01_settings" / "_tokens.css"
css_content = load_css_file(str(CSS_PATH))

# Define base theme structure with simplified column definitions
THEME = {
    'colors': {
        # Keep existing color variables
        'header_bg': 'var(--table-surface-header)',
        'header_text': '#000000',
        'cell_bg': 'var(--table-surface-cell)',
        'cell_text': 'var(--table-text-cell)',
        'border': 'var(--table-border)',
        'highlight': 'var(--table-surface-highlight)',
        'success': 'var(--color-success-600)',
        'danger': 'var(--color-danger-600)',
        'qtoq_bg': 'var(--table-surface-highlight)'
    },
    'typography': {
        # Keep existing typography variables
        'font_family': 'var(--font-family-sans)',
        'font_size': 'var(--table-font-size)',
        'header_weight': 'var(--font-weight-semibold)',
        'bold_weight': 'bold',
        'normal_weight': 'normal'
    },
    'spacing': {
        # Keep existing spacing variables
        'cell_padding': 'var(--space-2)',
        'header_padding': 'var(--space-2) var(--space-3)',
    },
    'columns': {
        'defaults': {
            'width': '100%',  # Changed from 'auto' to '100%'
            'min_width': '80px',  # Reduced from 100px for better compression
            'max_width': 'none',  # Changed from fixed 140px to allow flexibility
            'text_align': 'right'
        },
        'rank': {
            'width': 'fit-content',  # Changed from 'auto' to 'fit-content'
            'min_width': 'var(--table-col-min-width-rank)',
            'max_width': 'var(--table-col-max-width-rank)',
            'text_align': 'center'
        },
        'insurer': {
            'width': '100%',  # Changed from 'auto' to '100%'
            'min_width': 'var(--table-col-min-width-insurer)',
            'max_width': 'none',  # Changed from fixed value to allow expansion
            'text_align': 'left'
        },
        'change': {
            'width': 'fit-content',  # Changed from 'auto' to 'fit-content'
            'min_width': '100px',  # Reduced from 130px
            'max_width': 'none',  # Changed from fixed 170px to allow flexibility
            'text_align': 'center'
        }
    }
}

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
IDENTIFIER_COLS = {PLACE_COL, INSURER_COL}
SPECIAL_INSURERS = {
    'Топ': {'backgroundColor': 'var(--table-surface-highlight)', 'fontWeight': 'bold'},
    'Весь рынок': {'backgroundColor': 'var(--table-surface-highlight)', 'fontWeight': 'bold'}
}


def get_column_format(col_name: str) -> Format:
    """Get format configuration for a column"""
    # Special case for market share q-to-q change
    if 'market_share_q_to_q_change' in col_name:
        return Format(
            precision=2,
            scheme=Scheme.fixed,  # Not percentage
            group=Group.yes,
            groups=3,
            group_delimiter=',',
            sign='+'
        )
    
    # Regular percentage check for other columns
    is_percentage = any(x in col_name for x in ['market_share', 'q_to_q_change', 'ratio', 'rate'])
    return Format(
        precision=2 if is_percentage else 3,
        scheme=Scheme.percentage if is_percentage else Scheme.fixed,
        group=Group.yes,
        groups=3,
        group_delimiter=',',
        sign='+' if 'q_to_q_change' in col_name else ''
    )


def generate_dash_table_config(
    df: pd.DataFrame,
    period_type: str,
    columns_config: Optional[Dict[str, str]] = None,
    toggle_selected_market_share: Optional[List[str]] = None,
    toggle_selected_qtoq: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate complete table configuration with styling and formatting"""
    TABLE_THEME = resolve_theme_variables(THEME, css_content)
    show_market_share = toggle_selected_market_share and "show" in toggle_selected_market_share
    show_qtoq = toggle_selected_qtoq and "show" in toggle_selected_qtoq

    # Create a copy of the DataFrame to avoid modifying the original
    df_modified = df.copy()
    
    # Multiply market_share_q_to_q_change columns by 100
    market_share_qtoq_cols = [col for col in df_modified.columns if 'market_share_q_to_q_change' in col]
    for col in market_share_qtoq_cols:
        df_modified[col] = df_modified[col].apply(lambda x: '-' if x == 0 or x == '-' else x * 100)


    # Generate column configurations
    columns = []
    comparison_quarters = get_comparison_quarters(df.columns)

    for col in df.columns:
        if col in IDENTIFIER_COLS:
            translated_col = translate(col)
            columns.append({
                "id": col,
                "name": [translated_col, translated_col]
            })
            continue

        metric = next((m for m in sorted(METRICS.keys(), key=len, reverse=True) 
                      if col.startswith(m)), '')
        quarter = col[len(metric)+1:].split('_')[0] if metric else col.split('_')[0]

        is_qtoq = 'q_to_q_change' in col
        is_market_share = 'market_share' in col

        if is_qtoq:
            comparison = comparison_quarters.get(quarter, '')
            header = (f"{format_period(quarter, period_type, True)} vs "
                     f"{format_period(comparison, period_type, True)}") if comparison else format_period(quarter, period_type)
            base = 'Δ(п.п.)' if is_market_share else '%Δ'
        else:
            header = format_period(quarter, period_type)
            base = translate('market_share') if is_market_share else 'млрд руб.'

        columns.append({
            "id": col,
            "name": [base, header],
            "type": "numeric",
            "format": get_column_format(col)
        })

    # Generate styles
    style_cell_conditional = []
    for col in df.columns:
        col_type = ('rank' if col == PLACE_COL else
                   'insurer' if col == INSURER_COL else
                   'change' if 'q_to_q_change' in col else
                   'defaults')

        style_cell_conditional.append({
            'if': {'column_id': col},
            **{k: TABLE_THEME['columns'][col_type][k] for k in ['width', 'min_width', 'max_width', 'text_align']}
        })
    
        base_style = {
            'if': {'column_id': col},
            'textAlign': TABLE_THEME['columns'][col_type]['text_align'],
            'minWidth': TABLE_THEME['columns'][col_type]['min_width'],
            'width': 'auto',  # Allow columns to adjust based on content
            'maxWidth': ('none' if col == INSURER_COL else  # Let insurer column expand
                        TABLE_THEME['columns'][col_type]['max_width'])
        }
        style_cell_conditional.append(base_style)

    
    # Generate conditional styles
    style_data_conditional = [
        # Base cell background
        {'if': {'column_id': col for col in df.columns},
         'backgroundColor': TABLE_THEME['colors']['cell_bg']},

        # Rank changes styling
        {'if': {'column_id': 'N', 'filter_query': '{N} contains "(+"'},
         'background': f'linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), {TABLE_THEME["colors"]["success"]}15 calc(50% + 1.5ch), {TABLE_THEME["colors"]["success"]}15 calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'},

        # Special insurers styling
        *[{'if': {'filter_query': f'{{insurer}} contains "{insurer}"'},
           **style} for insurer, style in SPECIAL_INSURERS.items()],

        # QtoQ changes styling
        *[{'if': {'column_id': col, 'filter_query': f'{{{col}}} {op} 0'},
           'color': TABLE_THEME['colors']['success' if op == '>' else 'danger'],
           'fontWeight': TABLE_THEME['typography']['normal_weight'],
           'backgroundColor': TABLE_THEME['colors']['qtoq_bg']}
          for col in df.columns if '_q_to_q_change' in col
          for op in ['>', '<']]
    ]

    # Add negative rank change styling
    for i in range(1, 10):
        style_data_conditional.append({
            'if': {'column_id': 'N', 'filter_query': f'{{N}} contains "(-{i}"'},
            'background': f'linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), {TABLE_THEME["colors"]["danger"]}15 calc(50% + 1.5ch), {TABLE_THEME["colors"]["danger"]}15 calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)'
        })

    style_header_conditional = [
        # Styling for N and insurer columns to span both rows
        *[{'if': {'column_id': col, 'header_index': idx},
           'textAlign': 'left' if col == INSURER_COL else 'center',
           'verticalAlign': 'bottom',
           'height': '100%',
           'backgroundColor': '#F9FAFB',  # New color for N and Insurer
           'color': TABLE_THEME['colors']['header_text'] if idx == 0 else 'transparent',
           'fontWeight': TABLE_THEME['typography']['bold_weight'],
           f'border{"Bottom" if idx == 0 else "Top"}': 'none'
          } for col in IDENTIFIER_COLS for idx in [0, 1]],
        # Styling for other columns based on their type
        *[{'if': {'column_id': col, 'header_index': idx},
           'fontWeight': TABLE_THEME['typography']['bold_weight' if idx == 0 else 'normal_weight'],
           'textAlign': 'center',
           'backgroundColor': (
               '#F0FDF4' if any(x in col for x in ['market_share', 'market_share_q_to_q_change']) else 
               '#EFF6FF' if any(x in col for x in ['q_to_q_change']) or 
                          (col not in IDENTIFIER_COLS and 
                           not any(x in col for x in ['market_share', 'market_share_q_to_q_change'])) else 
               'inherit'
           )}
          for col in df.columns if col not in IDENTIFIER_COLS
          for idx in [0, 1]]
    ]

    return {
        'style_table': {
            'overflowX': 'auto',  # Enable horizontal scroll when needed
            'width': '100%',      # Take full width of container
            'maxWidth': '100%',   # Ensure table doesn't exceed container
        },
        'style_cell': {
            'fontFamily': TABLE_THEME['typography']['font_family'],
            'fontSize': TABLE_THEME['typography']['font_size'],
            'padding': TABLE_THEME['spacing']['cell_padding'],
            'whiteSpace': 'normal',   # Allow text wrapping
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'border': f"1px solid {TABLE_THEME['colors']['border']}",
            'minWidth': '0',          # Allow cells to shrink below content width
            'width': '100%',          # Make cells fill available space
            'maxWidth': '100%',       # Prevent cells from growing too large
        },
        'style_cell_conditional': style_cell_conditional,
        'style_header': {
            'backgroundColor': TABLE_THEME['colors']['header_bg'],
            'color': TABLE_THEME['colors']['header_text'],
            'fontWeight': TABLE_THEME['typography']['header_weight'],
            'textAlign': 'center',
            'whiteSpace': 'normal',
            'padding': TABLE_THEME['spacing']['header_padding']
        },
        'style_data': {
            'backgroundColor': TABLE_THEME['colors']['cell_bg'],
            'color': TABLE_THEME['colors']['cell_text']
        },
        'style_data_conditional': style_data_conditional,
        'style_header_conditional': style_header_conditional,
        'columns': [{**col, "hideable": False, "selectable": False, 
                    "deletable": False, "renamable": False} for col in columns],
        'data': df_modified.assign(insurer=lambda x: x['insurer'].map(map_insurer)).to_dict('records'),
        'hidden_columns': [
            col for col in df.columns
            if col not in IDENTIFIER_COLS and (
                ('market_share' in col and not show_market_share) or
                ('q_to_q_change' in col and not show_qtoq)
            )
        ],
        'css': [
            # Custom CSS for better responsiveness
            {
                'selector': '.dash-table-container',
                'rule': 'max-width: 100%; width: 100%; margin: 0; padding: 0;'
            },
            {
                'selector': '.dash-spreadsheet',
                'rule': 'max-width: 100%; width: 100%;'
            },
            {
                'selector': '.dash-cell',
                'rule': 'max-width: 100%; width: auto;'
            }
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
        'editable': False,
    }