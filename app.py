import os
import logging
from typing import List, Dict, Tuple, Optional
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from application import (
    APP_TITLE, PORT, DEBUG_MODE, save_df_to_csv,
    create_app_layout, get_logger, setup_logging,
    track_callback, track_callback_end, memory_monitor,
    insurance_lines_tree, get_required_metrics, calculate_metrics,
    process_insurers_data, add_growth_rows, add_market_share_rows,
    filter_year_quarter, filter_by_period_type,
    category_structure_162, category_structure_158, get_categories_by_level,
    FilterComponents, get_checklist_config,
    DATA_FILE_158, DATA_FILE_162, map_insurer
)
from application import (
    setup_buttons_callbacks, setup_debug_callbacks,
    setup_insurance_lines_callbacks, setup_sidebar_callbacks,
    setup_resize_observer_callback, setup_ui_callbacks,
    setup_sync_metrics_callback, setup_metric_callbacks, 
    setup_sync_insurers_callback, setup_insurers_callbacks
)


logger = get_logger(__name__)
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)


def load_insurance_dataframes():
    """
    Load and preprocess insurance datasets for forms 162 and 158.
    Returns two dataframes: df_162 and df_158
    """
    dtype_map = {
        'metric': 'object',
        'linemain': 'object',
        'insurer': 'object',
        'value': 'float64'
    }

    try:
        # Load 162 dataset
        df_162 = pd.read_csv(DATA_FILE_162, dtype=dtype_map)
        df_162['year_quarter'] = pd.to_datetime(df_162['year_quarter'])
        df_162['metric'] = df_162['metric'].fillna(0)

        # Load 158 dataset
        df_158 = pd.read_csv(DATA_FILE_158, dtype=dtype_map)
        df_158['year_quarter'] = pd.to_datetime(df_158['year_quarter'])
        df_158['metric'] = df_158['metric'].fillna(0)

        return df_162, df_158

    except Exception as e:
        print(f"Failed to load datasets: {str(e)}")
        raise

# Application initialization
print("Starting application initialization...")

app = dash.Dash(
    __name__,
    url_base_pathname="/",
    assets_folder='assets',
    assets_ignore='.ipynb_checkpoints/*',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None
)

app.title = APP_TITLE
app.layout = create_app_layout()

server = app.server

df_162, df_158 = load_insurance_dataframes()

setup_buttons_callbacks(app)
setup_debug_callbacks(app)
setup_resize_observer_callback(app)
setup_ui_callbacks(app)
setup_sync_metrics_callback(app)
setup_metric_callbacks(app)
setup_insurance_lines_callbacks(app, insurance_lines_tree)
setup_sidebar_callbacks(app)
setup_sync_insurers_callback(app)
setup_insurers_callbacks(app)

# First callback: Initial data processing and filtering
from typing import List, Dict, Tuple
import dash
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import pandas as pd

