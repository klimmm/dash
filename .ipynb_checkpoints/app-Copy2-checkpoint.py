import os
import logging




import psutil
import time
from functools import wraps
from typing import Optional

import signal
from functools import wraps
from contextlib import contextmanager

from app import *
from data_process.update_filter_options import *
# Global flag to enable/disable detailed memory tracking
logger = logging.getLogger(__name__)

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.last_check = time.time()
        self.check_interval = 60  # seconds

    def get_memory_usage(self) -> dict:
        """Get current memory usage stats"""
        mem = self.process.memory_info()
        return {
            'rss': mem.rss / 1024 / 1024,  # MB
            'vms': mem.vms / 1024 / 1024,  # MB
            'percent': self.process.memory_percent(),
            'system_used': psutil.virtual_memory().percen
        }

    def should_check(self) -> bool:
        """Determine if enough time has passed for next check"""
        return time.time() - self.last_check >= self.check_interval

    def log_memory(self, tag: str, logger: logging.Logger) -> None:
        try:
            mem_stats = self.get_memory_usage()
            print(  # Changed from logger.info to prin
                f"Memory at {tag}: "
                f"RSS={mem_stats['rss']:.1f}MB, "
                f"Process=%{mem_stats['percent']:.1f}, "
                f"System=%{mem_stats['system_used']:.1f}"
            )
            self.last_check = time.time()
        except Exception as e:
            print(f"Error monitoring memory: {str(e)}")  # Changed from logger.error to prin

# Create singleton instance
memory_monitor = MemoryMonitor()

