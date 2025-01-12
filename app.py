import logging
import pandas as pd
import dash_bootstrap_components as dbc
import dash
import os 
import gc
from dash import dcc, html

from functools import lru_cache
from pandas.tseries.offsets import DateOffset
from dash import Input, Output, State
from typing import Dict, List, Tuple, Any
from dash.exceptions import PreventUpdate
from pathlib import Path
from application.components.insurance_lines_tree import insurance_lines_tree
from application.callbacks.app_layout_callbacks import setup_tab_state_callbacks, setup_sidebar_callbacks
from application.callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from application.callbacks.filter_update_callbacks import setup_filter_update_callbacks
from config.main_config import APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158
from config.logging_config import (
        monitor_memory, memory_monitor,
        setup_logging, DebugLevels, get_logger,
        track_callback, track_callback_end
)
from charting.chart import create_chart
from data_process.data_utils import create_year_quarter_options, load_and_preprocess_data
from data_process.process_filters import MetricsProcessor
from data_process.table_data import get_data_table
from application.app_layout import create_app_layout
from application.callbacks.period_filter import setup_period_type_callbacks
logger = get_logger(__name__)
from config.default_values import DEFAULT_REPORTING_FORM
from data_process.data_utils import save_df_to_csv, get_required_metrics, map_insurer
from constants.filter_options import (
    BASE_METRICS, CALCULATED_METRICS, CALCULATED_RATIOS
)
from memory_profiler import profile
import hashlib
import time
from flask import Flask
from flask import jsonify

# Assets are in root, not in application folder
ASSETS_PATH = Path(__file__).parent / "assets"

# Create Flask app with correct static path
def create_flask_app():
    flask_app = Flask(__name__)
    flask_app.config.update(
        SEND_FILE_MAX_AGE_DEFAULT=0,
        TEMPLATES_AUTO_RELOAD=True
    )
    # Set static folder and URL path without application prefix
    flask_app.static_folder = str(ASSETS_PATH)
    flask_app.static_url_path = '/assets'
    return flask_app

server = create_flask_app()

# Initialize Dash app with correct paths
app = dash.Dash(
    __name__,
    server=server,
    assets_folder=str(ASSETS_PATH),
    url_base_pathname="/",
    assets_url_path='/assets',  # Keep this simple
    serve_locally=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None
)

app.title = APP_TITLE

# Versioning without application prefix
def get_asset_version():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

ASSET_VERSION = get_asset_version()

def custom_get_asset_url(path):
    # Remove application prefix since assets are served from root
    return f"/assets/{path}?v={ASSET_VERSION}"

app.get_asset_url = custom_get_asset_url

# Remove manual CSS injection from index_string
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
@server.route('/asset-check')
def asset_check():
    """Verify asset loading and paths"""
    main_css = Path(ASSETS_PATH) / 'styles' / 'main.css'
    
    info = {
        "assets_exists": ASSETS_PATH.exists(),
        "main_css_exists": main_css.exists(),
        "asset_files": [str(p) for p in ASSETS_PATH.rglob('*.css')],
        "asset_version": ASSET_VERSION,
        "asset_url_example": app.get_asset_url('styles/main.css')
    }
    return jsonify(info)

@server.route('/debug-info')
def debug_info():
    import os
    import json
    from flask import has_request_context, request
    
    # Get list of all CSS files
    styles_path = ASSETS_PATH / 'styles'
    css_files = []
    if styles_path.exists():
        for root, dirs, files in os.walk(styles_path):
            for file in files:
                if file.endswith('.css'):  # Only include CSS files
                    rel_path = Path(root).relative_to(ASSETS_PATH)
                    css_files.append(str(rel_path / file))
    
    # Get request info if available
    request_info = {}
    if has_request_context():
        request_info = {
            "base_url": request.base_url,
            "host_url": request.host_url,
            "path": request.path,
            "full_path": request.full_path,
            "script_root": request.script_root,
            "url_root": request.url_root,
            "headers": dict(request.headers)
        }
    
    info = {
        "environment": {
            "current_dir": os.getcwd(),
            "python_path": os.getenv('PYTHONPATH'),
            "app_root": app.config.get('APPLICATION_ROOT'),
        },
        "paths": {
            "assets_path": str(ASSETS_PATH),
            "static_folder": str(server.static_folder),
            "static_url_path": server.static_url_path,
        },
        "files": {
            "css_files": css_files,
            "main_css_path": str(ASSETS_PATH / 'styles' / 'main.css'),
            "main_css_exists": (ASSETS_PATH / 'styles' / 'main.css').exists(),
            "files_in_assets": [f for f in os.listdir(ASSETS_PATH) if os.path.isfile(ASSETS_PATH / f)] if os.path.exists(ASSETS_PATH) else [],
        },
        "configuration": {
            "asset_version": ASSET_VERSION,
            "dash_config": app.config,
            "flask_config": {k: str(v) for k, v in server.config.items() if isinstance(k, str)}
        },
        "request": request_info
    }
    
    response = app.server.make_response(json.dumps(info, indent=2))
    response.headers['Content-Type'] = 'application/json'
    return response

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


