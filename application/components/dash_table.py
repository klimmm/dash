# application.components.dash_table.py

from dataclasses import dataclass
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from dash.dash_table.Format import Format, Scheme, Group
from constants.translations import translate
from constants.filter_options import METRICS
from data_process.data_utils import map_insurer
from config.logging_config import get_logger
from application.components.table_theme import TableTheme, create_default_theme

logger = get_logger(__name__)
# Column identifier constants

class ColumnIds:
    """Constants for column identifiers"""
    PLACE = 'N'
    INSURER = 'insurer'

    @classmethod
    def is_identifier_column(cls, column_id: str) -> bool:
        """Check if column is an identifier column"""
        return column_id.lower() in [cls.PLACE.lower(), cls.INSURER.lower()]

    @classmethod
    def is_data_column(cls, column_id: str) -> bool:
        """Check if column is a data column"""
        return not cls.is_identifier_column(column_id)


class TableStyler:
    """Handles table styling with theme support"""
    
    def __init__(self, theme: Optional[TableTheme] = None):
        self.theme = theme or create_default_theme()

    def get_base_styles(self) -> Dict[str, Any]:
        """Generate base styles using theme configuration"""
        return {
            'style_table': {
                'overflowX': 'auto',
                'minWidth': '100%'
            },
            'style_cell': {
                'fontFamily': self.theme.get_typography('font_family'),
                'fontSize': self.theme.get_typography('font_size'),
                'padding': self.theme.get_spacing('cell_padding'),
                'height': self.theme.get_dimension('cell_height'),
                'minHeight': self.theme.get_dimension('cell_height'),
                'whiteSpace': 'normal',
                'border': f"1px solid {self.theme.get_color('border')}"
            },
            'style_header': {
                'backgroundColor': self.theme.get_color('header_bg'),
                'color': self.theme.get_color('header_text'),
                'fontWeight': self.theme.get_typography('header_weight'),
                'textAlign': 'center',
                'height': self.theme.get_dimension('header_height'),
                'minHeight': self.theme.get_dimension('header_height'),
                'whiteSpace': 'normal',
                'padding': self.theme.get_spacing('header_padding')
            },
            'style_data': {
                'backgroundColor': self.theme.get_color('cell_bg'),
                'color': self.theme.get_color('cell_text')
            }
        }
    def create_conditional_styles(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Create conditional styles for the table"""
        special_insurers = {
            'Топ': {
                'backgroundColor': self.theme.get_color('highlight'),
                'fontWeight': 'normal'
            },
            'Весь рынок': {
                'backgroundColor': self.theme.get_color('highlight'),
                'fontWeight': 'bold'
            },
        }
    
        row_styles = [
            {'if': {'filter_query': f'{{insurer}} contains "{insurer}"'}, **style}
            for insurer, style in special_insurers.items()
        ]
    
        column_styles = []
        for col in df.columns:
            if any(pattern in col for pattern in ('_q_to_q_change', '_market_share_q_to_q_change')):
                column_styles.extend(self._get_change_column_styles(col))
            elif ColumnIds.is_identifier_column(col):
                column_styles.append(self._get_identifier_column_style(col))
    
        return column_styles, row_styles


    def _get_change_column_styles(self, col: str) -> List[Dict[str, Any]]:
        """Generate styles for change columns"""
        return [
            {
                'if': {'column_id': col, 'filter_query': f'{{{col}}} > 0'},
                'color': self.theme.get_color('success'),
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': col, 'filter_query': f'{{{col}}} < 0'},
                'color': self.theme.get_color('danger'),
                'fontWeight': 'bold'
            },
            {
                'if': {'column_id': col},
                'backgroundColor': self.theme.get_color('qtoq_bg'),
            }
        ]

    def _get_identifier_column_style(self, col: str) -> Dict[str, Any]:
        """Generate styles for identifier columns"""
        return {
            'if': {'column_id': col},
            'backgroundColor': self.theme.get_color('insurer_bg'),
            'textAlign': 'left' if col.lower() == ColumnIds.INSURER.lower() else 'center',
        }
    
    def get_column_width_styles(self) -> List[Dict[str, Any]]:
        """Generate column width styles - only alignment, widths handled by CSS"""
        return [
            {
                'if': {'column_id': ColumnIds.PLACE},
                'textAlign': 'center'
            },
            {
                'if': {'column_id': ColumnIds.INSURER},
                'textAlign': 'left'
            }
        ]
    
    def get_header_styles(self) -> List[Dict[str, Any]]:
        """Get header styles using column constants"""
        identifier_columns = [ColumnIds.PLACE, ColumnIds.INSURER]
        return [
            {
                'if': {'column_id': col, 'header_index': 0},
                'borderBottom': 'none',
                'paddingBottom': '0',
            } for col in identifier_columns
        ] + [
            {
                'if': {'column_id': col, 'header_index': 1},
                'borderTop': 'none',
                'paddingTop': '0',
                'color': 'transparent'
            } for col in identifier_columns
        ]

    def get_data_column_style(self, column_id: str) -> Dict[str, Any]:
        """Generate style for data columns - only alignment"""
        return {
            'if': {'column_id': column_id},
            'textAlign': 'center'
        }


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
            if col_id in ['N', 'insurer']:
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

def prepare_dash_table_data(
    df: pd.DataFrame, 
    period_type: str,
    styler: Optional[TableStyler] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Prepare data and styling for the dash table"""
    table_columns = [{"name": col, "id": col} for col in df.columns]
    table_data = df.assign(insurer=lambda x: x['insurer'].map(map_insurer)).to_dict('records')

    formatter = ColumnFormatter()
    styler = styler or TableStyler()  # Use provided styler or create new one

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

    # Create single styler instance to be used throughout
    styler = TableStyler()

    # Prepare columns & data using the same styler
    table_columns, table_data, style_data_conditional = prepare_dash_table_data(
        df, 
        period_type,
        styler=styler  # Pass the styler instance
    )

    # Use hidden_columns for visibility control
    visible_columns = [ColumnIds.PLACE, ColumnIds.INSURER]
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
        # Place column - bottom center alignment
        {
            'if': {'column_id': ColumnIds.PLACE, 'header_index': 0},
            'textAlign': 'center',
            'verticalAlign': 'bottom',
            'borderBottom': 'none',
            'paddingBottom': styler.theme.get_spacing('cell_padding'),
        },
        {
            'if': {'column_id': ColumnIds.PLACE, 'header_index': 1},
            'borderTop': 'none',
            'paddingTop': '0',
            'color': 'transparent',
            'textAlign': 'center',
        },
        # Insurer column - bottom left alignment
        {
            'if': {'column_id': ColumnIds.INSURER, 'header_index': 0},
            'textAlign': 'left',
            'verticalAlign': 'bottom',
            'borderBottom': 'none',
            'paddingBottom': styler.theme.get_spacing('cell_padding'),
        },
        {
            'if': {'column_id': ColumnIds.INSURER, 'header_index': 1},
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