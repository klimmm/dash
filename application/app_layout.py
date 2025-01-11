import dash_bootstrap_components as dbc
from dash import dcc, html
from application.components.insurance_lines_tree import initial_state
from constants.translations import translate
from data_process.data_utils import category_structure_162, category_structure_158, get_categories_by_level
from constants.filter_options import VALUE_METRICS_OPTIONS, REPORTING_FORM_OPTIONS, PREMIUM_LOSS_OPTIONS
from config.default_values import (
    DEFAULT_PRIMARY_METRICS, DEFAULT_CHECKED_LINES, DEFAULT_END_QUARTER,
    DEFAULT_REPORTING_FORM, DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_PERIOD_TYPE,
    button_period_main
)
from config.logging_config import get_logger

logger = get_logger(__name__)

###############################################################################
# 1) CONFIG & CONSTANTS
###############################################################################
APP_CONFIG = {
    'dropdowns': {
        'insurance-line-dropdown': {
            'options': get_categories_by_level(category_structure_162 if DEFAULT_REPORTING_FORM == '0420162' else category_structure_158, level=2, indent_char="--"),
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

###############################################################################
# 2) FACTORY FUNCTION: CREATE_COMPONENT
###############################################################################
def create_component(component_type, id=None, **kwargs):
    component_kwargs = {
        k: v for k, v in kwargs.items()
        if k not in ["label_width", "component_width"]
    }

    if component_type == "dropdown":
        config = APP_CONFIG["dropdowns"].get(id, {})
        return dcc.Dropdown(
            id=id,
            options=config.get("options", []),
            value=config.get("value"),
            multi=False,
            placeholder=translate(config.get("placeholder", "")),
            clearable=config.get("clearable", True),
            className="dd-control"  # Update className
        )

    elif component_type == "button":
        return dbc.Button(
            component_kwargs.get("text", ""),
            id=id,
            size=component_kwargs.get("size", "sm"),
            className=component_kwargs.get("className", ""),
            color=component_kwargs.get("color", "primary"),
            style={"fontSize": "0.85rem", "padding": "0.3rem 0.6rem"}
        )

    elif component_type == "checklist":
        config = APP_CONFIG["checklists"].get(id, {}).copy()
        config.update({
            k: v for k, v in component_kwargs.items()
            if k in ["options", "value", "switch", "inline", "readonly"]
        })
        style = {"margin": 0, "fontSize": "0.85rem"}
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

    elif component_type == "input":
        config = APP_CONFIG["inputs"].get(id, {})
        return dcc.Input(
            id=id,
            type=config.get("type", "text"),
            min=config.get("min"),
            max=config.get("max"),
            step=config.get("step"),
            value=config.get("value"),
            className="form-control input-short",  # see CSS below
            style={"fontSize": "0.85rem"}
        )

    elif component_type == "label":
        return html.Label(
            component_kwargs.get("text", ""),
            className="filter-label"
        )

    elif component_type == "button":
        return dbc.Button(
            kwargs.get("text", ""),
            id=id,
            className=f"btn-custom {kwargs.get('className', '')}",
            color=kwargs.get("color", "primary"),
        )

    elif component_type == "input":
        return dcc.Input(
            id=id,
            className="form-control-custom input-short",
            **{k: v for k, v in kwargs.items() if k not in ["className"]}
        )

###############################################################################
# 3) HELPER FUNCTION: CREATE_FILTER_ROW
###############################################################################
def create_filter_row(label_text, component_id, component_type="dropdown", vertical=False, **kwargs):
    """
    Create a filter row with option for vertical layout
    
    Args:
        label_text (str): The label text
        component_id (str): The component identifier
        component_type (str): The type of component
        vertical (bool): If True, stack label above component
        **kwargs: Additional arguments passed to create_component
    """
    # Build the main component
    comp = create_component(component_type, id=component_id, **kwargs)

    # Wrap premium-loss-checklist if needed
    if component_id == "premium-loss-checklist":
        comp = html.Div(
            id="premium-loss-checklist-container",
            children=[comp]
        )

    if vertical:
        return html.Div([
            html.Label(label_text, className="filter-label d-block mb-2"),
            html.Div(comp, className="w-100")
        ], className="mb-3")
    else:
        # Original horizontal layout
        label_width = kwargs.get("label_width", 6)
        component_width = kwargs.get("component_width", 6)

        extra_class = "checklist-row" if component_type == "checklist" else ""
        
        return dbc.Row(
            [
                dbc.Col(
                    html.Label(label_text, className="filter-label"),
                    width=label_width
                ),
                dbc.Col(comp, width=component_width, className=f"{extra_class}-content")
            ],
            className="mb-1 filter-row"
        )
    
###############################################################################
# 4) MAIN LAYOUT: SIDEBAR + MAIN CONTENT (NO OVERLAP)
###############################################################################


def create_app_layout(initial_quarter_options=None):
    """
    Reorganized layout with all required components
    """
    try:

        APP_CONFIG['dropdowns']['end-quarter']['options'] = [
            {'label': q, 'value': q} for q in [q['value'] for q in initial_quarter_options]
        ]

        # Stores remain unchanged
        stores = [
            html.Div(id="_hidden-init-trigger", style={"display": "none"}),
            dcc.Store(id="show-data-table", data=True),
            dcc.Store(id="processed-data-store"),
            dcc.Store(id="filter-state-store"),
            dcc.Store(id='insurance-lines-state', data=initial_state),
            dcc.Store(id='expansion-state', data={'states': {}, 'all_expanded': False}),
            dcc.Store(id='tree-state', data={'states': {}, 'all_expanded': False}),
            dcc.Store(id='period-type', data=DEFAULT_PERIOD_TYPE)
        ]

        # Navbar definition
        # Update navbar definition
        navbar = dbc.Navbar(
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
        

        # Hierarchy buttons definition
        hierarchy_buttons = dbc.Row(
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

        period_type_buttonsgroup = html.Div([
            dbc.Row([
                dbc.ButtonGroup([
                    dbc.Button(
                        label,
                        id=f"btn-{value}",
                        size="sm",
                        className=button_period_main,
                        style={"height": "28px"}
                    )
                    for label, value in [
                        ("YTD", "ytd"),
                        ("YoY-Q", "yoy-q"),
                        ("YoY-Y", "yoy-y"),
                        ("QoQ", "qoq"),
                        ("MAT", "mat")
                    ]
                ]),
            ], className="mb-0"),
        ])


        # Sidebar content
        sidebar = dbc.CardBody(
            id="sidebar-filters",
            className="sidebar-filters p-3",
            children=[
                create_filter_row("Форма отчетности:", "reporting-form"),
                create_filter_row("Отчетный квартал:", "end-quarter"),
                html.Label("Тип данных:", className="filter-label mb-2"),
                period_type_buttonsgroup,
                html.Div(id="period-type-text", className="period-type-text mb-3"),
                create_filter_row("Кол-во периодов для сравнения:", "number-of-periods-data-table", component_type="input", label_width=9, component_width=3),
                create_filter_row("Линия:", "insurance-line-dropdown", vertical=True),
                create_filter_row("Основной показатель:", "primary-y-metric", vertical=True),
                create_filter_row("Бизнес:", "premium-loss-checklist", component_type="checklist", label_width=5, component_width=7),
                create_filter_row("Доп. показатель:", "secondary-y-metric", vertical=True),
                create_filter_row("Показать долю рынка:", "toggle-selected-market-share", component_type="checklist", label_width=10, component_width=2),
                create_filter_row("Показать динамику:", "toggle-selected-qtoq", component_type="checklist", label_width=10, component_width=2),
                create_filter_row("Кол-во страховщиков:", "number-of-insurers", component_type="input", label_width=9, component_width=3),                
                dbc.Button(
                    "Clear Filters",
                    id="clear-filters-button",
                    className="btn-custom btn-clear-filters",
                    color="warning"
                )
            ]
        )

        # Main content area
        main_content = html.Div(
            id="main-content",
            className="mc-container", # Changed from "main-content p-3"
            children=[
                dbc.Card([
                    dbc.CardBody([
                        html.H4(
                            id="table-title", 
                            className="mc-title" # Changed from "table-title"
                        ),
                        html.H4(
                            id="table-subtitle", 
                            className="mc-subtitle" # Changed from "table-subtitle mb-3"
                        ),
                        dcc.Loading(
                            id="loading-data-table",
                            type="default",
                            children=[
                                html.Div(
                                    id="data-table",
                                    className="dt-container" # Changed from "data-table-wrapper"
                                )
                            ]
                        )
                    ])
                ], className="mc-card"), # Changed from "mb-3"
                html.Div(
                    "Chart(s) / Additional Visuals Go Here", 
                    className="mc-charts" # Changed from "placeholder-charts mb-3"
                ),
                html.Div(
                    id="tree-container", 
                    className="mc-tree" # Changed from "tree-container"
                ),
                hierarchy_buttons
            ]
        )

        # Update debug footer
        debug_footer = html.Div(
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
                ),
            ]
        )

        # Final layout assembly
        layout = html.Div(
            id="app-container",
            className="app-container",
            children=[
                *stores,
                navbar,
                html.Div(
                    className="layout-wrapper p-3",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    sidebar,
                                    id="sidebar-col",
                                    className="sidebar-col",
                                    width="auto"
                                ),
                                dbc.Col(
                                    main_content,
                                    id="main-content-col",
                                    className="main-col",
                                    width=True
                                )
                            ],
                            className="gx-0 h-100"
                        ),
                    ]
                ),
                debug_footer
            ]
        )

        return layout

    except Exception as e:
        print(f"Error in create_app_layout: {str(e)}")
        raise