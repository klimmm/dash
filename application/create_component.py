from dash import dcc, html
import dash_bootstrap_components as dbc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from application.style_config import StyleConstants
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

class FilterComponents:
    """Filter component configurations and creation methods"""
    
    # Class-level constants
    BASE_STYLE = {"fontSize": "0.85rem"}
    
    # Component configurations
    COMPONENT_CONFIGS = {
        'button-groups': {
            'period-type': {
                'buttons': [
                    {"label": "YTD", "value": "ytd", "style": {}},
                    {"label": "YoY-Q", "value": "yoy-q", "style": {}},
                    {"label": "YoY-Y", "value": "yoy-y", "style": {"display": "none"}},
                    {"label": "QoQ", "value": "qoq", "style": {}},
                    {"label": "MAT", "value": "mat", "style": {"display": "none"}}
                ],
                'className': StyleConstants.BTN["PERIOD"]
            },
            'reporting-form': {
                'buttons': [
                    {"label": "0420158", "value": "0420158", "style": {}},
                    {"label": "0420162", "value": "0420162", "style": {}}
                ],
                'className': StyleConstants.BTN["PERIOD"]
            },
            'metric-toggles': {
                'buttons': [
                    {"label": "Доля рынка", "value": "market-share", "style": {}},
                    {"label": "Динамика", "value": "qtoq", "style": {}}
                ],
                'className': StyleConstants.BTN["PERIOD"]
            },
            'top-insurers': {  # New button group configuration
                'buttons': [
                    {"label": "Top 5", "value": "top-5", "style": {}},
                    {"label": "Top 10", "value": "top-10", "style": {}},
                    {"label": "Top 20", "value": "top-20", "style": {}}
                ],
                'className': StyleConstants.BTN["PERIOD"]
            },
            'periods-data-table': {  # New button group for periods selection
                'buttons': [
                    {"label": "1", "value": "period-1", "style": {}},
                    {"label": "2", "value": "period-2", "style": {}},
                    {"label": "3", "value": "period-3", "style": {}},
                    {"label": "4", "value": "period-4", "style": {}},
                    {"label": "5", "value": "period-5", "style": {}}
                ],
                'className': StyleConstants.BTN["PERIOD"]
            }
            
        },
        'dropdowns': {
            'insurance-line-dropdown': {
                'options': lambda: get_categories_by_level(
                    category_structure_162 if DEFAULT_REPORTING_FORM == '0420162' 
                    else category_structure_158,
                    level=2,
                    indent_char="--"
                ),
                'multi': False,
                'clearable': False,
                'value': DEFAULT_CHECKED_LINES,
                'placeholder': "Select a category..."
            },
            'primary-metric': {
                'options': VALUE_METRICS_OPTIONS,
                'value': DEFAULT_PRIMARY_METRICS,
                'multi': False,
                'clearable': False,
                'placeholder': "Select primary metric",
                'dynamic': True
            },
            'secondary-y-metric': {
                'options': [],
                'value': DEFAULT_SECONDARY_METRICS,
                'multi': False,
                'placeholder': "Доп. показатель...",
            },
            'selected-insurers': {
                'options': [],
                'value': DEFAULT_INSURER,
                'multi': False,
                'clearable': False
            },
            'end-quarter': {
                'options': [],
                'value': DEFAULT_END_QUARTER,
                'placeholder': "Select quarter...",
                'clearable': False
            }
        },
        'checklists': {
            'business-type-checklist': {
                'options': BUSINESS_TYPE_OPTIONS,
                'value': DEFAULT_BUSINESS_TYPE,
                'switch': True,
                'inline': True
            }
        },
        'radioitems': {
            'insurer-line-switch': {
                'options': [
                    {'label': 'Insurers', 'value': 'insurers'},
                    {'label': 'Line', 'value': 'line'}
                ],
                'value': 'insurers',
                'inline': True
            }
        }
    }

    @classmethod
    def update_dropdown_options(cls, dropdown_id: str, new_options: List[Dict[str, Any]]) -> None:
        """Update options for a specific dropdown component"""
        if dropdown_id in cls.COMPONENT_CONFIGS['dropdowns']:
            cls.COMPONENT_CONFIGS['dropdowns'][dropdown_id]['options'] = new_options
            logger.debug(f"Updated options for {dropdown_id}: {new_options}")
        else:
            logger.warning(f"Attempted to update unknown dropdown: {dropdown_id}")

    @classmethod
    def create_component(cls, component_type: str, id: Optional[str] = None, **kwargs) -> Any:
        """Create a UI component based on type and kwargs"""
        # Map component types to their config group
        group_mapping = {
            "radioitems": "radioitems",
            "button-group": "button-groups",
            "dropdown": "dropdowns",
            "checklist": "checklists"
        }
        
        component_group = group_mapping.get(component_type, f"{component_type}s")
        
        # Get base config and merge with kwargs
        base_config = {}
        if id and component_group in cls.COMPONENT_CONFIGS and id in cls.COMPONENT_CONFIGS[component_group]:
            base_config = cls.COMPONENT_CONFIGS[component_group][id].copy()
            
            # Handle callable options
            if callable(base_config.get('options')):
                base_config['options'] = base_config['options']()
        
        config = {**base_config, **kwargs}
        
        # Component factory mapping
        if component_type == "dropdown":
            if config.get('dynamic'):
                return cls._create_dynamic_dropdown(id, config)
            return dcc.Dropdown(
                id=id,
                options=config.get('options', []),
                value=config.get('value'),
                multi=config.get('multi', False),
                placeholder=translate(config.get('placeholder', '')),
                clearable=config.get('clearable', True),
                className=StyleConstants.FORM["DD"]
            )
        
        elif component_type == "checklist":
            style = {**cls.BASE_STYLE, "margin": 0}
            if config.get('readonly'):
                style.update({'pointerEvents': 'none', 'opacity': 0.5})
                
            return dbc.Checklist(
                id=id,
                options=config.get('options', []),
                value=config.get('value', []),
                switch=config.get('switch', False),
                inline=config.get('inline', False),
                style=style,
                className=StyleConstants.FORM["CHECKLIST"]
            )
            
        elif component_type == "radioitems":
            return dbc.RadioItems(
                id=id,
                options=config.get('options', []),
                value=config.get('value'),
                inline=config.get('inline', False),
                className=StyleConstants.FORM["CHECKLIST"]
            )
            
        elif component_type == "button-group":
            buttons = config.get('buttons', [])
            className = config.get('className', StyleConstants.BTN["PERIOD"])
            
            return html.Div([
                dbc.Row([
                    dbc.ButtonGroup([
                        dbc.Button(
                            button["label"],
                            id=f"btn-{button['value']}",
                            className=className,
                            style=button.get("style", {})
                        ) for button in buttons
                    ])
                ], className=StyleConstants.UTILS["MB_0"])
            ])
            
        return None

    @classmethod
    def _create_dynamic_dropdown(cls, id: str, config: Dict[str, Any]) -> html.Div:
        """Create a dynamic dropdown with add button"""
        return html.Div([
            html.Div(
                className="d-flex align-items-center w-100 mb-1 pr-1",
                children=[
                    html.Div(
                        className="dash-dropdown flex-grow-1",
                        children=[
                            dcc.Dropdown(
                                id=id,
                                options=config.get('options', []),
                                value=config.get('value'),
                                multi=config.get('multi', False),
                                placeholder=translate(config.get('placeholder', '')),
                                clearable=config.get('clearable', True),
                                className=StyleConstants.FORM["DD"]
                            )
                        ]
                    ),
                    html.Button(
                        "+",
                        id=f"{id}-add-btn",
                        className=f"{StyleConstants.BTN['ADD']}"
                    )
                ]
            ),
            html.Div(
                id=f"{id}-container",
                children=[],
                className="dynamic-dropdowns-container w-100 py-0 pr-1"
            ),
            dcc.Store(id=f"{id}-all-values", data=[])
        ], className="w-100 pt-1")

    @staticmethod
    def create_filter_row(
        label_text: str,
        component: Any,
        label_width: int = 6,
        component_width: int = 6,
        vertical: bool = False,
        component_id: Optional[str] = None,
        container_id: Optional[str] = None
    ) -> html.Div:
        """Create a filter row with label and component"""
        wrapped_component = (
            html.Div(id=container_id, children=[component]) 
            if container_id 
            else component
        )
        
        if vertical:
            return html.Div([
                html.Label(label_text, className=StyleConstants.FILTER["LABEL"]),
                html.Div(wrapped_component, className=StyleConstants.FILTER["CONTENT"])
            ], className=StyleConstants.FILTER["ROW_VERTICAL"])

        return dbc.Row([
            dbc.Col(
                html.Label(label_text, className=StyleConstants.FILTER["LABEL"]),
                width=label_width
            ),
            dbc.Col(
                wrapped_component,
                width=component_width,
                className=StyleConstants.FLEX["START"] if component_id == "business-type-checklist"
                else StyleConstants.FLEX["END"]
            )
        ], className=StyleConstants.FILTER["ROW_NO_MARGIN"])

def create_metric_dropdown(index: int, options: List[Dict], value: Optional[str]) -> html.Div:
    """
    Create a metric dropdown with remove button aligned horizontally
    
    Args:
        index: Index for the dropdown
        options: List of dropdown options
        value: Current selected value
        
    Returns:
        html.Div: Container with horizontally aligned dropdown and remove button
    """
    return html.Div(
        className="d-flex align-items-center w-100 mb-1 pr-1",
        children=[
            # Dropdown wrapper
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
                        className=StyleConstants.FORM["DD"]
                    )
                ]
            ),
            # Remove button using the new style
            html.Button(
                "✕",
                id={'type': 'remove-primary-metric-btn', 'index': index},
                className=StyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )