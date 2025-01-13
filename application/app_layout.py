import dash_bootstrap_components as dbc
from dash import dcc, html
from application.components.insurance_lines_tree import initial_state
from constants.translations import translate
from data_process.data_utils import category_structure_162, category_structure_158, get_categories_by_level
from constants.filter_options import VALUE_METRICS_OPTIONS, REPORTING_FORM_OPTIONS, PREMIUM_LOSS_OPTIONS
from config.default_values import (
    DEFAULT_PRIMARY_METRICS, DEFAULT_CHECKED_LINES, DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM, DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_PERIOD_TYPE
)
from config.logging_config import get_logger
from typing import Any, Optional, List

logger = get_logger(__name__)


from dataclasses import dataclass
from typing import Tuple, List
import dash
from dash import Input, Output, State
from dash.development.base_component import Component
from config.logging_config import get_logger, track_callback, track_callback_end
from config.logging_config import get_logger, track_callback, track_callback_end
from config.default_values import DEFAULT_CHECKED_LINES
logger = get_logger(__name__)



APP_CONFIG = {
    'dropdowns': {
        'insurance-line-dropdown': {
            'options': get_categories_by_level(
                category_structure_162 if DEFAULT_REPORTING_FORM == '0420162' else category_structure_158,
                level=2,
                indent_char="--"
            ),
            'value': DEFAULT_CHECKED_LINES[0] if isinstance(DEFAULT_CHECKED_LINES, list) else DEFAULT_CHECKED_LINES,
            'placeholder': "Select a category..."
        },
        'primary-y-metric': {
            'options': VALUE_METRICS_OPTIONS,
            'value': DEFAULT_PRIMARY_METRICS[0] if isinstance(DEFAULT_PRIMARY_METRICS, list) else DEFAULT_PRIMARY_METRICS,
            'placeholder': "Select primary metric"
        },
        'secondary-y-metric': {
            'options': [],
            'value': None,
            'placeholder': "Доп. показтель...",
            'multi': False
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
            'value': [],
            'switch': True,
            'inline': True
        },
        'toggle-selected-qtoq': {
            'options': [{"label": "", "value": "show"}],
            'value': [],
            'switch': True,
            'inline': True
        }
    },
    'inputs': {
        'number-of-insurers': {'type': 'number', 'min': 1, 'max': 999, 'step': 1, 'value': 10},
        'number-of-periods-data-table': {'type': 'number', 'min': 1, 'max': 999, 'step': 1, 'value': 2}
    }
}

def create_component(component_type: str, id: Optional[str] = None, **kwargs) -> Any:
    """
    Create a dashboard component based on type and configuration.
    
    Args:
        component_type: Type of component to create
        id: Component identifier
        **kwargs: Additional component configuration
    
    Returns:
        Dashboard component
    """
    base_style = {"fontSize": "0.85rem"}
    
    if component_type == "dropdown":
        config = APP_CONFIG["dropdowns"].get(id, {})
        return dcc.Dropdown(
            id=id,
            options=config.get("options", []),
            value=config.get("value"),
            multi=False,
            placeholder=translate(config.get("placeholder", "")),
            clearable=config.get("clearable", True),
            className="dd-control"
        )
    
    if component_type == "checklist":
        config = APP_CONFIG["checklists"].get(id, {}).copy()
        config.update({k: v for k, v in kwargs.items() if k in ["options", "value", "switch", "inline", "readonly"]})
        
        style = {**base_style, "margin": 0}
        if config.get("readonly"):
            style.update({"pointerEvents": "none", "opacity": 0.5})
            
        return dbc.Checklist(
            id=id,
            options=config.get("options", []),
            value=config.get("value", []),
            switch=config.get("switch", False),
            inline=config.get("inline", False),
            style=style
        )
    
    if component_type == "input":
        config = APP_CONFIG["inputs"].get(id, {})
        return dcc.Input(
            id=id,
            type=config.get("type", "text"),
            min=config.get("min"),
            max=config.get("max"),
            step=config.get("step"),
            value=config.get("value"),
            className="form-control input-short"
        )
    
    if component_type == "button":
        return dbc.Button(
            kwargs.get("text", ""),
            id=id,
            size=kwargs.get("size", "sm"),
            className=f"btn-custom {kwargs.get('className', '')}",
            color=kwargs.get("color", "primary"),
            style={**base_style, "padding": "0.3rem 0.6rem"}
        )
    
    if component_type == "label":
        return html.Label(
            kwargs.get("text", ""),
            className="filter-label mb-0"
        )

