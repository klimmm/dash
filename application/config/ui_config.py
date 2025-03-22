from typing import Dict, Optional, List

SIDEBAR_CONFIG = [
    {
        "label": "Базовые настройки",
        "rows": [
            [("Отчетный период:", 'end-quarter', 30, 60, None)],
            [("База сравнения:", 'period-type', 30, 60, None)],
            [("Глубина сравнения:", 'number-of-periods', 30, 60, None)],
            [("Форма отчетности:", 'reporting-form', 30, 60, None)]
        ],
        "open": True
    },
    {
        "label": "Компания",
        "rows": [
            [("", 'top-insurers', 0, 100, None)],
            [("", 'insurer', 0, 100, None)]
        ],
        "open": True
    },
    {
        "label": "Вид страхования",
        "rows": [
            [("", 'line_tree', 0, 0, None)]
        ],
        "open": True
    },    
    {
        "label": "Показатель",
        "rows": [
            [("", 'metric_tree', 0, 100, None)],
            [("Дополнительно:", 'view-metrics', 30, 0, None)]
        ],
        "open": True
    },
    {
        "label": "Настройка представления",
        "rows": [
            [("в строках:", 'index-col', 30, 0, None)],
            [("в столбцах:", 'pivot-col', 30, 0, None)]
        ],
        "open": True
    }
]


class FiltersSummaryConfig:
    """Configuration for filters summary display"""

    def __init__(self):
        self.structure = {
            "first_row": [
                ("reporting_form", "", " | ", False),
                ("quarters", "", "", True)
            ],
            "second_row": [
                ("lines", "Вид страхования: ", " | ", True),
                ("metrics", "Показатель: ", " | ", True),
                ("insurers", "Страховщик: ", "", True)
            ]
        }

        keys = {item[0] for row in self.structure.values() for item in row}
        self.data_mapping = {
            key: lambda context, k=key: getattr(context, k)
            for key in keys
        }


class DefaultValues:
    END_QUARTER: str = '2024Q4'
    PERIOD_TYPE: str = 'ytd'
    NUMBER_OF_PERIODS: int = 2
    REPORTING_FORM: str = '0420162'
    INSURER: List[str] = ['top-5']
    INSURERS: List[str] = ['top-10']
    TOP_INSURERS: int = 10
    # CHECKED_LINES: List[str] = ['дмс', 'нс и оглс', 'осаго', 'каско и ж/д', 'авиа, море, грузы', 'прочее имущество', 'предпр. и фин риски', 'прочая ответственность', 'страхование жизни']
    LINES: List[str] = ['дмс', 'нс и оглс', 'осаго']

    EXPANSION_STATES_LINES: Dict[str, bool] = {
        'все линии': True,
        'страхование нежизни': True,
        'авиа, море, грузы': True
    }
    # METRICS: List[str] = ['direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses', 'ceded_premiums', 'ceded_losses', 'new_contracts', 'contracts_end', 'premiums_interm', 'commissions_interm', 'new_sums', 'sums_end', 'claims_reported', 'claims_settled', 'premiums_interm_ratio']
    METRICS: List[str] = ['direct_premiums', 'direct_losses', 'ceded_premiums']

    EXPANSION_STATES_METRICS: Dict[str, bool] = {
        'direct_premiums': True,
        'direct_losses': True
    }

    METRICS_158: List[str] = ['total_premiums']
    METRICS_BY_FORM: Dict[str, List[str]] = {
        '0420162': METRICS,
        '0420158': METRICS_158
    }
    VIEW_METRICS: List[str] = ['change']
    VALUE_TYPES: List[str] = ['base', 'base_change']
    INDEX_COL: List[str] = ['insurer']
    PIVOT_COL: List[str] = ['metric', 'value_type', 'year_quarter']
    VIEW_MODE: str = ['table']
    SPLIT_COLS: List[str] = ['line', 'metric']
    REPORTING_FORM_TO_LINES_DICTIONARY = {
        '0420158': 'LINES_158_DICTIONARY',
        '0420162': 'LINES_162_DICTIONARY'
    }
    REPORTING_FORM_TO_METRICS_DICTIONARY = {
        '0420158': 'METRICS_158_DICTIONARY',
        '0420162': 'METRICS_162_DICTIONARY'
    }
    REPORTING_FORM_TO_INSURERS_DICTIONARY = {
        '0420158': 'CONVERTED_INSURERS_DICTIONARY',
        '0420162': 'CONVERTED_INSURERS_DICTIONARY'
    }



