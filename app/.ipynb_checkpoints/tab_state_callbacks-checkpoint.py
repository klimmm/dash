
import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import logging
from logging_config import get_logger
logger = get_logger(__name__)


def setup_tab_state_callbacks(app):
    @app.callback(
        [
            Output("insurance-filters", "style"),
            Output("reinsurance-filters", "style"),
            Output("insurance-tab", "className"),
            Output("reinsurance-tab", "className"),
            Output("reinsurance-tab-state", "data"),
        ],
        [
            Input("insurance-tab", "n_clicks"),
            Input("reinsurance-tab", "n_clicks"),
        ],
        [
            State("reinsurance-tab-state", "data"),
        ]
    )
    def toggle_insurance_reinsurance(insurance_clicks, reinsurance_clicks, is_reinsurance):
        ctx = dash.callback_contex
        if not ctx.triggered:
            # Initial state: show insurance, hide reinsurance
            return (
                {"display": "block"},
                {"display": "none"},
                "me-1 tab-like-button active",
                "tab-like-button",
                False
            )

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "insurance-tab":
            # Show insurance, hide reinsurance
            return (
                {"display": "block"},
                {"display": "none"},
                "me-1 tab-like-button active",
                "tab-like-button",
                False
            )
        elif button_id == "reinsurance-tab":
            # Show reinsurance, hide insurance
            return (
                {"display": "none"},
                {"display": "block"},
                "me-1 tab-like-button",
                "tab-like-button active",
                True
            )

        # Default case (should not happen)
        return (
            {"display": "block"},
            {"display": "none"},
            "me-1 tab-like-button active",
            "tab-like-button",
            False
        )
    @app.callback(
        [
            Output("graphs-content", "style"),
            Output("data-table-content", "style"),
            Output("data-table-tab", "className"),
            Output("data-table-tab-state", "data"),
        ],
        [
            Input("data-table-tab", "n_clicks"),
            Input("insurance-tab", "n_clicks"),
            Input("reinsurance-tab", "n_clicks"),
        ],
        [
            State("data-table-tab-state", "data"),
        ]
    )
    def toggle_data_table(n_clicks, insurance_clicks, reinsurance_clicks, current_state):
        ctx = dash.callback_contex
        if not ctx.triggered:
            # Initial state: show data table, hide graphs
            return (
                {"display": "none"},
                {"display": "block"},
                "tab-like-button active",
                True
            )

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "data-table-tab":
            # Toggle data table visibility
            if current_state:
                # Currently showing data table; hide it and show graphs
                return (
                    {"display": "block"},
                    {"display": "none"},
                    "tab-like-button",
                    False
                )
            else:
                # Currently showing graphs; hide them and show data table
                return (
                    {"display": "none"},
                    {"display": "block"},
                    "tab-like-button active",
                    True
                )

        elif button_id in ["insurance-tab", "reinsurance-tab"]:
            # If toggling insurance/reinsurance, ensure graphs are shown and data table is hidden
            return (
                {"display": "block"},
                {"display": "none"},
                "tab-like-button",
                False
            )

        # Default case (should not happen)
        raise PreventUpdate