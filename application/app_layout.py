import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import List, Optional
from application.insurance_lines_tree import create_lines_checklist_buttons, create_debug_footer
from application.create_component import FilterComponents
from application.filters import create_filters
from application.navbar_and_stores import create_navbar, create_stores
from application.style_config import StyleConstants

def create_app_layout(
    initial_quarter_options: Optional[List[dict]] = None, 
    initial_insurer_options: Optional[List[dict]] = None
) -> List:
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
                initial_insurer_options 
            )

        return dbc.Container([
            *create_stores(),
            create_navbar(),
            html.Div(id="dummy-output", style={"display": "none"}),
            html.Div(id="dummy-trigger", style={"display": "none"}),
            html.Div(id="tree-container", className=StyleConstants.CONTAINER["TREE"]),
            create_lines_checklist_buttons(),
            dbc.CardBody([
                dbc.Row([
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
                    ], md=12),
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