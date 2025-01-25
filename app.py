import os
import logging
import time
from typing import List, Dict, Tuple, Optional
from functools import lru_cache
from dataclasses import dataclass
import json
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash, ALL, callback_context
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from application import (
    APP_TITLE, PORT, DEBUG_MODE, DEFAULT_END_QUARTER, DEFAULT_REPORTING_FORM,
    create_app_layout, get_logger, monitor_memory, setup_logging,
    track_callback, track_callback_end, memory_monitor,
    insurance_lines_tree, get_required_metrics, calculate_metrics,
    process_insurers_data, create_metric_dropdown,
    add_growth_rows, add_market_share_rows, filter_year_quarter, filter_by_period_type,
    category_structure_162, category_structure_158, get_categories_by_level,
    FilterComponents, get_metric_options, get_checklist_config,
    DATA_FILE_158, DATA_FILE_162, map_insurer, StyleConstants
)

logger = get_logger(__name__)
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)

@dataclass
class DatasetConfig:
    """Configuration for an insurance dataset"""
    file_path: str
    form_id: str
    metrics: List[str]

DATASET_CONFIGS = {
    '162': DatasetConfig(DATA_FILE_162, '0420162', ['direct_premiums', 'inward_premiums']),
    '158': DatasetConfig(DATA_FILE_158, '0420158', ['total_premiums'])
}

class InsuranceDataStore:
    """Optimized data management for insurance datasets"""
    
    def __init__(self):
        logger.info("Initializing InsuranceDataStore...")
        self._dtype_map = {
            'datatypec': 'object',
            'linemain': 'object',
            'insurer': 'object',
            'value': 'float64'
        }
        self._initialize_store()

    def _initialize_store(self) -> None:
        """Initialize datasets and options"""
        self.datasets = {}
        self.quarter_options = {}
        self.insurer_options = {}

        for form_id, config in DATASET_CONFIGS.items():
            df = self._load_dataset(config)
            self.datasets[form_id] = df

            form_name = config.form_id
            self._set_options(df, form_name, config.metrics)

        self.initial_quarter_options = self.quarter_options[DEFAULT_REPORTING_FORM]
        self.initial_insurer_options = self.insurer_options[DEFAULT_REPORTING_FORM]

    def _load_dataset(self, config: DatasetConfig) -> pd.DataFrame:
        """Load and preprocess a single dataset"""
        start_time = time.time()
        try:
            df = pd.read_csv(config.file_path, dtype=self._dtype_map)
            df['year_quarter'] = pd.to_datetime(df['year_quarter'])
            df['metric'] = df['metric'].fillna(0)

            group_cols = [col for col in df.columns if col not in ('line_type', 'value')]
            df = (df.groupby(group_cols, observed=True)['value']
                   .sum()
                   .reset_index()
                   .sort_values('year_quarter', ascending=True))

            logger.debug(f"Dataset {config.form_id} loaded in {time.time() - start_time:.2f}s")
            return df

        except Exception as e:
            logger.error(f"Failed to load dataset {config.form_id}: {str(e)}")
            raise

    def _set_options(self, df: pd.DataFrame, form_name: str, metrics: List[str]) -> None:
        """Set quarter and insurer options for a dataset"""
        # Quarter options
        periods = pd.PeriodIndex(df['year_quarter'].dt.to_period('Q')).unique()
        self.quarter_options[form_name] = [
            {'label': p.strftime('%YQ%q'), 'value': p.strftime('%YQ%q')}
            for p in periods
        ]

        # Insurer options
        latest_data = df[
            (df['metric'].isin(metrics)) &
            (df['linemain'] == 'все линии') &
            (df['year_quarter'] == df['year_quarter'].max())
        ]

        pivot = latest_data.pivot_table(
            index='insurer',
            columns='metric',
            values='value',
            aggfunc='sum',
            fill_value=0
        )

        if len(metrics) > 1:
            pivot['total_premiums'] = pivot[metrics].sum(axis=1)

        sorted_insurers = pivot.sort_values('total_premiums', ascending=False).index
        self.insurer_options[form_name] = [
            {'label': map_insurer(insurer), 'value': insurer}
            for insurer in sorted_insurers
        ]

    @lru_cache(maxsize=2)
    def get_dataframe(self, reporting_form: str) -> pd.DataFrame:
        """Get cached dataframe by reporting form"""
        key = reporting_form[-3:]
        return self.datasets[key].copy()


