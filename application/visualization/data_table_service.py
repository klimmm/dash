# application/services/data_table_service.py
from typing import Any, Dict, List, Optional

import pandas as pd
from dash.dash_table.Format import Format, Scheme, Group


class DataTableService:
    def __init__(self, formatting_service):
        self.formatting_service = formatting_service
        self.logger = formatting_service.logger

    """Service for creating and styling data tables."""

    # Color and gradient constants
    COLORS = {
        'text': {'positive': '#059669', 'negative':
                 '#dc2626', 'neutral': '#000000'},
        'bg': {'market': '#F0FDF4', 'rank': '#EFF6FF'}
    }

    GRADIENT_BASE = (
        'linear-gradient(90deg, '
        'transparent 0%, '
        'transparent calc(50% - {}ch), '
        'rgba({}, {}, {}, 0.15) calc(50% + 1.5ch), '
        'rgba({}, {}, {}, 0.15) calc(50% + 2.5ch), '
        'transparent calc(50% + 3ch), '
        'transparent 100%)'
    )

    GRADIENTS = {
        'pos': GRADIENT_BASE.format(2, 75, 181, 67, 75, 181, 67),
        'neg': GRADIENT_BASE.format(1, 219, 68, 55, 219, 68, 55)
    }

    # Base styles for cells and headers
    BASE_CELL = {
        "fontFamily": "Arial, -apple-system, system-ui, sans-serif",
        "fontSize": "0.85rem",
        "padding": "0.3rem",
        "border": "0.01rem solid #D3D3D3",
        "boxSizing": "border-box",
        "textAlign": "left",
        "minWidth": "4.5rem"
    }

    BASE_HEADER = {
        "color": "#000000",
        "fontWeight": "bold",
        "textAlign": "center",
        "whiteSpace": "wrap",
        "textOverflow": 'ellipsis',
        "overflow": "hidden",
        "padding": "0rem",
        "border": "0.01rem solid #D3D3D3"
    }

    # CSS rules for table layout
    CSS_RULES = {
        'table_layout': {
            'selector':
            '.dash-spreadsheet tr, .dash-header, td.dash-cell, th.dash-header',
            'rules': {
                "boxSizing": "border-box !important",
                "height": "auto !important",
                "minHeight": "1.4rem !important",
                "maxHeight": "1.4rem !important",
                "lineHeight": "1.4",
                "margin": "0 !important"
            }
        },
        'cell_content': {
            'selector': (
                '.dash-cell-value, .dash-header-cell-value, '
                '.unfocused, .dash-cell div, .dash-header div, '
                '.cell-markdown, .dash-cell *'
            ),
            'rules': {
                "boxSizing": "border-box !important",
                "height": "auto !important",
                "minHeight": "1.4rem",
                "maxHeight": "1.4rem !important",
                "lineHeight": "1.4 !important",
                "overflow": "visible !important",
                "textOverflow": "clip !important",
                "whiteSpace": "normal !important",
                "wordWrap": "break-word !important",
                "borderWidth": "0.05rem !important"
            }
        }
    }

    # Class variable to store complete styles
    _complete_styles = None

    @classmethod
    def get_complete_styles(cls):
        """Generate the complete styles by combining base styles with variations."""

        cls._complete_styles = {
            'header': {
                'base': cls.BASE_HEADER,
                'text': {**cls.BASE_HEADER,
                         "textAlign": "left",
                         "borderTop": "0px",
                         "borderBottom": "0px",
                         "paddingLeft": "3px",
                         "verticalAlign": "middle"},
                'numeric': {**cls.BASE_HEADER,
                            "borderBottom": "0.01rem solid #D3D3D3",
                            "borderTop": "0.01rem solid #D3D3D3",
                            "padding-left": "0.3rem",
                            "padding-right": "0.3rem"}
            },
            'cell': {
                'base': cls.BASE_CELL
            },
            'column_types': {
                'text': {
                    'default': {
                        'header': {
                            'maxWidth': '10rem',
                            'color': lambda i, has_split: "#000000" if
                            (i == 0 and not has_split) or
                            (has_split and (i == 0 or i == 1))
                            else "transparent",
                            'textAlign': lambda i, has_split:
                                'left' if has_split and i == 0 else 'left',

                            'highlight_cols': [],
                            'borders': {
                                'top': lambda i, has_split:
                                "0.01rem solid #D3D3D3" if
                                (i == 0 and not has_split)
                                or (has_split and i == 1)
                                else "0rem",
                                'left': lambda i, has_split: "0" if
                                (i == 0 and has_split)
                                else "0.01rem solid #D3D3D3",
                                'right': lambda i, has_split: "0" if
                                (i == 0 and has_split)
                                else "0.01rem solid #D3D3D3",
                                'bottom': lambda i, has_split,
                                total_rows: "0.01rem solid #D3D3D3" if
                                (has_split and i == 0) or i == total_rows
                                else "0"
                            },
                            'paddingBottom': lambda i, has_split: "1rem" if
                            (i == 0 and has_split) else None,
                            'fontWeight': lambda i, has_split: "bold" if
                            i == 0 or (has_split and i == 1) else None
                        },
                        'base': {'minWidth': "15rem", 'maxWidth': "30rem"},
                        'conditionals': {}
                    }
                },
                'numeric': {type_name: {
                        'header': {


                            'textAlign': lambda i, has_split:
                                'left' if has_split and i == 0 else 'center',
                            'maxWidth': '15rem',
                            'backgroundColor': cls.COLORS['bg']
                            ['market' if 'market' in type_name else 'rank'],
                            'highlight_cols': ['value_type', 'year_quarter'],
                            'borders': {
                                'right': lambda i, has_split: "0" if
                                (i == 0 and has_split)
                                else "0.01rem solid #D3D3D3",
                            },
                            'fontWeight': lambda i, has_split: 'normal' if
                            (i != 0 and not has_split)
                            or (has_split and i != 0) else "bold",
                        },
                        'base': {'textAlign': 'center',
                                 'minWidth': '4.5rem',
                                 'maxWidth': '4.5rem'},
                        'conditionals': (
                            {
                                'contains "-"': {
                                    'color': cls.COLORS['text']['neutral'],
                                    'backgroundColor': '#f8f9fa'},
                                '>= 0': {
                                    'color': cls.COLORS['text']['positive'],
                                    'backgroundColor': '#f8f9fa'},
                                '< 0': {
                                    'color': cls.COLORS['text']['negative'],
                                    'backgroundColor': '#f8f9fa'},
                                'contains "∞"': {
                                    'color': cls.COLORS['text']['neutral'],
                                    'backgroundColor': '#f8f9fa'}
                            } if 'change' in type_name else
                            {
                                'contains "(+"': {
                                    'backgroundImage': cls.GRADIENTS['pos']},
                                **{f'contains "(-{i}"':
                                    {'backgroundImage': cls.GRADIENTS['neg']}
                                    for i in range(1, 10)}
                            } if type_name == 'rank' else {}
                        )
                    }
                    for type_name in ['market_share', 'market_share_change',
                                      'rank', 'base', 'base_change']
                }
            },
            'css_rules': cls.CSS_RULES
        }

        return cls._complete_styles

    # Datatable base configuration
    def get_datatable_config(self):
        """Get the base datatable configuration."""
        style = self.get_complete_styles()
        return {
            'style_cell': style['cell']['base'],
            'css': [
                dict(zip(('selector', 'rule'),
                         (rule['selector'],
                         '; '.join(f"{k.lower()}: {v}"
                                   for k, v in rule['rules'].items()))))
                for rule in style['css_rules'].values()
            ],
            'sort_action': 'none',
            'sort_mode': 'single',
            'filter_action': 'none',
            'merge_duplicate_headers': True,
            'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
            'column_selectable': False,
            'row_selectable': False,
            'row_deletable': False,
            'cell_selectable': False,
            'page_action': 'none',
            'editable': False,
            'style_data': {'cursor': 'pointer'},
            'style_table': {'width': 'fit-content', 'maxWidth': '100%',
                            'overflowX': 'visible', 'minWidth': 'auto'}
        }

    def create_column_styles(self, col: str, config: Dict[str, Any]
                             ) -> List[Dict[str, Any]]:
        """Create styles for a specific column based on configuration."""
        styles = []
        if config.get('base'):
            self.logger.debug(f"config {config}")
            styles.append({"if": {"column_id": col}, **config['base']})

        if conditionals := config.get('conditionals'):
            self.logger.debug(f"conditionals {conditionals}")
            styles.extend([
                {"if": {"column_id": col,
                        "filter_query": f"{{{col}}} {cond}"}, **style}
                for cond, style in conditionals.items()
            ])
        self.logger.debug(f"styles {styles}")
        return styles

    @classmethod
    def get_header_styles(cls, col: str, col_type: str,
                          column_config: Dict[str, Any],
                          names: List[str], pivot_cols: List[str],
                          has_split: bool
                          ) -> List[Dict[str, Any]]:
        """Get the styles for table headers."""
        style = cls.get_complete_styles()
        header_config = column_config['header']
        base_style = {k: v for k, v in style['header']['base'].items()
                      if k != "type"}

        styles = []
        for i, name in enumerate(names):
            style_dict = {"if": {"column_id": col,
                                 "header_index": i}, **base_style}
            style_dict.update(style['header'][col_type])

            if has_split and i == 0:
                style_dict["backgroundColor"] = "white"
            else:
                pivot_idx = i - (1 if has_split else 0)
                style_dict["backgroundColor"] = (
                    header_config['backgroundColor'] if pivot_cols[pivot_idx]
                    in header_config['highlight_cols'] else None)

            for key, func in header_config.get('borders', {}).items():
                style_dict[f"border{key.capitalize()}"] = (
                    func(i, has_split, len(names)) if key == 'bottom'
                    else func(i, has_split)
                )
            style_dict["maxWidth"] = header_config["maxWidth"]
            for attr in ['color', 'paddingBottom', 'fontWeight', 'textAlign']:
                if attr in header_config:
                    style_dict[attr] = header_config[attr](i, has_split)

            styles.append(style_dict)
        return styles

    def get_column(
        self,
        col: str,
        pivot_cols: List[str],
        index_cols: List[str],
        period_type: str,
        split_col: Optional[List[str]] = None,
        split_val: Optional[List[str]] = None,
        metric_vals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create configured datatable column with styling."""
        style = self.get_complete_styles()

        has_split = bool(split_col and split_val)

        names = [' - '.join(self.formatting_service.format_value(
            split_val, split_col, period_type))] if has_split else []

        if col in index_cols:
            names.extend([self.formatting_service.format_value(col)] *
                         (len(pivot_cols) - (1 if has_split else 0)))
            col_type, col_key = "text", "default"
            columns_format = None
        else:
            pivot_vals = col.split('&')
            self.logger.debug(f"metric_vals {metric_vals}")
            metric_unit = None
            metric = None
            if pivot_cols and pivot_vals and 'metric' in pivot_cols:
                metric = pivot_vals[pivot_cols.index('metric')]
                metric_unit = self.formatting_service.get_metric_unit(
                    pivot_vals[pivot_cols.index('metric')])
            elif split_col and split_val and 'metric' in split_col:
                metric = split_val[split_col.index('metric')]
                metric_unit = self.formatting_service.get_metric_unit(
                    split_val[split_col.index('metric')])
            else:
                metric = metric_vals

            names.extend(self.formatting_service.format_value(
                pivot_vals, pivot_cols, period_type, metric))

            col_type = "numeric"
            col_key = max((k for k in style['column_types'][col_type]
                          if k in col.lower() and k != 'base'),
                          key=len, default='base')
            is_pct = any(ind in col for ind in {
                'market_share', 'change'}) or metric_unit == '%'
            columns_format = Format(
                precision=2 if is_pct else 3,
                scheme=Scheme.percentage if is_pct and
                'market_share_change' not in col
                else Scheme.fixed,
                group=Group.yes,
                groups=3,
                sign='+' if 'change' in col else ''
            )
        column_config = style['column_types'][col_type][col_key]

        return names, col_type, column_config, columns_format

    def create_datatable(
        self,
        df: pd.DataFrame,
        pivot_cols: List[str],
        index_cols: List[str],
        period_type: str,
        value_types: List[str],
        split_cols: Optional[List[str]] = None,
        split_vals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create configured datatable with styling."""
        try:
            columns = []
            header_styles = []
            column_styles = []
            metric_vals = []
            if 'metric' in index_cols:
                metric_vals = df['metric'].unique().tolist()

            self.logger.debug(f"metric_vals {metric_vals}")
            for col in df.columns:
                names, col_type, column_config, columns_format = self.get_column(
                    col, pivot_cols, index_cols, period_type, split_cols, split_vals, metric_vals)
                self.logger.debug(f"Column {col}, names: {names}, type of names: {type(names)}")
                self.logger.debug(f"dynamic-table-{split_cols}-{str(split_vals).replace(' ', '')}")

                columns.append({
                    "id": col,
                    "name": names,
                    "type": col_type,
                    "format": columns_format
                })

                header_styles.extend(self.get_header_styles(
                    col, col_type, column_config, names, pivot_cols,
                    bool(split_cols and split_vals)))
                column_styles.extend(self.create_column_styles(col, column_config))
            self.logger.debug(f"column_styles {column_styles}")

            # Apply mapping functions to relevant columns
            for col in df.columns:
                if col in index_cols:
                    values = df[col].fillna('').tolist()  # Convert Series to list
                    mapped_values = self.formatting_service.format_value(values)
                    df[col] = mapped_values
            # Handle column visibility
            visibility_map = {
                'market_share': 'market_share' in value_types,
                'rank': 'rank' in value_types,
                'change': 'base_change' in value_types,
                'base': 'base' in value_types
            }
            hidden_cols = [
                col for col in df.columns
                if any(not show for key, show in visibility_map.items()
                       if key in col)
            ]
            return {
                'id':
                f"dynamic-table-{split_cols}-{str(split_vals).replace(' ', '')}",
                'columns': [{
                    **col,
                    'hideable': False,
                    'selectable': False,
                    'deletable': False,
                    'renamable': False
                } for col in columns],
                'hidden_columns': hidden_cols,
                'data': df.to_dict('records'),
                'style_header_conditional': header_styles,
                'style_data_conditional': [
                    *[{'if': {'row_index': i},
                       'backgroundColor': '#eeeff0',
                       'color': '#212529'}
                      for i, row in enumerate(df.to_dict('records'))
                      if any(kw in str(v).lower()
                             for v in row.values()
                             for kw in {'top', 'топ',
                                        'весь рынок', 'всего'} if v)],
                    *column_styles,
                    {'if': {'state': 'active'},
                     'backgroundColor': 'rgba(0, 116, 217, 0.1)'}
                ],
                **self.get_datatable_config()
            }
        except Exception as e:
            self.logger.error(f"Datatable creation error: {e}")
            raise