def monitor_memory(func):
    """Decorator to monitor memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_mem = memory_monitor.get_memory_usage()

        try:
            result = func(*args, **kwargs)
            return resul
        finally:
            end_mem = memory_monitor.get_memory_usage()
            mem_diff = end_mem['rss'] - start_mem['rss']
            print(  # Changed from logging.info to prin
                f"Memory {func.__name__}: Current={end_mem['rss']:.1f}MB, "
                f"Change={mem_diff:+.1f}MB, "
                f"Time={time.time()-start_time:.3f}s"
            )
    return wrapper




def create_dash_app() -> dash.Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    app.title = APP_TITLE
    app.index_string = f'''
    <!DOCTYPE html>
    <html>
        <head>
            {{%metas%}}
            <title>{{%title%}}</title>
            {{%favicon%}}
            {{%css%}}
        </head>
        <body>
            {{%app_entry%}}
            <footer>
                {{%config%}}
                {{%scripts%}}
                {{%renderer%}}
            </footer>
        </body>
    </htm

    '''
    return app

def main():
    print("Starting main()")
    # Initialize logging and debug level
    setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)
    set_debug_level(DebugLevels.VERBOSE)
    logger = get_logger(__name__)
    logger.warning(f"Starting the Insurance Data Analysis Dashboard")

    # Load and preprocess data
    try:
        insurance_df = load_and_preprocess_data(DATA_FILE_NEW)
        reinsurance_df = load_and_preprocess_data(DATA_FILE_REINSURANCE)
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        raise


    # Create application
    year_quarter_options = create_year_quarter_options(insurance_df)
    app = create_dash_app()
    layout, date_filter = create_app_layout(year_quarter_options)
    app.layout = layou

    # Setup basic callbacks
    setup_date_range_callbacks(app, date_filter)
    setup_tab_state_callbacks(app)
    setup_checklist_callbacks(app)
    setup_button_callbacks(app)

    # Add data stores
    app.layout.children.extend([
        dcc.Store(id='processed-data-store'),
        dcc.Store(id='filter-state-store'),
        dcc.Store(id='options-store'),
        dcc.Store(id='chart-options-store')
    ])

    logger.info(f"Dashboard layout created")

    # Callback 1: Handle value updates
    @app.callback(
        [
            Output('filter-state-store', 'data'),
            Output('x-column', 'value'),
            Output('series-column', 'value'),
            Output('group-column', 'value'),
            Output('main-insurer', 'value'),
            Output('compare-insurers-main', 'value'),
            Output('primary-y-metric', 'value'),
            Output('secondary-y-metric', 'value'),
            Output('premium-loss-checklist', 'value')
        ],
        [
            Input('show-reinsurance-chart', 'data'),
            Input('x-column', 'value'),
            Input('series-column', 'value'),
            Input('group-column', 'value'),
            Input('main-insurer', 'value'),
            Input('compare-insurers-main', 'value'),
            Input('primary-y-metric', 'value'),
            Input('secondary-y-metric', 'value'),
            Input('premium-loss-checklist', 'value'),
            Input('clear-filters-button', 'n_clicks'),
            Input('period-type', 'data'),
            Input('start-quarter', 'value'),
            Input('end-quarter', 'value'),
            Input('quarter-value-output', 'data'),
            Input('category-state', 'data'),
            Input('number-of-insurers', 'value'),
            Input('number-of-years-to-show', 'data'),
            Input('number-of-periods-data-table', 'value'),
            Input('reinsurance-geography-dropdown', 'value'),
            Input('reinsurance-form-dropdown', 'value'),
            Input('reinsurance-type-dropdown', 'value')

        ],
        [
            State('x-column', 'value'),
            State('series-column', 'value'),
            State('group-column', 'value'),
            State('main-insurer', 'value'),
            State('compare-insurers-main', 'value'),
            State('primary-y-metric', 'value'),
            State('secondary-y-metric', 'value'),
            State('premium-loss-checklist', 'value'),
            State('show-data-table', 'data'),
            State('stacking-groups-toggle', 'value'),
            State('stacking-series-toggle', 'value'),
        ],
        prevent_initial_call=True
    )
    @monitor_memory
    def update_filter_values(
            show_reinsurance_chart, x_column, series_column, group_column,
            main_insurer, compare_insurers, primary_y_metric, secondary_y_metric,
            premium_loss_selection, clear_filters_btn, period_type,
            start_quarter, end_quarter, quarter_value, selected_linemains,
            number_of_insurers, num_periods, num_periods_table, reinsurance_geography, reinsurance_form, reinsurance_type,

            x_column_state, series_column_state, group_column_state,
            main_insurer_state, compare_insurers_state,
            primary_y_metric_state, secondary_y_metric_state, premium_loss_selection_state,
            show_data_table_state):

        memory_monitor.log_memory("before_update_filter_values", logger)

        logger.warning(f"Starting the update_filter_values function")
        ctx = dash.callback_contex
        start_time = track_callback('app.main', 'update_filter_values', ctx)

        try:


            if not ctx.triggered:
                track_callback_end('app.main', 'update_filter_values', start_time, message_no_update="not ctx.triggered")
                raise PreventUpdate


            trigger = ctx.triggered[0]
            trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
            logger.debug(f"trigger {trigger}")
            logger.warning(f"trigger_id {trigger_id}")

            filter_values = {
                'x_column': x_column_state,
                'series_column': series_column_state,
                'group_column': group_column_state,
                'main_insurer': main_insurer_state,
                'compare_insurers_main': compare_insurers_state,
                'primary_y_metric': primary_y_metric_state,
                'secondary_y_metric': secondary_y_metric_state,
                'premium_loss_checklist':premium_loss_selection_state,


            }
            logger.warning(f"main_insurer_state {main_insurer_state}")


            if trigger_id:
                is_series_stacked, show_percentage,
                if trigger_id in ['compare-insurers-main', 'category-state', 'selected-categories-store', 'category-dropdown', 'secondary-y-metric']:
                    updates = handle_column_updates(trigger_id, x_column_state, series_column_state, group_column_state, x_column, series_column, group_column, main_insurer_state, compare_insurers_state, primary_y_metric_state, secondary_y_metric_state, selected_linemains)
                elif trigger_id in ['x-column', 'series-column', 'group-column']:
                    updates = handle_axis_updates(trigger_id, x_column_state, series_column_state, group_column_state, x_column, series_column, group_column, main_insurer_state, compare_insurers_state, primary_y_metric_state, secondary_y_metric_state, selected_linemains)
                elif trigger_id == 'premium-loss-checklist':
                    updates = handle_premium_loss_updates(premium_loss_selection)
                elif trigger_id in ['show-reinsurance-chart', 'clear-filters-button']:
                    updates = handle_view_updates(show_reinsurance_chart, show_data_table_state)
                else:
                    updates = {}

                filter_values.update(updates)

            filter_state = filter_values | {  # Using Python 3.9+ merge operator |
                'show_reinsurance_chart': show_reinsurance_chart,
                'trigger_id': trigger_id,
                'selected_linemains': selected_linemains,
                'period_type': period_type,
                'start_quarter': start_quarter,
                'end_quarter': end_quarter,
                'quarter_value': quarter_value,
                'show_data_table': show_data_table_state,
                'number_of_insurers': number_of_insurers,
                'num_periods': num_periods,
                'num_periods_table': num_periods_table,
                'reinsurance_geography': reinsurance_geography,
                'reinsurance_form': reinsurance_form,
                'reinsurance_type': reinsurance_type,
                'show_data_table': show_data_table_state
            }

            # Return store data plus individual filter values
            output = [filter_state] + list(filter_values.values())

            logger.warning(f"output {output}")


            #default_returns['filter-state-store'] = store_data
            track_callback_end('app.main', 'update_filter_values', start_time) #, result=output)

            return outpu

        except Exception as e:
            logger.error(f"Error in update_filter_values: {str(e)}", exc_info=True)
            raise
        finally:
            track_callback_end('app.main', 'update_filter_values', start_time) #, result=output)


    @app.callback(
        [
            Output('options-store', 'data'),
            Output('x-column', 'options'),
            Output('series-column', 'options'),
            Output('group-column', 'options'),
            Output('primary-y-metric', 'options'),
            Output('secondary-y-metric', 'options')
        ],
        [
            Input('filter-state-store', 'data'),
        ],

        prevent_initial_call=True
    )
    @monitor_memory  # Add this decorator
    def update_options(filter_state):
        memory_monitor.log_memory("before_update_options", logger)  # Add this line
        ctx = dash.callback_contex
        start_time = track_callback('app.main', 'update_options', ctx)

        try:
            x_column=filter_state['x_column']
            series_column=filter_state['series_column']
            group_column=filter_state['group_column']
            primary_y_metric=filter_state['primary_y_metric']
            secondary_y_metric=filter_state['secondary_y_metric']
            premium_loss_selection=filter_state['premium_loss_checklist']
            show_reinsurance_chart=filter_state['show_reinsurance_chart']
            main_insurer=filter_state['main_insurer']
            compare_insurers=filter_state['compare_insurers_main']
            selected_linemains=filter_state['selected_linemains']

            if not ctx.triggered:
                track_callback_end('app.main', 'update_options', start_time, message_no_update="not ctx.triggered")
                raise PreventUpdate

            #snapshot1 = tracemalloc.take_snapshot()
            trigger = ctx.triggered[0]
            trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
            logger.debug(f"trigger {trigger}")
            logger.debug(f"trigger_id {trigger_id}")

            filter_options = {
                'x_column_options': dash.no_update,
                'series_column_options': dash.no_update,
                'group_column_options': dash.no_update,
                'primary_y_metric_options': dash.no_update,
                'secondary_y_metric_options': dash.no_update,
            }

            # Update column and metric options
            updates = get_column_options(trigger_id, show_reinsurance_chart, x_column, series_column, group_column, main_insurer, compare_insurers, primary_y_metric, secondary_y_metric, selected_linemains)
            updates = get_metric_options(primary_y_metric, secondary_y_metric, show_reinsurance_chart, premium_loss_selection)
            filter_options.update(updates)

            # Return store data plus individual filter values
            output = [{'filter_options': filter_options}] + list(filter_options.values())
            return outpu

        except Exception as e:
            logger.error(f"Error in update_options: {str(e)}", exc_info=True)
            raise


        finally:

            track_callback_end('app.main', 'update_options', start_time)



    @app.callback(
        [
            Output('processed-data-store', 'data'),
            Output('main-insurer', 'options'),
            Output('compare-insurers-main', 'options')
        ],
        [
            Input('filter-state-store', 'data')
        ],
        prevent_initial_call=True
    )
    @monitor_memory
    def process_data(
            filter_state, top_n_list=[5, 10, 20]):

        memory_monitor.log_memory("before_process_data", logger)
        try:
            if not filter_state:
                raise PreventUpdate

            trigger = dash.callback_context.triggered[0]
            trigger_id = trigger['prop_id'].split('.')[0]
            start_time = track_callback('app.main', 'process_data',
                                      dash.callback_context)

            processor = MetricsProcessor()
            logger.debug(f"Processing with parameters: {filter_state}")
            df, insurer_options, compare_options, selected_insurers, prev_ranks = (
                processor.process_general_filters(
                    df=reinsurance_df if filter_state['show_reinsurance_chart'] else insurance_df,
                    show_data_table=filter_state['show_data_table'],
                    premium_loss_selection=filter_state['premium_loss_checklist'],
                    selected_metrics=(filter_state['primary_y_metric'] or ['direct_premiums']) if filter_state['show_data_table'] else ((filter_state['primary_y_metric'] or []) + (filter_state['secondary_y_metric'] or [])),
                    selected_linemains=filter_state['selected_linemains'],
                    period_type=filter_state['period_type'],
                    start_quarter=filter_state['start_quarter'],
                    end_quarter=filter_state['end_quarter'],
                    num_periods=filter_state['num_periods'] if not filter_state['show_data_table'] else filter_state['num_periods_table'],
                    quarter_value=filter_state['quarter_value'],
                    chart_columns=[filter_state['x_column'], filter_state['series_column'], filter_state['group_column']],
                    selected_insurers=([filter_state['main_insurer']] + (filter_state['compare_insurers_main'] or [])) if not filter_state['show_data_table'] and not filter_state['show_reinsurance_chart'] else None,
                    reinsurance_form=filter_state['reinsurance_form'],
                    reinsurance_geography=filter_state['reinsurance_geography'],
                    reinsurance_type=filter_state['reinsurance_type'],
                    number_of_insurers=filter_state['number_of_insurers'],
                    main_insurer=filter_state['main_insurer'],
                    top_n_list=top_n_lis
                )
            )
            #logger.error(f"head {df.head()}")
            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            output = {'df': df.to_dict('records'), 'prev_ranks': prev_ranks}, insurer_options, compare_options
            track_callback_end('app.main', 'process_data', start_time) #, result=output)
            #logger.error(f"heoutputad {output}")
            #logger.info(f"Output DataFrame shape: {df.shape}")
            #logger.info(f"Output DataFrame columns: {df.columns}")
            #logger.info(f"Sample data: {df.head()}")
            return outpu

        except Exception as e:
            logger.info(f"Error in process_data: {str(e)}", exc_info=True)
            raise

        finally:

            track_callback_end('app.main', 'process_data', start_time)


    @app.callback(
        [
            Output('data-table', 'children'),
            Output('table-title-row1', 'children'),
            Output('table-title-row2', 'children'),
            Output('stored-charts-container', 'children'),
            Output('chart-count', 'data'),
            Output('working-chart-container', 'children')
        ],
        [
            Input('processed-data-store', 'data'),
            Input('filter-state-store', 'data'),
            Input('primary-chart-type', 'value'),
            Input('secondary-chart-type', 'value'),
            Input('group-series-toggle', 'value'),
            Input('stacking-groups-toggle', 'value'),
            Input('stacking-series-toggle', 'value'),
            Input('show-percentage-toggle', 'value'),
            Input('show-100-percent-toggle', 'value'),
            Input('random-color-toggle', 'value'),
            Input('store-chart-button', 'n_clicks'),
            Input('clear-charts-button', 'n_clicks'),
            Input('toggle-selected-market-share', 'value'),
            Input('toggle-selected-qtoq', 'value'),
            Input('toggle-additional-market-share', 'value'),
            Input('toggle-additional-qtoq', 'value')

        ],
        [
            State('chart-count', 'data'),
            State('stored-charts-container', 'children'),
            State('working-chart-container', 'children')
        ],
        prevent_initial_call=True
    )
    @monitor_memory  # Add this decorator

    def process_ui(
            processed_data, filter_state,
              primary_chart_type, secondary_chart_type, group_by_series,
              is_groups_stacked, is_series_stacked, show_percentage,
              show_100_percent, random_color, create_clicks, clear_clicks,
              toggle_selected_market_share, toggle_selected_qtoq,
              toggle_additional_market_share, toggle_additional_qtoq,
              chart_count, stored_charts, working_chart):
        """Update UI elements based on processed data."""
        memory_monitor.log_memory("before_process_ui", logger)  # Add this line
        if not processed_data or not filter_state:
            raise PreventUpdate

        try:


            ctx = dash.callback_contex

            start_time = track_callback('app.main', 'process_ui', ctx)
            trigger = dash.callback_context.triggered[0]
            trigger_id = trigger['prop_id'].split('.')[0]
            logger.debug(f"head {trigger_id}")


            df = pd.DataFrame.from_records(processed_data['df'])
            #logger.error(f"trigger_id {df.head()}")

            df['year_quarter'] = pd.to_datetime(df['year_quarter'])

            #logger.error(f"trigger_id {df.head()}")
            default_returns = OrderedDict([
                ('data_table', dash.no_update),
                ('table_title_row1', dash.no_update),
                ('table_title_row2', dash.no_update),
                ('stored_charts_container', stored_charts or []),
                ('chart_count', chart_count or 0),
                ('working_chart_container', working_chart or html.Div())
            ])



            # Handle table or chart display
            if filter_state['show_data_table']:
                table_data = get_data_table(
                    df=df,
                    table_selected_metric=filter_state['primary_y_metric'],
                    selected_linemains=filter_state['selected_linemains'],
                    period_type=filter_state['period_type'],
                    number_of_insurers=filter_state['number_of_insurers'],
                    toggle_selected_market_share=toggle_selected_market_share,
                    toggle_selected_qtoq=toggle_selected_qtoq,
                    toggle_additional_market_share=toggle_additional_market_share,
                    toggle_additional_qtoq=toggle_additional_qtoq,
                    prev_ranks=processed_data['prev_ranks']
                )
                default_returns.update({
                    'data_table': table_data[0],
                    'table_title_row1': table_data[1],
                    'table_title_row2': table_data[2]
                })

            else:
                # Create chart using ChartManager

                chart_data = get_chart_data(
                    df=df,
                    selected_metrics=(filter_state['primary_y_metric'] or ['direct_premiums']) if filter_state['show_data_table'] else ((filter_state['primary_y_metric'] or []) + (filter_state['secondary_y_metric'] or [])),
                    selected_linemains=filter_state['selected_linemains'],
                    premium_loss_selection=filter_state['premium_loss_checklist'],
                    period_type=filter_state['period_type'],
                    x_column=filter_state['x_column'],
                    series_column=filter_state['series_column'],
                    group_column=filter_state['group_column'],
                    start_quarter=filter_state['start_quarter'],
                    end_quarter=filter_state['end_quarter'],
                    num_periods=filter_state['num_periods'],
                    is_groups_stacked=is_groups_stacked,
                    is_series_stacked=is_series_stacked,
                    group_by_series=group_by_series,
                    main_insurer=['total'] if filter_state['show_reinsurance_chart']
                        else filter_state['main_insurer'],
                    selected_insurers=([filter_state['main_insurer']] + (filter_state['compare_insurers_main'] or [])) if not filter_state['show_data_table'] and not filter_state['show_reinsurance_chart'] else ['total'],
                    number_of_insurers=filter_state['number_of_insurers'],
                    reinsurance_form=filter_state['reinsurance_form'],
                    reinsurance_geography=filter_state['reinsurance_geography'],
                    reinsurance_type=filter_state['reinsurance_type'],
                    top_n_list=[5, 10, 20]
                )

                chart_figure = create_chart(
                    chart_data=chart_data,
                    premium_loss_selection=filter_state['premium_loss_checklist'],
                    selected_linemains=filter_state['selected_linemains'],
                    primary_y_metric=filter_state['primary_y_metric'],
                    primary_chart_type=primary_chart_type,
                    period_type=filter_state['period_type'],
                    start_quarter=filter_state['start_quarter'],
                    end_quarter=filter_state['end_quarter'],
                    main_insurer=filter_state['main_insurer'],
                    compare_insurers=filter_state['compare_insurers_main'],
                    secondary_y_metric=filter_state['secondary_y_metric'],
                    secondary_chart_type=secondary_chart_type,
                    is_groups_stacked=is_groups_stacked,
                    is_series_stacked=is_series_stacked,
                    show_percentage=show_percentage,
                    show_100_percent=show_100_percent,
                    group_by_series=group_by_series,
                    x_column=filter_state['x_column'],
                    series_column=filter_state['series_column'],
                    group_column=filter_state['group_column'],
                    random_color=random_color
                )


                working_chart = html.Div(
                    dcc.Graph(
                        id={'type': 'dynamic-chart', 'index': f'chart-{chart_count}'},
                        figure=chart_figure,
                        style={'height': '700px'}
                    ),
                    className='working-chart'
                )

                if trigger_id == 'clear-charts-button':
                    stored_charts, chart_count = [], 0
                elif trigger_id == 'store-chart-button':
                    chart_count = (chart_count or 0) + 1
                    stored_charts = (stored_charts or []) + [working_chart]

                default_returns.update({
                    'stored_charts_container': stored_charts,
                    'chart_count': chart_count,
                    'working_chart_container': working_char
                })
            #logger.info(chart_figure)
            logger.warning(f"Returnung main output")


            return list(default_returns.values())



        except Exception as e:
            logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
            raise

        finally:



            track_callback_end('app.main', 'process_ui', start_time)

    return app

if __name__ == '__main__':
    try:
        print("Starting application initialization...")
        app = main()
        print("Starting server...")
        app.run_server(debug=DEBUG_MODE, port=PORT)
    except Exception as e:
        print(f"Error during startup: {e}")
        raise