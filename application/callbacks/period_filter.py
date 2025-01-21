# app/components/period_filter.py

import dash
from dash import no_update
from dash import Input, Output, State
from constants.translations import translate
from config.default_values import DEFAULT_REPORTING_FORM, DEFAULT_PERIOD_TYPE, DEFAULT_SHOW_MARKET_SHARE, DEFAULT_SHOW_CHANGES
from config.logging_config import get_logger, track_callback, track_callback_end
from application.style_config import StyleConstants


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
            output = (*button_classes, no_update, period_type_text)
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


    @app.callback(
        [
            Output("btn-0420158", "className"),
            Output("btn-0420162", "className"),
            Output('reporting-form', 'data'),
        ],
        [
            Input("btn-0420158", "n_clicks"),
            Input("btn-0420162", "n_clicks")
        ],
        [
            State('reporting-form', 'data')
        ]
    )
    def update_period_type(
        form_0420158_clicks, form_0420162_clicks,
        current_state
    ):
        
        logger.warning(f"reporting form current state {current_state}")
        logger.warning(f"DEFAULT_REPORTING_FORM: {DEFAULT_REPORTING_FORM}")  # Add this
        ctx = dash.callback_context
        start_time = track_callback('app.period_filter', 'update_period', ctx)
        button_map = {
            'btn-0420158': '0420158',
            'btn-0420162': '0420162'  # Fixed typo here
        }
        
        # Initialize current state and button classes
        current_state = current_state if current_state else DEFAULT_REPORTING_FORM
        button_classes = [button_period_main for _ in range(2)]
        active_main = current_state
        
        # Set initial active button class
        for i, (btn_id, btn_val) in enumerate(button_map.items()):
            logger.warning(f"Comparing {btn_val} with {active_main}")  # Add this
            if btn_val == active_main:
                button_classes[i] = button_period_main_active
                break
        
        # If no button clicked, return initial button classes but don't update state
        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.period_filter', 'update_period_type', start_time, result=output)
            return output
            
        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"update_reporting_form triggered by {triggered}")
            
            if triggered in button_map:
                # Reset button classes
                button_classes = [button_period_main for _ in range(2)]
                # Update state based on clicked button
                new_state = button_map[triggered]
                # Set active class for clicked button
                button_index = list(button_map.keys()).index(triggered)
                button_classes[button_index] = button_period_main_active
                logger.debug(f"reporting_form_state: {new_state}")
                output = (*button_classes, new_state)
                track_callback_end('app.period_filter', 'update_period_type', start_time, result=output)
                return output
                
        except Exception as e:
            logger.error(f"Error in update_period: {e}")
            
        # Default return if nothing else matches - update buttons but not state
        output = (*button_classes, dash.no_update)
        track_callback_end('app.period_filter', 'update_period_type', start_time, result=output)
        return output
    
    @app.callback(
        [
            Output("btn-market-share", "className"),
            Output("btn-qtoq", "className"),
            Output('toggle-selected-market-share', 'data'),
            Output('toggle-selected-qtoq', 'data'),
        ],
        [
            Input("btn-market-share", "n_clicks"),
            Input("btn-qtoq", "n_clicks")
        ],
        [
            State('toggle-selected-market-share', 'data'),
            State('toggle-selected-qtoq', 'data')
        ]
    )
    def update_metric_toggles(
        market_share_clicks, qtoq_clicks,
        market_share_state, qtoq_state
    ):
        logger.warning(f"xxx toggle states - market share: {market_share_state}, qtoq: {qtoq_state}")
        ctx = dash.callback_context
        start_time = track_callback('app.metric_toggles', 'update_toggles', ctx)
        
        button_map = {
            'btn-market-share': ('market-share', 0),  # (id, index in button_classes)
            'btn-qtoq': ('qtoq', 1)
        }
        
        # Initialize states
        market_share_state = market_share_state if market_share_state else []
        qtoq_state = qtoq_state if qtoq_state else []
        button_classes = [button_period_main for _ in range(2)]
        
        # Set initial active button classes based on current states
        if market_share_state == ['show']:
            button_classes[0] = button_period_main_active
        if qtoq_state == ['show']:
            button_classes[1] = button_period_main_active
        
        # If no button clicked, return initial states
        if not ctx.triggered:
            output = (*button_classes, dash.no_update, dash.no_update)
            track_callback_end('app.metric_toggles', 'update_toggles', start_time, result=output)
            return output
            
        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.warning(f"update_metric_toggles triggered by {triggered}")
            logger.warning(f"market_share_state {market_share_state}")
            if triggered in button_map:
                _, button_index = button_map[triggered]
                
                # Toggle button class and state
                if triggered == 'btn-market-share':
                    if market_share_state == ['show']:
                        button_classes[button_index] = button_period_main
                        market_share_state = []
                    else:
                        button_classes[button_index] = button_period_main_active
                        market_share_state = ['show']
                else:  # btn-qtoq
                    if qtoq_state == ['show']:
                        button_classes[button_index] = button_period_main
                        qtoq_state = []
                    else:
                        button_classes[button_index] = button_period_main_active
                        qtoq_state = ['show']
                logger.warning(f"market_share_state after {market_share_state}")
                output = (*button_classes, market_share_state, qtoq_state)
                track_callback_end('app.metric_toggles', 'update_toggles', start_time, result=output)
                return output
                
        except Exception as e:
            logger.error(f"Error in update_metric_toggles: {e}")
            
        # Default return if nothing else matches
        output = (*button_classes, market_share_state, qtoq_state)
        track_callback_end('app.metric_toggles', 'update_toggles', start_time, result=output)
        return output
    
        
    @app.callback(
        [
            Output("btn-top-5", "className"),
            Output("btn-top-10", "className"),
            Output("btn-top-20", "className"),
            Output('number-of-insurers', 'data'),
        ],
        [
            Input('btn-top-5', 'n_clicks'),
            Input('btn-top-10', 'n_clicks'),
            Input('btn-top-20', 'n_clicks')
        ],
        State('number-of-insurers', 'data'),
        prevent_initial_call=False
    )
    def update_top_insurers_value(n_clicks_5, n_clicks_10, n_clicks_20, state):
        """Update the number of insurers based on button clicks"""
        ctx = dash.callback_context
        logger.warning(f"number of clicked {n_clicks_5}, {n_clicks_10}, {n_clicks_20}")
        start_time = track_callback('app.metric_toggles', 'update_toggles', ctx)
    
        # Define button styling classes
    
        button_map = {
            'btn-top-5': ('top-5', 0),
            'btn-top-10': ('top-10', 1),
            'btn-top-20': ('top-20', 2)
        }
    
        # Initialize button classes
        button_classes = [button_period_main for _ in range(3)]
        
        # Set active button based on current state
        if state == 5:
            button_classes[0] = button_period_main_active
        elif state == 10:
            button_classes[1] = button_period_main_active
        elif state == 20:
            button_classes[2] = button_period_main_active
    
        value_map = {
            'btn-top-5': 5,
            'btn-top-10': 10,
            'btn-top-20': 20
        }
    
        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.metric_toggles', 'update_toggles', start_time, result=output)
            return output
    
        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.warning(f"update_metric_toggles triggered by {triggered}")
            
            if triggered in button_map:
                _, button_index = button_map[triggered]
                state = value_map.get(triggered, 10)
                
                # Update button classes based on new state
                button_classes = [button_period_main for _ in range(3)]
                button_classes[button_index] = button_period_main_active
                
                output = (*button_classes, state)
                track_callback_end('app.metric_toggles', 'update_toggles', start_time, result=output)
                return output
    
        except Exception as e:
            logger.error(f"Error in update_metric_toggles: {e}")
            raise

    @app.callback(
        [
            Output("btn-period-1", "className"),
            Output("btn-period-2", "className"),
            Output("btn-period-4", "className"),
            Output("btn-period-5", "className"),
            Output('number-of-periods-data-table', 'data'),
        ],
        [
            Input('btn-period-1', 'n_clicks'),
            Input('btn-period-2', 'n_clicks'),
            Input('btn-period-4', 'n_clicks'),
            Input('btn-period-5', 'n_clicks')
        ],
        State('number-of-periods-data-table', 'data'),
        prevent_initial_call=False
    )
    def update_periods_data_table_value(n_clicks_1, n_clicks_2, n_clicks_4, n_clicks_5, state):
        """Update the number of periods based on button clicks"""
        ctx = dash.callback_context
        logger.warning(f"number of clicked {n_clicks_1}, {n_clicks_2}, {n_clicks_4}, {n_clicks_5}")
        start_time = track_callback('app.metric_toggles', 'update_periods', ctx)
    
        # Define button styling classes
        button_period_main = StyleConstants.BTN["PERIOD"]
    
        button_map = {
            'btn-period-1': ('period-1', 0),
            'btn-period-2': ('period-2', 1),
            'btn-period-4': ('period-4', 2),
            'btn-period-5': ('period-5', 3)
        }
    
        # Initialize button classes
        button_classes = [button_period_main for _ in range(4)]
        
        # Set active button based on current state
        value_map = {
            'btn-period-1': 1,
            'btn-period-2': 2,
            'btn-period-4': 4,
            'btn-period-5': 5
        }
        
        # Set initial active button based on state
        for button_id, value in value_map.items():
            if state == value:
                _, index = button_map[button_id]
                button_classes[index] = button_period_main_active
    
        if not ctx.triggered:
            output = (*button_classes, dash.no_update)
            track_callback_end('app.metric_toggles', 'update_periods', start_time, result=output)
            return output
    
        try:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.warning(f"update_periods triggered by {triggered}")
            
            if triggered in button_map:
                _, button_index = button_map[triggered]
                state = value_map.get(triggered, 2)  # Default to 2 periods if something goes wrong
                
                # Update button classes based on new state
                button_classes = [button_period_main for _ in range(4)]
                button_classes[button_index] = button_period_main_active
                
                output = (*button_classes, state)
                track_callback_end('app.metric_toggles', 'update_periods', start_time, result=output)
                return output
    
        except Exception as e:
            logger.error(f"Error in update_periods: {e}")
            raise
    
