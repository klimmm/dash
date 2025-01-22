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
from constants.filter_options import VALUE_METRICS_OPTIONS, PREMIUM_LOSS_OPTIONS
from config.default_values import (
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM,
    DEFAULT_PREMIUM_LOSS_TYPES,
    DEFAULT_INSURER
)
from config.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ComponentConfig:
    """Configuration for UI components"""
    id: str
    options: List[Dict[str, Any]]
    value: Any
    placeholder: str = ""
    clearable: bool = True
    required: bool = True
    multi: bool = False
    switch: bool = False
    inline: bool = False
    type: str = "text"
    min: Optional[int] = None
    max: Optional[int] = None
    step: Optional[int] = None



class FilterComponents:
    """Filter component configurations and creation methods"""
    BASE_STYLE = {"fontSize": "0.85rem"}
    
    # Define component configurations as class variable
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
            'primary-y-metric': {
                'options': VALUE_METRICS_OPTIONS,
                'value': DEFAULT_PRIMARY_METRICS,
                'multi': False,
                'clearable': False,
                'placeholder': "Select primary metric"
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
            'premium-loss-checklist': {
                'options': PREMIUM_LOSS_OPTIONS,
                'value': DEFAULT_PREMIUM_LOSS_TYPES,
                'switch': True,
                'inline': True
            },
            'toggle-selected-market-share': {
                'options': [{"label": "", "value": "show"}],
                'value': ['show'],
                'switch': True,
                'inline': True
            },
            'toggle-selected-qtoq': {
                'options': [{"label": "", "value": "show"}],
                'value': ['show'],
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
        },
        'inputs': {
            'number-of-insurers': {
                'value': 10,
                'type': 'number',
                'required': True,
                'min': 1,
                'max': 999,
                'step': 1
            },
            'number-of-periods-data-table': {
                'value': 2,
                'type': 'number',
                'required': True,
                'min': 1,
                'max': 999,
                'step': 1
            }
        }
    }

    @classmethod
    def update_dropdown_options(cls, dropdown_id: str, new_options: list) -> None:
        """Update options for a specific dropdown component"""
        if dropdown_id in cls.COMPONENT_CONFIGS['dropdowns']:
            cls.COMPONENT_CONFIGS['dropdowns'][dropdown_id]['options'] = new_options

    @classmethod
    def create_component(cls, component_type: str, id: Optional[str] = None, **kwargs) -> Any:
        """Create a UI component based on type and kwargs"""
        # Map component types to their config group
        group_mapping = {
            "radioitems": "radioitems",
            "button-group": "button-groups"
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
        component_factories = {
            "dropdown": lambda: dcc.Dropdown(
                id=id,
                options=config.get('options', []),
                value=config.get('value'),
                multi=config.get('multi', False),
                placeholder=translate(config.get('placeholder', '')),
                clearable=config.get('clearable', True),
                className=StyleConstants.FORM["DD"]
            ),
            "checklist": lambda: dbc.Checklist(
                id=id,
                options=config.get('options', []),
                value=config.get('value', []),
                switch=config.get('switch', False),
                inline=config.get('inline', False),
                style={**cls.BASE_STYLE, "margin": 0, 
                       **({'pointerEvents': 'none', 'opacity': 0.5} if config.get('readonly') else {})},
                className=StyleConstants.FORM["CHECKLIST"]
            ),
            "radioitems": lambda: dbc.RadioItems(
                id=id,
                options=config.get('options', []),
                value=config.get('value'),
                inline=config.get('inline', False),
                className=StyleConstants.FORM["CHECKLIST"]
            ),
            "input": lambda: dcc.Input(
                id=id,
                type=config.get('type', 'text'),
                min=config.get('min'),
                max=config.get('max'),
                step=config.get('step'),
                value=config.get('value'),
                required=config.get('required', True),
                className=StyleConstants.FORM["INPUT"]
            ),
            "button-group": lambda: html.Div([
                dbc.Row([
                    dbc.ButtonGroup([
                        dbc.Button(
                            button["label"],
                            id=f"btn-{button['value']}",
                            className=config.get('className', StyleConstants.BTN["PERIOD"]),
                            style=button.get("style", {})
                        )
                        for button in config.get('buttons', [])
                    ])
                ], className=StyleConstants.UTILS["MB_0"])
            ])
        }
        
        return component_factories.get(component_type, lambda: None)()

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
        """Create a filter row with label and component
        
        Args:
            label_text: Text for the label
            component: The component to include in the row
            label_width: Width of label column (1-12)
            component_width: Width of component column (1-12)
            vertical: Whether to stack label and component vertically
            component_id: ID of the component for styling
            container_id: If provided, wraps component in a div with this ID
        """
        # Wrap component in container if container_id is provided
        wrapped_component = (
            html.Div(id=container_id, children=[component]) 
            if container_id 
            else component
        )
        logger.warning(f"wrapped_component{wrapped_component}")
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
                className=StyleConstants.FLEX["START"] if component_id == "premium-loss-checklist" 
                else StyleConstants.FLEX["END"]
            )
        ], className=StyleConstants.FILTER["ROW_NO_MARGIN"])