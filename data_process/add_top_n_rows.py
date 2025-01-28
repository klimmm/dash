import pandas as pd

def add_top_n_rows(df, top_n_list=[5, 10, 20], excluded_insurers=['total'], 
                           group_by_cols=None, value_col='value', insurer_col='insurer'):
    """
    Calculate top-N insurers aggregations for different N values.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe containing insurer data
    top_n_list : list, optional
        List of N values to calculate top-N aggregations for. Default is [5, 10, 20]
    excluded_insurers : list, optional
        List of insurer names to exclude from calculations. Default is ['total']
    group_by_cols : list, optional
        List of columns to group by. If None, will use all columns except insurer and value columns
    value_col : str, optional
        Name of the column containing values to aggregate. Default is 'value'
    insurer_col : str, optional
        Name of the column containing insurer names. Default is 'insurer'
        
    Returns:
    --------
    pandas.DataFrame
        Concatenated dataframe containing original data and top-N aggregations
    """
    # Input validation
    required_cols = [insurer_col, value_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain columns: {required_cols}")
    
    # If group_by_cols not specified, use all columns except insurer and value
    if group_by_cols is None:
        group_by_cols = [col for col in df.columns if col not in [insurer_col, value_col]]
    
    # Validate group_by_cols exist in dataframe
    if not all(col in df.columns for col in group_by_cols):
        raise ValueError(f"Not all grouping columns found in DataFrame: {group_by_cols}")
    
    # Initialize list with original dataframe
    dfs = [df.copy()]
    
    # Calculate top-N aggregations
    for n in top_n_list:
        if n != 999:  # Skip 999 as it's likely a special case
            # Filter out excluded insurers and get top N
            top_n_df = (
                df[~df[insurer_col].isin(excluded_insurers)]
                .groupby(group_by_cols)
                .apply(lambda x: x.nlargest(n, value_col))
                .reset_index(drop=True)
                .groupby(group_by_cols, observed=True)[value_col]
                .sum()
                .reset_index()
            )
            
            # Add top-N identifier
            top_n_df[insurer_col] = f'top-{n}'
            dfs.append(top_n_df)
    
    # Concatenate all dataframes
    result_df = pd.concat(dfs, ignore_index=True)
    
    return result_df

# Example usage:
# result = calculate_top_n_insurers(
#     df,
#     top_n_list=[5, 10, 20],
#     excluded_insurers=['total'],
#     group_by_cols=['year', 'month'],  # specify your grouping columns
#     value_col='value',
#     insurer_col='insurer'
# )