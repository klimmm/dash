import dash
import dash_bootstrap_components as dbc
import logging
import os
import pandas as pd
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from flask import Flask
from functools import lru_cache
from pandas.tseries.offsets import DateOffset
from typing import Dict, List, Tuple, Any
from application.app_layout import create_app_layout, setup_sidebar_callbacks
from application.app_layout_callbacks import setup_debug_callbacks, setup_resize_observer_callback
from application.market_callbacks import setup_market_analysis_callbacks
from application.callbacks.filter_update_callbacks import setup_filter_update_callbacks
from application.callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from application.callbacks.period_filter import setup_period_type_callbacks
from application.components.insurance_lines_tree import insurance_lines_tree
from charting.chart import create_chart
from config.default_values import DEFAULT_REPORTING_FORM
from config.logging_config import memory_monitor, setup_logging, get_logger, track_callback, track_callback_end
from config.main_config import APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158
from data_process.calculate_metrics import get_required_metrics
from data_process.data_utils import create_year_quarter_options, load_and_preprocess_data, get_insurer_options, save_df_to_csv
from data_process.process_filters import filter_by_date_range_and_period_type, process_insurers_data, add_market_share_rows, add_growth_rows
from data_process.table_data import get_data_table
from data_process.calculate_metrics import calculate_metrics


app = dash.Dash(
    __name__,
    url_base_pathname="/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None
)
server = app.server  # Get the Flask server from Dash instead

app.title = APP_TITLE
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" type="text/css" href="/assets/styles/main.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

logger = get_logger(__name__)
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)
logger.info("Starting the Insurance Data Analysis Dashboard")

try:
    # Load both datasets
    insurance_df_162 = load_and_preprocess_data(DATA_FILE_162)
    insurance_df_158 = load_and_preprocess_data(DATA_FILE_158)

    # Create separate quarter options for both forms
    quarter_options_162 = create_year_quarter_options(insurance_df_162)
    quarter_options_158 = create_year_quarter_options(insurance_df_158)

    # Create separate insurer options for both forms
    insurer_options_162 = get_insurer_options(insurance_df_162, '0420162')
    insurer_options_158 = get_insurer_options(insurance_df_158, '0420158')

    # Set initial options based on default reporting form
    initial_quarter_options = quarter_options_162 if DEFAULT_REPORTING_FORM == '0420162' else quarter_options_158
    initial_insurer_options = insurer_options_162 if DEFAULT_REPORTING_FORM == '0420162' else insurer_options_158

    logger.debug(f"initial_insurer_options: {initial_insurer_options}")
    logger.debug(f"initial_quarter_options: {initial_quarter_options}")

except Exception as e:
    logger.error(f"Initialization failed: {str(e)}")
    raise

logger.info(f" year_quarter_unique {insurance_df_162['year_quarter'].unique()}")
logger.debug(f"initial_insurer_options{initial_insurer_options}")

layout = create_app_layout(initial_quarter_options, initial_insurer_options)
app.layout = layout


@lru_cache(maxsize=512)
def get_cached_grouped_df(
    reporting_form: str,
    period_type: str,
    end_quarter: str,
    line_type_tuple: tuple,
    selected_lines_tuple: tuple
) -> pd.DataFrame:

    df = insurance_df_162 if reporting_form == '0420162' else insurance_df_158

    # Apply quarter filtering
    end_quarter_ts = pd.Period(end_quarter, freq='Q').to_timestamp(how='end')
    start_quarter_str = '2019Q1' if reporting_form == '0420162' else '2022Q1'
    start_quarter = pd.Period(start_quarter_str, freq='Q').to_timestamp()
    if period_type == 'ytd':
        start_quarter_interim = start_quarter.replace(month=1)
    elif period_type in ['mat', 'yoy_y']:
        start_quarter_interim = start_quarter - DateOffset(months=9)
    else:
        start_quarter_interim = start_quarter

    # Create masks for filtering
    mask = (df['year_quarter'] >= start_quarter_interim) & (df['year_quarter'] <= end_quarter_ts)
    # Apply line_type filtering if provided
    if line_type_tuple:
        mask &= df['line_type'].isin(line_type_tuple)

    filtered_df = df.loc[mask].copy()

    # Determine group columns (exclude 'line_type' and 'value')
    group_cols = [col for col in filtered_df.columns if col not in ['line_type', 'value']]

    # Perform grouping and aggregation
    grouped_df = filtered_df.groupby(group_cols, observed=True)['value'].sum().reset_index()

    # Apply selected_lines filtering if provided
    if selected_lines_tuple:
        mask = grouped_df['linemain'].isin(selected_lines_tuple)
        filtered_grouped_df = grouped_df.loc[mask].copy()
    else:
        filtered_grouped_df = grouped_df.copy()

    return filtered_grouped_df

