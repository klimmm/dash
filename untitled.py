

def _setup_filter_update_callbacks(app: Dash, quarter_options_162, quarter_options_158) -> None:
    @app.callback(
        [Output('primary-y-metric', 'options'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value'),
         Output('end-quarter', 'options'),
         Output('insurance-line-dropdown', 'options'),
         Output('premium-loss-checklist-container', 'children'),
         Output('filter-state-store', 'data')],
        [
         Input('reporting-form', 'data'),
         Input('primary-y-metric', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('premium-loss-checklist', 'value'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data'),
         Input('end-quarter', 'value')],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')],  # Add filter state store state
        prevent_initial_call=True
    )
    def update_options(
            reporting_form,
            primary_metric,
            secondary_metric,
            current_values,
            lines, 
            period_type,
            end_quarter,
            num_periods_selected: int,
            show_table, 
            current_filter_state,
            line_type: List[str] = None
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



            

            # Update filter state with new values
            filter_state = current_filter_state or {}
            updated_filter_state = {
                **filter_state,
                'primary_y_metric': primary_metric_value,
                'secondary_y_metric': secondary_metric_value,
                'selected_metrics': selected_metrics,
                'premium_loss_checklist': values or [],
                'selected_lines': lines,
                'show_data_table': bool(show_table),
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
                updated_filter_state  # Include updated filter state in output
            )
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, result=output)
            return output
        except Exception as e:
            logger.error(f"Error in update_options: {str(e)}", exc_info=True)
            track_callback_end('app.callbacks.filter_update_callbacks', 'update_options', start_time, error=str(e))
            raise

def _setup_data_processing_callback(app: dash.Dash, data_store: InsuranceDataStore):
    @app.callback(
        Output('processed-data-store', 'data'),
        [Input('filter-state-store', 'data'),
         Input('selected-insurers', 'value'),
         Input('number-of-periods-data-table', 'data'),
         Input('number-of-insurers', 'data'),
         Input('end-quarter', 'value')],
        State('show-data-table', 'data'),
        prevent_initial_call=True
    )
    def prepare_cached_data(
        filter_state: Dict[str, Any],
        selected_insurers: List[str],
        num_periods_selected: int,
        number_of_insurers: int,
        end_quarter: str,
        show_data_table: bool,
        line_type: List[str] = None
    ) -> Dict:
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE
        """
        ctx = dash.callback_context
        start_time = track_callback('main', 'prepare_grouped_data', ctx)
        memory_monitor.log_memory("before_prepare_data", logger)
        if not ctx.triggered:
            track_callback_end('main', 'process_data', start_time)
            raise PreventUpdate

        try:

            if not filter_state or not all([
                filter_state.get('period_type'),
                filter_state.get('selected_metrics', []),
                filter_state.get('premium_loss_checklist', []),
                filter_state.get('selected_lines', [])
            ]):
                logger.warning("Invalid filter state")
                output = {'df': [], 'prev_ranks': {}}
                return output

            # Get and filter base data
            # df = data_store.get_dataframe(filter_state['reporting_form'])

            # end_quarter_ts = pd.Period(end_quarter, freq='Q').to_timestamp(how='end')

            # Apply filters
            '''mask = df['year_quarter'] <= end_quarter_ts
            if line_type:
                mask &= df['line_type'].isin(line_type)

            df = df[mask]'''

            # Group data
            '''group_cols = [col for col in df.columns if col not in ('line_type', 'value')]
            df = df.groupby(group_cols, observed=True)['value'].sum().reset_index()

            if df.empty:
                output = {'df': [], 'prev_ranks': {}}
                return output'''

            # Apply filters and calculate metrics
           ''' df = (df[df['linemain'].isin(filter_state['selected_lines'])]
                   .pipe(lambda x: x[x['metric'].isin(
                       get_required_metrics(
                           filter_state['selected_metrics'],
                           filter_state['premium_loss_checklist']
                       )
                   )])
                   .pipe(filter_by_date_range_and_period_type,
                         period_type=filter_state['period_type']))'''

            '''if df.empty:
                output = {'df': [], 'prev_ranks': {}}
                return output'''

            # Process periods
            # periods = sorted(df['year_quarter'].unique(), reverse=True)
            '''if not periods:
                output = {'df': [], 'prev_ranks': {}}
                return output'''

            '''periods_to_keep = periods[:min(num_periods_selected, len(periods)) + 1]
            df = df[df['year_quarter'].isin(periods_to_keep)]'''

            # Process insurers
            latest_quarter = df['year_quarter'].max()
            num_insurers = min(
                number_of_insurers,
                len(df[df['year_quarter'] == latest_quarter]['insurer'].unique())
            )

            df, prev_ranks = process_insurers_data(
                df=df,
                selected_insurers=selected_insurers,
                top_n_list=[5, 10, 20],
                show_data_table=show_data_table,
                selected_metrics=filter_state['selected_metrics'],
                number_of_insurers=num_insurers
            )

            # Calculate metrics
            df = calculate_metrics(
                df,
                filter_state['selected_metrics'],
                filter_state['premium_loss_checklist']
            )

            logger.debug(f"metrics {df['metric'].unique()}")
            logger.debug(f"selected_metrics {filter_state['selected_metrics']}")

            # Filter the DataFrame based on selected metrics
            df = df[df['metric'].isin(filter_state['selected_metrics'])]

            # Add market share rows
            df = add_market_share_rows(
                df,
                selected_insurers,
                filter_state['selected_metrics'],
                show_data_table
            )

            # Add growth rows
            df = add_growth_rows(
                df,
                selected_insurers,
                show_data_table,
                num_periods_selected,
                filter_state['period_type']
            )

            # Format dates
            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            output = {
                'df': df.to_dict('records'),
                'prev_ranks': prev_ranks
            }

            return output

        except Exception as e:
            logger.error(f"Error in prepare_cached_data: {str(e)}", exc_info=True)
            track_callback_end('main', 'process_data', start_time, error=str(e))
            output = {'df': [], 'prev_ranks': {}}
            return output

        finally:
            track_callback_end('main', 'process_data', start_time, result=output)
