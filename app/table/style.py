from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, TypedDict

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


class ColumnConfig(TypedDict):
    type: str
    width: str
    align: str


class BaseStyle(TypedDict):
    fontFamily: str
    fontSize: str
    padding: str
    borderWidth: str
    boxSizing: str
    borderSpacing: str
    borderCollapse: str


class HeaderStyle(TypedDict):
    backgroundColor: str
    color: str
    fontWeight: str
    textAlign: str
    padding: str


class DataStyle(TypedDict):
    backgroundColor: str
    color: str


@dataclass
class TableStyle:
    # Define class-level constants
    DEFAULT_COLS: ClassVar[Dict[str, ColumnConfig]] = {
        'RANK': {'type': 'N', 'width': '3.9rem', 'align': 'center'},
        'INSURER': {'type': 'insurer', 'width': '17rem', 'align': 'left'},
        'LINE': {'type': 'linemain', 'width': '17rem', 'align': 'left'},
        'CHANGE': {'type': '_change', 'width': '6rem', 'align': 'center'},
        'DEFAULT': {'type': 'default', 'width': '6rem', 'align': 'right'}
    }

    DEFAULT_ROW_TYPES: ClassVar[Dict[str, str]] = {
        'SECTION': 'is_section_header',
        'TOP': 'топ',
        'TOTAL': 'весь рынок'
    }

    DEFAULT_BASE_STYLES: ClassVar[Dict[str, Dict[str, str]]] = {
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

    # Instance attributes initialized with class defaults
    COLS: Dict[str, ColumnConfig] = field(
        default_factory=lambda: TableStyle.DEFAULT_COLS.copy()
    )
    ROW_TYPES: Dict[str, str] = field(
        default_factory=lambda: TableStyle.DEFAULT_ROW_TYPES.copy()
    )
    BASE_STYLES: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: TableStyle.DEFAULT_BASE_STYLES.copy()
    )

    @classmethod
    def _get_col_config(cls, col: str) -> ColumnConfig:
        """Get column configuration based on column name."""
        for config in cls.DEFAULT_COLS.values():
            if config['type'] == col or ('_change' in col
                                         and config['type'] == '_change'):
                return config
        return cls.DEFAULT_COLS['DEFAULT']

    def _gen_cell_style(self, col: str) -> Dict[str, Any]:
        """Generate cell style configuration."""
        config = self._get_col_config(col)
        return {
            'if': {'column_id': col},
            'minWidth': config['width'],
            'maxWidth': config['width'],
            'width': config['width'],
            'textAlign': config['align']
        }

    def _gen_header_style(self, col: str, idx: int) -> Dict[str, Any]:
        """Generate header style for column."""
        style: Dict[str, Any] = {'if': {'column_id': col, 'header_index': idx}}
        config = self._get_col_config(col)

        if config['type'] in ('insurer', 'linemain', 'N'):
            style.update({
                'textAlign': 'center' if (idx == 1 and config['type'] == 'N')
                else 'left',
                'paddingLeft': '15px' if idx == 0 else '3px',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderLeft': '0.05rem solid #D3D3D3' if idx == 1 or idx == 2
                else '0px',
                'borderRight': '0.05rem solid #D3D3D3',
                'borderTop': '0.05rem solid #D3D3D3' if idx == 1 else '0px',
                'backgroundColor': '#FFFFFF' if idx == 0 else '#f8f9fa',
                'color': '#000000' if idx in (0, 1) else 'transparent',
                'fontWeight': 'bold' if idx == 0 else 'normal'
            })
        else:
            style.update({
                'backgroundColor': '#FFFFFF' if idx == 0 else '#F0FDF4'
                if 'market_share' in col else '#EFF6FF',
                'paddingBottom': '6px' if idx == 0 else '0px',
                'borderTop': '0.05rem solid #D3D3D3' if idx == 1 else '0px',
                'fontWeight': 'bold' if idx == 0 else 'normal'
            })
        return style

    def _gen_conditional_styles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate all conditional styles.

        Args:
            df: Input DataFrame to generate styles for

        Returns:
            List of style dictionaries for conditional formatting
        """
        styles: List[Dict[str, Any]] = []

        # Softer, more professional color gradients
        POSITIVE_GRADIENT = (
            "linear-gradient(90deg, "
            "transparent 0%, "
            "transparent calc(50% - 2ch), "
            "rgba(75, 181, 67, 0.15) calc(50% + 1.5ch), "  # Muted green with lower opacity
            "rgba(75, 181, 67, 0.15) calc(50% + 2.5ch), "
            "transparent calc(50% + 3ch), "
            "transparent 100%)"
        )
        
        NEGATIVE_GRADIENT = (
            "linear-gradient(90deg, "
            "transparent 0%, "
            "transparent calc(50% - 1ch), "
            "rgba(219, 68, 55, 0.15) calc(50% + 1.5ch), "  # Muted red with lower opacity
            "rgba(219, 68, 55, 0.15) calc(50% + 2.5ch), "
            "transparent calc(50% + 3ch), "
            "transparent 100%)"
        )

        # Add positive value style
        styles.append({
            'if': {
                'column_id': 'N',
                'filter_query': '{N} contains "(+"'
            },
            'backgroundImage': POSITIVE_GRADIENT
        })

        # Add negative value style

        for i in range(1, 10):
            styles.append({
                'if': {
                    'column_id': 'N',
                    'filter_query': f'{{N}} contains "(-{i}"'
                },
                'backgroundImage': NEGATIVE_GRADIENT
            })

        change_cols = [col for col in df.columns if '_change' in col]
        for col in change_cols:
            styles.extend([
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} > 0'},
                 'color': '#059669', 'backgroundColor': '#f8f9fa'},
                {'if': {'column_id': col, 'filter_query': f'{{{col}}} < 0'},
                 'color': '#dc2626', 'backgroundColor': '#f8f9fa'}
            ])

        for idx, row in enumerate(df.to_dict('records')):
            if any(row.get(k) for k in self.ROW_TYPES.values()):
                style: Dict[str, Any] = {
                    'if': {'row_index': idx},
                    'backgroundColor': '#f8f9fa',
                    'fontWeight': 'bold'
                }
                if row.get(self.ROW_TYPES['SECTION']):
                    style.update({
                        'backgroundColor': '#E5E7EB',
                        'borderTop': '0.05rem solid #D3D3D3',
                        'color': '#374151'
                    })
                styles.append(style)

        return styles

    @classmethod
    def _get_css_rules(cls) -> Dict[str, Dict[str, str]]:
        BASIC_CELL_STYLES = {
            "rule": (
                "box-sizing: border-box !important; "
                "height: auto !important; "
                "min-height: 1.2rem; "
                "max-height: none !important; "
                "line-height: 1.4; "
                "margin: 0 !important;"
            )
        }

        EXTENDED_CELL_STYLES = {
            "rule": (
                "box-sizing: border-box !important; "
                "height: auto !important; "
                "min-height: 1.2rem; "
                "max-height: none !important; "
                "line-height: 1.4; "
                "overflow: visible !important; "
                "text-overflow: clip !important; "
                "white-space: normal !important; "
                "word-wrap: break-word !important; "
                "border-right-width: 0.05rem !important; "
                "border-left-width: 0.05rem !important; "
                "border-top-width: 0.05rem !important; "
                "border-bottom-width: 0.05rem !important;"
            )
        }

        return {
            'th.dash-header.column-0': {
                "rule": "border-top-width: 0 !important;"
            },
            '.dash-spreadsheet tr, .dash-header, td.dash-cell, th.dash-header':
            BASIC_CELL_STYLES,
            '.dash-cell-value, .dash-header-cell-value, .unfocused, '
            '.dash-cell div, .dash-header div, .cell-markdown, .dash-cell *':
            EXTENDED_CELL_STYLES
        }

    def _get_all_styles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate complete style configuration."""
        return {
            'style_cell': self.BASE_STYLES['cell'],
            'style_header': self.BASE_STYLES['header'],
            'style_data': self.BASE_STYLES['data'],
            'style_cell_conditional': [
                self._gen_cell_style(col) for col in df.columns
            ],
            'style_header_conditional': [
                self._gen_header_style(col, idx)
                for col in df.columns
                for idx in range(3)
            ],
            'style_data_conditional': self._gen_conditional_styles(df),
            'css': [{'selector': s, 'rule': r["rule"]}
                    for s, r in self._get_css_rules().items()]
        }


def get_table_styles_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate complete table configuration."""
    return TableStyle()._get_all_styles(df)