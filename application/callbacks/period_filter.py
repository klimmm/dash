# app/components/period_filter.py

import dash
from dash import Input, Output, State
from constants.translations import translate
from config.default_values import (
    DEFAULT_PERIOD_TYPE
)
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


button_period_main = "btn-custom btn-period"
button_period_main_active = "btn-custom btn-period active"


def setup_period_type_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for period filter"""

    @app.callback(
        [
            Output("btn-ytd", "className"),
            Output("btn-yoy-q", "className"),
            Output("btn-yoy-y", "className"),
            Output("btn-qoq", "className"),
            Output("btn-mat", "className"),
            Output('period-type', 'data'),
            Output('period-type-text', 'children')
        ],
        [
            Input("btn-ytd", "n_clicks"),
            Input("btn-yoy-q", "n_clicks"),
            Input("btn-yoy-y", "n_clicks"),
            Input("btn-qoq", "n_clicks"),
            Input("btn-mat", "n_clicks")
        ],
        [
            State('period-type', 'data')
        ]
    )
    def update_period_type(
        ytd_clicks, yoy_q_clicks, yoy_y_clicks, qoq_clicks, mat_clicks,
        current_state
    ):
        ctx = dash.callback_context
        start_time = track_callback('app.period_filter', 'update_period', ctx)

        button_map = {
            'btn-ytd': 'ytd',
            'btn-yoy-q': 'yoy_q',
            'btn-yoy-y': 'yoy_y',
            'btn-qoq': 'qoq',
            'btn-mat': 'mat'
        }

        # Initialize current state and button classes
        current_state = current_state if current_state else DEFAULT_PERIOD_TYPE
        button_classes = [button_period_main for _ in range(5)]
        active_main = current_state

        # Set initial active button class
        for i, (btn_id, btn_val) in enumerate(button_map.items()):
            if btn_val == active_main:
                button_classes[i] = button_period_main_active
                break

        # If no button clicked, return initial state
        if not ctx.triggered:
            period_type_text = translate(current_state)
            output = (*button_classes, current_state, period_type_text)
            track_callback_end('app.period_filter', 'update_period_type', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"update_period triggered by {triggered}")

            if triggered in button_map:
                # Reset button classes
                button_classes = [button_period_main for _ in range(5)]

                # Update state based on clicked button
                new_state = button_map[triggered]

                # Set active class for clicked button
                button_index = list(button_map.keys()).index(triggered)
                button_classes[button_index] = button_period_main_active

                period_type_text = translate(new_state)

                logger.debug(f"'date_type_state: {new_state}")

                output = (*button_classes, new_state, period_type_text)
                track_callback_end('app.period_filter', 'update_period_type', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_period: {e}")