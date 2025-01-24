import os
import logging
from typing import List, Dict, Any

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from application import (
    APP_TITLE, PORT, DEBUG_MODE,
    create_app_layout, get_logger,
    setup_logging, track_callback, track_callback_end, memory_monitor,
    insurance_lines_tree, get_required_metrics, calculate_metrics,
    process_insurers_data, filter_by_date_range_and_period_type,
    add_growth_rows, add_market_share_rows,
    category_structure_162, category_structure_158, get_categories_by_level,
    FilterComponents, get_metric_options, get_premium_loss_state
)
from data_store import InsuranceDataStore

# Initialize logging
logger = get_logger(__name__)
setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)




def create_app(data_store: InsuranceDataStore) -> dash.Dash:
    """Create and configure Dash application"""
    app = dash.Dash(
        __name__,
        url_base_pathname="/",
        assets_folder='assets',
        assets_ignore='.ipynb_checkpoints/*',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        update_title=None
    )
    server = app.server
    app.title = APP_TITLE
    app.layout = create_app_layout(
        data_store.initial_quarter_options,
        data_store.initial_insurer_options
    )

    _setup_callbacks(app, data_store)

    return app


def _setup_callbacks(app: dash.Dash, data_store: InsuranceDataStore):
    """Configure all application callbacks"""
    from application import (
        setup_buttons_callbacks, setup_debug_callbacks,
        setup_insurance_lines_callbacks,
        setup_sidebar_callbacks,
        setup_resize_observer_callback, setup_ui_callbacks
    )

    callbacks = [
        setup_buttons_callbacks,
        setup_debug_callbacks,
        (setup_insurance_lines_callbacks, insurance_lines_tree),
        setup_sidebar_callbacks,
        setup_resize_observer_callback,
        setup_ui_callbacks
    ]

    for callback in callbacks:
        if isinstance(callback, tuple):
            callback[0](app, *callback[1:])
        else:
            callback(app)

    _setup_filter_update_callbacks(
        app,
        data_store.quarter_options['0420162'],
        data_store.quarter_options['0420158'],
        data_store
    )