def create_filter_row(
    label_text: str,
    component_id: str,
    component_type: str = "dropdown",
    vertical: bool = False,
    **kwargs
) -> html.Div:
    """
    Create a filter row with label and component.
    
    Args:
        label_text: Text for the label
        component_id: Component identifier
        component_type: Type of component to create
        vertical: Whether to use vertical layout
        **kwargs: Additional component configuration
    
    Returns:
        Filter row component
    """
    component = create_component(component_type, id=component_id, **kwargs)
    
    if component_id == "premium-loss-checklist":
        component = html.Div(
            id="premium-loss-checklist-container",
            children=[component]
        )
    
    if vertical:
        return html.Div([
            html.Label(label_text, className="filter-label d-block mb-2"),
            html.Div(component, className="filter-content w-100")  # Added filter-content class
        ], className="filter-row filter-row--vertical mb-3")  # Added filter-row classes
    
    label_width = kwargs.get("label_width", 6)
    component_width = kwargs.get("component_width", 6)
    
    return dbc.Row(
        [
            dbc.Col(
                html.Label(label_text, className="filter-label"),
                width=label_width
            ),
            dbc.Col(
                component,
                width=component_width,
                className="d-flex justify-content-end"
            )
        ],
        className="filter-row mb-1"  # Removed explicit row class since dbc.Row adds it automatically
    )



import dash
from dash import Input, Output, State
from dataclasses import dataclass
from typing import Tuple, Dict
from config.logging_config import get_logger

logger = get_logger(__name__)




def create_hierarchy_buttons() -> dbc.Row:
    """Create hierarchy control buttons."""
    return dbc.Row(
        [
            dbc.Col([
                dbc.Button("Показать все", id="expand-all-button",
                          style={"display": "none"}, color="secondary"),
                dbc.Button("Показать иерархию", id="collapse-button",
                          style={"display": "none"}, color="info", className="ms-1"),
                dbc.Button("Drill down", id="detailize-button",
                          style={"display": "none"}, color="success", className="ms-1")
            ])
        ],
        className="mb-3"
    )

def create_period_buttons() -> html.Div:
    """Create period type selection buttons."""
    period_types = [
        ("YTD", "ytd"),
        ("YoY-Q", "yoy-q"),
        ("YoY-Y", "yoy-y"),
        ("QoQ", "qoq"),
        ("MAT", "mat")
    ]
    
    return html.Div([
        dbc.Row([
            dbc.ButtonGroup([
                dbc.Button(
                    label,
                    id=f"btn-{value}",
                    className="btn-custom btn-period"
                )
                for label, value in period_types
            ])
        ], className="mb-0")
    ])