@lru_cache(maxsize=256)
def get_cached_grouped_df(
    reporting_form: str,
    start_quarter_interm: pd.Timestamp,
    end_quarter_ts: pd.Timestamp,
    line_type_tuple: tuple
) -> pd.DataFrame:
    """
    Caches the grouped DataFrame based on reporting_form, start_quarter_interm, end_quarter_ts, and line_type_tuple.

    Parameters:
    - reporting_form (str): The reporting form identifier.
    - start_quarter_interm (pd.Timestamp): The start quarter as a Timestamp.
    - end_quarter_ts (pd.Timestamp): The end quarter as a Timestamp.
    - line_type_tuple (tuple): Tuple of line types to filter. Empty tuple if no filtering.

    Returns:
    - pd.DataFrame: The grouped and filtered DataFrame.
    """
    # Select the appropriate DataFrame
    df = insurance_df_162 if reporting_form == '0420162' else insurance_df_158

    # Ensure 'year_quarter' is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
        df = df.copy()
        df['year_quarter'] = pd.to_datetime(df['year_quarter'])

    # Apply quarter filtering
    mask = (df['year_quarter'] >= start_quarter_interm) & (df['year_quarter'] <= end_quarter_ts)

    # Apply line_type filtering if provided
    if line_type_tuple:
        mask &= df['line_type'].isin(line_type_tuple)

    filtered_df = df.loc[mask].copy()

    # Determine group columns (exclude 'line_type' and 'value')
    group_cols = [col for col in filtered_df.columns if col not in ['line_type', 'value']]

    # Perform grouping and aggregation
    grouped_df = filtered_df.groupby(group_cols, observed=True)['value'].sum().reset_index()

    return grouped_df

@lru_cache(maxsize=512)
def get_cached_filtered_grouped_df(
    reporting_form: str,
    start_quarter_interm: pd.Timestamp,
    end_quarter_ts: pd.Timestamp,
    line_type_tuple: tuple,
    selected_lines_tuple: tuple
) -> pd.DataFrame:
    """
    Caches the final filtered DataFrame based on selected_lines.

    Parameters:
    - reporting_form (str): The reporting form identifier.
    - start_quarter_interm (pd.Timestamp): The start quarter as a Timestamp.
    - end_quarter_ts (pd.Timestamp): The end quarter as a Timestamp.
    - line_type_tuple (tuple): Tuple of line types to filter. Empty tuple if no filtering.
    - selected_lines_tuple (tuple): Tuple of selected lines to filter. Empty tuple if no filtering.

    Returns:
    - pd.DataFrame: The final filtered and grouped DataFrame.
    """
    # Retrieve the grouped_df from the first cache tier
    grouped_df = get_cached_grouped_df(
        reporting_form,
        start_quarter_interm,
        end_quarter_ts,
        line_type_tuple
    )

    # Apply selected_lines filtering if provided
    if selected_lines_tuple:
        mask = grouped_df['linemain'].isin(selected_lines_tuple)
        filtered_grouped_df = grouped_df.loc[mask].copy()
    else:
        filtered_grouped_df = grouped_df.copy()

    return filtered_grouped_df


@lru_cache(maxsize=128)
def get_cached_required_metrics(
    selected_metrics: tuple,
    premium_loss_checklist: tuple,
    reporting_form: str
) -> frozenset:
    """
    Caches the required metrics based on input parameters.

    Parameters:
    - selected_metrics (tuple): Selected metrics.
    - premium_loss_checklist (tuple): Premium loss checklist.
    - reporting_form (str): Reporting form identifier.

    Returns:
    - frozenset: A set of required metrics.
    """
    return frozenset(
        get_required_metrics(
            selected_metrics,
            {**CALCULATED_METRICS, **CALCULATED_RATIOS},
            premium_loss_checklist,
            BASE_METRICS
        )
    )

