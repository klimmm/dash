
@lru_cache(maxsize=512)  # LRU cache first
@track_cache_stats      # Then our tracking
def get_cached_grouped_df(
    reporting_form: str,
    period_type: str,
    end_quarter: str,
    line_type_tuple: tuple
) -> pd.DataFrame:
    start_time = time.time()
    
    # Select dataset with minimal logging
    df = insurance_df_162 if reporting_form == '0420162' else insurance_df_158
    '''ogger.info(f"Initial DataFrame shape: {df.shape}")
    
    # Log each operation timing
    filter_start = time.time()
    end_quarter_ts = pd.Period(end_quarter, freq='Q').to_timestamp(how='end')
    start_quarter_ts = min(df['year_quarter'].unique())
    
    mask = (
        (df['year_quarter'] >= start_quarter_ts) & 
        (df['year_quarter'] <= end_quarter_ts)
    )
    if line_type_tuple:
        mask &= df['line_type'].isin(line_type_tuple)
    
    filtered_df = df[mask]
    filter_time = time.time() - filter_start
    logger.info(f"Filtering: {filter_time:.2f}s, Rows after filter: {len(filtered_df)}")

    # Grouping operation
    group_start = time.time()
    group_cols = [col for col in filtered_df.columns if col not in ('line_type', 'value')]
    grouped_df = filtered_df.groupby(group_cols, observed=True)['value'].sum().reset_index()
    group_time = time.time() - group_start
    logger.info(f"Grouping: {group_time:.2f}s, Final rows: {len(grouped_df)}")'''
    
    return df