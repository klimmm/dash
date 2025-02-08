from config.default_values import DEFAULT_BUTTON_VALUES

BUTTON_CONFIG = {
    'view-metrics': {
        'buttons': [
            {'label': 'Доля', 'value': 'market-share'},
            {'label': 'Динамика', 'value': 'qtoq'}
        ],
        'class_key': 'MARKET_SHARE',
        'multi_select': True,
        'default_state': {
            'market-share': DEFAULT_BUTTON_VALUES['market_share'],
            'qtoq': DEFAULT_BUTTON_VALUES['qtoq']
        }
    },
    'top-insurers': {
        'buttons': [
            {'label': 'Топ-5', 'value': 5},
            {'label': 'Топ-10', 'value': 10},
            {'label': 'Топ-20', 'value': 20},
            {'label': 'Выбрать страховщика:', 'value': 'custom'}
        ],
        'class_key': 'TOP_N',
        'default': DEFAULT_BUTTON_VALUES['top_n']
    },
    'period-type': {
        'buttons': [
            {'label': 'YTD', 'value': 'ytd'},
            {'label': 'YoY-Q', 'value': 'yoy_q'},
            {'label': 'YoY-Y', 'value': 'yoy_y', 'hidden': True},
            {'label': 'QoQ', 'value': 'qoq'},
            {'label': 'MAT', 'value': 'mat', 'hidden': True}
        ],
        'class_key': 'PERIOD_TYPE',
        'default': DEFAULT_BUTTON_VALUES['period_type']
    },
    'reporting-form': {
        'buttons': [
            {'label': '0420158', 'value': '0420158'},
            {'label': '0420162', 'value': '0420162'}
        ],
        'class_key': 'REPORTING_FORM',
        'default': DEFAULT_BUTTON_VALUES['reporting_form']
    },
    'periods-data-table': {
        'buttons': [
            {'label': str(i), 'value': i}
            for i in range(1, 6)
        ],
        'class_key': 'NUM_PERIODS',
        'default': DEFAULT_BUTTON_VALUES['periods']
    },
    'table-split-mode': {
        'buttons': [
            {'label': 'В разрезе страховщиков', 'value': 'insurer'},
            {'label': 'В разрезе видов страхования', 'value': 'line'}
        ],
        'class_key': 'TABLE_SPLIT',
        'default': DEFAULT_BUTTON_VALUES['split_mode']
    }
}