@lru_cache(maxsize=128)
def calculate_start_quarter(
    reporting_form: str,
    period_type: str
) -> pd.Timestamp:
    """
    Calculates the start quarter based on reporting_form and period_type.

    Parameters:
    - reporting_form (str): Reporting form identifier.
    - period_type (str): Type of the period (e.g., 'ytd', 'mat', 'yoy_y').

    Returns:
    - pd.Timestamp: The calculated start quarter.
    """
    start_quarter_str = '2018Q1' if reporting_form == '0420162' else '2022Q1'
    start_quarter = pd.Period(start_quarter_str, freq='Q').to_timestamp()

    if period_type == 'ytd':
        return start_quarter.replace(month=1)
    elif period_type in ['mat', 'yoy_y']:
        return start_quarter - DateOffset(months=9)
    else:
        return start_quarter  # Ensure it's a Timestamp for consistency



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
# @monitor_memory
# @profile
def process_data(
    filter_state: Dict[str, Any],
    period_type: str,
    end_quarter: str,
    num_periods_table: int,
    number_of_insurers: int,
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
    
        reporting_form = filter_state['reporting_form']
    
        # Calculate start quarter based on reporting_form and period_type
        start_quarter_interm = calculate_start_quarter(reporting_form, period_type)
    
        # Convert end_quarter to Timestamp (end of the quarter)
        end_quarter_period = pd.Period(end_quarter, freq='Q')
        end_quarter_ts = end_quarter_period.to_timestamp(how='end')
    
        # Convert line_type and selected_lines to tuples for hashing
        line_type_tuple = tuple(sorted(set(line_type))) if line_type else ()
        selected_lines_tuple = tuple(sorted(set(filter_state['selected_lines']))) if filter_state.get('selected_lines') else ()
    
        # Get cached, filtered, and grouped DataFrame including selected_lines
        grouped_df = get_cached_filtered_grouped_df(
            reporting_form,
            start_quarter_interm,
            end_quarter_ts,
            line_type_tuple,
            selected_lines_tuple
        )
    
        # Get cached required metrics
        selected_metrics = tuple(sorted(set(filter_state['selected_metrics'])))
        premium_loss_checklist = tuple(sorted(set(filter_state['premium_loss_checklist'])))
        required_metrics_set = get_cached_required_metrics(
            selected_metrics,
            premium_loss_checklist,
            reporting_form
        )
    
        # Apply additional filters: 'metric'
        if 'metric' in grouped_df.columns:
            mask = grouped_df['metric'].isin(required_metrics_set)
            df = grouped_df.loc[mask].copy()
        else:
            df = grouped_df.copy()

        processor = MetricsProcessor()
        # logger.debug(f"Process data - processing with parameters: {filter_state}, period_type: {period_type}, end_quarter: {end_quarter}, num_periods_table: {num_periods_table}, number_of_insurers: {number_of_insurers} ")
        # logger.debug(f"reporting_form: {filter_state['reporting_form']}")

        df, insurer_options, compare_options, selected_insurers, prev_ranks, number_of_periods_options, number_of_insurer_options = (
            processor.process_general_filters(
                df=df,
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
     Output('working-chart-container', 'children')],
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

        unique_insurers = df['insurer'].unique().tolist()
        
        # Get main insurer (first one)
        main_insurer = unique_insurers[:1][0]  # or simply unique_insurers[0]
        
        # Get next 4 insurers (excluding main insurer)
        compare_insurers = unique_insurers[1:5]
        
        # Filter dataframe to keep only these insurers
        df = df[df['insurer'].isin([main_insurer] + compare_insurers)]
        
        #logger.warning(f"compare_insurers {compare_insurers}")
        logger.warning(f"primary_y_metric {filter_state['primary_y_metric']}")
        logger.warning(f"secondary_y_metric {filter_state['secondary_y_metric']}")
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
            start_quarter='2018Q1' if filter_state['reporting_form'] == '0420162' else '2022Q1',
            end_quarter=end_quarter
)

        working_chart = dcc.Graph(
            id={'type': 'dynamic-chart', 'index': f'working-chart'},
            figure=chart_figure
        )

        # logger.debug(f"table_data {table_data}")
        # logger.debug("Returning table data")
        return table_data[0], table_data[1], table_data[2], working_chart

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