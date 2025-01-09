process_dataframe.py

    df = filter_by_date_range_and_period_type(
            df, period_type, start_quarter, end_quarter, num_periods)       
    df = filter_by_life_nonlife_and_direct_inward(df, premium_loss_selection)        
    df = filter_reinsurance(df, reinsurance_form, reinsurance_geography, reinsurance_type)  
    df = filter_required_metrics(df, extended_metrics) 
    df = filter_by_insurance_lines(df, selected_linemains)
    df = add_calculated_metrics(df, selected_metrics)
    df = add_total_rows(df)

process_ranks.py

    df = df[df['linemain'] == 'all_lines']

    df = add_top_n_rows(df, top_n_list)
    
    ranking_df = add_others_rows(
        df, selected_insurers, top_n_list)
    
    top_n_insurers, insurer_options, benchmark_options, compare_options = get_top_n_insurers_and_insurer_options(
            ranking_df, main_insurer, number_of_insurers, selected_metrics, top_n_list) 

process_market_metrics.py

    extended_metrics = (selected_metrics or []) + ['total_premiums', 'total_losses']  
    
    df = add_market_share_rows(df)
    df = add_averages_and_ratios(df, extended_metrics)
    df = add_growth_rows_long(df, num_periods, period_type)   

data_processing.py
    def aggregate_based_on_chart_cols(
    df: pd.DataFrame, 
    x_column: str, 
    series_column: str, 
    group_column: str,     