def setup_metric_callbacks(app: Dash, data_store: InsuranceDataStore) -> None:
    """Setup callbacks for managing primary and secondary metric dropdowns"""
    
    @app.callback(
        [Output('primary-metric', 'options'),
         Output('primary-metric', 'value'),
         Output('primary-metric-container', 'children'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value')],
        [Input('reporting-form', 'data'),
         Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
         Input('primary-metric-add-btn', 'n_clicks'),
         Input({'type': 'remove-primary-metric-btn', 'index': ALL}, 'n_clicks')],
        [State('primary-metric-container', 'children'),
         State('secondary-y-metric', 'value')]
    )
    def update_metric_dropdowns(
        reporting_form: str,
        main_dropdown_primary_metric: str,
        dynamic_dropdowns_primary_metric: List[str],
        add_primary_metric_btn_clicks: int,
        remove_primary_metric_btn_clicks: List[int],
        existing_primary_metric_dropdowns: List,
        secondary_metric: str
    ) -> Tuple:
        """Update metric dropdowns based on user interactions"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            # Initialize dropdowns if None
            existing_primary_metric_dropdowns = existing_primary_metric_dropdowns or []
            dynamic_dropdowns_primary_metric = [v for v in (dynamic_dropdowns_primary_metric or []) if v is not None]
            all_selected_primary_metric = [main_dropdown_primary_metric] + dynamic_dropdowns_primary_metric

            logger.debug(f"secondary_metric {secondary_metric}")
            logger.debug(f"primary_metric {main_dropdown_primary_metric}")
            logger.debug(f"all_selected_primary_metric {all_selected_primary_metric}")
            # Get initial metric options
            primary_metric_options, secondary_metric_options, valid_primary_metric, secondary_metric_value = (
                get_metric_options(reporting_form, all_selected_primary_metric, secondary_metric)
            )
            # Get all selected values
            main_dropdown_primary_metric_value = valid_primary_metric[0]
            dynamic_dropdowns_primary_metric_values = [v for v in valid_primary_metric if v != main_dropdown_primary_metric_value]
            logger.debug(f"dynamic_dropdowns_primary_metric_values {dynamic_dropdowns_primary_metric_values}")
            logger.debug(f"primary_metric_value {main_dropdown_primary_metric_value}")
            all_selected_primary_metric = valid_primary_metric
            logger.debug(f"all_selected_primary_metric {all_selected_primary_metric}")
            # Handle remove button click
            if '.n_clicks' in ctx.triggered[0]['prop_id'] and '"type":"remove-primary-metric-btn"' in ctx.triggered[0]['prop_id']:
                component_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
                removed_index = component_id['index']

                if ctx.triggered[0]['value'] is not None:
                    dynamic_dropdowns_primary_metric_values = [v for i, v in enumerate(dynamic_dropdowns_primary_metric_values) if i != removed_index]
                    existing_primary_metric_dropdowns = [
                        d for i, d in enumerate(existing_primary_metric_dropdowns) if i != removed_index
                    ]

            # Handle add button click
            if 'primary-metric-add-btn' in ctx.triggered[0]['prop_id']:
                new_primary_metric_dropdown = create_metric_dropdown(
                    index=len(existing_primary_metric_dropdowns),
                    options=[opt for opt in primary_metric_options if opt['value'] not in all_selected_primary_metric],
                    value=None
                )
                existing_primary_metric_dropdowns.append(new_primary_metric_dropdown)
            
            # Update existing dropdowns
            updated_primary_metric_dropdowns = []
            for i, _ in enumerate(existing_primary_metric_dropdowns):
                current_primary_metric = dynamic_dropdowns_primary_metric_values[i] if i < len(dynamic_dropdowns_primary_metric_values) else None
                other_primaey_metric_selected = [v for v in all_selected_primary_metric if v != current_primary_metric]
                
                primary_metric_dropdown_options = [
                    opt for opt in primary_metric_options 
                    if opt['value'] not in other_primaey_metric_selected
                ]
                
                updated_primary_metric_dropdowns.append(create_metric_dropdown(
                    index=i,
                    options=primary_metric_dropdown_options,
                    value=current_primary_metric
                ))
            
            # Filter primary metric options
            filtered_primary_metric_options = [
                opt for opt in primary_metric_options 
                if opt['value'] not in dynamic_dropdowns_primary_metric_values
]
            
            return (
                filtered_primary_metric_options,
                main_dropdown_primary_metric_value,
                updated_primary_metric_dropdowns,
                secondary_metric_options,
                secondary_metric_value[0] if secondary_metric_value else []
            )

        except Exception as e:
            logger.error(f"Error in update_metric_dropdowns: {str(e)}", exc_info=True)
            raise

def setup_data_process_callback(app: Dash, data_store: InsuranceDataStore) -> None:
    """Setup the main data processing callback"""
    
    @app.callback(
        [Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('business-type-checklist-container', 'children'),
         Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data')],
        [Input('reporting-form', 'data'),
         Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
         Input('secondary-y-metric', 'value'),
         Input('business-type-checklist', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data'),
         Input('number-of-periods-data-table', 'data'),
         Input('number-of-insurers', 'data'),
         Input('selected-insurers', 'value'),
         Input('end-quarter', 'value')],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')]
    )
    def process_data(
            reporting_form: str,
            primary_metric: str,
            dynamic_dropdowns_primary_metric_values: List[str],
            secondary_metric: str,
            current_checklist_values: List[str],
            lines: List[str],
            period_type: str,
            num_periods_selected: int,
            number_of_insurers: int,
            selected_insurers: List[str],
            end_quarter: str,
            show_data_table: bool,
            current_filter_state: Dict,
            line_type: Optional[List[str]] = None,
            top_n_list: List[int] = [5, 10, 20]
    ) -> Tuple:
        """Process insurance data and update UI components"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        start_time = track_callback('main', 'process_data', ctx)
        memory_monitor.log_memory("start_process_data", logger)

        try:
            # Get options based on reporting form
            end_quarter_options = data_store.quarter_options[reporting_form]
            category_structure = category_structure_162 if reporting_form == '0420162' else category_structure_158
            insurance_line_primary_metric_dropdown_options = get_categories_by_level(category_structure, level=2, indent_char="--")

            # Get all metric values (ensuring they are strings, not lists)
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

            # Process data
            df = data_store.get_dataframe(reporting_form)
            df, num_periods = filter_year_quarter(df, end_quarter, period_type, num_periods_selected)

            # Get required metrics (passing properly formatted list)
            required_metrics = get_required_metrics(all_metrics, business_type_checklist)

            # Filter and process data
            df = (df[df['linemain'].isin(lines) & df['metric'].isin(required_metrics)]
                   .pipe(filter_by_period_type, period_type=period_type))

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
                   .pipe(add_growth_rows, selected_insurers, show_data_table, num_periods_selected, period_type))

            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            # Update filter state
            updated_filter_state = {
                **(current_filter_state or {}),
                'primary_y_metric': primary_metric,
                'secondary_y_metric': secondary_metric,
                'selected_metrics': all_metrics,
                'business_type_checklist': business_type_checklist,
                'selected_lines': lines,
                'show_data_table': bool(show_data_table),
                'reporting_form': reporting_form,
                'period_type': period_type,
            }

            result = (
                end_quarter_options,
                insurance_line_primary_metric_dropdown_options,
                [checklist_component],
                updated_filter_state,
                {'df': df.to_dict('records'), 'prev_ranks': prev_ranks}
            )

            track_callback_end('main', 'process_data', start_time, result=result)
            memory_monitor.log_memory("end_process_data", logger)
            return result

        except Exception as e:
            logger.error(f"Error in process_data: {str(e)}", exc_info=True)
            track_callback_end('main', 'process_data', start_time, error=str(e))
            raise
def setup_sync_metrics_callback(app: Dash) -> None:
    """Setup callback for syncing metric values"""
    
    @app.callback(
        Output('primary-metric-all-values', 'data'),
        [Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value')]
    )
    def sync_metric_values(main_value: str, dynamic_values: List[str]) -> List[str]:
        """Sync all metric values into a single store"""
        return [main_value] + [v for v in dynamic_values if v is not None]

def setup_callbacks(app: Dash, data_store: InsuranceDataStore) -> None:
    """Configure all application callbacks"""
    # Callbacks that only need app
    from application import (
        setup_buttons_callbacks, setup_debug_callbacks,
        setup_insurance_lines_callbacks, setup_sidebar_callbacks,
        setup_resize_observer_callback, setup_ui_callbacks
    )
    app_only_callbacks = [
        setup_buttons_callbacks,
        setup_debug_callbacks,
        setup_resize_observer_callback,
        setup_ui_callbacks,
        setup_sync_metrics_callback
    ]

    # Callbacks that need both app and data_store
    data_store_callbacks = [
        setup_metric_callbacks,
        setup_data_process_callback
    ]

    # Special callbacks with additional arguments
    special_callbacks = [
        (setup_insurance_lines_callbacks, [insurance_lines_tree]),
        (setup_sidebar_callbacks, [])
    ]

    # Set up app-only callbacks
    for callback in app_only_callbacks:
        callback(app)

    # Set up callbacks that need data_store
    for callback in data_store_callbacks:
        callback(app, data_store)

    # Set up special callbacks with additional arguments
    for callback, extra_args in special_callbacks:
        callback(app, *extra_args)

def main():
    """Application entry point"""
    try:
        port = int(os.environ.get("PORT", PORT))
        print(f"Starting server on port {port}...")
        app.run_server(debug=DEBUG_MODE, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

# Application initialization
print("Starting application initialization...")
data_store = InsuranceDataStore()

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
app.layout = create_app_layout(
    data_store.initial_quarter_options,
    data_store.initial_insurer_options
)

setup_callbacks(app, data_store)
server = app.server

if __name__ == '__main__':
    main()