# app.components.dropdown

from constants.translations import translate
import dash_bootstrap_components as dbc
from dash import dcc
from data_process.data_utils import category_structure, get_categories_by_level
from constants.filter_options import VALUE_METRICS_OPTIONS, REPORTING_FORM_OPTIONS
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_CHECKED_LINES, DEFAULT_END_QUARTER, DEFAULT_REPORTING_FORM
from app.layout_config import dash_dropdown_style, multi_select_value_style
from config.logging_config import get_logger
logger = get_logger(__name__)


# Modify the default values to take first item if they're lists
DEFAULT_SINGLE_LINE = DEFAULT_CHECKED_LINES[0] if isinstance(DEFAULT_CHECKED_LINES, list) else DEFAULT_CHECKED_LINES
DEFAULT_SINGLE_METRIC = DEFAULT_PRIMARY_METRICS[0] if isinstance(DEFAULT_PRIMARY_METRICS, list) else DEFAULT_PRIMARY_METRICS


DROPDOWN_CONFIG = {
    'insurance-line-dropdown': {
        'label': False,
        'options': get_categories_by_level(category_structure, level=2),
        'value': DEFAULT_SINGLE_LINE,  # Single value now
        'multi': False,  # Changed to False
        'placeholder': "Select a category..."  # Updated placeholder
    },
    'primary-y-metric': {
        'label': False,
        'options': VALUE_METRICS_OPTIONS,
        'value': DEFAULT_SINGLE_METRIC,  # Single value now
        'multi': False,  # Changed to False
        'placeholder': "Select primary metric"  # Updated placeholder
    },
    'end-quarter': {
        'label': False,
        'options': [],  # Will be populated by RangeFilter
        'value': DEFAULT_END_QUARTER,
        'multi': False,
        'placeholder': "Select quarter...",
        'clearable': False
    },
    'reporting-form': {
        'label': False,
        'options': REPORTING_FORM_OPTIONS,
        'value': DEFAULT_REPORTING_FORM,
        'multi': False,
        'placeholder': "Select reporting form...",
        'clearable': False
    }
}

def create_dropdown_component(id, width=12, xs=12, sm=12, md=12, col_class=None, dropdown_class=None):
    """Create a dropdown component without label since labels are handled in layout"""
    if id not in DROPDOWN_CONFIG:
        raise ValueError(f"No configuration found for dropdown id: {id}")
    
    config = DROPDOWN_CONFIG[id]
    current_value = config['value']
    if isinstance(current_value, list):
        current_value = current_value[0] if current_value else None
    
    logger.debug(f"Dropdown {id} value: {current_value}")
    return dbc.Col(
        dcc.Dropdown(
            id=id,
            options=config['options'],
            value=current_value,
            multi=False,
            placeholder=translate(config.get('placeholder', '')),
            clearable=config.get('clearable', True),
            className=dropdown_class
        ),
        xs=xs, sm=sm, md=md,
        className=col_class
    )

def wrap_single_value(value):
    """Helper function to wrap single values in a list"""
    if value is None:
        return []
    return [value] if not isinstance(value, list) else value