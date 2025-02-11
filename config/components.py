from typing import Any, cast, Dict, List, Union

from app.style_constants import StyleConstants
from config.default_values import (
     DEFAULT_BUTTON_VALUES,
     DEFAULT_CHECKED_LINES,
     DEFAULT_END_QUARTER,
     DEFAULT_INSURER,
     DEFAULT_METRICS,
     DEFAULT_REPORTING_FORM,
)
from config.types import ButtonGroupConfig, DropdownConfigs, TreeDropdownConfig
from constants.translations import translate
from core.lines.tree import Tree
from core.metrics.options import get_metric_options

# -------- Configuration Helpers --------


def get_initial_metric_options() -> List[Dict[str, Any]]:
    """Get initial metric options for dropdown configuration."""
    options, _ = get_metric_options(DEFAULT_REPORTING_FORM, DEFAULT_METRICS)
    return options


def get_line_tree_for_form(lines_tree_158: Tree, lines_tree_162: Tree) -> Tree:
    """Get the appropriate tree based on the reporting form."""
    return (lines_tree_162 if DEFAULT_REPORTING_FORM == '0420162' else
            lines_tree_158)

# -------- Transforms --------


def period_type_transform(value: Union[str, int]) -> str:
    """Transform period type value to translated string"""
    return (translate(str(value)) if isinstance(value, int) else
            translate(value))

# -------- Configurations --------


BUTTON_GROUP_CONFIG: Dict[str, ButtonGroupConfig] = {
    'view-metrics': {
        'buttons': [
            {'label': 'Динамика', 'value': 'change'},
            {'label': 'Доля рынка', 'value': 'market-share'}
        ],
        'class_key': 'VIEW_METRICS',
        'multi_select': True,
        'default': cast(Union[str, int], DEFAULT_BUTTON_VALUES['view_metrics'])
    },
    'top-insurers': {
        'buttons': [
            {'label': 'Топ-5', 'value': 5},
            {'label': 'Топ-10', 'value': 10},
            {'label': 'Топ-20', 'value': 20},
            {'label': 'Выбрать:', 'value': 'custom'}
        ],
        'class_key': 'TOP_N',
        'default': [cast(Union[str, int], DEFAULT_BUTTON_VALUES['top_n'])]
    },
    'period-type': {
        'buttons': [
            {'label': 'YTD', 'value': 'ytd'},
            {'label': 'YoY-Q', 'value': 'yoy-q'},
            {'label': 'YoY-Y', 'value': 'yoy-y', 'hidden': True},
            {'label': 'QoQ', 'value': 'qoq'},
            {'label': 'MAT', 'value': 'mat', 'hidden': True}
        ],
        'class_key': 'PERIOD_TYPE',
        'output_transforms': [period_type_transform],
        'default': [cast(Union[str, int],
                         DEFAULT_BUTTON_VALUES['period_type'])]
    },
    'reporting-form': {
        'buttons': [
            {'label': '0420158', 'value': '0420158'},
            {'label': '0420162', 'value': '0420162'}
        ],
        'class_key': 'REPORTING_FORM',
        'default': [cast(Union[str, int],
                         DEFAULT_BUTTON_VALUES['reporting_form'])]
    },
    'periods-data-table': {
        'buttons': [
            {'label': str(f"{i}Y"), 'value': i}
            for i in range(1, 6)
        ],
        'class_key': 'NUM_PERIODS',
        'default': [cast(Union[str, int], DEFAULT_BUTTON_VALUES['periods'])]
    },
    'table-split-mode': {
        'buttons': [
            {'label': 'Страховщиков', 'value': 'insurer'},
            {'label': 'Видов страхования', 'value': 'line'}
        ],
        'class_key': 'TABLE_SPLIT',
        'default': [cast(Union[str, int], DEFAULT_BUTTON_VALUES['split_mode'])]
    }
}

DROPDOWN_CONFIG: DropdownConfigs = {
    'defaults': {
        'className': StyleConstants.DROPDOWN,
        'clearable': False,
        'disabled': False,
        'multi': False,
        'optionHeight': 18,
        'placeholder': [],
        'searchable': False,
        'options': [],
        'style': None,
        'value': []
    },
    'components': {
        'insurer': {
            'id': 'selected-insurers',
            'multi': True,
            'value': DEFAULT_INSURER,
            'placeholder': "Выберите страховщика",
            'disabled': True
        },
        'metric': {
            'id': 'metrics',
            'multi': True,
            'value': DEFAULT_METRICS,
            'placeholder': "Выберите показатель",
            'options': get_initial_metric_options()
        },
        'end_quarter': {
            'id': 'end-quarter',
            'value': DEFAULT_END_QUARTER,
            'options': [{'label': translate(DEFAULT_END_QUARTER),
                        'value': DEFAULT_END_QUARTER}],
            'placeholder': "Select quarter"
        }
    }
}

TREE_DROPDOWN_CONFIG: Dict[str, TreeDropdownConfig] = {
    'line-tree': {
        'config': {
            'placeholder': "Выберите вид страхования",
            'is_open': False,
            'states': {},
            'selected': DEFAULT_CHECKED_LINES,
        },
        'tree': get_line_tree_for_form
    }
}