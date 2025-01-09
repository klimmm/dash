from dash import html, dcc, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import dash
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging
import json
from dash.exceptions import PreventUpdate

# Set up logging with formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PERIOD_TYPE = {'main': 'qoq', 'sub': None}
DEFAULT_AGGREGATION_TYPE = 'previous_quarter'
DEFAULT_Q_VALUE = 4
DEFAULT_START_QUARTER = '2022Q1'
DEFAULT_END_QUARTER = '2023Q4'
DEFAULT_NUMBER_OF_PERIODS = 1
DEFAULT_BUTTON_INDEX = 0

class DateRangeFilter:
    def __init__(self, available_quarters: Optional[List[str]] = None):
        """Initialize with test quarters if provided"""
        self.available_quarters = available_quarters or self._generate_default_quarters()
        logger.info(f"Initialized with quarters: {self.available_quarters}")

    def _generate_default_quarters(self) -> List[str]:
        quarters = []
        current = datetime.now()
        year = current.year
        quarter = (current.month - 1) // 3 + 1

        for i in range(8):
            quarters.append(f"{year}Q{quarter}")
            quarter -= 1
            if quarter < 1:
                quarter = 4
                year -= 1

        return sorted(quarters)

    def create_layout(self) -> html.Div:
        return html.Div([
            # Period Type Selection
            html.Div([
                self._create_period_selector(),
                html.Div(id="date-type-output"),
            ], className="mb-3"),

            # Range Selection
            html.Div([
                self._create_range_selector(),
            ], className="mb-3"),

            # State Stores
            dcc.Store(id='date-type-state', data=DEFAULT_PERIOD_TYPE),
            dcc.Store(id='period-type', data=DEFAULT_AGGREGATION_TYPE),
            dcc.Store(id='quarter-value-output', data=DEFAULT_Q_VALUE),
            dcc.Store(id='quarter-options-store', data=self.available_quarters),
            dcc.Store(id='number-of-years-to-show', data=DEFAULT_NUMBER_OF_PERIODS),

            # Display current state (for debugging)
            html.Pre(id='debug-output', style={'whiteSpace': 'pre-wrap'})
        ])

    def _create_period_selector(self) -> html.Div:
        """Create the period type selector buttons with distinct styling"""
        return html.Div([
            dbc.ButtonGroup([
                dbc.Button(
                    label,
                    id={"type": "main-btn", "index": value},
                    size="sm",
                    className="py-0 btn-custom",  # Main button style
                    style={"height": "36px"}
                )
                for label, value in [
                    ("YTD", "ytd"),
                    ("YoY", "yoy"),
                    ("QoQ", "qoq"),
                    ("MAT", "mat"),
                    ("Cum", "cum")
                ]
            ]),
            dbc.Collapse(
                dbc.ButtonGroup(id="additional-options"),
                id="collapse",
                is_open=True,
                className="d-inline-block ms-1"
            )
        ])

    def _create_range_selector(self) -> html.Div:
        return html.Div([
            dbc.ButtonGroup([
                dbc.Button(
                    label,
                    id=f"btn-{value}",
                    n_clicks=0,
                    size="sm",
                    className="py-0 btn-custom",
                    style={"height": "36px"}
                )
                for label, value in [
                    ("1Y", "1y"),
                    ("2Y", "2y"),
                    ("5Y", "5y"),
                    ("Custom", "custom")
                ]
            ]),
            dbc.Collapse(
                self._create_custom_range_input(),
                id="custom-range-collapse",
                is_open=False,
                className="ms-1"
            )
        ])

    def _create_custom_range_input(self) -> html.Div:
        return html.Div([
            dbc.Input(
                id="custom-year-input",
                type="number",
                style={"width": 75, "height": "36px"},
                className="me-2"
            ),
            dcc.Dropdown(
                id='start-quarter',
                options=[{'label': q, 'value': q} for q in self.available_quarters],
                value=DEFAULT_START_QUARTER,
                clearable=False,
                style={"width": 100}
            ),
            dcc.Dropdown(
                id='end-quarter',
                options=[{'label': q, 'value': q} for q in self.available_quarters],
                value=DEFAULT_END_QUARTER,
                clearable=False,
                style={"width": 100}
            ),
            dbc.Button(
                "Go",
                id="btn-custom-year",
                className="py-0 btn-custom ms-2",
                style={"height": "36px"}
            )
        ], className="d-flex align-items-center")

    def _create_custom_range_input(self) -> html.Div:
        """Create the custom range input controls - removed Go button"""
        return html.Div([
            dbc.Input(
                id="custom-year-input",
                type="number",
                style={"width": 75, "height": "36px"},
                className="me-2"
            ),
            dcc.Dropdown(
                id='start-quarter',
                options=[{'label': q, 'value': q} for q in self.available_quarters],
                value=DEFAULT_START_QUARTER,
                clearable=False,
                style={"width": 100}
            ),
            dcc.Dropdown(
                id='end-quarter',
                options=[{'label': q, 'value': q} for q in self.available_quarters],
                value=DEFAULT_END_QUARTER,
                clearable=False,
                style={"width": 100}
            )
        ], className="d-flex align-items-center")

    def _calculate_range(self, years: int, end_quarter: str = None) -> Tuple[str, str]:

        if end_quarter is None:
            current_date = datetime.now()
            current_year = current_date.year
            current_quarter = (current_date.month - 1) // 3 + 1
            target_end = f"{current_year}Q{current_quarter}"

            end_quarter = next(
                (q for q in reversed(self.available_quarters) if q <= target_end),
                self.available_quarters[-1]
            )

        end_year = int(end_quarter.split('Q')[0])
        target_start_year = end_year - years
        target_start = f"{target_start_year}Q{end_quarter[-1]}"

        start_quarter = next(
            (q for q in self.available_quarters if q >= target_start),
            self.available_quarters[0]
        )

        logger.info(f"Calculating range for {years} years: {start_quarter} - {end_quarter}")

        return start_quarter, end_quarter


    def setup_callbacks(self, app: dash.Dash) -> None:
        @app.callback(
            [Output('date-type-state', 'data'),
             Output("collapse", "is_open"),
             Output("additional-options", "children"),
             Output({"type": "main-btn", "index": ALL}, "className")],  # Added main button styles
            [Input({"type": "main-btn", "index": ALL}, "n_clicks"),
             Input({"type": "sub-btn", "index": ALL}, "n_clicks")],
            [State('date-type-state', 'data'),
             State({"type": "main-btn", "index": ALL}, "id")]  # Added main button IDs
        )
        def update_period_selection(main_clicks, sub_clicks, current_state, main_btn_ids):
            """Handle period type selection"""
            ctx = dash.callback_contex
            if not ctx.triggered:
                button_classes = ["py-0 btn-custom"] * len(main_btn_ids)
                # Set active class for current main button
                for i, btn_id in enumerate(main_btn_ids):
                    if btn_id['index'] == current_state['main']:
                        button_classes[i] = "py-0 btn-custom active"
                return current_state, True, [], button_classes

            try:
                triggered = ctx.triggered[0]["prop_id"].split(".")[0]
                logger.info(f"Button triggered: {triggered}")
                button_info = json.loads(triggered)
                button_type, button_index = button_info["type"], button_info["index"]

                # Initialize button classes
                button_classes = ["py-0 btn-custom"] * len(main_btn_ids)

                new_state = current_state.copy()
                if button_type == "main-btn":
                    prev_main = new_state['main']
                    new_state['main'] = button_index

                    # Set active class for clicked main button
                    for i, btn_id in enumerate(main_btn_ids):
                        if btn_id['index'] == button_index:
                            button_classes[i] = "py-0 btn-custom active"

                    # Always set appropriate default sub when changing main button
                    if button_index == "ytd":
                        new_state['sub'] = '1h'  # Default for YTD
                    elif button_index == "yoy":
                        new_state['sub'] = 'q'   # Default for YoY
                    else:
                        new_state['sub'] = None

                    logger.info(f"Changed main from {prev_main} to {button_index}, new sub: {new_state['sub']}")

                    # Generate sub-buttons based on main selection
                    is_open = button_index in ["ytd", "yoy"]
                    sub_buttons = []
                    if button_index == "ytd":
                        sub_buttons = [
                            ("3M", "3m"), ("1H", "1h"),
                            ("9M", "9m"), ("FY", "fy")
                        ]
                    elif button_index == "yoy":
                        sub_buttons = [("Q", "q"), ("Y", "y")]

                    additional_options = [
                        dbc.Button(
                            label,
                            id={"type": "sub-btn", "index": value},
                            size="sm",
                            className=("py-0 ms-1 btn-secondary-custom active"
                                     if value == new_state['sub']
                                     else "py-0 ms-1 btn-secondary-custom"),
                            style={"height": "36px"}
                        )
                        for label, value in sub_buttons
                    ]
                    return new_state, is_open, additional_options, button_classes

                elif button_type == "sub-btn":
                    new_state['sub'] = button_index
                    logger.info(f"Sub button clicked: {button_index}")
                    # Keep current main button active
                    for i, btn_id in enumerate(main_btn_ids):
                        if btn_id['index'] == new_state['main']:
                            button_classes[i] = "py-0 btn-custom active"
                    return new_state, True, dash.no_update, button_classes

            except Exception as e:
                logger.error(f"Error in update_period_selection: {e}")
                raise PreventUpdate

            return current_state, True, [], button_classes









        @app.callback(
            [Output('number-of-years-to-show', 'data'),
             Output('start-quarter', 'value'),
             Output('end-quarter', 'value'),
             Output("btn-1y", "className"),
             Output("btn-2y", "className"),
             Output("btn-5y", "className"),
             Output("btn-custom", "className"),
             Output("custom-range-collapse", "is_open"),
             Output("custom-year-input", "value")],
            [Input("btn-1y", "n_clicks"),
             Input("btn-2y", "n_clicks"),
             Input("btn-5y", "n_clicks"),
             Input("btn-custom", "n_clicks"),
             Input("custom-year-input", "value"),
             Input("start-quarter", "value"),
             Input("end-quarter", "value"),
             Input("btn-custom", "n_clicks")],
            [State("custom-range-collapse", "is_open"),
             State('number-of-years-to-show', 'data'),
             State("end-quarter", "value")],
        )
        def update_range_selection(btn1, btn2, btn5, btn_custom, custom_year,
                                 start_q, end_q, n_clicks_custom, is_custom_open, current_years, current_end_quarter):
            ctx = dash.callback_contex
            if not ctx.triggered:
                initial_classes = ["py-0 btn-custom"] * 4
                initial_classes[DEFAULT_BUTTON_INDEX] = "py-0 btn-custom active"
                return (DEFAULT_NUMBER_OF_PERIODS, DEFAULT_START_QUARTER, DEFAULT_END_QUARTER,
                       *initial_classes, False, DEFAULT_NUMBER_OF_PERIODS)

            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.info(f"Range selection triggered by: {triggered_id}")

            button_classes = ["py-0 btn-custom"] * 4

            # Handle year buttons
            years_map = {
                "btn-1y": (1, 0),
                "btn-2y": (2, 1),
                "btn-5y": (5, 2)
            }


            #is_custom_open is_custom_open
            logger.info(f"current_end_quarter : {current_end_quarter}")
            if triggered_id in years_map:
                years, btn_index = years_map[triggered_id]
                start_q, end_q = self._calculate_range(years)
                button_classes[btn_index] = "py-0 btn-custom active"
                # Close custom collapse and sync custom year inpu
                return years, start_q, end_q, *button_classes, False, years

            # Handle custom button and inputs
            if triggered_id == "btn-custom":
                button_classes[3] = "py-0 btn-custom active"
                new_is_open = not is_custom_open
                # Sync custom year input with current years
                return current_years, start_q, end_q, *button_classes, new_is_open, current_years

            if is_custom_open:
                button_classes[3] = "py-0 btn-custom active"

                if triggered_id == "custom-year-input" and custom_year:
                    try:
                        years = int(custom_year)
                        start_q, end_q = self._calculate_range(years, end_quarter=current_end_quarter)

                        return years, start_q, end_q, *button_classes, True, years
                    except (ValueError, TypeError):
                        logger.error(f"Invalid custom year input: {custom_year}")

                elif triggered_id in ["start-quarter", "end-quarter"]:
                    try:
                        start_year = int(start_q.split('Q')[0])
                        end_year = int(end_q.split('Q')[0])
                        start_q_num = int(start_q.split('Q')[1])
                        end_q_num = int(end_q.split('Q')[1])

                        years = end_year - start_year
                        if end_q_num < start_q_num:
                            years -= 1
                        years = max(years, 0)

                        logger.info(f"Quarters changed, calculated years: {years}")

                        return years, start_q, end_q, *button_classes, True, years
                    except (ValueError, IndexError):
                        logger.error("Error calculating years from quarters")

            return current_years, start_q, end_q, *button_classes, is_custom_open, custom_year or current_years

        '''@app.callback(
            Output("custom-range-collapse", "is_open"),
            [Input("btn-custom", "n_clicks")],
            [State("custom-range-collapse", "is_open")]
        )
        def toggle_custom_range(n_clicks, is_open):
            if n_clicks:
                return not is_open
            return is_open '''



        @app.callback(
            [Output('period-type', 'data'),
             Output('quarter-value-output', 'data'),
             Output({"type": "sub-btn", "index": ALL}, "className")],
            [Input("end-quarter", "value"),
             Input('date-type-state', 'data')],
            [State({"type": "sub-btn", "index": ALL}, "id")]
        )
        def update_period_config(end_q, date_type_state, sub_btn_ids):
            """Update period type, quarter value and sub-button styling"""

            ctx = dash.callback_contex
            logger.info(f"Updating period config for state: {date_type_state}")
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.info(f"triggered_id: {triggered_id}")

            main = date_type_state.get('main')
            sub = date_type_state.get('sub')

            # Initialize all sub-buttons as inactive
            sub_classes = ["py-0 ms-1 btn-secondary-custom"] * len(sub_btn_ids)

            if triggered_id == "end-quarter" and main == 'ytd':
                try:
                    quarter_num = int(end_q.split('Q')[1])
                    quarter_to_sub = {
                        1: '3m',
                        2: '1h',
                        3: '9m',
                        4: 'fy'
                    }
                    new_sub = quarter_to_sub.get(quarter_num)

                    # Update sub-button styles
                    for i, btn_id in enumerate(sub_btn_ids):
                        if btn_id['index'] == new_sub:
                            sub_classes[i] = "py-0 ms-1 btn-secondary-custom active"

                    # Update state with new sub value
                    date_type_state['sub'] = new_sub

                    return 'same_q_last_year_ytd', quarter_num, sub_classes

                except (ValueError, IndexError):
                    logger.error("Error calculating quarter value from end quarter")

            # Set active sub-button if any
            if sub:
                for i, btn_id in enumerate(sub_btn_ids):
                    if btn_id['index'] == sub:
                        sub_classes[i] = "py-0 ms-1 btn-secondary-custom active"

            # Period type mapping
            if main == 'ytd':
                period_type = 'same_q_last_year_ytd'
                quarter_map = {'3m': 1, '1h': 2, '9m': 3, 'fy': 4}
                quarter_value = quarter_map.get(sub, 2)
            elif main == 'yoy':
                if sub == 'q':
                    period_type = 'same_q_last_year'
                    quarter_value = 1
                elif sub == 'y':
                    period_type = 'same_q_last_year_mat'
                    quarter_value = 4
                else:
                    period_type = 'same_q_last_year'
                    quarter_value = 1
            elif main == 'qoq':
                period_type = 'previous_quarter'
                quarter_value = 4
            elif main == 'mat':
                period_type = 'previous_q_mat'
                quarter_value = 4
            elif main == 'cum':
                period_type = 'cumulative_sum'
                quarter_value = 4
            else:
                period_type = DEFAULT_AGGREGATION_TYPE
                quarter_value = DEFAULT_Q_VALUE

            logger.info(f"Period type set to: {period_type}, Quarter value: {quarter_value}")
            return period_type, quarter_value, sub_classes









        # Debug callback to display current state
        @app.callback(
            Output('debug-output', 'children'),
            [Input('date-type-state', 'data'),
             Input('period-type', 'data'),
             Input('quarter-value-output', 'data'),
             Input('number-of-years-to-show', 'data')]
        )
        def update_debug_output(date_type, period_type, quarter_value, years):
            return f"""
Current State:
-------------
Date Type: {json.dumps(date_type, indent=2)}
Period Type: {period_type}
Quarter Value: {quarter_value}
Years to Show: {years}
"""










# Sample quarters for testing
test_quarters = [
    '2021Q1', '2021Q2', '2021Q3', '2021Q4',
    '2022Q1', '2022Q2', '2022Q3', '2022Q4',
    '2023Q1', '2023Q2', '2023Q3', '2023Q4',
    '2024Q1', '2024Q2'
]

if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    date_filter = DateRangeFilter(available_quarters=test_quarters)
    app.layout = date_filter.create_layout()
    date_filter.setup_callbacks(app)
    logger.info("Starting server...")
    app.run_server(debug=True)
