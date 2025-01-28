import dash_bootstrap_components as dbc
from dash import dcc, html
from application.filters import create_filters
from application.navbar_and_stores import create_navbar, create_stores
from constants.style_config import StyleConstants


def create_lines_checklist_buttons() -> dbc.Row:
    """Create hierarchy control buttons."""
    return dbc.Row(
        [
            dbc.Col([
                dbc.Button("Показать все", id="expand-all-button",
                          style={"display": "none"}, color="secondary"),
                dbc.Button("Показать иерархию", id="collapse-button",
                          style={"display": "none"}, color="info", className="ms-1"),
                dbc.Button("Drill down", id="detailize-button",
                          style={"display": "none"}, color="info", className="ms-1"),
            ])
        ],
        className="mb-3"
    )


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
def create_app_layout():
    try:
        return dbc.Container([
            *create_stores(),
            create_navbar(),
            html.Div(id="dummy-output", style={"display": "none"}),
            html.Div(id="dummy-trigger", style={"display": "none"}),
            html.Div(id="tree-container", className=StyleConstants.CONTAINER["TREE"]),
            
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Show Additional Filters",
                            id="toggle-sidebar-button-sidebar",
                            className=StyleConstants.BTN["SIDEBAR_SHOW"],
                            style={"display": "none"}

                        ),
                        create_lines_checklist_buttons(),
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