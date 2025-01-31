from dash import dcc, html
from application.style_config import StyleConstants
import dash_bootstrap_components as dbc


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
