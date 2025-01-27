import os
import logging
from typing import List, Dict, Tuple
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL
from dash import no_update
import uuid


from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from application import (
    APP_TITLE, PORT, DEBUG_MODE,
    create_app_layout, get_logger, setup_logging,
    track_callback, track_callback_end, memory_monitor,
    insurance_lines_tree, get_required_metrics,
    filter_year_quarter, filter_by_period_type,
    category_structure_162, category_structure_158, get_categories_by_level,
    get_checklist_config, ChecklistComponent,
    DATA_FILE_158, DATA_FILE_162, map_insurer, calculate_metrics, process_insurers_data
)
from memory_profiler import profile
from application import (
    setup_buttons_callbacks, setup_debug_callbacks,
    setup_insurance_lines_callbacks, setup_sidebar_callbacks,
    setup_resize_observer_callback, setup_ui_callbacks,
    setup_metric_callbacks, 
    setup_insurers_callbacks,
    setup_process_data_callback
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


@app.callback(
    [Output('end-quarter', 'options'),
     Output('insurance-line-dropdown', 'options'),
     Output('business-type-checklist-container', 'children'),
     Output('intermediate-data-store', 'data'),
     Output('insurer-options-store', 'data'),
    ],  # New output
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
#n@profile
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
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    start_time = track_callback('main', 'prepare_data', ctx)

    
    # memory_monitor.log_memory("start_prepare_data", logger)

    try:
        
        trigger_id = ctx.triggered[0]['prop_id']
        logger.debug(f"trigger_id {trigger_id}")
        logger.debug(f"current_lines {current_lines}")
        logger.debug(f"lines {lines}")
        logger.warning(f"top_n_list {top_n_list}")
        '''if 'insurance-lines-state' in trigger_id and current_lines == lines:
            track_callback_end('main', 'prepare_data', start_time, message_no_update="current_lines == lines")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update'''

        
        # Setup category structure based on reporting form
        category_structure = category_structure_162 if reporting_form == '0420162' else category_structure_158
        insurance_line_dropdown_options = get_categories_by_level(category_structure, level=2, indent_char="--")

        # Get all metric values
        logger.warning(f"primary_metrics in prepare data {primary_metrics}")
        
        logger.debug(f"secondary_metric {secondary_metric}")
        
        secondary_metrics = [secondary_metric] if isinstance(secondary_metric, str) else (secondary_metric or [])
        
        all_metrics = (primary_metrics or []) + secondary_metrics
        logger.debug(f"all_metrics {all_metrics}")
        logger.debug(f"period_type {period_type}")
        
        # Get checklist configuration
        checklist_mode, allowed_types = get_checklist_config(all_metrics, reporting_form)
        checklist_values = allowed_types or current_checklist_values
        business_type_checklist = checklist_values or []

        checklist_component = ChecklistComponent.create_checklist(
            id='business-type-checklist',
            options=['direct', 'inward'],
            value=checklist_values,
            readonly=checklist_mode
        )

        # Process initial data
        df = df_162 if reporting_form == '0420162' else df_158

        end_quarter_options = [
            {'label': p.strftime('%YQ%q'), 'value': p.strftime('%YQ%q')} 
            for p in pd.PeriodIndex(df['year_quarter'].dt.to_period('Q')).unique()
        ]
        logger.debug(f"yq before filter_year_quarter {df['year_quarter'].unique()}")
        #df, num_periods = filter_year_quarter(df, end_quarter, period_type, num_periods_selected)
        logger.debug(f"yq before filter_by_period_type {df['year_quarter'].unique()}")
        # Get required metrics and filter data
        required_metrics = get_required_metrics(all_metrics, business_type_checklist)
        df = (df[df['linemain'].isin(lines) & df['metric'].isin(required_metrics)]
               .pipe(filter_year_quarter, end_quarter, period_type, num_periods_selected)
               .pipe(filter_by_period_type, period_type=period_type))

        dfs = [df]  # Start with original dataframe
        excluded_insurers = ['total']
        group_cols = [col for col in df.columns if col not in ['insurer', 'value']]
        #top_n_list = [5, 10, 20]
        for n in top_n_list:
            if n != 999:
                top_n_df = (
                    df[~df['insurer'].isin(excluded_insurers)]
                    .groupby(group_cols)
                    .apply(lambda x: x.nlargest(n, 'value'))
                    .reset_index(drop=True)
                    .groupby(group_cols, observed=True)['value']
                    .sum()
                    .reset_index()
                )
                top_n_df['insurer'] = f'top-{n}'
                dfs.append(top_n_df)

        # Concatenate all dataframes
        result_df = pd.concat(dfs, ignore_index=True)

        df = calculate_metrics(result_df, all_metrics, business_type_checklist)

        logger.debug(f"df {df}")


        # Calculate insurer options
        metric_to_use = next(m for m in required_metrics if m in df['metric'].unique())
        latest = df[
            (df['metric'] == metric_to_use) & 
            (df['linemain'] == lines[0]) & 
            (df['year_quarter'] == df['year_quarter'].max())
        ].sort_values('value', ascending=False)

        # First get the unique insurers and add our top-n values
        unique_insurers = list(latest['insurer'].unique())
        filtered_insurers = ['top-5', 'top-10', 'top-20'] + [
            i for i in unique_insurers 
            if not i.startswith('top-')
        ]
        
        # Create the options list from our filtered insurers
        insurer_options = [
            {'label': map_insurer(i), 'value': i} 
            for i in filtered_insurers
            if i.lower() != 'total'  
        ]


        df_top_5, _, _, _ = process_insurers_data(
            df=df,
            selected_metrics=all_metrics,
            selected_insurers=['top-5']
        )

        df_top_10, _, _, _ = process_insurers_data(
            df=df,
            selected_metrics=all_metrics,
            selected_insurers=['top-10']
        )

        df_top_20, _, _, _ = process_insurers_data(
            df=df,
            selected_metrics=all_metrics,
            selected_insurers=['top-20']
        )

        insurers_top5 = df_top_5['insurer'].unique()
        insurers_top10 = df_top_10['insurer'].unique()
        insurers_top20 = df_top_20['insurer'].unique()
        logger.warning(f"insurers_top5: {insurers_top5}")
        logger.warning(f"insurers_top10: {insurers_top10}")
        logger.warning(f"insurers_top20: {insurers_top20}")

        insurer_options_store = {
            'top5': df_top_5['insurer'].unique().tolist(),
            'top10': df_top_10['insurer'].unique().tolist(),
            'top20': df_top_20['insurer'].unique().tolist(),
            'insurer_options': insurer_options
        }


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
            '_trigger': uuid.uuid4().hex  # Add a unique trigger value

        }

        result = (
            end_quarter_options,
            insurance_line_dropdown_options,
            [checklist_component],
            intermediate_data,
            insurer_options_store
        )
        logger.debug("PREPARE DATA OUTPUTS:")
        logger.debug(f"end_quarter options len: {len(end_quarter_options)}")
        logger.debug(f"insurance_line_dropdown options len: {len(insurance_line_dropdown_options)}")
        logger.debug(f"checklist_component: {checklist_component}")
        logger.debug(f"intermediate_data keys: {intermediate_data.keys()}")

        
        track_callback_end('main', 'prepare_data', start_time, result=result)

        
        # memory_monitor.log_memory("end_prepare_data", logger)

        logger.debug(f"PREPARE DATA - Setting new intermediate data with hash: {hash(str(intermediate_data))}")
        logger.debug(f"PREPARE DATA - Created intermediate_data:")
        logger.debug(f"Records in df: {len(intermediate_data['df'])}")
        logger.debug(f"Data completeness check: {all(key in intermediate_data for key in ['df', 'all_metrics', 'required_metrics'])}")


        
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