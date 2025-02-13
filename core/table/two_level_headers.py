import pandas as pd
from config.logging import get_logger

logger = get_logger(__name__)
VALID_PIVOT_COLUMNS = {'line', 'insurer', 'metric_base'}


def create_two_level_headers(df, pivot_column: str = 'metric_base'):
    """
    Create two-level headers with pivot values as horizontal columns.
    Args:
        df: Input DataFrame
        pivot_column: Column to pivot ('line', 'insurer', or 'metric_base')
    Returns:
        DataFrame with two-level headers
    """
    if pivot_column not in VALID_PIVOT_COLUMNS:
        raise ValueError(f"pivot_column must be one of {VALID_PIVOT_COLUMNS}")

    df = df.reset_index(
    ) if not VALID_PIVOT_COLUMNS.issubset(df.columns) else df.copy()

    df['_order'] = range(len(df))

    # Identify columns
    metric_cols = [col for col in df.columns if 'q' in col.lower()]
    logger.debug(f"Using metric_cols: {metric_cols}")
    index_cols = list(set(df.columns) - set(metric_cols) - {pivot_column,
                                                            '_order'})
    logger.debug(f"Using index columns: {index_cols}")

    # Get original order and pivot
    order_df = df.groupby(index_cols)['_order'].min().reset_index()
    pivoted = (df.set_index(index_cols + [pivot_column])[metric_cols]
               .unstack(pivot_column)
               .swaplevel(axis=1)
               .reset_index())

    # Flatten and fix column names
    pivoted.columns = [col[0] if isinstance(col, tuple) and col[1] == "" and
                       col[0] in index_cols else col
                       for col in pivoted.columns]

    # Merge missing keys if any
    if not set(index_cols).issubset(pivoted.columns):
        keys_df = df[index_cols].drop_duplicates()
        common_cols = [
            col for col in keys_df.columns if col in pivoted.columns]
        pivoted = pd.merge(keys_df, pivoted, on=common_cols, how='right')

    # Create final result with original order
    result = (pd.merge(order_df, pivoted, on=index_cols, how='left')
              .sort_values('_order')
              .drop(columns=['_order']))

    # Rebuild headers
    new_cols = [
        ('', col) if not isinstance(col, tuple) else col
        for col in result.columns]
    result.columns = pd.MultiIndex.from_tuples(new_cols)

    # Reorder value columns based on original data
    key_cols = [col for col in result.columns if col[0] == '']
    value_cols = [col for col in result.columns if col[0] != '']
    desired_order = df[pivot_column].unique()
    new_value_cols = [col for premium in desired_order
                      for col in value_cols if col[0] == premium]


    result = result[key_cols + new_value_cols]
    
    # Convert column MultiIndex to DataFrame for manipulation
    header_df = result.columns.to_frame(index=False).T
    header_df.columns = range(header_df.shape[1])
    data_df = result.copy()
    data_df.columns = range(data_df.shape[1])
    final_df = pd.concat([header_df, data_df], ignore_index=True)
    
    # Combine first two rows into headers
    combined_headers = []
    for col in range(final_df.shape[1]):
        first_val = str(final_df.iloc[0, col])
        second_val = str(final_df.iloc[1, col])
        
        # If first value is empty, use second value
        if first_val == '':
            combined_headers.append(second_val)
        # If second value is empty, use first value
        elif second_val == '':
            combined_headers.append(first_val)
        # If both have values, combine them
        else:
            combined_headers.append(f"{first_val}_{second_val}")
    
    # Create final DataFrame with combined headers and drop the first two rows
    final_df.columns = combined_headers
    final_df = final_df.iloc[2:].reset_index(drop=True)
    
    return final_df