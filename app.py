import os
import logging
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from typing import List, Dict, Tuple
from memory_profiler import profile
from application import (
    create_app_layout, load_insurance_dataframes, insurance_lines_tree,
    APP_TITLE, PORT, DEBUG_MODE, setup_logging, get_logger,
    track_callback, track_callback_end, memory_monitor,
    get_year_quarter_options, get_checklist_config,
    get_insurance_line_options, get_insurer_options,
    get_required_metrics,
    filter_year_quarter, filter_by_period_type,
    add_top_n_rows, calculate_metrics
    )
from application import (
    setup_process_data_callback,
    setup_metric_callbacks, setup_insurers_callbacks,
    setup_buttons_callbacks, setup_debug_callbacks,
    setup_insurance_lines_callbacks, setup_sidebar_callbacks,
    setup_resize_observer_callback, setup_ui_callbacks
    )
logger = get_logger(__name__)
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)

print("Starting application initialization...")

app = dash.Dash(
    __name__,
    url_base_pathname="/",
    assets_folder='assets',
    assets_ignore='.ipynb_checkpoints/*',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None,
    serve_locally=True
)

app.config.assets_external_path = '/'  # Add here
print("Registered paths:", app.registered_paths)
print("Static routes:", list(app.server.url_map.iter_rules()))
app.title = APP_TITLE

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
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

app.layout = create_app_layout()

server = app.server

df_162, df_158 = load_insurance_dataframes()

setup_buttons_callbacks(app)
setup_debug_callbacks(app)
setup_resize_observer_callback(app)
setup_ui_callbacks(app)
setup_process_data_callback(app)

setup_metric_callbacks(app)
setup_insurance_lines_callbacks(app, insurance_lines_tree)
setup_sidebar_callbacks(app)
setup_insurers_callbacks(app)


def process_data_optimized(df, lines, required_metrics, end_quarter, period_type, num_periods_selected, top_n_list, all_metrics, business_type_checklist):
    # Make a copy and convert to categorical
    df = df.copy()
    categorical_columns = ['linemain', 'metric', 'insurer']
    for col in categorical_columns:
        df[col] = df[col].astype('category')

    # Create mask and filter
    mask = df['linemain'].isin(lines) & df['metric'].isin(required_metrics)
    df_filtered = df.loc[mask]

    # Process the filtered dataframe
    result = (df_filtered
             .pipe(filter_year_quarter, end_quarter, period_type, num_periods_selected)
             .pipe(filter_by_period_type, period_type=period_type)
             .pipe(add_top_n_rows, top_n_list=top_n_list)
             .pipe(calculate_metrics, all_metrics, business_type_checklist)
             )

    # Convert back from categorical if needed
    for col in categorical_columns:
        if col in result.columns:
            result[col] = result[col].astype(str)

    return result


@app.callback(
    [Output('end-quarter', 'options'),
     Output('insurance-line-dropdown', 'options'),
     Output('business-type-checklist-container', 'children'),
     Output('intermediate-data-store', 'data'),
     Output('insurer-options-store', 'data'),
     ],
    [Input('secondary-y-metric', 'value'),
     Input('primary-metric-all-values', 'data'),
     Input('business-type-checklist', 'value'),
     Input('number-of-periods-data-table', 'data'),
     Input('number-of-insurers', 'data'),
     Input('end-quarter', 'value')],
    [
     State('period-type', 'data'),
     State('insurance-lines-state', 'data'),
     State('reporting-form', 'data'),
     State('show-data-table', 'data'),
     State('filter-state-store', 'data'),
     State('insurance-lines-state', 'data'),
    ]
)
@profile
def prepare_data(
        secondary_metric: str,
        primary_metrics: List[str],
        current_checklist_values: List[str],
        num_periods_selected: int,
        top_n_list: List[int],
        end_quarter: str,
        period_type: str,
        lines: List[str],
        reporting_form: str,
        show_data_table: bool,
        current_filter_state: Dict,
        current_lines: List[str],
) -> Tuple:
    """First part of data processing: Initial filtering and setup"""
    # memory_monitor.log_memory("start_prepare_data", logger)

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate  
    trigger_id = ctx.triggered[0]['prop_id']
    start_time = track_callback('main', 'prepare_data', ctx)

    try:
        df = df_162 if reporting_form == '0420162' else df_158

        insurance_line_dropdown_options = get_insurance_line_options(reporting_form, level=2, indent_char="--")

        end_quarter_options = get_year_quarter_options(df)

        all_metrics = (primary_metrics or []) + ([secondary_metric] if isinstance(secondary_metric, str) else (secondary_metric or []))

        checklist_component, business_type_checklist = get_checklist_config(all_metrics, reporting_form, current_checklist_values)

        required_metrics = get_required_metrics(all_metrics, business_type_checklist)

        df = (df[df['linemain'].isin(lines) & df['metric'].isin(required_metrics)]
              .pipe(filter_year_quarter, end_quarter, period_type, num_periods_selected)
              .pipe(filter_by_period_type, period_type=period_type)
              .pipe(add_top_n_rows, top_n_list=top_n_list)
              .pipe(calculate_metrics, all_metrics, required_metrics, business_type_checklist)
               )

        insurer_options_store = get_insurer_options(df, all_metrics, lines)

        intermediate_data = {
            'df': df.to_dict('records'),
            'all_metrics': all_metrics,
            'business_type_checklist': business_type_checklist,
            'required_metrics': required_metrics,
            'lines': lines,
            'period_type': period_type,
            'num_periods_selected': num_periods_selected,
            'reporting_form': reporting_form,
        }

        result = (
            end_quarter_options,
            insurance_line_dropdown_options,
            [checklist_component],
            intermediate_data,
            insurer_options_store
        )

        track_callback_end('main', 'prepare_data', start_time, result=result)
        # memory_monitor.log_memory("end_prepare_data", logger)

        return result

    except Exception as e:
        logger.error(f"Error in prepare data: {str(e)}", exc_info=True)
        track_callback_end('main', 'prepare_data', start_time, error=str(e))
        raise


def main():
    """Application entry point"""
    try:
        port = int(os.environ.get("PORT", PORT))
        print(f"Starting server on port {port}...")
        app.run_server(debug=DEBUG_MODE, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

if __name__ == '__main__':
    main()