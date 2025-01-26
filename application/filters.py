"""
Optimized implementation of filter components and styling for dashboard application.
Major improvements:
1. Consolidated style definitions into a more maintainable structure
2. Simplified component creation logic
3. Reduced redundancy in filter configurations
4. Improved type hints and documentation
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Union
from functools import partial

from constants.translations import translate
from data_process.data_utils import (
    category_structure_162,
    category_structure_158,
    get_categories_by_level
)
from constants.filter_options import VALUE_METRICS_OPTIONS, BUSINESS_TYPE_OPTIONS
from config.default_values import (
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM,
    DEFAULT_BUSINESS_TYPE,
    DEFAULT_INSURER
)
from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class StyleConfig:
    """Centralized style configuration"""
    COLORS = {
        'primary': '#8884d8',
        'secondary': '#82ca9d',
        'positive': '#4ade80',
        'negative': '#f87171',
        'grid': 'rgb(226, 232, 240)',
        'text': {
            'primary': 'rgb(17, 24, 39)',
            'secondary': 'rgb(107, 114, 128)',
            'muted': 'rgb(156, 163, 175)'
        },
        'border': 'rgb(226, 232, 240)'
    }
    
    CARD = {
        'base': {
            'border-radius': '0.5rem',
            'border': '1px solid rgb(226, 232, 240)',
            'background-color': 'white',
            'box-shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            'height': '100%'
        },
        'header': {
            'padding': '1rem 1.5rem 0.5rem',
            'border-bottom': 'none',
            'background-color': 'transparent'
        }
    }

class StyleConstants:
    """CSS class names and style constants"""
    
    NAV = "main-nav"
    LAYOUT = "layout-wrapper"
    SIDEBAR = "sidebar-col"
    SIDEBAR_COLLAPSED = "sidebar-col collapsed"
    TREE = "tree"
    
    CONTAINER = {
        "CHART": "chart-container",
        "CHART_COLLAPSED": "chart-container collapsed",
        "TREE": "tree-container",
        "DATA_TABLE": "datatable-container",
        "TITLES": "titles-container",
        "TITLES_CHART": "titles-container-chart",
        "CARD": "card-container",
        "TABS": "tabs-container",
        "GRAPH": "graph-container"
    }
    
    FORM = {
        "DD": "dd-control",
        "CHECKLIST": "checklist",
        "INPUT": "form-control input-short"
    }
    
    BTN = {
        "PERIOD": "btn-custom btn-period",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TAB": "btn-custom btn-tab",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "ADD": "btn-metric-add pr-1",
        "REMOVE": "btn-metric-remove"
    }
    
    FILTER = {
        "LABEL": "filter-label",
        "CONTENT": "filter-content w-100",
        "ROW": "filter-row",
        "ROW_VERTICAL": "filter-row filter-row--vertical",
        "ROW_NO_MARGIN": "filter-row mb-0",
        "COLUMN": "filter-column",
        "MAIN": "main-filter-column"
    }
    
    FLEX = {
        "START": "d-flex justify-content-start",
        "END": "d-flex justify-content-end",
        "CENTER": "d-flex justify-content-center"
    }
    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text"
    }

class FilterComponentFactory:
    """Factory for creating filter components with consistent styling"""
    
    BASE_STYLE = {"fontSize": "0.85rem"}
    
    @staticmethod
    def create_dropdown(
        id: str,
        options: List[Dict],
        value: Any = None,
        multi: bool = False,
        placeholder: str = "",
        clearable: bool = True,
        dynamic: bool = False
    ) -> Union[html.Div, dcc.Dropdown]:
        """Create a dropdown component with optional dynamic behavior"""
        dropdown = dcc.Dropdown(
            id=id,
            options=options,
            value=value,
            multi=multi,
            placeholder=translate(placeholder),
            clearable=clearable,
            className=StyleConstants.FORM["DD"],
            optionHeight=18
        )
        
        if not dynamic:
            return dropdown
            
        return html.Div([
            html.Div(
                className="d-flex align-items-center w-100",
                children=[
                    html.Div(dropdown, className="dash-dropdown flex-grow-1"),
                    html.Button("+", id=f"{id}-add-btn", className=StyleConstants.BTN["ADD"])
                ]
            ),
            html.Div(id=f"{id}-container", children=[], className="dynamic-dropdowns-container w-100 py-0 pr-1"),
            dcc.Store(id=f"{id}-all-values", data=[])
        ], className="w-100")

    @staticmethod
    def create_checklist(
        id: str,
        options: List[Dict],
        value: List = None,
        switch: bool = False,
        inline: bool = False,
        readonly: bool = False
    ) -> dbc.Checklist:
        """Create a checklist component"""
        style = {**FilterComponentFactory.BASE_STYLE, "margin": 0}
        if readonly:
            style.update({'pointerEvents': 'none', 'opacity': 0.5})

        return dbc.Checklist(
            id=id,
            options=options,
            value=value or [],
            switch=switch,
            inline=inline,
            style=style,
            className=StyleConstants.FORM["CHECKLIST"]
        )

    @staticmethod
    def create_button_group(
        component_id: str,
        buttons: List[Dict[str, Any]],
        section_prefix: str,
        className: str = StyleConstants.BTN["PERIOD"]
    ) -> html.Div:
        """Create a button group component with consistent styling
        
        Args:
            component_id: Identifier for the button group
            buttons: Button configurations
            section_prefix: Prefix for button IDs (e.g. 'expanded' or 'collapsed')
            className: CSS class for styling buttons
        """
        # Get button config from the button_configs dictionary
        button_config = buttons
        button_list = button_config.get('buttons') if isinstance(button_config, dict) else button_config
        custom_className = button_config.get('className', className) if isinstance(button_config, dict) else className
    
        return html.Div([
            dbc.Row([
                dbc.ButtonGroup([
                    dbc.Button(
                        btn["label"],
                        id=f"{section_prefix}-btn-{component_id}-{btn['value']}",
                        className=custom_className,
                        style=btn.get("style", {})
                    ) for btn in button_list
                ])
            ], className=StyleConstants.UTILS["MB_0"])
        ])
    

    @staticmethod
    def create_filter_row(
        label: str,
        component: Any,
        label_width: int = 6,
        component_width: int = 6,
        vertical: bool = False,
        component_id: Optional[str] = None
    ) -> html.Div:
        """Create a filter row with label and component"""
        if vertical:
            return html.Div([
                html.Label(label, className=StyleConstants.FILTER["LABEL"]),
                html.Div(component, className=StyleConstants.FILTER["CONTENT"])
            ], className=StyleConstants.FILTER["ROW_VERTICAL"])
        
        flex_class = (
            StyleConstants.FLEX["CENTER"]
            if component_id == "business-type-checklist"
            else StyleConstants.FLEX["CENTER"]
        )
        
        return dbc.Row([
            dbc.Col(
                html.Label(label, className=StyleConstants.FILTER["LABEL"]),
                width=label_width
            ),
            dbc.Col(
                component,
                width=component_width,
                className=flex_class
            )
        ], className=StyleConstants.FILTER["ROW_NO_MARGIN"])

def create_metric_dropdown(index: int, options: List[Dict], value: Optional[str]) -> html.Div:
    """Create a metric dropdown with remove button"""
    return html.Div(
        className="d-flex align-items-center w-100",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    dcc.Dropdown(
                        id={'type': 'dynamic-primary-metric', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select primary metric",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18
                    )
                ]
            ),
            html.Button(
                "✕",
                id={'type': 'remove-primary-metric-btn', 'index': index},
                className=StyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )

def create_insurer_dropdown(index: int, options: List[Dict], value: Optional[str]) -> html.Div:
    return html.Div(
        className="d-flex align-items-center w-100 mb-1 pr-1",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    dcc.Dropdown(
                        id={'type': 'dynamic-selected-insurers', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select insurer",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18

                    )
                ]
            ),
            html.Button(
                "✕",
                id={'type': 'remove-selected-insurers-btn', 'index': index},
                className=StyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )


def create_filter_section(
    config: Dict,
    style_class: str,
    section_prefix: str,
    button_configs: Dict[str, List[Dict]]
) -> List[html.Div]:
    """Helper function to create filter sections"""
    factory = FilterComponentFactory()
    rows = []
    for section in config:
        columns = []
        for col_data in section['columns']:
            label, comp_type, comp_id, label_width, comp_width = col_data
            
            # Create component based on type
            if comp_type == 'dropdown':
                # Configure dropdown options and values based on component id
                dropdown_configs = {
                    'primary-metric': {
                        'options': VALUE_METRICS_OPTIONS,
                        'value': DEFAULT_PRIMARY_METRICS,
                        'dynamic': True,
                        'clearable': False
                    },
                    'secondary-y-metric': {
                        'options': VALUE_METRICS_OPTIONS,
                        'value': DEFAULT_SECONDARY_METRICS,
                        'placeholder': "Доп. показатель..."
                    },
                    'selected-insurers': {
                        'options': [{'label': 'Весь рынок', 'value': 'total'}],
                        'value': DEFAULT_INSURER,
                        'clearable': False,
                        'dynamic': True
                    },
                    'end-quarter': {
                        'options': [{'label': '2024Q3', 'value': '2024Q3'}],
                        'value': DEFAULT_END_QUARTER,
                        'clearable': False
                    },
                    'insurance-line-dropdown': {
                        'options': get_categories_by_level(
                            category_structure_162 if DEFAULT_REPORTING_FORM == '0420162' 
                            else category_structure_158,
                            level=2,
                            indent_char="--"
                        ),
                        'value': DEFAULT_CHECKED_LINES,
                        'dynamic': True,
                        'clearable': False
                    }
                }
                
                config = dropdown_configs.get(comp_id, {})
                component = factory.create_dropdown(
                    id=comp_id,
                    options=config.get('options', []),
                    value=config.get('value'),
                    dynamic=config.get('dynamic', False),
                    clearable=config.get('clearable', True),
                    placeholder=config.get('placeholder', "Select...")
                )
            elif comp_type == 'checklist':
                component = factory.create_checklist(
                    id=comp_id,
                    options=BUSINESS_TYPE_OPTIONS,
                    value=DEFAULT_BUSINESS_TYPE,
                    switch=True,
                    inline=True
                )
                if comp_id == 'business-type-checklist':
                    component = html.Div(
                        id='business-type-checklist-container',
                        children=[component]
                    )
            elif comp_type == 'button-group':
                button_config = button_configs.get(comp_id, [])
                # Create button configuration with className
                if comp_id in ['period-type', 'periods-data-table', 'metric-toggles'] and section.get('row_className') == 'button-groups-row':
                    button_config = {
                        'buttons': button_config,
                        'className': 'btn-custom btn-group-control'
                    }
                component = factory.create_button_group(
                    component_id=comp_id,
                    buttons=button_config,
                    section_prefix=section_prefix
                )
            else:
                continue
            
            if label:  # Only create filter row if there's a label
                component = factory.create_filter_row(
                    label=label,
                    component=component,
                    label_width=label_width,
                    component_width=comp_width,
                    component_id=comp_id
                )
            
            columns.append(dbc.Col(
                component,
                **section.get('column_widths', {'xs': 12, 'sm': 12, 'md': 6}),
                className=StyleConstants.FILTER["MAIN"]
            ))
        
        # Combine the base style_class with any row-specific className
        row_className = style_class
        if section.get('row_className'):
            row_className = f"{section.get('row_className')}"
        
        row_kwargs = {
            'children': columns,
            'className': row_className
        }
        
        if section.get('id'):
            row_kwargs['id'] = section['id']
            
        if section.get('style'):
            row_kwargs['style'] = section['style']
            
        row = dbc.Row(**row_kwargs)
        rows.append(row)
    
    return rows

def create_filters() -> html.Div:
    """Create the complete filter interface"""
    factory = FilterComponentFactory()
    
    # Define filter configurations
    filter_configs = {
        'sidebar_collapsed': [
            {
                'id': 'sidebar-col',
                'columns': [
                    ('Отчетный квартал:', 'dropdown', 'end-quarter', 8, 4),
                    ('Бизнес:', 'checklist', 'business-type-checklist', 3, 9),
                    ('Доп. показатель:', 'dropdown', 'secondary-y-metric', 4, 8)
                ],
                'column_widths': {'xs': 6, 'sm': 6, 'md': 4}
            }
        ],
        'sidebar': [
            {
                'columns': [
                    ('Отчетность:', 'button-group', 'reporting-form', 3, 9),
                    (' ', 'button-group', 'top-insurers', 3, 9)
                ],
                'column_widths': {'xs': 6, 'sm': 6, 'md': 4}
            },
            {
                'columns': [
                    ('Страховщик:', 'dropdown', 'selected-insurers', 3, 9),
                    ('Вид страхования:', 'dropdown', 'insurance-line-dropdown', 3, 9),
                    ('Показатель:', 'dropdown', 'primary-metric', 3, 9)
                ]
            },
            {  # Bottom row with three columns for button groups
                'columns': [
                    (' ', 'button-group', 'period-type', 1, 11),
                    (' ', 'button-group', 'periods-data-table', 1, 11),
                    (' ', 'button-group', 'metric-toggles', 1, 11)
                ],
                'column_widths': {'xs': 4, 'sm': 4, 'md': 4},
                'row_className': 'button-groups-row'
            }
        ]
    }

    # Button configurations
    button_configs = {
        'reporting-form': [
            {"label": "0420158", "value": "0420158"},
            {"label": "0420162", "value": "0420162"}
        ],
        'top-insurers': [
            {"label": "Top 5", "value": "top-5"},
            {"label": "Top 10", "value": "top-10"},
            {"label": "Top 20", "value": "top-20"}
        ],
        'period-type': [
            {"label": "YTD", "value": "ytd"},
            {"label": "YoY-Q", "value": "yoy-q"},
            {"label": "YoY-Y", "value": "yoy-y", "style": {"display": "none"}},
            {"label": "QoQ", "value": "qoq"},
            {"label": "MAT", "value": "mat", "style": {"display": "none"}}
        ],
        'periods-data-table': [
            {"label": str(i), "value": f"period-{i}"} 
            for i in range(1, 6)
        ],
        'metric-toggles': [
            {"label": "Доля рынка", "value": "market-share"},
            {"label": "Динамика", "value": "qtoq"}
        ]
    }

    # Create all filter sections
    collapsed_rows = create_filter_section(
        filter_configs['sidebar_collapsed'],
        StyleConstants.SIDEBAR_COLLAPSED,
        section_prefix="collapsed",
        button_configs=button_configs
    )
    
    sidebar_rows = create_filter_section(
        filter_configs['sidebar'],
        StyleConstants.SIDEBAR,
        section_prefix="expanded",
        button_configs=button_configs
    )
    
    # Add period type text div after first row
    period_type_div = html.Div(
        id="period-type-text",
        className=StyleConstants.UTILS["PERIOD_TYPE"],
        style={"display": "none"}
    )
    
    all_rows = (
        collapsed_rows[:1] +
        [period_type_div] +
        collapsed_rows[1:] +
        sidebar_rows
    )
    
    return html.Div(dbc.CardBody(all_rows))