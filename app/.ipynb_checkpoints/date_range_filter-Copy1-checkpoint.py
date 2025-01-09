from dash import html, dcc, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import dash
import logging
from default_values import DEFAULT_PERIOD_TYPE, DEFAULT_Q_VALUE, DEFAULT_AGGREGATION_TYPE
from constants.filter_options import *
from default_values import *
from datetime import datetime
# Set up logging
from logging_config import get_logger, custom_profile, track_callback, track_callback_end
logger = logging.getLogger(__name__)
import json
from dash.exceptions import PreventUpdate




def create_date_type_selector():
    return dbc.Row([
        html.Div([
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button(
                        "YTD",
                        id={"type": "main-btn", "index": "ytd"},
                        size="sm",
                        className="py-0 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "YoY",
                        id={"type": "main-btn", "index": "yoy"},
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "QoQ",
                        id={"type": "main-btn", "index": "qoq"},
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "MAT",
                        id={"type": "main-btn", "index": "mat"},
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "Cum",
                        id={"type": "main-btn", "index": "cum"},
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                ]),
                dbc.Collapse(
                    dbc.ButtonGroup(id="additional-options"),
                    id="collapse",
                    is_open=True,
                    className="d-inline-block ms-1"
                )
            ], className="d-flex align-items-center"),
            dcc.Store(id='date-type-state', data=DEFAULT_PERIOD_TYPE),
            html.Div(id="date-type-output", style={'display': 'inline-block', 'marginRight': '10px'}),
            dcc.Store(id='period-type', data=DEFAULT_AGGREGATION_TYPE),
            dcc.Store(id='quarter-value-output', data=DEFAULT_Q_VALUE)

        ], className="p-0")
    ], align="center")