def _setup_filter_update_callbacks(app: Dash, quarter_options_162, quarter_options_158, data_store) -> None:
    @app.callback(
        [Output('primary-y-metric', 'options'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value'),
         Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('premium-loss-checklist-container', 'children'),
         Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data'),
        ],
        [
         Input('reporting-form', 'data'),
         Input('primary-y-metric', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('premium-loss-checklist', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data'),
         Input('number-of-periods-data-table', 'data'),
         Input('number-of-insurers', 'data'),
         Input('selected-insurers', 'value'),
         Input('end-quarter', 'value')],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')], 
        prevent_initial_call=True
    )
    def update_options(
            reporting_form,
            primary_metric,
            secondary_metric,
            current_values,
            lines, 
            period_type,
            num_periods_selected: int,
            number_of_insurers: int,
            selected_insurers: List[str],
            end_quarter: str,
            show_data_table: bool, 
            current_filter_state,
            line_type: List[str] = None,
            top_n_list=[5, 10, 20]
    ):
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE
        """
        ctx = dash.callback_context
        start_time = track_callback('app.callbacks.filter_update_callbacks', 'update_options', ctx)
        if not ctx.triggered:
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time)
            raise PreventUpdate
        try:

            metric_options = get_metric_options(reporting_form, primary_metric, secondary_metric)

            # Get validated metrics from the return value
            primary_metric_value = metric_options.get('primary_metric')
            secondary_metric_value = metric_options.get('secondary_metric')
            selected_metrics = (primary_metric_value or []) + (secondary_metric_value or [])

            end_quarter_options = quarter_options_162 if reporting_form == '0420162' else quarter_options_158
            insurance_line_dropdown_options = get_categories_by_level(
                category_structure_162 if reporting_form == '0420162' else category_structure_158, 
                level=2, 
                indent_char="--"
            )

            # Use validated metrics for selected_metrics
            readonly, enforced_values = get_premium_loss_state(selected_metrics, reporting_form)
            values = enforced_values if enforced_values is not None else current_values
            premium_loss_checklist = values or []
            component = FilterComponents.create_component(
                'checklist',
                id='premium-loss-checklist',
                readonly=readonly,
                value=values
            )

            df = data_store.get_dataframe(reporting_form)
            end_quarter_ts = pd.Period(end_quarter, freq='Q').to_timestamp(how='end')

            mask = df['year_quarter'] <= end_quarter_ts
            if line_type:
                mask &= df['line_type'].isin(line_type)

            df = df[mask]

            group_cols = [col for col in df.columns if col not in ('line_type', 'value')]
            df = df.groupby(group_cols, observed=True)['value'].sum().reset_index()

            df = (df[df['linemain'].isin(lines)]
                   .pipe(lambda x: x[x['metric'].isin(
                       get_required_metrics(
                           selected_metrics, premium_loss_checklist
                       )
                   )])
                   .pipe(filter_by_date_range_and_period_type,
                         period_type=period_type))
            periods = sorted(df['year_quarter'].unique(), reverse=True)

            periods_to_keep = periods[:min(num_periods_selected, len(periods)) + 1]
            df = df[df['year_quarter'].isin(periods_to_keep)]

            # Process insurers
            latest_quarter = df['year_quarter'].max()
            num_insurers = min(
                number_of_insurers,
                len(df[df['year_quarter'] == latest_quarter]['insurer'].unique())
            )

            df, prev_ranks = process_insurers_data(
                df=df,
                selected_insurers=selected_insurers,
                top_n_list=top_n_list,
                show_data_table=show_data_table,
                selected_metrics=selected_metrics,
                number_of_insurers=num_insurers
            )


            # Calculate metrics
            df = calculate_metrics(
                df,
                selected_metrics,
                premium_loss_checklist
            )

            logger.debug(f"metrics {df['metric'].unique()}")
            logger.debug(f"selected_metrics {selected_metrics}")

            # Filter the DataFrame based on selected metrics
            df = df[df['metric'].isin(selected_metrics)]

            # Add market share rows
            df = add_market_share_rows(
                df,
                selected_insurers,
                selected_metrics,
                show_data_table
            )

            # Add growth rows
            df = add_growth_rows(
                df,
                selected_insurers,
                show_data_table,
                num_periods_selected,
                period_type
            )

            # Format dates
            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            # Update filter state with new values
            filter_state = current_filter_state or {}
            updated_filter_state = {
                **filter_state,
                'primary_y_metric': primary_metric_value,
                'secondary_y_metric': secondary_metric_value,
                'selected_metrics': selected_metrics,
                'premium_loss_checklist': premium_loss_checklist,
                'selected_lines': lines,
                'show_data_table': bool(show_data_table),
                'reporting_form': reporting_form,
                'period_type': period_type,
            }
            logger.debug(f"component: {[component]}")

            output = (
                metric_options['primary_y_metric_options'],
                primary_metric_value[0],
                metric_options['secondary_y_metric_options'],
                secondary_metric_value[0] if secondary_metric_value else [],
                end_quarter_options,
                insurance_line_dropdown_options,
                [component],
                updated_filter_state,
                {'df': df.to_dict('records'), 'prev_ranks': prev_ranks}
            )
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, result=output)
            return output
        except Exception as e:
            logger.error(f"Error in update_options: {str(e)}", exc_info=True)
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, error=str(e))
            raise

def main():
    """Application entry point"""
    try:
        print("Starting application initialization...")
        data_store = InsuranceDataStore()
        app = create_app(data_store)

        port = int(os.environ.get("PORT", PORT))
        print(f"Starting server on port {port}...")
        app.run_server(debug=DEBUG_MODE, port=port, host='0.0.0.0')

    except Exception as e:
        print(f"Error during startup: {e}")
        raise


if __name__ == '__main__':
    main()