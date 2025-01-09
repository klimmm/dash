

    logger.debug(f"main insurer: {main_insurer}")
    logger.debug(f"x_column: {x_column}")
    logger.debug(f"x_column: {x_column}")


    logger.debug(f"type(df): {type(df)}")


    '''if 'insurer' in chart_columns and main_insurer != ['total']:

        df = add_total_top_bench_rows(df, main_insurer, top_n_insurers, selected_insurers, end_quarter, top_n_list)

    else:
        logger.debug(f"column insurer not in requested chart_columns, proceeding without adding benchmark insurers.")'''
    duplicates = df[df.duplicated()]
    logger.debug(f"dublicates: {duplicates}")
        logger.debug(f" column linemain is in requested chart_columns, filtering out all_lines.")
        logger.debug(f"column linemain not in requested chart_columns, keeping only all_lines")

    logger.debug(f"dublicates: {df[df.duplicated()]}")
    logger.debug(f"Unique lines df after filtering for line column: {df['linemain'].unique().tolist()}")
    logger.debug(f"Unique values df after filtering for line column: {df['value'].unique().tolist()}")


        logger.debug(f"There are market_share metrics in selected metrics, calculating market share metrics.")
    else:
        logger.debug(f"No market_share metrics in selected metrics, proceeding without calculating market share metrics.")
    logger.debug(f"dublicates: {df[df.duplicated()]}")
    logger.debug(f"Unique insurers after market share {df['insurer'].unique().tolist()}")


    logger.debug(f"Unique metrics df after checking for market share metrics in selected metrics: {df['metric'].unique().tolist()}")
    logger.debug(f"Unique values df after checking for market share metrics in selected metrics: {df['value'].unique().tolist()}")

    logger.debug(f"dublicates: {df[df.duplicated()]}")
    logger.debug(f"Unique insurer df after checking for market share metrics in selected metrics: {df['insurer'].unique().tolist()}")

        logger.debug(f"There are selected metrics not in base metrics.")
    else:
        logger.debug(f"All selected metrics are in base metrics")
    logger.debug(f"unique metricv alues : {df['metric'].unique()}")
    logger.info(f"Unique insurer df after averages_and_ratio: {df['insurer'].unique().tolist()}")

    logger.debug(f"Unique metrics df after averages_and_ratio: {df['metric'].unique().tolist()}")
    logger.debug(f"Unique value df after averages_and_ratios: {df['value'].unique().tolist()}")

    logger.debug(f"dublicates: {df[df.duplicated()]}")

    logger.debug(f"unique metricv alues before add_growth_rows_long: {df['metric'].unique()}")
        logger.debug(f"There are q_to_q_change metrics in selected metrics, calculating q_to_q change metrics.")

    else:
         logger.debug(f"No q_to_q_change metrics in selected metrics, proceeding without calculating q_to_q change metrics.")
    logger.debug(f"unique metricv alues after add_growth_rows_long: {df['metric'].unique()}")

    #df = df.sort_values(by='year_quarter', ascending=False)

    #df = df[df['year_quarter'].isin(df['year_quarter'].unique()[:num_periods])]

    # Extract years and get N most recent unique years

    logger.debug(f"unique metricv alues : {df['metric'].unique()}")


    #current_date = datetime.now()
    #cutoff_date = current_date - timedelta(days=365 * num_periods)

    #df = df[df['year_quarter'] >= cutoff_date]

    logger.info(f"unique insdurers before filter for insurers alues : {df['insurer'].unique()}")
    logger.info(f"selected_insurerss : {selected_insurers}")

    logger.info(f"Unique value df before qchecking for insurers: {df['value'].unique().tolist()}")
        logger.debug(f" column insurer is in requested chart_columns, filtering for selected_insurers.")

        logger.debug(f"column insurer not in requested chart_columns, proceed with filtering for main insurer.")
        logger.info(f"Unique insurer df after add aver: {df['insurer'].unique().tolist()}")

        #if 'linemain' in chart_columns:
        #    df = df[df['insurer'] == main_insurer] if main_insurer in df['insurer'].unique() else df[df['insurer'] == 'total']


    duplicates = df[df.duplicated()]
    logger.debug(f"dublicates: {duplicates}")


    logger.info(f"Unique value df after qchecking for linamain: {df['value'].unique().tolist()}")
    duplicates = df[df.duplicated()]
    logger.debug(f"dublicates: {duplicates}")

    logger.info(f"unique metricv alues : {df['metric'].unique()}")
    logger.info(f"selected_metrics m : {selected_metrics}")

        logger.debug(f" column metric is in requested chart_columns, filtering for selected_metrics.")
        logger.debug(f"main_metric: {main_metric}")

            logger.debug(f" no main metric in unique metric values, filtering for 'total'")

            logger.warning(f" no main metric in unique insurer values, filtering for 'total_premiums")

    logger.info(f"Unique value df after qchecking for metric: {df['insurer'].unique().tolist()}")
    duplicates = df[df.duplicated()]
    logger.debug(f"dublicates: {duplicates}")
    #unique_years = df['year_quarter'].dt.year.unique()
    #years_to_keep = sorted(unique_years, reverse=True)[:num_periods]

    # Filter the DataFrame
    #df = df[df['year_quarter'].dt.year.isin(years_to_keep)]
        logger.warning(f" year_quarter not in in requested chart_columns, keeping the most recent date only")

    duplicates = df[df.duplicated()]
    logger.debug(f"dublicates: {duplicates}")


    logger.info(f"Unique value df after qchecking for metric: {df['insurer'].unique().tolist()}")
    logger.debug(f"columns after percent calc by chart columns: {df.columns}")

    logger.info(f"Unique insurer df after aggregate_based_on_chart_cols: {df['insurer'].unique().tolist()}")


    logger.info(f"Unique insurer df after chart data: {df['insurer'].unique().tolist()}")

    logger.debug(f"columns after percent calc by chart columns: {chart_data.columns}")

    logger.debug(f"x_column: {x_column}")
    logger.debug(f"series_column: {series_column}")
    logger.debug(f"group_column: {group_column}")
    logger.debug(f"columns before aggregating by chart columns: {df.columns}")
    logger.info(f"Unique values in year_quarter: {df['insurer'].unique().tolist()}")

    logger.debug(f"Unique values in year_quarter: {df['year_quarter'].unique().tolist()}")

    logger.debug(f"unique quarter values before aggregating by chart columns: {df['quarter'].unique()}")
    logger.debug(f"unique year values before aggregating by chart columns: {df['year'].unique()}")

    logger.info(f"columns before agg by chart columns: {df.columns}")
    logger.info(f"Unique values in in x_column: {df[x_column].unique().tolist()}")
    logger.info(f"Unique values in in series_column: {df[series_column].unique().tolist()}")
    logger.info(f"Unique values in in group_column: {df[group_column].unique().tolist()}")

    # Get all columns from the DataFrame

    #group_columns = [col for col in df.columns if col in [x_column, series_column, group_column]]
    #logger.debug(f"group_columns: {group_columns}")

    #df = df.groupby(group_columns)['value'].sum().reset_index()
        logger.debug(f" column metric in requested chart_columns, filtering for main_metric")
        logger.info(f"main_metric: {main_metric}")
        logger.info(f"unique metricv alues : {df['metric'].unique()}")


    # Define the columns to group by
    # Define the columns to group by
    # Define the columns to group by
    # Define the columns to group by
    # Define the columns to group by

    logger.debug(f"columns after_agg by chart columns: {df.columns}")
    logger.debug(f"Unique values in in x_column after_agg: {df[x_column].unique().tolist()}")
    logger.debug(f"Unique values in in series_column after_agg: {df[series_column].unique().tolist()}")
    logger.debug(f"Unique values in in group_column after_agg: {df[group_column].unique().tolist()}")
    #logger.debug(f"unique quarter values after aggregating by chart columns: {df['quarter'].unique()}")
    #logger.debug(f"unique year values after aggregating by chart columns: {df['year'].unique()}")

    logger.debug(f"x_column: {x_column}")
    logger.debug(f"series_column: {series_column}")
    logger.debug(f"group_column: {group_column}")
    logger.debug(f"is_groups_stacked: {is_groups_stacked}")
    logger.debug(f"is_series_stacked: {is_series_stacked}")
    logger.debug(f"group_by_series: {group_by_series}")

    logger.debug(f"columns before percent calc by chart columns: {df.columns}")

    df = df.copy()
    logger.debug(f"columns after percent calc by chart columns: {df.columns}")

    logger.debug(f"columns after percent calc by chart columns: {df.columns}")
    logger.debug(f"columns after percent calc by chart columns: {df.columns}")
    logger.debug(f"columns after percent calc by chart columns: {df.columns}")



        logger.debug(f"selected_linemains {selected_linemains}")



        logger.error(f"period_type  {period_type}")
        logger.error(f"num_periods  {num_periods}")
        logger.error(f"start_quarter  {start_quarter}")
        logger.error(f"end_quarter  {end_quarter}")
        logger.error(f"end_quarter  {end_quarter}")
        logger.error(f"quarter_value  {quarter_value}")
        logger.error(f"series_column  {series_column}")
        logger.error(f"group_column  {group_column}")
        logger.error(f"main_insurer  {main_insurer}")
        logger.error(f"compare_insurers  {compare_insurers}")
        logger.error(f"primary_y_metric  {primary_y_metric}")
        logger.error(f"secondary_y_metric  {secondary_y_metric}")
        logger.error(f"premium_loss_selection  {premium_loss_selection}")

        '''logger.debug(f" chart_selected_metric  {chart_selected_metric}")
        logger.debug(f"table_selected_metric   {table_selected_metric}")
        logger.debug(f"selected_insurers  {selected_insurers}")
        logger.debug(f"main_insurer after_process_inputs {main_insurer}")
        logger.debug(f"compare_insurers after_process_inputs  {compare_insurers}")
        logger.debug(f"primary_y_metric after_process_inputs {primary_y_metric}")
        logger.debug(f"secondary_y_metric after_process_inputs  {secondary_y_metric}")
        logger.debug(f"chart_columns  {chart_columns}")'''

                    logger.error(f"period_type {filter_state['period_type']}")
            logger.error(f"num_periods  {num_periods}")
            logger.error(f"start_quarter  {filter_state['start_quarter']}")
            logger.error(f"end_quarter  {filter_state['end_quarter']}")
            logger.error(f"quarter_value  {filter_state['quarter_value']}")
            logger.error(f"number_of_insurers  {number_of_insurers}")
            #logger.error(f"series_column  {series_column}")
            #logger.error(f"group_column  {group_column}")
            logger.error(f"selected_insurers  {selected_insurers}")
            logger.error(f"table_selected_metric  {table_selected_metric}")
            logger.error(f"main_insurer  {main_insurer}")
            logger.error(f"chart_columns  {chart_columns}")
            logger.error(f"table_selected_metric  {table_selected_metric}")
            logger.error(f"chart_selected_metric  {chart_selected_metric}")
            logger.error(f"premium_loss_selection  {filter_values['premium_loss_checklist']}")
            logger.error(f"selected_linemains  {filter_state['selected_linemains']}")
        #logger.debug(f"selected_insurers {selected_insurers}")