def setup_debug_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for debug panel functionality."""
    
    @app.callback(
        Output("debug-collapse", "is_open"),
        Input("debug-toggle", "n_clicks"),
        State("debug-collapse", "is_open"),
    )
    def toggle_debug_collapse(n_clicks: int, is_open: bool) -> bool:
        """
        Toggle the debug log collapse panel.
        
        Args:
            n_clicks: Number of times the toggle button was clicked
            is_open: Current state of the debug panel
            
        Returns:
            bool: New state of the debug panel
        """
        ctx = dash.callback_context
        start_time = track_callback('app.tab_state_callbacks', 'toggle_debug_collapse', ctx)
        
        try:
            result = not is_open if n_clicks else is_open
            track_callback_end(
                'app.tab_state_callbacks',
                'toggle_debug_collapse',
                start_time,
                result="not is_open" if n_clicks else "is_open"
            )
            return result
            
        except Exception as e:
            logger.exception("Error in toggle_debug_collapse")
            track_callback_end(
                'app.tab_state_callbacks',
                'toggle_debug_collapse',
                start_time,
                error=str(e)
            )
            raise

def create_debug_footer() -> html.Div:
    """Create debug footer component."""
    return html.Div(
        id="debug-footer",
        className="debug-footer",
        children=[
            dbc.Button(
                "Toggle Debug Logs",
                id="debug-toggle",
                color="secondary",
                className="btn-custom btn-debug-toggle"
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Debug Logs", className="debug-title"),
                        html.Pre(id="debug-output", className="debug-output")
                    ]),
                    className="debug-card"
                ),
                id="debug-collapse",
                is_open=False
            )
        ], style={"display": "none"},
    )




logger = get_logger(__name__)

@dataclass
class SidebarState:
    """Manages sidebar-related classes and states."""
    chart_cont_class: str
    main_class: str
    sidebar_col_class: str
    nav_btn_text: str
    nav_btn_class: str
    inner_btn_class: str

    @classmethod
    def expanded(cls) -> 'SidebarState':
        """Create expanded sidebar state."""
        return cls(
            chart_cont_class="chart-container",
            main_class="sidebar-filters",
            sidebar_col_class="sidebar-col",
            nav_btn_text="Hide Filters",
            nav_btn_class="btn-custom btn-sidebar-toggle-nav",
            inner_btn_class="btn-custom btn-sidebar-toggle-inner"
        )

    @classmethod
    def collapsed(cls) -> 'SidebarState':
        """Create collapsed sidebar state."""
        return cls(
            chart_cont_class="chart-container collapsed",
            main_class="sidebar-filters collapsed",
            sidebar_col_class="sidebar-col collapsed",
            nav_btn_text="Show Filters",
            nav_btn_class="btn-custom btn-sidebar-toggle-nav",
            inner_btn_class="btn-custom btn-sidebar-toggle-inner"
        )

    def to_tuple(self) -> Tuple[str, str, str, str, str]:
        """Convert state to callback output tuple."""
        return (
            self.chart_cont_class,
            self.main_class,
            self.sidebar_col_class,
            self.nav_btn_text,
            self.nav_btn_class,
            self.inner_btn_class
        )

def setup_sidebar_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""
    
    @app.callback(
        [
            Output("chart-container", "className"),
            Output("sidebar-filters", "className"),
            Output("sidebar-col", "className"),
            Output("toggle-sidebar-button", "children"),
            Output("toggle-sidebar-button", "className"),
            Output("toggle-sidebar-button-sidebar", "className")
        ],
        [
            Input("toggle-sidebar-button", "n_clicks"),
            Input("toggle-sidebar-button-sidebar", "n_clicks")
        ],
        [
            State("sidebar-col", "className")
        ],
        prevent_initial_call=True  # Prevent callback from firing on initial load
    )
    def toggle_sidebar(
        nav_clicks: int,
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
            
            logger.warning(f"nav_clicks{nav_clicks}, sidebar_clicks {sidebar_clicks}, current_class {current_class},trigger {ctx.triggered[0]}, new state {new_state.to_tuple()} ")
            
            return new_state.to_tuple()
            
        except Exception as e:
            logger.exception("Error in toggle_sidebar")
            track_callback_end('app.sidebar_callbacks', 'toggle_sidebar', start_time, error=str(e))
            raise


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
                fluid=True,
                children=[
                    dbc.Button(
                        "Show Filters",
                        id="toggle-sidebar-button",
                        color="secondary",
                        className="btn-custom btn-sidebar-toggle"
                    ),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Button(
                        "Data Table",
                        id="data-table-tab",
                        color="light",
                        className="btn-custom btn-table-tab"
                    )
                ]
            )
        ],
        color="dark",
        dark=True,
        className="main-navbar"
    )

def create_sidebar_filters() -> dbc.CardBody:
    """Create sidebar filters component."""
    return dbc.CardBody(
        id="sidebar-filters",
        className="sidebar-filters",
        children=[
            create_filter_row("Форма отчетности:", "reporting-form", label_width=9, component_width=3),
            create_filter_row("Отчетный квартал:", "end-quarter", label_width=9, component_width=3),
            html.Label("Тип данных:", className="filter-label mb-2"),
            create_period_buttons(),
            html.Div(id="period-type-text", className="period-type__text mb-3"),
            create_filter_row("Кол-во периодов для сравнения:", "number-of-periods-data-table", 
                            component_type="input", label_width=9, component_width=3),
            create_filter_row("Линия:", "insurance-line-dropdown", vertical=True),
            create_filter_row("Основной показатель:", "primary-y-metric", vertical=True),
            create_filter_row("Бизнес:", "premium-loss-checklist", 
                            component_type="checklist", label_width=4, component_width=8),
            create_filter_row("Доп. показатель:", "secondary-y-metric", vertical=True),
            create_filter_row("Показать долю рынка:", "toggle-selected-market-share",
                            component_type="checklist", label_width=10, component_width=2),
            create_filter_row("Показать динамику:", "toggle-selected-qtoq",
                            component_type="checklist", label_width=10, component_width=2),
            create_filter_row("Кол-во страховщиков:", "number-of-insurers",
                            component_type="input", label_width=9, component_width=3),
            dbc.Button(
                "Hide Filters",
                id="toggle-sidebar-button-sidebar",
                color="warning",
                className="btn-custom btn-period active"
            ),
            html.Div(id="tree-container", className="tree-container"),
            create_hierarchy_buttons()
        ]
    )

def create_data_table_section() -> dbc.CardBody:
    """Create data table section component."""
    return dbc.CardBody([
        html.H4(id="table-title", className="table-title"),
        html.H4(id="table-subtitle", className="table-subtitle mb-3"),
        dcc.Loading(
            id="loading-data-table",
            type="default",
            children=html.Div(id="data-table")
        )
    ], className="datatable-container")

def create_app_layout(initial_quarter_options: Optional[List[dict]] = None) -> List:
    """
    Create the main application layout.
    
    Args:
        initial_quarter_options: Initial options for quarter selection
        
    Returns:
        List of layout components
    """
    try:
        if initial_quarter_options:
            APP_CONFIG['dropdowns']['end-quarter']['options'] = [
                {'label': q, 'value': q} for q in [q['value'] for q in initial_quarter_options]
            ]
        
        return dbc.Container([  # Wrap everything in Container
            *create_stores(),
            create_navbar(),
            dbc.Row([
                dbc.Col(
                    create_sidebar_filters(),
                    id="sidebar-col",
                    className="sidebar-col",
                    width=6
                ),
                dbc.Col(
                    dbc.CardBody([
                        html.Div([
                            html.H4(id="table-title", className="table-title"),
                            html.H4(id="table-subtitle", className="table-subtitle mb-3")
                        ], className="titles-container"),
                        html.Div([
                            dcc.Loading(
                                id="loading-data-table",
                                type="default",
                                children=html.Div(id="data-table")
                            )
                        ], className="datatable-container"),
                    ], className="table-wrapper"),
                ),              
            ], className="first-row-container"),
            html.Div([
                html.Div([
                    html.H4(id="table-title-chart", className="table-title"),
                    html.H4(id="table-subtitle-chart", className="table-subtitle mb-3")
                    
                ], className="titles-container-chart"),
                html.Div([
                    dcc.Graph(
                        id='graph', 
                        style={'height': '100%', 'width': '100%'}
                    ),
                ], className="graph-container")
            ], id="chart-container",
            className="chart-container",
            style={"display": "none"},
            ),    
            create_debug_footer()
        ], fluid=True)  # fluid=True for full width

        
    except Exception as e:
        print(f"Error in create_app_layout: {str(e)}")
        raise