def generate_outputs(state):
    if state['main'] in ["ytd", "yoy"]:
        is_open = True
        additional_options = [
            dbc.Button(
                "3M",
                id={"type": "sub-btn", "index": "3m"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
            dbc.Button(
                "1H",
                id={"type": "sub-btn", "index": "1h"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
            dbc.Button(
                "9M",
                id={"type": "sub-btn", "index": "9m"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
            dbc.Button(
                "FY",
                id={"type": "sub-btn", "index": "fy"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
        ] if state['main'] == "ytd" else [
            dbc.Button(
                "Q",
                id={"type": "sub-btn", "index": "q"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
            dbc.Button(
                "Y",
                id={"type": "sub-btn", "index": "y"},
                size="sm",
                className="py-0 ms-1 btn-secondary-custom",
                style={"height": "36px"}
            ),
        ]

        # Set active class for selected sub-button
        if state['sub']:
            for btn in additional_options:
                if btn.id['index'] == state['sub']:
                    btn.className = btn.className + " active"
    else:
        is_open = False
        additional_options = []

    # Set button classes instead of colors
    main_classes = [
        f"py-0 btn-custom{' active' if i == state['main'] else ''}"
        for i in ["ytd", "yoy", "qoq", "mat", "cum"]
    ]

    output_text = ""
    period_type, quarter_value = get_period_type_and_quarter(state['main'], state['sub'])

    return state, is_open, additional_options, main_classes, output_text, period_type, quarter_value


def get_period_type_and_quarter(main, sub):
    if main == 'ytd':
        period_type = 'same_q_last_year_ytd'
        quarter_value = {'3m': 1, '1h': 2, '9m': 3, 'fy': 4}.get(sub, 2)  # Default to 2 if sub is None
    elif main == 'yoy':
        if sub == 'q':
            period_type = 'same_q_last_year'
            quarter_value = 1
        elif sub == 'y':
            period_type = 'same_q_last_year_mat'
            quarter_value = 4
        else:
            period_type =  'same_q_last_year'  # Default if sub is None
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
        period_type = 'previous_quarter'  # Defaul
        quarter_value = 4  # Defaul

    return period_type, quarter_value



def create_date_range_selector(year_quarter_options, DEFAULT_START_QUARTER, DEFAULT_END_QUARTER, DEFAULT_NUMBER_OF_PERIODS):
    return dbc.Row([
        dbc.Col([
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button(
                        "1Y",
                        id="btn-1y",
                        n_clicks=0,
                        size="sm",
                        className="py-0 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "2Y",
                        id="btn-2y",
                        n_clicks=0,
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "5Y",
                        id="btn-5y",
                        n_clicks=0,
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                    dbc.Button(
                        "Custom",
                        id="btn-custom",
                        n_clicks=0,
                        size="sm",
                        className="py-0 ms-1 btn-custom",
                        style={"height": "36px"}
                    ),
                ]),
                dbc.Collapse([
                    html.Div([
                        html.Div([
                            dbc.Input(
                                id="custom-year-input",
                                type="number",
                                style={
                                    "width": 75,
                                    "height": "36px"
                                },
                                className="filter-dropdown py-0"
                            ),
                        ], style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "marginRight": "4px"
                        }),

                        html.Div([
                            dcc.Dropdown(
                                id='start-quarter',
                                options=year_quarter_options,
                                value=DEFAULT_START_QUARTER,
                                clearable=False,
                                className="filter-dropdown",
                                style={
                                    "width": 100,
                                    "height": "36px"
                                }
                            ),
                        ], style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "marginRight": "4px"
                        }),

                        html.Div([
                            dcc.Dropdown(
                                id='end-quarter',
                                options=year_quarter_options,
                                value=DEFAULT_END_QUARTER,
                                clearable=False,
                                className="filter-dropdown",
                                style={
                                    "width": 100,
                                    "height": "36px"
                                }
                            ),
                        ], style={
                            "display": "inline-block",
                            "verticalAlign": "middle",
                            "marginRight": "4px"
                        }),

                        html.Div([
                            dbc.Button(
                                "Go",
                                id="btn-custom-year",
                                className="py-0 btn-custom",
                                style={"height": "36px"}
                            ),
                        ], style={
                            "display": "inline-block",
                            "verticalAlign": "middle"
                        }),
                    ], className="d-flex align-items-center")
                ],
                id="custom-range-collapse",
                is_open=False,
                className="horizontal-collapse-container ms-1"),
                dcc.Store(id='hidden-periods', data=0),
                # Store the options in a hidden div
                dcc.Store(id='quarter-options-store', data=year_quarter_options)
            ], className="d-flex align-items-center")
        ], width=12, className="p-0"),

        # Hidden elements
        dbc.Col([
            html.Div([
                dcc.Dropdown(
                    id='number-of-years-to-show',
                    options=[{'label': str(i), 'value': i} for i in range(1, 27)],
                    value=DEFAULT_NUMBER_OF_PERIODS,
                    clearable=False,
                    style={'display': 'none', 'width': '100px', "height": "36px"}
                ),
            html.Div("\u00A0", style={'display': 'inline-block', 'marginRight': '10px'}),
            ], className="d-flex align-items-center justify-content-end")
        ], width=12, className="d-flex align-items-center")
    ], align="center")





def load_initial_state() -> Tuple[Dict[str, Any], bool]:
    """
    Load the initial state for date type and quarter selection.

    Returns:
        Tuple containing the generated outputs and a boolean indicating if PreventUpdate should be raised.
    """
    initial_state = DEFAULT_PERIOD_TYPE
    return generate_outputs(initial_state)


def setup_layout_callbacks(app: dash.Dash) -> None:
    """
    Setup callbacks related to layout interactions.

    Args:
        app (dash.Dash): The Dash application instance.
    """
    @app.callback(
        [
            Output("number-of-years-to-show", "value"),
            Output("btn-1y", "className"),
            Output("btn-2y", "className"),
            Output("btn-5y", "className"),
            Output("btn-custom", "className"),
            Output("custom-range-collapse", "is_open"),
            Output("start-quarter", "value"),
            Output("end-quarter", "value"),
            Output("custom-year-input", "value"),
        ],
        [
            Input("btn-1y", "n_clicks"),
            Input("btn-2y", "n_clicks"),
            Input("btn-5y", "n_clicks"),
            Input("btn-custom", "n_clicks"),
            Input("btn-custom-year", "n_clicks")
        ],
        [
            State("custom-year-input", "value"),
            State("number-of-years-to-show", "value"),
            State("custom-range-collapse", "is_open"),
            State("start-quarter", "value"),
            State("end-quarter", "value"),
            State("btn-1y", "className"),
            State("btn-2y", "className"),
            State("btn-5y", "className"),
            State("btn-custom", "className"),
            State("quarter-options-store", "data")
        ]
    )
    def update_periods_classes_and_collapse(
        btn1: int, btn2: int, btn5: int, btn_custom: int, btn_custom_year: int,
        custom_year: Any, current_periods: int, is_open: bool,
        start_quarter: str, end_quarter: str, class_1y: str,
        class_2y: str, class_5y: str, class_custom: str,
        year_quarter_options: List[Dict[str, str]]
    ) -> List[Any]:
        """
        Update the number of years to show, button classes, and collapse state based on user interaction.

        Args:
            btn1 (int): Click count for 1-year button.
            btn2 (int): Click count for 2-year button.
            btn5 (int): Click count for 5-year button.
            btn_custom (int): Click count for custom button.
            btn_custom_year (int): Click count for custom year button.
            custom_year (Any): Current value of custom year input.
            current_periods (int): Current number of periods selected.
            is_open (bool): Current state of the custom range collapse.
            start_quarter (str): Current start quarter.
            end_quarter (str): Current end quarter.
            class_1y (str): Current class for 1-year button.
            class_2y (str): Current class for 2-year button.
            class_5y (str): Current class for 5-year button.
            class_custom (str): Current class for custom button.
            year_quarter_options (List[Dict[str, str]]): Available quarter options.

        Returns:
            List[Any]: Updated values for outputs.
        """
        ctx = dash.callback_contex
        if not ctx.triggered:
            initial_classes = ["py-0 btn-custom"] * 4
            initial_classes[DEFAULT_BUTTON_INDEX] = "py-0 btn-custom active"
            return DEFAULT_NUMBER_OF_PERIODS, *initial_classes, False, start_quarter, end_quarter, None
        start_time = track_callback('setup_layout_callbacks', 'update_periods_classes_and_collapse', ctx)
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        logger.debug(f"triggered_id def update_periods_classes_and_collapse {button_id}")

        periods = current_periods
        classes = ["py-0 btn-custom"] * 4

        available_quarters = sorted([opt['value'] for opt in year_quarter_options])

        def calculate_quarters(num_years: int) -> Tuple[str, str]:
            current_date = datetime.now()
            current_year = current_date.year
            current_quarter = (current_date.month - 1) // 3 + 1
            target_end = f"{current_year}Q{current_quarter}"

            # Find the actual end quarter
            end_quarter = next((q for q in reversed(available_quarters) if q <= target_end), available_quarters[-1])
            end_year = int(end_quarter.split('Q')[0])
            target_start_year = end_year - num_years
            target_start = f"{target_start_year}Q{end_quarter[-1]}"

            # Find the actual start quarter
            start_quarter = next((q for q in available_quarters if q >= target_start), available_quarters[0])
            return start_quarter, end_quarter

        if button_id == "btn-custom":
            is_open = not is_open
            classes = [class_1y, class_2y, class_5y, class_custom]
            return periods, *classes, is_open, start_quarter, end_quarter, custom_year

        elif button_id == "btn-1y":
            periods = 1
            classes[0] = "py-0 btn-custom active"
            is_open = False
            start_quarter, end_quarter = calculate_quarters(1)

        elif button_id == "btn-2y":
            periods = 2
            classes[1] = "py-0 btn-custom active"
            is_open = False
            start_quarter, end_quarter = calculate_quarters(2)

        elif button_id == "btn-5y":
            periods = 5
            classes[2] = "py-0 btn-custom active"
            is_open = False
            start_quarter, end_quarter = calculate_quarters(5)

        elif button_id == "btn-custom-year" and custom_year:
            try:
                periods = int(custom_year)
            except ValueError:
                periods = current_periods  # Retain current periods if invalid inpu
                logger.debug(f"Invalid custom year input: {custom_year}")
            classes[3] = "py-0 btn-custom active"
            start_quarter, end_quarter = calculate_quarters(periods)

        else:
            classes[3] = "py-0 btn-custom active" if is_open else "py-0 btn-custom"


        result = periods, *classes, is_open, start_quarter, end_quarter, custom_year

        track_callback_end('setup_layout_callbacks', 'update_periods_classes_and_collapse', start_time, result=result)


        return resul

    @app.callback(
        Output({"type": "sub-btn", "index": MATCH}, "className"),
        Input({"type": "sub-btn", "index": MATCH}, "n_clicks"),
        State('date-type-state', 'data'),
    )
    def update_sub_button_class(n_clicks: int, current_state: Dict[str, Any]) -> str:
        """
        Update the class name of a sub-button based on its active state.

        Args:
            n_clicks (int): Number of clicks on the sub-button.
            current_state (Dict[str, Any]): Current state data.

        Returns:
            str: Updated class name for the sub-button.
        """
        if not n_clicks:
            raise PreventUpdate

        ctx = dash.callback_contex
        start_time = track_callback('setup_layout_callbacks', 'update_sub_button_class', ctx)
        try:
            # Safely parse the triggered ID
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"triggered_id def update_sub_button_class {triggered_id}")

            button_info = json.loads(triggered_id)
            button_index = button_info["index"]
        except (json.JSONDecodeError, KeyError) as e:

            logger.error(f"Error parsing triggered_id: {ctx}, Error: {e}")
            raise PreventUpdate

        result = "py-0 ms-1 btn-secondary-custom active" if button_index == current_state.get('sub') else "py-0 ms-1 btn-secondary-custom"

        track_callback_end('setup_layout_callbacks', 'update_sub_button_class', start_time, result=result)


        return resul

    @app.callback(
        Output('date-type-state', 'data'),
        Output("collapse", "is_open"),
        Output("additional-options", "children"),
        Output({"type": "main-btn", "index": ALL}, "color"),
        Output("date-type-output", "children"),
        Output('period-type', 'data'),
        Output('quarter-value-output', 'data'),
        Input({"type": "main-btn", "index": ALL}, "n_clicks"),
        Input({"type": "sub-btn", "index": ALL}, "n_clicks"),
        State('date-type-state', 'data'),
    )
    def update_date_type_state(
        main_clicks: List[int], sub_clicks: List[int], current_state: Dict[str, Any]
    ) -> List[Any]:
        """
        Update the date type state based on main and sub button clicks.

        Args:
            main_clicks (List[int]): Click counts for main buttons.
            sub_clicks (List[int]): Click counts for sub buttons.
            current_state (Dict[str, Any]): Current date type state.

        Returns:
            List[Any]: Updated state data and UI components.
        """
        ctx = dash.callback_contex
        start_time = track_callback('setup_layout_callbacks', 'update_date_type_state', ctx)
        if not ctx.triggered:
            # Initial load
            logger.debug("Initial state loaded")
            return load_initial_state()

        try:

            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"triggered_id def update_date_type_state {triggered_id}")
            button_info = json.loads(triggered_id)
            button_type, button_index = button_info["type"], button_info["index"]
            logger.debug(f"Button clicked: {button_type} - {button_index}")

            new_state = current_state.copy()
            if button_type == "main-btn":
                new_state['main'] = button_index
                new_state['sub'] = None
            elif button_type == "sub-btn":
                new_state['sub'] = button_index

            logger.debug(f"Current State - Main: {new_state['main'].upper()}, Sub: {new_state['sub'].upper() if new_state['sub'] else 'None'}")

            # Generate outputs based on the new state
            outputs = generate_outputs(new_state)
            track_callback_end('setup_layout_callbacks', 'update_date_type_state', start_time, result=outputs)

            return outputs

        except (json.JSONDecodeError, KeyError) as e:
            track_callback_end('setup_layout_callbacks', 'update_date_type_state', start_time, error=e)
            logger.error(f"Error parsing triggered_id: {ctx}, Error: {e}")
            raise PreventUpdate
        except Exception as e:
            track_callback_end('setup_layout_callbacks', 'update_date_type_state', start_time, error=e)
            logger.exception("Error in update_date_type_state")
            raise

    @app.callback(
        Output({"type": "sub-btn", "index": MATCH}, "color"),
        Input({"type": "sub-btn", "index": MATCH}, "n_clicks"),
        State('date-type-state', 'data'),
    )
    def update_sub_button_color(n_clicks: int, current_state: Dict[str, Any]) -> str:
        """
        Update the color of a sub-button based on its active state.

        Args:
            n_clicks (int): Number of clicks on the sub-button.
            current_state (Dict[str, Any]): Current state data.

        Returns:
            str: Updated color for the sub-button.
        """
        if not n_clicks:
            raise PreventUpdate

        ctx = dash.callback_contex
        start_time = track_callback('setup_layout_callbacks', 'update_sub_button_color', ctx)
        try:
            # Safely parse the triggered ID
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            logger.debug(f"triggered_id def update_sub_button_color {triggered_id}")


            button_info = json.loads(triggered_id)
            button_index = button_info["index"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing triggered_id: {ctx}, Error: {e}")
            raise PreventUpdate

        result = "success" if button_index == current_state.get('sub') else "primary"

        track_callback_end('setup_layout_callbacks', 'update_filter_values', start_time, result=result)


        return resul

