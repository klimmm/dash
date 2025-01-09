from app import *
from data_process.update_filter_options import *


def create_dash_app() -> dash.Dash:
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    app.title = APP_TITLE
    return app

def main():
    # Initialize logging and debug level
    setup_logging(console_level=logging.INFO, file_level=logging.DEBUG)
    set_debug_level(DebugLevels.VERBOSE)
    logger = get_logger(__name__)

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
        dcc.Store(id='chart-options-store')
    ])

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
            Input('compare-insurers-main', 'value'),
            Input('primary-y-metric', 'value'),
            Input('secondary-y-metric', 'value'),
            Input('premium-loss-checklist', 'value'),
            Input('clear-filters-button', 'n_clicks'),
            Input('period-type', 'data'),
            Input('start-quarter', 'value'),
            Input('end-quarter', 'value'),
            Input('quarter-value-output', 'data'),
            Input('category-state', 'data')
        ],
        [
            State('x-column', 'value'),
            State('series-column', 'value'),
            State('group-column', 'value'),
            State('main-insurer', 'value'),
            State('compare-insurers-main', 'value'),
            State('primary-y-metric', 'value'),
            State('secondary-y-metric', 'value'),
            State('show-data-table', 'data')
        ],
        prevent_initial_call=True
    )
    def update_filter_values(
            show_reinsurance_chart, x_column, series_column, group_column,
            compare_insurers, primary_y_metric, secondary_y_metric,
            premium_loss_selection, clear_filters_btn, period_type,
            start_quarter, end_quarter, quarter_value, selected_linemains,
            x_column_state, series_column_state, group_column_state,
            main_insurer_state, compare_insurers_state,
            primary_y_metric_state, secondary_y_metric_state,
            show_data_table_state):

        try:
            if not dash.callback_context.triggered:
                raise PreventUpdate

            trigger = dash.callback_context.triggered[0]
            trigger_id = trigger['prop_id'].split('.')[0]

            default_returns = OrderedDict([
                ('filter-state-store', dash.no_update),
                ('x_column', dash.no_update),
                ('series_column', dash.no_update),
                ('group_column', dash.no_update),
                ('main_insurer', dash.no_update),
                ('compare_insurers_main', dash.no_update),
                ('primary_y_metric', dash.no_update),
                ('secondary_y_metric', dash.no_update),
                ('premium_loss_checklist', dash.no_update)
            ])

            chart_columns = [x_column, series_column, group_column]

            if trigger_id in ['compare-insurers-main', 'selected-categories-store', 'secondary-y-metric']:
                updates = handle_column_updates(trigger_id, chart_columns, selected_linemains)
                if 'group_column' in updates:
                    group_column = updates['group_column']
                default_returns.update(updates)

            elif trigger_id in ['x-column', 'series-column', 'group-column']:
                updates = handle_axis_updates(
                    trigger_id, x_column_state, series_column_state,
                    group_column_state, x_column, series_column, group_column
                )
                if 'x_column' in updates:
                    x_column = updates['x_column']
                if 'series_column' in updates:
                    series_column = updates['series_column']
                if 'group_column' in updates:
                    group_column = updates['group_column']
                default_returns.update(updates)

            elif trigger_id == 'premium-loss-checklist':
                updates = handle_premium_loss_updates(premium_loss_selection)
                if 'primary_y_metric' in updates:
                    primary_y_metric = updates['primary_y_metric']
                if 'secondary_y_metric' in updates:
                    secondary_y_metric = updates['secondary_y_metric']
                default_returns.update(updates)

            elif trigger_id in ['show-reinsurance-chart', 'clear-filters-button']:
                updates = handle_view_updates(show_reinsurance_chart, show_data_table_state)
                x_column = updates['x_column']
                series_column = updates['series_column']
                group_column = updates['group_column']
                main_insurer = updates['main_insurer']
                compare_insurers = updates['compare_insurers_main']
                primary_y_metric = updates['primary_y_metric']
                secondary_y_metric = updates['secondary_y_metric']
                premium_loss_selection = updates['premium_loss_checklist']
                default_returns.update(updates)

            store_data = {
                'filter_values': {
                    'x_column': x_column,
                    'series_column': series_column,
                    'group_column': group_column,
                    'main_insurer': main_insurer_state if 'main_insurer' not in locals() else main_insurer,
                    'compare_insurers_main': compare_insurers,
                    'primary_y_metric': primary_y_metric,
                    'secondary_y_metric': secondary_y_metric,
                    'premium_loss_checklist': premium_loss_selection
                },
                'show_reinsurance_chart': show_reinsurance_chart,
                'trigger_id': trigger_id,
                'selected_linemains': selected_linemains,
                'period_type': period_type,
                'start_quarter': start_quarter,
                'end_quarter': end_quarter,
                'quarter_value': quarter_value,
                'show_data_table': show_data_table_state
            }

            default_returns['filter-state-store'] = store_data

            return list(default_returns.values())

        except Exception as e:
            logger.error(f"Error in update_filter_values: {str(e)}", exc_info=True)
            raise
    # Callback 2: Process data and update options
    @app.callback(
        [
            Output('processed-data-store', 'data'),
            Output('data-table', 'children'),
            Output('table-title-row1', 'children'),
            Output('table-title-row2', 'children'),
            Output('stored-charts-container', 'children'),
            Output('chart-count', 'data'),
            Output('working-chart-container', 'children'),
            Output('x-column', 'options'),
            Output('series-column', 'options'),
            Output('group-column', 'options'),
            Output('main-insurer', 'options'),
            Output('compare-insurers-main', 'options'),
            Output('primary-y-metric', 'options'),
            Output('secondary-y-metric', 'options')
        ],
        [
            Input('filter-state-store', 'data'),
            Input('show-data-table', 'data'),
            Input('number-of-insurers', 'value'),
            Input('number-of-years-to-show', 'data'),
            Input('reinsurance-geography-dropdown', 'value'),
            Input('reinsurance-form-dropdown', 'value'),
            Input('reinsurance-type-dropdown', 'value'),
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
            Input('toggle-additional-qtoq', 'value'),
            Input('number-of-periods-data-table', 'value')
        ],
        [
            State('chart-count', 'data'),
            State('stored-charts-container', 'children')
        ],
        prevent_initial_call=True
    )
    def process_data_and_update_options(
            filter_state, show_data_table, number_of_insurers, num_periods,
            reinsurance_geography, reinsurance_form, reinsurance_type,
            primary_chart_type, secondary_chart_type, group_by_series,
            is_groups_stacked, is_series_stacked, show_percentage,
            show_100_percent, random_color, create_clicks, clear_clicks,
            toggle_selected_market_share, toggle_selected_qtoq,
            toggle_additional_market_share, toggle_additional_qtoq,
            num_periods_table, chart_count, stored_charts):

        try:
            if not filter_state:
                raise PreventUpdate

            tracemalloc.start()
            snapshot1 = tracemalloc.take_snapshot()
            start_time = track_callback('app.main', 'process_data_and_update_options', dash.callback_context)

            default_returns = OrderedDict([
                ('processed_data', dash.no_update),
                ('data_table', dash.no_update),
                ('table_title_row1', dash.no_update),
                ('table_title_row2', dash.no_update),
                ('stored_charts_container', stored_charts or []),
                ('chart_count', chart_count or 0),
                ('working_chart_container', html.Div()),
                ('x_column_options', dash.no_update),
                ('series_column_options', dash.no_update),
                ('group_column_options', dash.no_update),
                ('main_insurer_options', dash.no_update),
                ('compare_insurers_main_options', dash.no_update),
                ('primary_y_metric_options', dash.no_update),
                ('secondary_y_metric_options', dash.no_update)
            ])

            filter_values = filter_state['filter_values']
            show_reinsurance_chart = filter_state['show_reinsurance_chart']

            # Process metrics and filters
            primary_y_metric, secondary_y_metric, chart_selected_metric, table_selected_metric,
            main_insurer, compare_insurers, selected_insurers, chart_columns = process_inputs(
                filter_values['primary_y_metric'],
                filter_values['secondary_y_metric'],
                filter_values['main_insurer'],
                filter_values['compare_insurers_main'],
                filter_values['x_column'],
                filter_values['series_column'],
                filter_values['group_column']
            )

            # Update column and metric options
            updates = get_column_options(
                filter_values['x_column'],
                filter_values['series_column'],
                filter_values['group_column'],
                show_reinsurance_char
            )
            default_returns.update(updates)

            updates = get_metric_options(
                primary_y_metric,
                secondary_y_metric,
                table_selected_metric,
                show_reinsurance_chart,
                filter_values['premium_loss_checklist']
            )
            default_returns.update(updates)

            # Process data
            df = insurance_df if not show_reinsurance_chart else reinsurance_df
            processor = MetricsProcessor()

            df, insurer_options, compare_options, selected_insurers, prev_ranks = processor.process_general_filters(
                df=df,
                show_data_table=show_data_table,
                premium_loss_selection=filter_values['premium_loss_checklist'],
                selected_metric=(table_selected_metric or ['direct_premiums']) if show_data_table else chart_selected_metric,
                selected_linemains=filter_state['selected_linemains'],
                period_type=filter_state['period_type'],
                start_quarter=filter_state['start_quarter'],
                end_quarter=filter_state['end_quarter'],
                quarter_value=filter_state['quarter_value'],
                chart_columns=chart_columns,
                selected_insurers=selected_insurers if not show_data_table and not show_reinsurance_chart else None,
                reinsurance_form=reinsurance_form,
                reinsurance_geography=reinsurance_geography,
                reinsurance_type=reinsurance_type,
                number_of_insurers=number_of_insurers,
                main_insurer=main_insurer
            )

            default_returns.update({
                'main_insurer_options': insurer_options,
                'compare_insurers_main_options': compare_options
            })

            trigger = dash.callback_context.triggered[0]
            trigger_id = trigger['prop_id'].split('.')[0]

            # Handle table or chart display
            if show_data_table:
                table_data = get_data_table(
                    df=df,
                    selected_metric=table_selected_metric,
                    selected_linemains=filter_state['selected_linemains'],
                    period_type=filter_state['period_type'],
                    number_of_insurers=number_of_insurers,
                    toggle_selected_market_share=toggle_selected_market_share,
                    toggle_selected_qtoq=toggle_selected_qtoq,
                    toggle_additional_market_share=toggle_additional_market_share,
                    toggle_additional_qtoq=toggle_additional_qtoq,
                    prev_ranks=prev_ranks
                )
                default_returns.update({
                    'data_table': table_data[0],
                    'table_title_row1': table_data[1],
                    'table_title_row2': table_data[2]
                })
            else:
                chart_data = get_chart_data(
                    df=df,
                    selected_metric=chart_selected_metric,
                    selected_linemains=filter_state['selected_linemains'],
                    premium_loss_selection=filter_values['premium_loss_checklist'],
                    period_type=filter_state['period_type'],
                    x_column=filter_values['x_column'],
                    series_column=filter_values['series_column'],
                    group_column=filter_values['group_column'],
                    start_quarter=filter_state['start_quarter'],
                    end_quarter=filter_state['end_quarter'],
                    num_periods=num_periods,
                    is_groups_stacked=is_groups_stacked,
                    is_series_stacked=is_series_stacked,
                    group_by_series=group_by_series,
                    main_insurer=['total'] if show_reinsurance_chart else main_insurer,
                    selected_insurers=selected_insurers,
                    number_of_insurers=number_of_insurers,
                    reinsurance_form=reinsurance_form,
                    reinsurance_geography=reinsurance_geography,
                    reinsurance_type=reinsurance_type
                )

                chart_figure = create_chart(
                    data=chart_data,
                    premium_loss_selection=filter_values['premium_loss_checklist'],
                    selected_linemains=filter_state['selected_linemains'],
                    primary_y_metric=primary_y_metric,
                    primary_chart_type=primary_chart_type,
                    period_type=filter_state['period_type'],
                    start_quarter=filter_state['start_quarter'],
                    end_quarter=filter_state['end_quarter'],
                    main_insurer=main_insurer,
                    compare_insurers=compare_insurers,
                    secondary_y_metric=secondary_y_metric,
                    secondary_chart_type=secondary_chart_type,
                    is_groups_stacked=is_groups_stacked,
                    is_series_stacked=is_series_stacked,
                    show_percentage=show_percentage,
                    show_100_percent=show_100_percent,
                    group_by_series=group_by_series,
                    x_column=filter_values['x_column'],
                    series_column=filter_values['series_column'],
                    group_column=filter_values['group_column'],
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

            # Store processed data
            default_returns['processed_data'] = {
                'df': df.to_dict('records'),
                'selected_insurers': selected_insurers,
                'prev_ranks': prev_ranks
            }

            return list(default_returns.values())

        except Exception as e:
            logger.error(f"Error in process_data_and_update_options: {str(e)}", exc_info=True)
            raise

        finally:
            snapshot2 = tracemalloc.take_snapshot()
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            logger.info("[ Top 10 memory differences ]")
            for stat in top_stats[:10]:
                logger.info(stat)
            tracemalloc.stop()
            track_callback_end('app.main', 'process_data_and_update_options', start_time)

    return app

if __name__ == '__main__':
    app = main()
    app.run_server(debug=DEBUG_MODE, port=PORT)