# First callback: Initial data processing and filtering
@app.callback(
    [Output('end-quarter', 'options'),
     Output('insurance-line-dropdown', 'options'),
     Output('business-type-checklist-container', 'children'),
     Output('intermediate-data-store', 'data')],
    [Input('reporting-form', 'data'),
     Input('primary-metric', 'value'),
     Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
     Input('secondary-y-metric', 'value'),
     Input('business-type-checklist', 'value'),
     Input('insurance-lines-state', 'data'),
     Input('period-type', 'data'),
     Input('number-of-periods-data-table', 'data'),
     Input('end-quarter', 'value')],
    [State('show-data-table', 'data'),
     State('filter-state-store', 'data')]
)
def process_data_part1(
        reporting_form: str,
        primary_metric: str,
        dynamic_dropdowns_primary_metric_values: List[str],
        secondary_metric: str,
        current_checklist_values: List[str],
        lines: List[str],
        period_type: str,
        num_periods_selected: int,
        end_quarter: str,
        show_data_table: bool,
        current_filter_state: Dict
) -> Tuple:
    """First part of data processing: Initial filtering and setup"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    start_time = track_callback('main', 'process_data_part1', ctx)
    memory_monitor.log_memory("start_process_data_part1", logger)

    try:
        # Setup category structure based on reporting form
        category_structure = category_structure_162 if reporting_form == '0420162' else category_structure_158
        insurance_line_dropdown_options = get_categories_by_level(category_structure, level=2, indent_char="--")

        # Get all metric values
        all_metrics = []
        if primary_metric:
            all_metrics.append(primary_metric)
        if dynamic_dropdowns_primary_metric_values:
            all_metrics.extend([v for v in dynamic_dropdowns_primary_metric_values if v is not None])
        if secondary_metric:
            all_metrics.append(secondary_metric)

        # Get checklist configuration
        checklist_mode, allowed_types = get_checklist_config(all_metrics, reporting_form)
        checklist_values = allowed_types or current_checklist_values
        business_type_checklist = checklist_values or []

        checklist_component = FilterComponents.create_component(
            component_type='checklist',
            id='business-type-checklist',
            readonly=checklist_mode,
            value=checklist_values
        )

        # Process initial data
        df = df_162 if reporting_form == '0420162' else df_158
        
        end_quarter_options = [
            {'label': p.strftime('%YQ%q'), 'value': p.strftime('%YQ%q')} 
            for p in pd.PeriodIndex(df['year_quarter'].dt.to_period('Q')).unique()
        ]

        df, num_periods = filter_year_quarter(df, end_quarter, period_type, num_periods_selected)

        # Get required metrics and filter data
        required_metrics = get_required_metrics(all_metrics, business_type_checklist)
        df = (df[df['linemain'].isin(lines) & df['metric'].isin(required_metrics)]
               .pipe(filter_by_period_type, period_type=period_type))

        # Calculate insurer options
        metric_to_use = next(m for m in required_metrics if m in df['metric'].unique())
        latest = df[
            (df['metric'] == metric_to_use) & 
            (df['linemain'] == lines[0]) & 
            (df['year_quarter'] == df['year_quarter'].max())
        ].sort_values('value', ascending=False)

        insurer_options = [
            {'label': map_insurer(i), 'value': i} 
            for i in latest['insurer']
        ]

        # Create intermediate data structure
        intermediate_data = {
            'df': df.to_dict('records'),
            'all_metrics': all_metrics,
            'business_type_checklist': business_type_checklist,
            'required_metrics': required_metrics,
            'lines': lines,
            'period_type': period_type,
            'num_periods_selected': num_periods_selected,
            'reporting_form': reporting_form,
            'insurer_options': insurer_options,
            'num_periods': num_periods  # Add this if needed for calculations
        }

        result = (
            end_quarter_options,
            insurance_line_dropdown_options,
            [checklist_component],
            intermediate_data  # Pass as is, without additional nesting
        )

        track_callback_end('main', 'process_data_part1', start_time, result=result)
        memory_monitor.log_memory("end_process_data_part1", logger)
        return result

    except Exception as e:
        logger.error(f"Error in process_data_part1: {str(e)}", exc_info=True)
        track_callback_end('main', 'process_data_part1', start_time, error=str(e))
        raise

# Second callback: Process insurers and calculate metrics
@app.callback(
    [Output('filter-state-store', 'data'),
     Output('processed-data-store', 'data')],
    [Input('intermediate-data-store', 'data'),
     Input('selected-insurers', 'value'),
     Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
     Input('number-of-insurers', 'data')],
    [State('show-data-table', 'data'),
     State('filter-state-store', 'data')]
)
def process_data_part2(
        intermediate_data: Dict,
        selected_insurers: str,
        selected_dynamic_insurers: List[str],
        number_of_insurers: int,
        show_data_table: bool,
        current_filter_state: Dict,
        top_n_list: List[int] = [5, 10, 20]
) -> Tuple:
    """Second part of data processing: Insurer processing and metric calculations"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    start_time = track_callback('main', 'process_data_part2', ctx)
    memory_monitor.log_memory("start_process_data_part2", logger)

    try:
        if not isinstance(intermediate_data, dict):
            logger.error(f"Invalid intermediate_data type: {type(intermediate_data)}")
            raise PreventUpdate
        logger.warning(f"selected_insurers {selected_insurers}")
        logger.warning(f"selected_dynamic_insurers {selected_dynamic_insurers}")
        selected_insurers = (selected_dynamic_insurers or []) + [selected_insurers]
        # Reconstruct DataFrame from intermediate data
        df = pd.DataFrame.from_records(intermediate_data.get('df', []))
        all_metrics = intermediate_data.get('all_metrics', [])
        business_type_checklist = intermediate_data.get('business_type_checklist', [])
        lines = intermediate_data.get('lines', [])
        period_type = intermediate_data.get('period_type', '')
        num_periods_selected = intermediate_data.get('num_periods_selected', 0)
        logger.warning(f"selected_insurers {selected_insurers}")
        # Process insurers data
        df, prev_ranks, num_insurers = process_insurers_data(
            df=df,
            selected_insurers=selected_insurers,
            top_n_list=top_n_list,
            show_data_table=show_data_table,
            selected_metrics=all_metrics,
            number_of_insurers=number_of_insurers
        )

        # Calculate metrics and add additional rows
        df = (df.pipe(calculate_metrics, all_metrics, business_type_checklist)
               .pipe(add_market_share_rows, selected_insurers, all_metrics, show_data_table)
               .pipe(add_growth_rows, selected_insurers, show_data_table, 
                    num_periods_selected, period_type))

        df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

        # Update filter state
        updated_filter_state = {
            **(current_filter_state or {}),
            'primary_y_metric': all_metrics[0] if all_metrics else None,
            'secondary_y_metric': all_metrics[-1] if len(all_metrics) > 1 else None,
            'selected_metrics': all_metrics,
            'business_type_checklist': business_type_checklist,
            'selected_lines': lines,
            'show_data_table': bool(show_data_table),
            'reporting_form': intermediate_data.get('reporting_form'),
            'period_type': period_type,
        }

        result = (
            updated_filter_state,
            {'df': df.to_dict('records'), 'prev_ranks': prev_ranks}
        )

        track_callback_end('main', 'process_data_part2', start_time, result=result)
        memory_monitor.log_memory("end_process_data_part2", logger)
        return result

    except Exception as e:
        logger.error(f"Error in process_data_part2: {str(e)}", exc_info=True)
        track_callback_end('main', 'process_data_part2', start_time, error=str(e))
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