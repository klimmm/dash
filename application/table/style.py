from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TableStyle:
    COLS = {
        'RANK': {'type': 'N', 'width': '3.9rem', 'align': 'center'},
        'INSURER': {'type': 'insurer', 'width': '17rem', 'align': 'left'},
        'LINE': {'type': 'linemain', 'width': '17rem', 'align': 'left'},
        'CHANGE': {'type': '_change', 'width': '6rem', 'align': 'center'},
        'DEFAULT': {'type': 'default', 'width': '6rem', 'align': 'right'}
    }

    ROW_TYPES = {'SECTION': 'is_section_header', 'TOP': 'топ', 'TOTAL': 'весь рынок'}

    BASE_STYLES = {
        'cell': {
            'fontFamily': 'Arial, -apple-system, system-ui, sans-serif',
            'fontSize': '0.85rem',
            'padding': '0.3rem',
            'borderWidth': '0.05rem',
            'boxSizing': 'border-box',
            'borderSpacing': '0',
            'borderCollapse': 'collapse'
        },
        'header': {
            'backgroundColor': '#f8f9fa',
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

    @staticmethod
    def get_col_config(col: str) -> Dict[str, str]:
        """Get column configuration based on column name."""
        for config in TableStyle.COLS.values():
            if config['type'] == col or ('_change' in col and config['type'] == '_change'):
                return config
        return TableStyle.COLS['DEFAULT']

    def gen_cell_style(self, col: str) -> Dict[str, Any]:
        """Generate cell style configuration."""
        config = self.get_col_config(col)
        return {
            'if': {'column_id': col},
            'minWidth': config['width'],
            'maxWidth': config['width'],
            'width': config['width'],
            'textAlign': config['align']
        }

    def gen_header_style(self, col: str, idx: int) -> Dict[str, Any]:
        """Generate header style for column."""
        style = {'if': {'column_id': col, 'header_index': idx}}
        config = self.get_col_config(col)

        if config['type'] in ('insurer', 'linemain', 'N'):
            style.update({
                'textAlign': 'center' if (idx == 1 and config['type'] == 'N') else 'left',
                'paddingLeft': '15px' if idx == 0 else '3px',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderLeft': '0.05rem solid #D3D3D3' if idx == 1 or idx == 2 else '0px',
                'borderRight': '0.05rem solid #D3D3D3',
                'borderTop': '0.05rem solid #D3D3D3' if idx == 1 else '0px',
                'backgroundColor': '#FFFFFF' if idx == 0 else '#f8f9fa',
                'color': '#000000' if idx in (0, 1) else 'transparent',
                'fontWeight': 'bold' if idx == 0 else 'normal'
            })
        else:
            style.update({
                'backgroundColor': '#FFFFFF' if idx == 0 else
                                   '#F0FDF4' if 'market_share' in col else '#EFF6FF',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderTop': '0.05rem solid #D3D3D3' if idx == 1 else '0px',
                'fontWeight': 'bold' if idx == 0 else 'normal'
            })
        return style

    def gen_conditional_styles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate all conditional styles."""
        styles = []

        # Rank styles
        styles.append({
            'if': {'column_id': 'N', 'filter_query': '{N} contains "(+"'},
            'backgroundImage': "linear-gradient(90deg, transparent 0%, transparent calc(50% - 2ch), rgba(0, 255, 0, 0.15) calc(50% + 1.5ch), rgba(0, 255, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)"
        })

        for i in range(1, 10):
            styles.append({
                'if': {'column_id': 'N', 'filter_query': f'{{N}} contains "(-{i}"'},
                'backgroundImage': "linear-gradient(90deg, transparent 0%, transparent calc(50% - 1ch), rgba(255, 0, 0, 0.15) calc(50% + 1.5ch), rgba(255, 0, 0, 0.15) calc(50% + 2.5ch), transparent calc(50% + 3ch), transparent 100%)"
            })

        # Change column styles
        change_cols = [col for col in df.columns if '_change' in col]
        for col in change_cols:
            styles.extend([
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} > 0'},
                 'color': '#059669', 'backgroundColor': '#f8f9fa'},
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} < 0'},
                 'color': '#dc2626', 'backgroundColor': '#f8f9fa'}
            ])

        # Row styles
        for idx, row in enumerate(df.to_dict('records')):
            if any(row.get(k) for k in self.ROW_TYPES.values()):
                style = {'if': {'row_index': idx},
                         'backgroundColor': '#f8f9fa',
                         'fontWeight': 'bold'}
                if row.get(self.ROW_TYPES['SECTION']):
                    style.update({
                        'backgroundColor': '#E5E7EB',
                        'borderTop': '0.05rem solid #D3D3D3',
                        'color': '#374151'
                    })
                styles.append(style)

        return styles

    @classmethod
    def get_css_rules(cls) -> Dict[str, str]:
        return {
            'th.dash-header.column-0': "border-top-width: 0 !important;",
            '.dash-spreadsheet tr, .dash-header, td.dash-cell, th.dash-header': (
                "box-sizing: border-box !important; "
                "height: auto !important; min-height: 1.2rem; max-height: none !important; "
                "line-height: 1.4; box-sizing: border-box !important; margin: 0 !important;"
            ),
            '.dash-cell-value, .dash-header-cell-value, .unfocused, .dash-cell div, '
            '.dash-header div, .cell-markdown, .dash-cell *': (
                "box-sizing: border-box !important; "
                "height: auto !important; min-height: 1.2rem; max-height: none !important; "
                "line-height: 1.4; box-sizing: border-box !important; "
                "overflow: visible !important; text-overflow: clip !important; "
                "white-space: normal !important; word-wrap: break-word !important; "
                "box-sizing: border-box !important;"
                "border-right-width: 0.05rem !important;"
                "border-left-width: 0.05rem !important;"
                "border-top-width: 0.05rem !important;"
                "border-bottom-width: 0.05rem !important;"
            )
        }

    def get_all_styles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate complete style configuration."""
        return {
            'style_cell': self.BASE_STYLES['cell'],
            'style_header': self.BASE_STYLES['header'],
            'style_data': self.BASE_STYLES['data'],
            'style_cell_conditional': [self.gen_cell_style(col) for col in df.columns],
            'style_header_conditional': [
                self.gen_header_style(col, idx)
                for col in df.columns
                for idx in range(3)
            ],
            'style_data_conditional': self.gen_conditional_styles(df),
            'css': [{'selector': s, 'rule': r.strip()} for s, r in self.get_css_rules().items()]
        }


def get_table_styles_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate complete table configuration."""
    return TableStyle().get_all_styles(df)


__all__ = ['get_table_styles_config']