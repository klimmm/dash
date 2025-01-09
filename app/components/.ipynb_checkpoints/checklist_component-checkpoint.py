# checklist_component.py
from constants.filter_options import PREMIUM_LOSS_OPTIONS
from config.default_values import DEFAULT_PREMIUM_LOSS_TYPES
from dash import html
import dash_bootstrap_components as dbc
from app.layout_config import common_label_style, switch_wrapper_style, common_container_style


CHECKLIST_CONFIG = {
    'premium-loss-checklist': {
        'options': PREMIUM_LOSS_OPTIONS,
        'value': DEFAULT_PREMIUM_LOSS_TYPES,
        'show_label': True,
        'label': '',
        'col_width': 12,
        'switch': True,
        'inline': True
    },
    'toggle-selected-market-share': {
        'options': [{"label": "", "value": "show"}],
        'value': ["show"],
        'show_label': True,
        'label': 'Show market share:',
        'col_width': 6,
        'switch': True,
        'inline': True
    },
    'toggle-selected-qtoq': {
        'options': [{"label": "", "value": "show"}],
        'value': ["show"],
        'show_label': True,
        'label': 'Show growth:',
        'col_width': 6,
        'switch': True,
        'inline': True
    }
}


def create_checklist_component(id, readonly=False, value=None, container_class=None, label_class=None, switch_class=None, inline_class=None):
    """Create a checklist component"""
    config = CHECKLIST_CONFIG.get(id, {})
    class_names = []
    if config.get('switch', False) and switch_class:
        class_names.append(switch_class)
    if config.get('inline', False) and inline_class:
        class_names.append(inline_class)
        
    checklist_value = value if value is not None else config.get('value', [])
    
    checklist_style = {"margin": 0}
    if readonly:
        checklist_style.update({
            "pointerEvents": "none",
            "opacity": 0.5
        })
    
    return html.Div([
        html.Label(
            config.get('label', ''),
            className=label_class
        ),
        html.Div([
            dbc.Checklist(
                id=id,
                options=config.get('options', []),
                value=checklist_value,
                switch=config.get('switch', False),
                inline=config.get('inline', False),
                className=" ".join(class_names) if class_names else None,
                style=checklist_style
            )
        ], style=switch_wrapper_style)
    ], className=container_class)