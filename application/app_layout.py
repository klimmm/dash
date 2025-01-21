import dash_bootstrap_components as dbc
import dash
from dash import dcc, html
from typing import Any, Dict, List, Optional, Union, Tuple
from dash import Input, Output, State
from dataclasses import dataclass

from application.components.insurance_lines_tree import initial_state, create_lines_checklist_buttons, create_debug_footer
from constants.translations import translate
from data_process.data_utils import (
    category_structure_162,
    category_structure_158,
    get_categories_by_level
)
from constants.filter_options import (
    VALUE_METRICS_OPTIONS,
    REPORTING_FORM_OPTIONS,
    PREMIUM_LOSS_OPTIONS
)
from config.default_values import (
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM,
    DEFAULT_PREMIUM_LOSS_TYPES,
    DEFAULT_PERIOD_TYPE,
    DEFAULT_INSURER
)
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


class StyleConstants:

    NAV = "main-nav"
    LAYOUT = "layout-wrapper"
    SIDEBAR = "sidebar-col"
    SIDEBAR_COLLAPSED = "sidebar-col collapsed"
    TREE = "tree"

    # Layout containers
    CONTAINER = {
        "CHART": "chart-container",
        "CHART_COLLAPSED": "chart-container collapsed",
        "TREE": "tree-container",
        "DATA_TABLE": "datatable-container",
        "TITLES": "titles-container",
        "TITLES_CHART": "titles-container-chart",
        "CARD": "card-container",
        "TABS": "tabs-container",
        "GRAPH": "graph-container"
    }

    # Market analysis
    MARKET = {
        "TITLE": "market-analysis-title",
        "CONTENT": "market-analysis-content"
    }

    # Form elements
    FORM = {
        "DD": "dd-control",
        "CHECKLIST": "checklist",
        "INPUT": "form-control input-short"
    }

    # Buttons
    BTN = {
        "PERIOD": "btn-custom btn-period",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TAB": "btn-custom btn-tab",
        "TABLE_TAB": "btn-custom btn-table-tab"
    }

    # Filters
    FILTER = {
        "LABEL": "filter-label",
        "CONTENT": "filter-content w-100",
        "ROW": "filter-row",
        "ROW_VERTICAL": "filter-row filter-row--vertical",
        "ROW_NO_MARGIN": "filter-row mb-0",
        "COLUMN": "filter-column",
        "MAIN": "main-filter-column"
    }

    # Tabs
    TAB = {
        "DEFAULT": "tab",
        "SELECTED": "tab-selected"
    }

    # Utilities
    FLEX = {
        "START": "d-flex justify-content-start",
        "END": "d-flex justify-content-end"
    }

    TABLE = {
        "TITLE": "table-title",
        "SUBTITLE": "table-subtitle mb-3",
    }

    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text"
    }


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
    _config = None

    @classmethod
    def _initialize_config(cls):
        """Initialize component configurations"""
        if cls._config is None:
            cls._config = {
                'dropdowns': {
                    'insurance-line-dropdown': {
                        'options': get_categories_by_level(
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
                        'multi': True,
                        'placeholder': "Доп. показатель...",
                    },
                    'selected-insurers': {
                        'label': False,
                        'options': [],
                        'value': ','.join(DEFAULT_INSURER),
                        'multi': False,
                        'clearable': False
                    },
                    'end-quarter': {
                        'options': [],
                        'value': DEFAULT_END_QUARTER,
                        'placeholder': "Select quarter...",
                        'clearable': False
                    },
                    'reporting-form': {
                        'options': REPORTING_FORM_OPTIONS,
                        'value': DEFAULT_REPORTING_FORM,
                        'placeholder': "Select reporting form...",
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
        cls._initialize_config()
        if dropdown_id in cls._config['dropdowns']:
            cls._config['dropdowns'][dropdown_id]['options'] = new_options

    @classmethod
    def create_component(cls, component_type: str, id: Optional[str] = None, **kwargs) -> Any:
        """Create a UI component based on type and kwargs"""
        cls._initialize_config()

        # Get base config if id is provided
        base_config = {}


        if component_type == "radioitems":
            component_group = "radioitems"
        else:
            component_group = f"{component_type}s"

        # logger.deug(f"Looking for config in group: {component_group}")

        if id and component_group in cls._config and id in cls._config[component_group]:
            base_config = cls._config[component_group][id]
            logger.debug(f"Found base config: {base_config}")

        # Merge base config with kwargs
        config = {**base_config, **kwargs}

        if component_type == "dropdown":
            return dcc.Dropdown(
                id=id,
                options=config.get('options', []),
                value=config.get('value'),
                multi=config.get('multi', False),
                placeholder=translate(config.get('placeholder', '')),
                clearable=config.get('clearable', True),
                className=StyleConstants.FORM["DD"]
            )

        if component_type == "checklist":
            style = {**cls.BASE_STYLE, "margin": 0}
            if config.get('readonly'):
                style.update({"pointerEvents": "none", "opacity": 0.5})

            return dbc.Checklist(
                id=id,
                options=config.get('options', []),
                value=config.get('value', []),
                switch=config.get('switch', False),
                inline=config.get('inline', False),
                style=style,
                className=StyleConstants.FORM["CHECKLIST"]
            )

        if component_type == "radioitems":
            options = config.get('options', [])
            value = config.get('value')
            inline = config.get('inline', False)

            logger.debug(f"Creating RadioItems with: options={options}, value={value}, inline={inline}")

            return dbc.RadioItems(
                id=id,
                options=options,
                value=value,
                inline=inline,
                className=StyleConstants.FORM["CHECKLIST"]
            )

        if component_type == "input":
            return dcc.Input(
                id=id,
                type=config.get('type', 'text'),
                min=config.get('min'),
                max=config.get('max'),
                step=config.get('step'),
                value=config.get('value'),
                required=config.get('required', True),
                className=StyleConstants.FORM["INPUT"]
            )

    @staticmethod
    def create_filter_row(
        label_text: str,
        component: Any,
        label_width: int = 6,
        component_width: int = 6,
        vertical: bool = False,
        component_id: Optional[str] = None
    ) -> html.Div:
        """Create a filter row with label and component"""
        if vertical:
            return html.Div([
                html.Label(label_text, className=StyleConstants.FILTER["LABEL"]),
                html.Div(component, className=StyleConstants.FILTER["CONTENT"])
            ], className=StyleConstants.FILTER["ROW_VERTICAL"])

        return dbc.Row([
            dbc.Col(
                html.Label(label_text, className=StyleConstants.FILTER["LABEL"]),
                width=label_width
            ),
            dbc.Col(
                component,
                width=component_width,
                className=StyleConstants.FLEX["START"] if component_id == "premium-loss-checklist" \
                else StyleConstants.FLEX["END"]
            )
        ], className=StyleConstants.FILTER["ROW_NO_MARGIN"])


def create_filters() -> html.Div:
    """Create the complete filter interface"""
    components = FilterComponents()

    # Create premium loss checklist with container
    premium_loss_checklist = components.create_component("checklist", "premium-loss-checklist")
    premium_loss_container = html.Div(
        id="premium-loss-checklist-container",
        children=[premium_loss_checklist]
    )

    left_column_row1 = [

        components.create_filter_row(
            "Форма отчетности:",
            components.create_component("dropdown", "reporting-form"),
            label_width=8,
            component_width=4
        )
    ]

    middle_column_row1 = [
        components.create_filter_row(
            "Отчетный квартал:",
            components.create_component("dropdown", "end-quarter"),
            label_width=8,
            component_width=4
        )
    ]

    right_column_row1 = [
        dbc.Row([
            dbc.Col([html.Label("Тип данных:", className=StyleConstants.FILTER["LABEL"])], xs=4, sm=3),
            dbc.Col([create_period_type_buttons()], xs=8, sm=9),
        ], className=StyleConstants.FILTER["ROW_NO_MARGIN"]),
        html.Div(id="period-type-text", className=StyleConstants.UTILS["PERIOD_TYPE"], style={"display": "none"})
    ]

    left_column_row2 = [

        components.create_filter_row(
            "Кол-во страховщиков:",
            components.create_component("input", "number-of-insurers"),
            label_width=9,
            component_width=3
        ),

    ]

    middle_column_row2 = [

        components.create_filter_row(
            "Показать динамику:",
            components.create_component("checklist", "toggle-selected-qtoq"),
            label_width=10,
            component_width=2
        ),

    ]


    right_column_row2 = [
        components.create_filter_row(
            "Бизнес:",
            premium_loss_container,
            label_width=3,
            component_width=9,
            component_id="premium-loss-checklist"
        ),      


    ]
    left_column_row3 = [


        components.create_filter_row(
            "Доп. показатель:",
            components.create_component("dropdown", "secondary-y-metric"),
            label_width=4,
            component_width=8    
        )
    ]

    middle_column_row3 = [


        components.create_filter_row(
            "Кол-во периодов:",
            components.create_component("input", "number-of-periods-data-table"),
            label_width=9,
            component_width=3
        )
    ]


    right_column_row3 = [
    
        components.create_filter_row(
            "Показать долю рынка:",
            components.create_component("checklist", "toggle-selected-market-share"),
            label_width=10,
            component_width=2
        )






        
    ]


    return html.Div(dbc.CardBody([
        dbc.Row([
            dbc.Col(left_column_row1, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(middle_column_row1, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(right_column_row1, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(right_column_row2, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(left_column_row2, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(middle_column_row2, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(middle_column_row3, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col(right_column_row3, xs=6, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]), 
            dbc.Col(left_column_row3, xs=12, sm=4, md=4, className=StyleConstants.FILTER["MAIN"]),
            
        ], className=StyleConstants.SIDEBAR_COLLAPSED, id="sidebar-col"),
        dbc.Row([
            dbc.Col([
                components.create_filter_row(
                    "Insurer/Line",
                    components.create_component("radioitems", "insurer-line-switch"),
                    label_width=2,
                    component_width=10
                ),
            ], xs=12, sm=6, md=6, className=StyleConstants.FILTER["MAIN"], style={"display": "none"}),

        ], className=StyleConstants.SIDEBAR),
        dbc.Row([
            dbc.Col([
                components.create_filter_row(
                    "Страховщик:",
                    components.create_component("dropdown", "selected-insurers"),
                    label_width=4,
                    component_width=8
                ),
            ], xs=12, sm=6, md=4, className=StyleConstants.FILTER["MAIN"]),            
            dbc.Col([
                components.create_filter_row(
                    "Вид страхования:",
                    components.create_component("dropdown", "insurance-line-dropdown"),
                    label_width=4,
                    component_width=8
                )
            ],  xs=12, sm=6, md=4, className=StyleConstants.FILTER["MAIN"]),
            dbc.Col([
                components.create_filter_row(
                    "Показатель:",
                    components.create_component("dropdown", "primary-y-metric"),
                    label_width=4,
                    component_width=8
                )
            ], xs=12, sm=6, md=4, className=StyleConstants.FILTER["MAIN"]),
        ], className=StyleConstants.SIDEBAR),
    ]))


def create_period_type_buttons() -> html.Div:
    """Create period type selection buttons"""
    period_types = [
        ("YTD", "ytd", {}),
        ("YoY-Q", "yoy-q", {}),
        ("YoY-Y", "yoy-y", {"display": "none"}),
        ("QoQ", "qoq", {}),
        ("MAT", "mat", {"display": "none"})
    ]
    return html.Div([
        dbc.Row([
            dbc.ButtonGroup([
                dbc.Button(
                    label,
                    id=f"btn-{value}",
                    className=StyleConstants.BTN["PERIOD"],
                    style=style
                )
                for label, value, style in period_types
            ])
        ], className=StyleConstants.UTILS["MB_0"])
    ])


def create_stores() -> List[html.Div]:
    """Create store components for app state management."""
    return [
        html.Div(id="_hidden-init-trigger", style={"display": "none"}),
        dcc.Store(id="show-data-table", data=True),
        dcc.Store(id="processed-data-store"),
        dcc.Store(id="filter-state-store"),
        dcc.Store(id='insurance-lines-state', data=initial_state),
        dcc.Store(id='expansion-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='tree-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='period-type', data=DEFAULT_PERIOD_TYPE)
    ]


def create_navbar() -> dbc.Navbar:
    """Create navigation bar component."""
    return dbc.Navbar(
        [
            dbc.Container(
                # fluid=True,
                children=[
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Button(
                        "Data Table",
                        id="data-table-tab",
                        color="light",
                        className=StyleConstants.BTN["TABLE_TAB"]
                    )
                ]
            )
        ],
        color="dark",
        dark=True,
        className=StyleConstants.NAV
    )


@dataclass
class SidebarState:
    """Manages sidebar-related classes and states."""
    chart_cont_class: str
    sidebar_col_class: str
    inner_btn_text: str
    inner_btn_class: str

    @classmethod
    def expanded(cls) -> 'SidebarState':
        """Create expanded sidebar state."""
        return cls(
            chart_cont_class = StyleConstants.CONTAINER["CHART"],
            sidebar_col_class=StyleConstants.SIDEBAR,
            inner_btn_text="Hide Filters",
            inner_btn_class = StyleConstants.BTN["SIDEBAR_HIDE"]
        )

    @classmethod
    def collapsed(cls) -> 'SidebarState':
        """Create collapsed sidebar state."""
        return cls(
            chart_cont_class = StyleConstants.CONTAINER["CHART_COLLAPSED"],
            sidebar_col_class=StyleConstants.SIDEBAR_COLLAPSED,
            inner_btn_text="Show Filters",
            inner_btn_class = StyleConstants.BTN["SIDEBAR_SHOW"]
        )

    def to_tuple(self) -> Tuple[str, str, str, str, str]:
        """Convert state to callback output tuple."""
        return (
            self.chart_cont_class,
            self.sidebar_col_class,
            self.inner_btn_text,
            self.inner_btn_class
        )


def setup_sidebar_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""

    @app.callback(
        [
            Output("chart-container", "className"),
            Output("sidebar-col", "className"),
            Output("toggle-sidebar-button-sidebar", "children"),
            Output("toggle-sidebar-button-sidebar", "className")
        ],
        [
            Input("toggle-sidebar-button-sidebar", "n_clicks")
        ],
        [
            State("sidebar-col", "className")
        ],
        prevent_initial_call=True  # Prevent callback from firing on initial load
    )
    def toggle_sidebar(
        sidebar_clicks: int,
        current_class: str
    ) -> Tuple[str, str, str, str, str]:
        """
        Toggle sidebar visibility and update related elements.
        """
        ctx = dash.callback_context
        start_time = track_callback('app.sidebar_callbacks', 'toggle_sidebar', ctx)

        try:
            # If no button was clicked (initial load), return expanded state
            if not ctx.triggered:
                return SidebarState.expanded().to_tuple()

            # Determine current state
            is_expanded = current_class and "collapsed" not in current_class

            # Return opposite state
            new_state = SidebarState.collapsed() if is_expanded else SidebarState.expanded()

            track_callback_end('app.sidebar_callbacks', 'toggle_sidebar', start_time, 
                             result=f"toggled_to_{'collapsed' if is_expanded else 'expanded'}")

            logger.debug(f"sidebar_clicks {sidebar_clicks}, current_class {current_class},trigger {ctx.triggered[0]}, new state {new_state.to_tuple()} ")

            return new_state.to_tuple()

        except Exception as e:
            logger.exception("Error in toggle_sidebar")
            track_callback_end('app.sidebar_callbacks', 'toggle_sidebar', start_time, error=str(e))
            raise


def create_market_analysis_component():
    """Creates the market analysis component without data dependencies"""
    layout = html.Div([
        html.H1("Анализ динамики Топ-10 страховых компаний", className=StyleConstants.MARKET["TITLE"]),

        dbc.Row([
            dbc.Col(html.Div(id="market-volume-card"), md=12, className=StyleConstants.CONTAINER["CARD"]),
            dbc.Col(html.Div(id="market-concentration-card"), md=12, className=StyleConstants.CONTAINER["CARD"]),
            dbc.Col(html.Div(id="leaders-card"), md=12, className=StyleConstants.CONTAINER["CARD"])
        ]),
        dcc.Tabs(
            id="market-analysis-tabs",
            value="overview",
            children=[
                dcc.Tab(
                    label="Структура рынка",
                    value="overview",
                    className=StyleConstants.TAB["DEFAULT"],
                    selected_className=StyleConstants.TAB["SELECTED"]
                ),
                dcc.Tab(
                    label="Изменения показателей",
                    value="changes",
                    className=StyleConstants.TAB["DEFAULT"],
                    selected_className=StyleConstants.TAB["SELECTED"]
                ),
                dcc.Tab(
                    label="Темпы роста vs Рынок",
                    value="growth",
                    className=StyleConstants.TAB["DEFAULT"],
                    selected_className=StyleConstants.TAB["SELECTED"]
                ),
                dcc.Tab(
                    label="Вклад в рост",
                    value="contribution",
                    className=StyleConstants.TAB["DEFAULT"],
                    selected_className=StyleConstants.TAB["SELECTED"]
                )
            ],
            className=StyleConstants.CONTAINER["TABS"]
        ),
        html.Div(id="market-analysis-tab-content", className=StyleConstants.MARKET["CONTENT"])
    ], id="market-analysis-container")
    return layout


def create_app_layout(initial_quarter_options: Optional[List[dict]] = None, initial_insurer_options: Optional[List[dict]] = None) -> List:
    try:

        components = FilterComponents()
        if initial_quarter_options:
            components.update_dropdown_options(
                'end-quarter',
                [{'label': q, 'value': q} for q in [q['value'] for q in initial_quarter_options]]
            )
        if initial_insurer_options:
            components.update_dropdown_options(
                'selected-insurers',
                initial_insurer_options  # Pass the options directly since they're already in the correct format
            )

        return dbc.Container([  # Wrap everything in Container
            *create_stores(),
            create_navbar(),
            html.Div(id="dummy-output", style={"display": "none"}),
            html.Div(id="dummy-trigger", style={"display": "none"}),
            html.Div(id="tree-container", className=StyleConstants.CONTAINER["TREE"]),
            create_lines_checklist_buttons(),
            dbc.CardBody([
                dbc.Row([  # Added Row to properly structure columns
                    dbc.Col([
                        dbc.Button(
                            "Show Additional Filters",
                            id="toggle-sidebar-button-sidebar",
                            className=StyleConstants.BTN["SIDEBAR_SHOW"]
                        ),

                        create_filters(),
                        dbc.Row([
                            dbc.Col([
                                html.H4(id="table-title", className=StyleConstants.TABLE["TITLE"]),
                                html.H4(id="table-subtitle", className=StyleConstants.TABLE["SUBTITLE"], 
                                       style={"display": "none"}),
                            ], className=StyleConstants.CONTAINER["TITLES"], style={"display": "none"}),
                        ]),
                        html.Div([
                            dcc.Loading(
                                id="loading-data-table",
                                type="default",
                                children=html.Div(id="data-table")
                            )
                        ], className=StyleConstants.CONTAINER["DATA_TABLE"]),
                    ], md=12),  # Added column size
                    dbc.Col([
                        create_market_analysis_component()
                    ], style={"display": "none"}, md=2)  # Added column size
                ])
            ], className=StyleConstants.LAYOUT),
            html.Div([
                html.Div([
                    html.H4(id="table-title-chart", className=StyleConstants.TABLE["TITLE"], 
                           style={"display": "none"}),
                    html.H4(id="table-subtitle-chart", className=StyleConstants.TABLE["SUBTITLE"], 
                           style={"display": "none"})
                ], className=StyleConstants.CONTAINER["TITLES_CHART"], style={"display": "none"}),
                html.Div([
                    dcc.Graph(
                        id='graph',
                        style={'height': '100%', 'width': '100%'}
                    ),
                ], className=StyleConstants.CONTAINER["GRAPH"])
            ], id="chart-container", className=StyleConstants.CONTAINER["CHART"], style={"display": "none"}),
            create_debug_footer()
        ], fluid=True)
    except Exception as e:
        print(f"Error in create_app_layout: {str(e)}")
        raise