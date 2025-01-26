"""
Optimized callbacks for button interactions in the filter interface.
"""

import dash
from dash import no_update
from dash import Input, Output, State
from constants.translations import translate
from config.default_values import (
    DEFAULT_REPORTING_FORM, 
    DEFAULT_PERIOD_TYPE, 
    DEFAULT_SHOW_MARKET_SHARE, 
    DEFAULT_SHOW_CHANGES
)
from config.logging_config import get_logger, track_callback, track_callback_end
from application.style_config import StyleConstants

logger = get_logger(__name__)

button_period_main = "btn-custom btn-period"
button_period_main_active = "btn-custom btn-period active"

def setup_buttons_callbacks(app: dash.Dash) -> None:
    """Setup callbacks for period filter with new button IDs"""

    @app.callback(
        [
            Output("expanded-btn-period-type-ytd", "className"),
            Output("expanded-btn-period-type-yoy-q", "className"),
            Output("expanded-btn-period-type-yoy-y", "className"),
            Output("expanded-btn-period-type-qoq", "className"),
            Output("expanded-btn-period-type-mat", "className"),
            Output('period-type', 'data'),
            Output('period-type-text', 'children')
        ],
        [
            Input("expanded-btn-period-type-ytd", "n_clicks"),
            Input("expanded-btn-period-type-yoy-q", "n_clicks"),
            Input("expanded-btn-period-type-yoy-y", "n_clicks"),
            Input("expanded-btn-period-type-qoq", "n_clicks"),
            Input("expanded-btn-period-type-mat", "n_clicks")
        ],
        [State('period-type', 'data')]
    )
    def update_period_type(ytd_clicks, yoy_q_clicks, yoy_y_clicks, qoq_clicks, mat_clicks, current_state):
        ctx = dash.callback_context
        start_time = track_callback('app.buttons_callbacks', 'update_period_type', ctx)

        button_map = {
            'expanded-btn-period-type-ytd': 'ytd',
            'expanded-btn-period-type-yoy-q': 'yoy_q',
            'expanded-btn-period-type-yoy-y': 'yoy_y',
            'expanded-btn-period-type-qoq': 'qoq',
            'expanded-btn-period-type-mat': 'mat'
        }

        # Rest of the function remains the same, just use new button IDs
        current_state = current_state if current_state else DEFAULT_PERIOD_TYPE
        button_classes = [button_period_main for _ in range(5)]
        active_main = current_state

        for i, (btn_id, btn_val) in enumerate(button_map.items()):
            if btn_val == active_main:
                button_classes[i] = button_period_main_active
                break

        if not ctx.triggered:
            period_type_text = translate(current_state)
            output = (*button_classes, no_update, period_type_text)
            track_callback_end('app.buttons_callbacks', 'update_period_type', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"update_period triggered by {triggered}")

            if triggered in button_map:
                button_classes = [button_period_main for _ in range(5)]
                new_state = button_map[triggered]
                button_index = list(button_map.keys()).index(triggered)
                button_classes[button_index] = button_period_main_active
                period_type_text = translate(new_state)

                output = (*button_classes, new_state, period_type_text)
                track_callback_end('app.buttons_callbacks', 'update_period_type', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_period: {e}")
            raise

    @app.callback(
        [
            Output("expanded-btn-reporting-form-0420158", "className"),
            Output("expanded-btn-reporting-form-0420162", "className"),
            Output('reporting-form', 'data'),
        ],
        [
            Input("expanded-btn-reporting-form-0420158", "n_clicks"),
            Input("expanded-btn-reporting-form-0420162", "n_clicks")
        ],
        [State('reporting-form', 'data')]
    )
    def update_reporting_form(form_0420158_clicks, form_0420162_clicks, current_state):
        ctx = dash.callback_context
        start_time = track_callback('app.buttons_callbacks', 'update_reporting_form', ctx)

        button_map = {
            'expanded-btn-reporting-form-0420158': '0420158',
            'expanded-btn-reporting-form-0420162': '0420162'
        }

        # Rest of the function remains the same, just use new button IDs
        current_state = current_state if current_state else DEFAULT_REPORTING_FORM
        button_classes = [button_period_main for _ in range(2)]
        active_main = current_state

        for i, (btn_id, btn_val) in enumerate(button_map.items()):
            if btn_val == active_main:
                button_classes[i] = button_period_main_active
                break

        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.buttons_callbacks', 'update_reporting_form', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            if triggered in button_map:
                button_classes = [button_period_main for _ in range(2)]
                new_state = button_map[triggered]
                button_index = list(button_map.keys()).index(triggered)
                button_classes[button_index] = button_period_main_active
                
                output = (*button_classes, new_state)
                track_callback_end('app.buttons_callbacks', 'update_reporting_form', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_reporting_form: {e}")
            raise

    @app.callback(
        [
            Output("expanded-btn-metric-toggles-market-share", "className"),
            Output("expanded-btn-metric-toggles-qtoq", "className"),
            Output('toggle-selected-market-share', 'data'),
            Output('toggle-selected-qtoq', 'data'),
        ],
        [
            Input("expanded-btn-metric-toggles-market-share", "n_clicks"),
            Input("expanded-btn-metric-toggles-qtoq", "n_clicks")
        ],
        [
            State('toggle-selected-market-share', 'data'),
            State('toggle-selected-qtoq', 'data')
        ]
    )
    def update_ms_dynamic_toggles(market_share_clicks, qtoq_clicks, market_share_state, qtoq_state):
        ctx = dash.callback_context
        start_time = track_callback('app.buttons_callbacks', 'update_ms_dynamic_toggles', ctx)

        button_map = {
            'expanded-btn-metric-toggles-market-share': ('market-share', 0),
            'expanded-btn-metric-toggles-qtoq': ('qtoq', 1)
        }

        # Rest of the function remains the same, just use new button IDs
        market_share_state = market_share_state if market_share_state else []
        qtoq_state = qtoq_state if qtoq_state else []
        button_classes = [button_period_main for _ in range(2)]

        if market_share_state == ['show']:
            button_classes[0] = button_period_main_active
        if qtoq_state == ['show']:
            button_classes[1] = button_period_main_active

        if not ctx.triggered:
            output = (*button_classes, dash.no_update, dash.no_update)
            track_callback_end('app.buttons_callbacks', 'update_ms_dynamic_toggles', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            if triggered in button_map:
                _, button_index = button_map[triggered]
                
                if triggered == 'expanded-btn-metric-toggles-market-share':
                    if market_share_state == ['show']:
                        button_classes[button_index] = button_period_main
                        market_share_state = []
                    else:
                        button_classes[button_index] = button_period_main_active
                        market_share_state = ['show']
                else:
                    if qtoq_state == ['show']:
                        button_classes[button_index] = button_period_main
                        qtoq_state = []
                    else:
                        button_classes[button_index] = button_period_main_active
                        qtoq_state = ['show']

                output = (*button_classes, market_share_state, qtoq_state)
                track_callback_end('app.buttons_callbacks', 'update_ms_dynamic_toggles', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_metric_toggles: {e}")
            raise

    @app.callback(
        [
            Output("expanded-btn-top-insurers-top-5", "className"),
            Output("expanded-btn-top-insurers-top-10", "className"),
            Output("expanded-btn-top-insurers-top-20", "className"),
            Output('number-of-insurers', 'data'),
        ],
        [
            Input("expanded-btn-top-insurers-top-5", "n_clicks"),
            Input("expanded-btn-top-insurers-top-10", "n_clicks"),
            Input("expanded-btn-top-insurers-top-20", "n_clicks")
        ],
        State('number-of-insurers', 'data'),
        prevent_initial_call=False
    )
    def update_number_insurers(n_clicks_5, n_clicks_10, n_clicks_20, state):
        ctx = dash.callback_context
        start_time = track_callback('app.buttons_callbacks', 'update_number_insurers', ctx)

        button_map = {
            'expanded-btn-top-insurers-top-5': ('top-5', 0),
            'expanded-btn-top-insurers-top-10': ('top-10', 1),
            'expanded-btn-top-insurers-top-20': ('top-20', 2)
        }

        value_map = {
            'expanded-btn-top-insurers-top-5': 5,
            'expanded-btn-top-insurers-top-10': 10,
            'expanded-btn-top-insurers-top-20': 20
        }

        button_classes = [button_period_main for _ in range(3)]
        
        if state == 5:
            button_classes[0] = button_period_main_active
        elif state == 10:
            button_classes[1] = button_period_main_active
        elif state == 20:
            button_classes[2] = button_period_main_active

        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.buttons_callbacks', 'update_number_insurers', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if triggered in button_map:
                _, button_index = button_map[triggered]
                state = value_map.get(triggered, 10)
                
                button_classes = [button_period_main for _ in range(3)]
                button_classes[button_index] = button_period_main_active
                
                output = (*button_classes, state)
                track_callback_end('app.buttons_callbacks', 'update_number_insurers', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_number_insurers: {e}")
            raise

    @app.callback(
        [
            Output("expanded-btn-periods-data-table-period-1", "className"),
            Output("expanded-btn-periods-data-table-period-2", "className"),
            Output("expanded-btn-periods-data-table-period-3", "className"),
            Output("expanded-btn-periods-data-table-period-4", "className"),
            Output("expanded-btn-periods-data-table-period-5", "className"),
            Output('number-of-periods-data-table', 'data'),
        ],
        [
            Input("expanded-btn-periods-data-table-period-1", "n_clicks"),
            Input("expanded-btn-periods-data-table-period-2", "n_clicks"),
            Input("expanded-btn-periods-data-table-period-3", "n_clicks"),
            Input("expanded-btn-periods-data-table-period-4", "n_clicks"),
            Input("expanded-btn-periods-data-table-period-5", "n_clicks")
        ],
        State('number-of-periods-data-table', 'data'),
        prevent_initial_call=False
    )
    def update_number_periods(n_clicks_1, n_clicks_2, n_clicks_3, n_clicks_4, n_clicks_5, state):
        ctx = dash.callback_context
        start_time = track_callback('app.buttons_callbacks', 'update_number_periods', ctx)

        button_map = {
            'expanded-btn-periods-data-table-period-1': ('period-1', 0),
            'expanded-btn-periods-data-table-period-2': ('period-2', 1),
            'expanded-btn-periods-data-table-period-3': ('period-3', 2),
            'expanded-btn-periods-data-table-period-4': ('period-4', 3),
            'expanded-btn-periods-data-table-period-5': ('period-5', 4)
        }

        value_map = {
            'expanded-btn-periods-data-table-period-1': 1,
            'expanded-btn-periods-data-table-period-2': 2,
            'expanded-btn-periods-data-table-period-3': 3,
            'expanded-btn-periods-data-table-period-4': 4,
            'expanded-btn-periods-data-table-period-5': 5
        }

        button_classes = [button_period_main for _ in range(5)]
        
        # Set initial active button based on state
        for button_id, value in value_map.items():
            if state == value:
                _, index = button_map[button_id]
                button_classes[index] = button_period_main_active

        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.buttons_callbacks', 'update_number_periods', start_time, result=output)
            return output

        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            
            if triggered in button_map:
                _, button_index = button_map[triggered]
                state = value_map.get(triggered, 2)  # Default to 2 periods
                
                button_classes = [button_period_main for _ in range(5)]
                button_classes[button_index] = button_period_main_active
                
                output = (*button_classes, state)
                track_callback_end('app.buttons_callbacks', 'update_number_periods', start_time, result=output)
                return output

        except Exception as e:
            logger.error(f"Error in update_periods: {e}")
            raise