# Setup basic callbacks
setup_period_type_callbacks(app)
setup_debug_callbacks(app)
setup_insurance_lines_callbacks(app, insurance_lines_tree)
setup_filter_update_callbacks(app, quarter_options_162, quarter_options_158)
setup_sidebar_callbacks(app)
setup_market_analysis_callbacks(app)
setup_resize_observer_callback(app)
logger.debug("Dashboard layout created")

@app.callback(
    [Output('processed-data-store', 'data'),
     Output('number-of-periods-data-table', 'value'),
     Output('number-of-insurers', 'value')],
    [Input('filter-state-store', 'data'),
     Input('selected-insurers', 'value'),
     Input('period-type', 'data'),
     Input('end-quarter', 'value'),
     Input('number-of-periods-data-table', 'value'),
     Input('number-of-insurers', 'value'),
     Input('insurer-line-switch', 'value'),
    ],
    [State('show-data-table', 'data')],
    prevent_initial_call=True
)

def process_data(
    filter_state: Dict[str, Any],
    selected_insurers: List[str],
    period_type: str,
    end_quarter: str,
    num_periods_selected: int,
    number_of_insurers: int,
    insurer_line_switch: str,
    show_data_table: bool,
    line_type: List[str] = None
) -> Tuple:
    """Process data based on filter state."""
    ctx = dash.callback_context
    start_time = track_callback('application.main', 'process_data', dash.callback_context)
    if not filter_state:
        track_callback_end('application.main', 'process_data', start_time, message_no_update="not filter_state")
        raise PreventUpdate
    memory_monitor.log_memory("before_process_data", logger)

    try:
        logger.debug(f"Process data - processing with parameters: {filter_state}, period_type: {period_type}, end_quarter: {end_quarter}, num_periods_selected: {num_periods_selected}, number_of_insurers: {number_of_insurers} ")
        logger.debug(f"insurer_line_switch: {insurer_line_switch}")
        logger.debug(f"processdata selected_lines: {filter_state['selected_lines']}")
        
        reporting_form = filter_state['reporting_form']
        selected_lines = filter_state['selected_lines']
        selected_metrics = filter_state['selected_metrics']
        premium_loss_selection = filter_state['premium_loss_checklist']
        line_type_tuple = tuple(sorted(set(line_type))) if line_type else ()
        selected_lines_tuple = tuple(sorted(set(selected_lines))) if selected_lines else ()
        grouped_df = get_cached_grouped_df(reporting_form, period_type,end_quarter, line_type_tuple, selected_lines_tuple)

        required_metrics_set = get_required_metrics(selected_metrics, premium_loss_selection)
        mask = grouped_df['metric'].isin(required_metrics_set)
        df = grouped_df.loc[mask].copy()

        df = filter_by_date_range_and_period_type(df, period_type=period_type)

        number_of_unique_periods = len(df['year_quarter'].unique())
        periods_to_keep = sorted(df['year_quarter'].unique(), reverse=True)[:min(num_periods_selected, number_of_unique_periods) + 1]
        df = df[df['year_quarter'].isin(periods_to_keep)]
        save_df_to_csv(df, "df_x.csv")
        
        end_quarter_df = df[df['year_quarter'] == sorted(df['year_quarter'].unique())[-1]]
        number_of_insurer_options = len(end_quarter_df['insurer'].unique())          
        top_n_list=[5, 10, 20]
        df, prev_ranks = process_insurers_data(df, selected_insurers, top_n_list, show_data_table, selected_metrics, min(number_of_insurers, number_of_insurer_options))

        df = calculate_metrics(df, selected_metrics, premium_loss_selection)

        df = df[df['metric'].isin(selected_metrics)]

        df = add_market_share_rows(df, selected_insurers, selected_metrics, show_data_table)

        df = add_growth_rows(df, selected_insurers, show_data_table, num_periods_selected, period_type)

        save_df_to_csv(df, "process_dataframe.csv")

        df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')
        output = ({'df': df.to_dict('records'), 'prev_ranks': prev_ranks}, min(num_periods_selected, number_of_unique_periods), min(number_of_insurers, number_of_insurer_options))
        # logger.debug(f"metrics unique: {df['metric'].unique() }")

        return output

    except Exception as e:
        logger.error(f"Error in process_data: {str(e)}", exc_info=True)
        track_callback_end('application.main', 'process_data', start_time, error=e)
        raise

    finally:
        track_callback_end('application.main', 'process_data', start_time, result=output)