class TreeServiceConfig:
    """Configuration for tree services."""

    def __init__(self):
        # Dictionary of tree configurations
        self.tree_configs = {
            'metric': {
                'component_id': 'metric',
                'data_source_map': DefaultValues.REPORTING_FORM_TO_METRICS_DICTIONARY,
                'default_checked': DefaultValues.METRICS,
                'default_expansions': DefaultValues.EXPANSION_STATES_METRICS,
                'use_custom_top_level': True,
                'multi': True
            },
            'line': {
                'component_id': 'line',
                'data_source_map': DefaultValues.REPORTING_FORM_TO_LINES_DICTIONARY,
                'default_checked': DefaultValues.LINES,
                'default_expansions': DefaultValues.EXPANSION_STATES_LINES,
                'use_custom_top_level': False,
                'multi': False
            },
            'insurer': {
                'component_id': 'insurer',
                'data_source_map': DefaultValues.REPORTING_FORM_TO_INSURERS_DICTIONARY,
                'default_checked': DefaultValues.INSURERS,
                'default_expansions': {},
                'use_custom_top_level': False,
                'multi': True

            }
        }

    def get_tree_config(self, component_id):
        """Get configuration for a specific tree by component ID."""
        return self.tree_configs.get(component_id, {})

    def get_all_configs(self):
        """Get all tree configurations."""
        return self.tree_configs

    def add_tree_config(self, component_id, config):
        """Add or update a tree configuration."""
        self.tree_configs[component_id] = config


