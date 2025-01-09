import logging
import pandas as pd
import dash_bootstrap_components as dbc
import dash
import os 
from dash import Input, Output, State
from typing import Dict, List, Tuple, Any
from dash.exceptions import PreventUpdate
from pathlib import Path
from app.components.insurance_lines_tree import insurance_lines_tree
from app.callbacks.app_layout_callbacks import setup_tab_state_callbacks, setup_sidebar_callbacks
from app.callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from app.callbacks.filter_update_callbacks import setup_filter_update_callbacks
from config.main_config import APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158
from config.logging_config import (
        monitor_memory, memory_monitor,
        setup_logging, DebugLevels, get_logger,
        track_callback, track_callback_end
)
from data_process.data_utils import create_year_quarter_options, load_and_preprocess_data
from data_process.process_filters import MetricsProcessor
from data_process.table_data import get_data_table
from app.app_layout import create_app_layout
from app.callbacks.period_filter import setup_period_type_callbacks
logger = get_logger(__name__)
from config.default_values import DEFAULT_REPORTING_FORM

# Initialize the Dash app
app = dash.Dash(
    __name__,
    assets_folder=Path(__file__).parent / "assets",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
app.title = APP_TITLE
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
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

# Initialize the Flask server
server = app.server

# Initialize logging and debug level
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)
logger.info("Starting the Insurance Data Analysis Dashboard")

try:
    insurance_df_162 = load_and_preprocess_data(DATA_FILE_162)
    insurance_df_158 = load_and_preprocess_data(DATA_FILE_158)
except Exception as e:
    logger.error(f"Failed to load data: {str(e)}")
    raise

# Create application and initialize filters
quarter_options_162 = create_year_quarter_options(insurance_df_162)
quarter_options_158 = create_year_quarter_options(insurance_df_158)
initial_quarter_options = quarter_options_162 if DEFAULT_REPORTING_FORM == '0420162' else quarter_options_158

layout = create_app_layout(initial_quarter_options)
app.layout = layout

# Setup basic callbacks
setup_period_type_callbacks(app)
setup_tab_state_callbacks(app)
setup_insurance_lines_callbacks(app, insurance_lines_tree)
setup_filter_update_callbacks(app, quarter_options_162, quarter_options_158)
setup_sidebar_callbacks(app)

logger.debug("Dashboard layout created")

@app.callback(
    [Output('processed-data-store', 'data'),
     Output('number-of-periods-data-table', 'value'),
     Output('number-of-insurers', 'value')],
    [Input('filter-state-store', 'data'),
     Input('period-type', 'data'),
     Input('end-quarter', 'value'),
     Input('number-of-periods-data-table', 'value'),
     Input('number-of-insurers', 'value')],
    [State('show-data-table', 'data')],
    prevent_initial_call=True
)
@monitor_memory
def process_data(
    filter_state: Dict[str, Any],
    period_type: str,
    end_quarter: str,
    num_periods_table: int,
    number_of_insurers: int,
    show_data_table: bool
) -> Tuple:
    """Process data based on filter state."""
    ctx = dash.callback_context
    start_time = track_callback('app.main', 'process_data', dash.callback_context)
    if not filter_state:
        track_callback_end('app.main', 'process_data', start_time, message_no_update="not filter_state")
        raise PreventUpdate
    memory_monitor.log_memory("before_process_data", logger)
    try:
        processor = MetricsProcessor()
        logger.debug(f"Process data - processing with parameters: {filter_state}, period_type: {period_type}, end_quarter: {end_quarter}, num_periods_table: {num_periods_table}, number_of_insurers: {number_of_insurers} ")
        logger.debug(f"reporting_form: {filter_state['reporting_form']}")

        df, insurer_options, compare_options, selected_insurers, prev_ranks, number_of_periods_options, number_of_insurer_options = (
            processor.process_general_filters(
                df=insurance_df_162 if filter_state['reporting_form'] == '0420162' else insurance_df_158,
                show_data_table=show_data_table,
                premium_loss_selection=filter_state['premium_loss_checklist'],
                selected_metrics=filter_state['selected_metrics'] or ['direct_premiums'],
                selected_linemains=filter_state['selected_lines'],
                period_type=period_type,
                start_quarter='2018Q1' if filter_state['reporting_form'] == '0420162' else '2022Q1',
                end_quarter=end_quarter,
                num_periods=num_periods_table,
                chart_columns=[],
                selected_insurers=None,
                number_of_insurers=number_of_insurers,
                top_n_list=[5, 10, 20]
            )
        )

        df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')
        output = ({'df': df.to_dict('records'), 'prev_ranks': prev_ranks}, min(num_periods_table, number_of_periods_options), min(number_of_insurers, number_of_insurer_options))
        logger.debug(f"metrics unique: {df['metric'].unique() }")

        return output

    except Exception as e:
        logger.error(f"Error in process_data: {str(e)}", exc_info=True)
        track_callback_end('app.main', 'process_data', start_time, error=e)
        raise

    finally:
        track_callback_end('app.main', 'process_data', start_time, result=output)

@app.callback(
    [Output('data-table', 'children'),
     Output('table-title', 'children'),
     Output('table-subtitle', 'children')],
    [Input('processed-data-store', 'data'),
     Input('toggle-selected-market-share', 'value'),
     Input('toggle-selected-qtoq', 'value')],
    [State('filter-state-store', 'data'),
     State('period-type', 'data'),
     State('end-quarter', 'value'),
     State('number-of-insurers', 'value')],
    prevent_initial_call=True
)
@monitor_memory
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
    start_time = track_callback('app.main', 'process_ui', dash.callback_context)

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
        logger.debug(f"table_data {table_data}")
        logger.debug("Returning table data")
        return table_data[0], table_data[1], table_data[2]

    except Exception as e:
        logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
        raise

    finally:
        track_callback_end('app.main', 'process_ui', start_time)

if __name__ == '__main__':
    try:
        print("Starting application initialization...")
        port = int(os.environ.get("PORT", PORT))
        print("Starting server...")
        app.run_server(debug=DEBUG_MODE, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error during startup: {e}")
        raise