from config.default_values import (
    DEFAULT_REPORTING_FORM,
    DEFAULT_PERIOD_TYPE,
    DEFAULT_SHOW_MARKET_SHARE,
    DEFAULT_SHOW_CHANGES,
    TOP_N_LIST,
    DEFAULT_NUMBER_OF_PERIODS,
    DEFAULT_SPLIT_MODE
)
from application.style.style_constants import StyleConstants



class StyleConstants:

    BTN = {
        "PERIOD": "btn-custom btn-period",
        "GROUP_CONTROL": "btn-custom btn-group-control",
        "MARKET_SHARE": "btn-custom btn-group-control",
        "TOP_N": "btn-custom btn-group-control",
        "PERIOD_TYPE": "btn-custom btn-period",
        "REPORTING_FORM": "btn-custom btn-period",
        "NUM_PERIODS": "btn-custom btn-group-control",
        "DEFAULT": "btn-custom btn-group-control",
        "TABLE_SPLIT": "btn-custom btn-group-control",
        "PERIOD_ACTIVE": "btn-custom btn-period active",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "GROUP_CONTROL_ACTIVE": "btn-custom btn-group-control active",
        "DEBUG": "btn-custom btn-debug-toggle",
        "BUTTON_GROUP_ROW": "mb-0"
    }



BUTTON_CONFIG = {
    'metric-toggles': {
        'values': ['market-share', 'qtoq'],
        'class_key': 'MARKET_SHARE',
        'total_buttons': 2,
        'multi_choice': True,
        'default_state': {'market-share': DEFAULT_SHOW_MARKET_SHARE, 'qtoq': DEFAULT_SHOW_CHANGES},
        'buttons': [
            {"label": "Доля", "value": "market-share"},
            {"label": "Динамика", "value": "qtoq"}
        ]
    },
    'top-insurers': {
        'values': [5, 10, 20, 'custom'],
        'class_key': 'TOP_N',
        'total_buttons': 4,
        'multi_choice': False,
        'default_state': TOP_N_LIST,
        'buttons': [
            {"label": "Топ-5", "value": "5"},
            {"label": "Топ-10", "value": "10"},
            {"label": "Топ-20", "value": "20"},
            {"label": "Выбрать страховщика:", "value": "custom"}
        ]
    },
    'period-type': {
        'values': ['ytd', 'yoy_q', 'yoy_y', 'qoq', 'mat'],
        'class_key': 'PERIOD_TYPE',
        'total_buttons': 5,
        'default_state': DEFAULT_PERIOD_TYPE,
        'buttons': [
            {"label": "YTD", "value": "ytd"},
            {"label": "YoY-Q", "value": "yoy-q"},
            {"label": "YoY-Y", "value": "yoy-y", "style": {"display": "none"}},
            {"label": "QoQ", "value": "qoq"},
            {"label": "MAT", "value": "mat", "style": {"display": "none"}}
        ]
    },
    'reporting-form': {
        'values': ['0420158', '0420162'],
        'class_key': 'REPORTING_FORM',
        'total_buttons': 2,
        'default_state': DEFAULT_REPORTING_FORM,
        'buttons': [
            {"label": "0420158", "value": "0420158"},
            {"label": "0420162", "value": "0420162"}
        ]
    },
    'periods-data-table': {
        'values': list(range(1, 6)),
        'class_key': 'NUM_PERIODS',
        'default_state': DEFAULT_NUMBER_OF_PERIODS,
        'total_buttons': 5,
        'buttons': [
            {"label": str(i), "value": f"{i}"} 
            for i in range(1, 6)
        ]
    },
    'table-split-mode': {
        'values': ['insurer', 'line'],
        'class_key': "TABLE_SPLIT",
        'total_buttons': 2,
        'default_state': DEFAULT_SPLIT_MODE,
        'buttons': [
            {"label": "В разрезе страховщиков", "value": "insurer"},
            {"label": "В разрезе видов страхования", "value": "line"},
        ]

    }
}