class UIComponentConfigManager:
    """Central manager for UI component configurations including buttons and dropdowns."""

    def __init__(self):
        # Combined configuration dictionary with component type specification
        self.config = {
            # Button configurations
            'index-col': {
                'type': 'button',
                'options': [
                    {'label': 'Вид', 'value': 'line'},
                    {'label': 'Страховщик', 'value': 'insurer'},
                    {'label': 'Показатель', 'value': 'metric'}
                ],
                'value': DefaultValues.INDEX_COL
            },
            'pivot-col': {
                'type': 'button',
                'options': [
                    {'label': 'Вид', 'value': 'line'},
                    {'label': 'Страховщик', 'value': 'insurer'},
                    {'label': 'Показатель', 'value': 'metric'}
                ],
                'multi': True,
                'value': DefaultValues.PIVOT_COL
            },
            'view-metrics': {
                'type': 'button',
                'options': [
                    {'label': 'Динамика', 'value': 'change'},
                    {'label': 'Доля рынка', 'value': 'market-share'},
                    {'label': 'Ранк', 'value': 'rank'}
                ],
                'multi': True,
                'value': DefaultValues.VIEW_METRICS
            },
            'top-insurers': {
                'type': 'button',
                'options': [
                    {'label': 'Топ-5', 'value': '5'},
                    {'label': 'Топ-10', 'value': '10'},
                    {'label': 'Топ-20', 'value': '20'},
                    {'label': 'Выбрать:', 'value': 'total'}
                ],
                'value': DefaultValues.TOP_INSURERS
            },
            'period-type': {
                'type': 'button',
                'options': [
                    {'label': 'YTD', 'value': 'ytd'},
                    {'label': 'YoY-Q', 'value': 'yoy-q'},
                    {'label': 'YoY-Y', 'value': 'yoy-y'},
                    {'label': 'QoQ', 'value': 'qoq'},
                    {'label': 'MAT', 'value': 'mat', 'hidden': True}
                ],
                'value': DefaultValues.PERIOD_TYPE
            },
            'reporting-form': {
                'type': 'button',
                'options': [
                    {'label': '0420158', 'value': '0420158'},
                    {'label': '0420162', 'value': '0420162'}
                ],
                'value': DefaultValues.REPORTING_FORM
            },
            'number-of-periods': {
                'type': 'button',
                'options': [{'label': str(i), 'value': i} for i in range(1, 7)],
                'value': DefaultValues.NUMBER_OF_PERIODS
            },
            'view-mode': {
                'type': 'button',
                'options': [
                    {'label': 'Table View', 'value': 'table'},
                    {'label': 'Chart View', 'value': 'chart'},
                    {'label': 'Combined View', 'value': 'combined'}
                ],
                'value': DefaultValues.VIEW_MODE
            },

            # Dropdown configurations
            'insurer': {
                'type': 'dropdown',
                'id': 'selected-insurers',
                'multi': True,
                'value': [],
                'placeholder': "Все компании",
                'disabled': True,
                'options': []
            },
            'end-quarter': {
                'type': 'dropdown',
                'id': 'end-quarter',
                'multi': False,
                'value': DefaultValues.END_QUARTER,
                'disabled': False,
                'options': []
            },
            'log_level': {
                'type': 'dropdown',
                'id': 'log-level-filter',
                'multi': True,
                'value': ['DEBUG'],
                'options': [{'label': level, 'value': level} for level in
                            ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']]
            },
            'module': {
                'type': 'dropdown',
                'id': 'module-filter',
                'multi': True,
                'value': [],
                'options': [],
                'placeholder': "All modules"
            }
        }

    def get_button_config(self, button_id: Optional[str] = None) -> Dict:
        """
        Get configuration for a specific button or all button configurations.

        Args:
            button_id: Optional ID of the button

        Returns:
            Dictionary with button configuration(s) or empty dict if not found
        """
        if button_id:
            config = self.config.get(button_id, {}).copy()
            if config.get('type') == 'button':
                # Remove 'type' field before returning to avoid issues with existing components
                if 'type' in config:
                    del config['type']
                return config
            return {}

        # Return all button configs with 'type' field removed
        button_configs = {}
        for key, value in self.config.items():
            if value.get('type') == 'button':
                config_copy = value.copy()
                if 'type' in config_copy:
                    del config_copy['type']
                button_configs[key] = config_copy
        return button_configs
    
    def get_dropdown_config(self, dropdown_id: Optional[str] = None) -> Dict:
        """
        Get configuration for a specific dropdown or all dropdown configurations.
        
        Args:
            dropdown_id: Optional ID of the dropdown
            
        Returns:
            Dictionary with dropdown configuration(s) or empty dict if not found
        """
        if dropdown_id:
            config = self.config.get(dropdown_id, {}).copy()
            if config.get('type') == 'dropdown':
                # Remove 'type' field before returning to avoid issues with existing components
                if 'type' in config:
                    del config['type']
                return config
            return {}

        # Return all dropdown configs with 'type' field removed
        dropdown_configs = {}
        for key, value in self.config.items():
            if value.get('type') == 'dropdown':
                config_copy = value.copy()
                if 'type' in config_copy:
                    del config_copy['type']
                dropdown_configs[key] = config_copy
        return dropdown_configs

    def update_config(self, component_id: str, updates: Dict) -> bool:
        """
        Update configuration for a specific component.

        Args:
            component_id: ID of the component to update
            updates: Dictionary with updates to apply
            
        Returns:
            Boolean indicating success or failure
        """
        if component_id in self.config:
            self.config[component_id].update(updates)
            return True
        return False
    
    def update_options(self, component_id: str, new_options: List[Dict]) -> bool:
        """
        Update options for a specific component.
        
        Args:
            component_id: ID of the component
            new_options: New options list
            
        Returns:
            Boolean indicating success or failure
        """
        if component_id in self.config and 'options' in self.config[component_id]:
            self.config[component_id]['options'] = new_options
            return True
        return False