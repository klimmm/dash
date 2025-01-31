BUTTON_CONFIG = {
    'metric-toggles': {
        'values': ['market-share', 'qtoq'],
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 2,
        'multi_choice': True,
        'default_state': {'market-share': [], 'qtoq': []},
        'buttons': [
            {"label": "Доля", "value": "market-share"},
            {"label": "Динамика", "value": "qtoq"}
        ]
    },
    'top-insurers': {
        'values': [5, 10, 20, 999],
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 4,
        'multi_choice': True,
        'default_state': [],
        'buttons': [
            {"label": "Total", "value": "999"},
            {"label": "Top5", "value": "5"},
            {"label": "Top10", "value": "10"},
            {"label": "Top20", "value": "20"}
        ]
    },
    'period-type': {
        'values': ['ytd', 'yoy_q', 'yoy_y', 'qoq', 'mat'],
        'style_type': 'PERIOD',
        'total_buttons': 5,
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
        'style_type': 'PERIOD',
        'total_buttons': 2,
        'buttons': [
            {"label": "0420158", "value": "0420158"},
            {"label": "0420162", "value": "0420162"}
        ]
    },
    'periods-data-table': {
        'values': list(range(1, 6)),
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 5,
        'buttons': [
            {"label": str(i), "value": f"period-{i}"} 
            for i in range(1, 6)
        ]
    },
    'table-split-mode': {
        'values': ['line', 'insurer'],
        'style_type': 'GROUP_CONTROL',
        'total_buttons': 2,
        'buttons': [
            {"label": "line", "value": "line"},
            {"label": "insurer", "value": "insurer"}
        ]

    }
}
