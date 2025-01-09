# input_component.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from app.layout_config import common_label_style, common_input_style, common_container_style

INPUT_CONFIG = {
    'number-of-insurers': {
        'label': 'Number of insurers:',
        'type': 'number',
        'min': 1,
        'max': 100,
        'step': 1,
        'value': 10,
        'col_width': 6
    },
    'number-of-periods-data-table': {
        'label': 'Number of periods:',
        'type': 'number',
        'min': 1,
        'max': 27,
        'step': 1,
        'value': 2,
        'col_width': 6
    }
}


def create_input_component(id, container_class=None, label_class=None, input_class=None):
    """Create an input component"""
    config = INPUT_CONFIG.get(id, {})
    return html.Div([
        html.Label(
            config.get('label', ''),
            className=label_class
        ),
        dcc.Input(
            id=id,
            type=config.get('type', 'text'),
            min=config.get('min'),
            max=config.get('max'),
            step=config.get('step'),
            value=config.get('value'),
            style=common_input_style,
            className=input_class
        )
    ], className=container_class)