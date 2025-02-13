import pandas as pd
import numpy as np
from core.io import save_df_to_csv
from config.logging import timer, get_logger
logger = get_logger(__name__)

@timer
def split_metric_column(df):
    # Define possible suffixes
    suffixes = ['_base_change', '_market_share', '_market_share_change']
    save_df_to_csv(df, "df_before_split.csv")
    # Create new columns
    df['metric_base'] = df['metric'].copy()
    df['value_type'] = 'base'  # Default value for metrics without suffix

    # Process each suffix
    for suffix in suffixes:
        # Find rows where metric ends with the suffix
        mask = df['metric'].str.endswith(suffix)

        # Update base metric by removing suffix
        df.loc[mask, 'metric_base'] = df.loc[mask, 'metric'].str.replace(suffix, '')

        # Update metric type by removing leading underscore
        df.loc[mask, 'value_type'] = suffix.lstrip('_')

    # Drop original metric column if needed
    # df = df.drop('metric', axis=1)
    save_df_to_csv(df, "df_after_split.csv")
    return df


@timer
def add_rank_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add ranks and rank changes for each combination of year_quarter/line/metric for base value_type,
    excluding special insurers.
    """
    # Create copy and split efficiently
    result_df = df.copy()
    base_mask = result_df['value_type'] == 'base'
    base_df = result_df[base_mask]
    other_metrics_df = result_df[~base_mask]
    
    special_insurers = {'top-5', 'top-10', 'top-20', 'total'}
    special_mask = base_df['insurer'].isin(special_insurers)
    regular_df = base_df[~special_mask]
    special_df = base_df[special_mask]

    # Initialize columns
    regular_df['rank'] = None
    regular_df['rank_change'] = None
    
    # Faster rank calculation using groupby.rank()
    regular_df['rank'] = regular_df.groupby(['year_quarter', 'line', 'metric'])['value'].rank(ascending=False, method='min')
    
    # Calculate rank changes using shift within groups
    regular_df['rank_change'] = regular_df.sort_values('year_quarter').groupby(['line', 'metric', 'insurer'])['rank'].shift(1) - regular_df['rank']
    
    # Add nulls to other DataFrames
    special_df['rank'] = None
    special_df['rank_change'] = None
    other_metrics_df['rank'] = None
    other_metrics_df['rank_change'] = None
    
    # Combine maintaining original order
    result_df = pd.concat([regular_df, special_df, other_metrics_df])
    logger.debug(f" value_type unique {result_df['value_type'].unique()}")
    return result_df