@app.callback(
    [Output('data-table', 'children'),
     Output('table-title', 'children'),
     Output('table-subtitle', 'children'),
     Output('table-title-chart', 'children'),
     Output('table-subtitle-chart', 'children'),
     Output('graph', 'figure')],
    [Input('processed-data-store', 'data'),
     Input('toggle-selected-market-share', 'value'),
     Input('toggle-selected-qtoq', 'value')],
    [State('filter-state-store', 'data'),
     State('period-type', 'data'),
     State('end-quarter', 'value'),
     State('number-of-insurers', 'value')],
    prevent_initial_call=True
)
# @monitor_memory
def process_ui(
    processed_data: Dict,
    toggle_selected_market_share: bool,
    toggle_selected_qtoq: bool,
    filter_state: Dict,
    period_type: str,
    end_quarter: str,
    number_of_insurers: int
) -> List:
    """Update table based on processed data."""
    memory_monitor.log_memory("before_process_ui", logger)
    start_time = track_callback('application.main', 'process_ui', dash.callback_context)

    try:
        df = pd.DataFrame.from_records(processed_data['df'])
        df['year_quarter'] = pd.to_datetime(df['year_quarter'])
        table_data = get_data_table(
            df=df,
            table_selected_metric=filter_state['selected_metrics'],
            selected_linemains=filter_state['selected_lines'],
            period_type=period_type,
            number_of_insurers=number_of_insurers,
            toggle_selected_market_share=toggle_selected_market_share,
            toggle_selected_qtoq=toggle_selected_qtoq,
            prev_ranks=processed_data['prev_ranks']
        )

        logger.debug(f"toggle_selected_market_share {toggle_selected_market_share}")
        unique_insurers = df['insurer'].unique().tolist()

        # Get main insurer (first one)
        main_insurer = unique_insurers[:1][0]  # or simply unique_insurers[0]
        
        # Get next 4 insurers (excluding main insurer)
        compare_insurers = unique_insurers[1:5]

        # Filter dataframe to keep only these insurers
        df = df[df['insurer'].isin([main_insurer] + compare_insurers)]

        #logger.debug(f"compare_insurers {compare_insurers}")
        logger.debug(f"primary_y_metric {filter_state['primary_y_metric']}")
        logger.debug(f"secondary_y_metric {filter_state['secondary_y_metric']}")
        df = df[df['metric'] == filter_state['primary_y_metric'][0]]
        chart_figure, _ = create_chart(
            # Data parameters
            chart_data=df,
            # premium_loss_selection=filter_state['premium_loss_checklist'],
            selected_linemains=filter_state['selected_lines'],
            main_insurer=main_insurer,
            compare_insurers=compare_insurers,
            # Metric parameters
            primary_y_metric=filter_state['primary_y_metric'],
            secondary_y_metric=filter_state['secondary_y_metric'],

            # Time period parameters
            period_type=period_type,
            start_quarter='2019Q1' if filter_state['reporting_form'] == '0420162' else '2022Q1',
            end_quarter=end_quarter
        )
        # logger.debug(f"table_data {table_data}")
        # logger.debug(f"chart_figure {chart_figure}")
        # logger.debug(f"table_data {table_data}")
        # logger.debug("Returning table data")
        
        return table_data[0], table_data[1], table_data[2], table_data[1], table_data[2], chart_figure

    except Exception as e:
        logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
        raise

    finally:
        track_callback_end('application.main', 'process_ui', start_time)


if __name__ == '__main__':
    try:
        print("Starting application initialization...")
        port = int(os.environ.get("PORT", PORT))


        print("Starting server...")
        app.run_server(debug=DEBUG_MODE, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error during startup: {e}")
        raise