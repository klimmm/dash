# application.components.dash_table.py

from dataclasses import dataclass
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from dash.dash_table.Format import Format, Scheme, Group
from constants.translations import translate
from constants.filter_options import METRICS
from data_process.data_utils import map_insurer
from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass(frozen=True)
class TableColors:
    PRIMARY: str = '#3C5A99'
    SECONDARY: str = '#6C757D'
    BACKGROUND: str = '#F8F9FA'
    TEXT: str = '#212529'
    SUCCESS: str = '#28a745'
    DANGER: str = '#dc3545'
    HIGHLIGHT: str = '#FFFFE0'
    SOHAGS: str = '#D4EDDA'
    QTOQ_BG: str = '#E9ECEF'
    INSURER_BG: str = '#F1F3F5'

@dataclass(frozen=True)
class TableStyles:
    FONT_FAMILY: str = 'var(--font-family-base)'
    BASE_FONT_SIZE: str = '0.8rem'
    HEADER_FONT_SIZE: str = '0.8rem'
    CELL_FONT_SIZE: str = '0.8rem'
    
    NUMBER_COL_WIDTH: str = '2rem'
    INSURER_COL_WIDTH: str = '10rem'
    DATA_COL_WIDTH: str = '5rem'
    
    CELL_PADDING: str = 'var(--spacing-md)'
    HEADER_PADDING: str = 'var(--spacing-sm) var(--spacing-lg) var(--spacing-sm) var(--spacing-sm)'

class TableStyler:
    def __init__(self):
        self.colors = TableColors()
        self.styles = TableStyles()

    def get_base_styles(self) -> Dict[str, Any]:
        return {
            'style_table': {
                'overflowX': 'auto',
                'backgroundColor': 'var(--color-bg)',
                'boxShadow': '0 0.25rem 0.375rem rgba(0, 0, 0, 0.1)',
                'borderRadius': 'var(--border-radius)',
            },
            'style_cell': {
                'textAlign': 'left',
                'padding': self.styles.CELL_PADDING,
                'border': '1px solid var(--color-border)',
                'fontSize': self.styles.CELL_FONT_SIZE,
                'fontFamily': self.styles.FONT_FAMILY,
                'color': 'var(--color-text)',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            'style_header': {
                'backgroundColor': self.colors.PRIMARY,
                'color': 'white',
                'fontWeight': 'bold',
                'textTransform': 'none',
                'borderBottom': '2px solid var(--color-border)',
                'textAlign': 'center',
                'fontSize': self.styles.HEADER_FONT_SIZE,
                'height': 'auto',
                'minHeight': '3.333rem',
                'whiteSpace': 'normal',
                'position': 'relative',
                'padding': self.styles.HEADER_PADDING,
            },
            'style_data': {
                'backgroundColor': 'var(--color-bg)',
            },
        }

    def create_conditional_styles(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        special_insurers = {
            'Топ': {'backgroundColor': self.colors.HIGHLIGHT, 'fontWeight': 'normal'},
            'Весь рынок': {'backgroundColor': self.colors.HIGHLIGHT, 'fontWeight': 'bold'},
            'СОГАЗ': {'backgroundColor': self.colors.SOHAGS, 'fontWeight': 'normal'},
            'Газпром': {'backgroundColor': self.colors.SOHAGS, 'fontWeight': 'normal'},
            'КПСК': {'backgroundColor': self.colors.SOHAGS, 'fontWeight': 'normal'},
        }

        row_styles = [
            {'if': {'filter_query': f'{{insurer}} contains "{insurer}"'}, **style}
            for insurer, style in special_insurers.items()
        ]

        column_styles = []
        for col in df.columns:
            if any(pattern in col for pattern in ('_q_to_q_change', '_market_share_q_to_q_change')):
                column_styles.extend(self._get_change_column_styles(col))
            elif col.lower() in ['место', 'insurer']:
                column_styles.append(self._get_identifier_column_style(col))

        return column_styles, row_styles

    def _get_change_column_styles(self, col: str) -> List[Dict[str, Any]]:
        return [
            {
                'if': {'column_id': col, 'filter_query': f'{{{col}}} > 0'},
                'color': self.colors.SUCCESS,
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': col, 'filter_query': f'{{{col}}} < 0'},
                'color': self.colors.DANGER,
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': col},
                'backgroundColor': self.colors.QTOQ_BG,
            }
        ]

    def _get_identifier_column_style(self, col: str) -> Dict[str, Any]:
        return {
            'if': {'column_id': col},
            'backgroundColor': self.colors.INSURER_BG,
            'textAlign': 'left' if col.lower() == 'insurer' else 'center',
        }

    def get_column_width_styles(self) -> List[Dict[str, Any]]:
        return [
            {
                'if': {'column_id': 'Место'},
                'width': self.styles.NUMBER_COL_WIDTH,
                'minWidth': self.styles.NUMBER_COL_WIDTH,
                'maxWidth': self.styles.NUMBER_COL_WIDTH,
                'textAlign': 'center'
            },
            {
                'if': {'column_id': 'insurer'},
                'width': self.styles.INSURER_COL_WIDTH,
                'minWidth': self.styles.INSURER_COL_WIDTH,
                'maxWidth': self.styles.INSURER_COL_WIDTH,
                'textAlign': 'left'
            }
        ]

    def get_data_column_style(self, column_id: str) -> Dict[str, Any]:
        return {
            'if': {'column_id': column_id},
            'width': self.styles.DATA_COL_WIDTH,
            'minWidth': self.styles.DATA_COL_WIDTH,
            'maxWidth': self.styles.DATA_COL_WIDTH,
            'textAlign': 'center'
        }

    def get_header_styles(self) -> List[Dict[str, Any]]:
        return [
            {
                'if': {'column_id': col, 'header_index': 0},
                'borderBottom': 'none',
                'paddingBottom': '0',
            } for col in ['Место', 'insurer']
        ] + [
            {
                'if': {'column_id': col, 'header_index': 1},
                'borderTop': 'none',
                'paddingTop': '0',
                'color': 'transparent'
            } for col in ['Место', 'insurer']
        ]


class ColumnFormatter:
    @staticmethod
    def get_format(col_type: str) -> Format:
        if 'market_share' in col_type or 'q_to_q_change' in col_type:
            return Format(precision=2, scheme=Scheme.percentage)
        return Format(
            precision=3,
            scheme=Scheme.fixed,
            group=Group.yes,
            groups=3,
            group_delimiter=','
        )

    @staticmethod
    def parse_quarter(quarter_str: str, period_type: str) -> str:
        if not quarter_str or 'Q' not in quarter_str:
            return quarter_str
        try:
            year, q = quarter_str.split('Q')
            period_map = {
                'ytd': {'1': '3 мес.', '2': '6 мес.', '3': '9 мес.', '4': '12 мес.'},
                'default': {'1': '1 кв.', '2': '2 кв.', '3': '3 кв.', '4': '4 кв.'}
            }
            quarter_map = period_map.get(period_type, period_map['default'])
            return f"{quarter_map.get(q, q)} {year}"
        except Exception:
            return quarter_str

    def format_columns(self, columns: List[Dict[str, Any]], metrics: Dict[str, Dict[str, str]], period_type: str) -> List[Dict[str, Any]]:
        formatted_columns = []
        for col in columns:
            col_id = col['id']
            if col_id in ['Место', 'insurer']:
                formatted_columns.append(self._format_identifier_column(col_id))
                continue

            metric, quarter, additional_info = self._parse_column_components(col_id, metrics)
            column_name = self._get_column_name(metric, quarter, additional_info, metrics, period_type)

            formatted_columns.append({
                'id': col_id,
                'type': 'numeric',
                'format': self.get_format(additional_info),
                'name': column_name
            })
        return formatted_columns

    def _parse_column_components(self, col_id: str, metrics: Dict[str, Dict[str, str]]) -> Tuple[str, str, str]:
        metric = next((m for m in sorted(metrics.keys(), key=len, reverse=True) 
                       if col_id.startswith(m)), None)
        if metric:
            remaining = col_id[len(metric)+1:].split('_')
            quarter = remaining[0] if remaining else ""
            additional_info = '_'.join(remaining[1:]) if len(remaining) > 1 else ""
        else:
            parts = col_id.split('_')
            metric, quarter, *additional_parts = parts + ["", ""]
            additional_info = '_'.join(additional_parts)
        return metric, quarter, additional_info

    def _format_identifier_column(self, col_id: str) -> Dict[str, Any]:
        translated_col = translate(col_id)
        return {
            'name': [translated_col, translated_col],
            'id': col_id
        }

    def _get_column_name(self, metric: str, quarter: str, additional_info: str, 
                        metrics: Dict[str, Dict[str, str]], period_type: str) -> List[str]:
        translated_metric = translate(metrics.get(metric, {}).get('label', metric))
        if 'market_share_q_to_q_change' in additional_info:
            return [f"{translated_metric}, {translate('market_share')}", translate('q_to_q_change')]
        elif 'market_share' in additional_info:
            return [f"{translated_metric}, {translate('market_share')}", self.parse_quarter(quarter, period_type)]
        elif 'q_to_q_change' in additional_info:
            return [f"{translated_metric}, {translate('млрд руб.')}", translate('q_to_q_change')]
        else:
            return [f"{translated_metric}, {translate('млрд руб.')}", self.parse_quarter(quarter, period_type)]

def prepare_dash_table_data(df: pd.DataFrame, period_type: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    table_columns = [{"name": col, "id": col} for col in df.columns]
    table_data = df.assign(insurer=lambda x: x['insurer'].map(map_insurer)).to_dict('records')

    formatter = ColumnFormatter()
    styler = TableStyler()

    table_columns = formatter.format_columns(table_columns, METRICS, period_type)
    column_styles, row_styles = styler.create_conditional_styles(df)

    return table_columns, table_data, (column_styles + row_styles)

def generate_dash_table_config(
    df: pd.DataFrame,
    period_type: str,
    columns_config: Optional[Dict[str, str]] = None,
    toggle_selected_market_share: Optional[List[str]] = None,
    toggle_selected_qtoq: Optional[List[str]] = None,
) -> Dict[str, Any]:
    show_selected_market_share = toggle_selected_market_share and "show" in toggle_selected_market_share
    show_selected_qtoq = toggle_selected_qtoq and "show" in toggle_selected_qtoq

    # Prepare columns & data
    table_columns, table_data, style_data_conditional = prepare_dash_table_data(df, period_type)
    styler = TableStyler()

    # Use hidden_columns for visibility control
    visible_columns = ['Место', 'insurer']
    hidden_columns = [
        col['id'] for col in table_columns
        if col['id'] not in visible_columns and (
            ('_market_share' in col['id'] and not show_selected_market_share) or
            ('_q_to_q_change' in col['id'] and not show_selected_qtoq)
        )
    ]

    # Make all columns non-hideable and non-toggleable
    enforced_columns = [
        {
            **col_def,
            "hideable": False,
            "selectable": False,
            "deletable": False,
            "renamable": False
        } for col_def in table_columns
    ]

    # Get base styles from the styler instance
    base_styles = styler.get_base_styles()
    
    # Updated header styles with specific alignments for N and insurer
    style_header_conditional = [
        # N column - bottom center alignment
        {
            'if': {'column_id': 'Место', 'header_index': 0},
            'textAlign': 'center',
            'verticalAlign': 'bottom',
            'borderBottom': 'none',
            'paddingBottom': 'var(--spacing-sm)',
        },
        {
            'if': {'column_id': 'Место', 'header_index': 1},
            'borderTop': 'none',
            'paddingTop': '0',
            'color': 'transparent',
            'textAlign': 'center',
        },
        # Insurer column - bottom left alignment
        {
            'if': {'column_id': 'insurer', 'header_index': 0},
            'textAlign': 'left',
            'verticalAlign': 'bottom',
            'borderBottom': 'none',
            'paddingBottom': 'var(--spacing-sm)',
        },
        {
            'if': {'column_id': 'insurer', 'header_index': 1},
            'borderTop': 'none',
            'paddingTop': '0',
            'color': 'transparent',
            'textAlign': 'left',
        }
    ]
    
    # Style conditionals without column visibility CSS
    style_cell_conditional = styler.get_column_width_styles() + [
        styler.get_data_column_style(col['id'])
        for col in enforced_columns if col['id'] not in visible_columns
    ]

    # Enhanced CSS rules with more specificity and !important flags
    css_rules = [
        # Target the toggle button container and all its variations
        {
            'selector': '''
                .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner 
                    .dash-fixed-content .dash-fixed-row .dash-fixed-row-info .dash-table-menu__toggle,
                .dash-spreadsheet-inner th .column-header--toggle,
                th .column-header--toggle,
                .dash-table-menu__toggle,
                .dash-table-menu__toggle--open,
                .dash-table-menu__toggle--closed,
                .dash-spreadsheet-menu,
                .dash-spreadsheet-menu *
            ''',
            'rule': '''
                display: none !important;
                width: 0 !important;
                height: 0 !important;
                opacity: 0 !important;
                pointer-events: none !important;
                position: absolute !important;
                visibility: hidden !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                clip: rect(0 0 0 0) !important;
                clip-path: inset(50%) !important;
            '''
        },
        # Target menu items and dropdowns
        {
            'selector': '''
                .dash-table-menu,
                .dash-menu-item,
                .dash-menu-item--show-hide-toggle-columns,
                .dash-menu-item--hide-columns,
                .show-hide-toggle-columns,
                .dash-table-menu__dropdown,
                .dash-table-menu__dropdown--content,
                [class*="dash-menu-item"]
            ''',
            'rule': '''
                display: none !important;
                width: 0 !important;
                height: 0 !important;
                opacity: 0 !important;
                pointer-events: none !important;
                position: absolute !important;
                visibility: hidden !important;
            '''
        },
        # Hide sort icons
        {
            'selector': '''
                .dash-header-cell::after,
                .dash-header-cell--sort-asc::after,
                .dash-header-cell--sort-desc::after
            ''',
            'rule': '''
                display: none !important;
                content: none !important;
            '''
        },
        # Header alignment specificity
        {
            'selector': '.dash-header[data-dash-column="N"]',
            'rule': '''
                text-align: center !important;
                vertical-align: bottom !important;
            '''
        },
        {
            'selector': '.dash-header[data-dash-column="insurer"]',
            'rule': '''
                text-align: left !important;
                vertical-align: bottom !important;
            '''
        },
        # Remove any menu-related margins/padding
        {
            'selector': '.dash-spreadsheet th',
            'rule': '''
                padding-right: var(--spacing-md) !important;
            '''
        }
    ]

    # Return table configuration with modified settings
    return {
        **base_styles,
        'columns': enforced_columns,
        'data': table_data,
        'hidden_columns': hidden_columns,
        'style_header_conditional': style_header_conditional,
        'style_cell_conditional': style_cell_conditional,
        'style_data_conditional': style_data_conditional,
        'sort_action': 'none',
        'sort_mode': None,
        'filter_action': 'none',
        'merge_duplicate_headers': True,
        'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
        'column_selectable': False,
        'row_selectable': False,
        'cell_selectable': False,
        'page_action': 'none',
        'css': css_rules,
        'style_table': {
            'overflowX': 'auto',
            'minWidth': '100%'
        },
        'editable': False,
        'dropdown': {},
        'tooltip_conditional': [],
        'tooltip_data': [],
        'tooltip_header': {}
    }