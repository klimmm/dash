import pandas as pd
import numpy as np
import logging
logger = logging.getLogger(__name__)


def process_and_melt_pivot_table(df: pd.DataFrame) -> pd.DataFrame:

    pivot_df = pd.pivot_table(
        df,
        values='value',
        index=['year', 'datatype', 'insurer', 'insurance_line'],
        columns='quarter',
        aggfunc='first'
    )

    # Ensure all quarters are present
    for quarter in range(1, 5):
        if quarter not in pivot_df.columns:
            pivot_df[quarter] = np.nan

    pivot_df = fill_missing_quarters(pivot_df)
    pivot_df = calculate_net_values(pivot_df)
    melted_df = melt_pivot_table(pivot_df)

    return melted_df


def fill_missing_quarters(pivot_df: pd.DataFrame) -> None:
    """
    Fill missing quarter values in the pivot table.

    Args:
        pivot_df (pd.DataFrame): The pivot table DataFrame to fill.
    """
    pivot_df[1] = pivot_df[1].fillna(0)

    mask_2 = pivot_df[2].isna()
    pivot_df.loc[mask_2 & (pivot_df[1] == 0), 2] = 0
    pivot_df.loc[mask_2 & (pivot_df[1] != 0) & pivot_df[3].notna(), 2] = (
        pivot_df[3] - pivot_df[1]
    ) / 2 + pivot_df[1]
    pivot_df.loc[mask_2 & (pivot_df[1] != 0) & pivot_df[3].isna() & pivot_df[4].notna(), 2] = (
        pivot_df[4] - pivot_df[1]
    ) / 3 + pivot_df[1]
    pivot_df.loc[mask_2 & (pivot_df[1] != 0) & pivot_df[3].isna() & pivot_df[4].isna(), 2] = pivot_df[1]

    mask_3 = pivot_df[3].isna()
    pivot_df.loc[mask_3 & (pivot_df[2] == 0), 3] = 0
    pivot_df.loc[mask_3 & (pivot_df[2] != 0) & pivot_df[4].notna(), 3] = (
        pivot_df[4] - pivot_df[2]
    ) / 2 + pivot_df[2]
    pivot_df.loc[mask_3 & (pivot_df[2] != 0) & pivot_df[4].isna(), 3] = pivot_df[2]

    pivot_df.loc[pivot_df[4].isna(), 4] = pivot_df[3]

    return pivot_df


def calculate_net_values(pivot_df: pd.DataFrame) -> None:
    """
    Calculate net values for each quarter.
    Args:
        pivot_df (pd.DataFrame): The pivot table DataFrame to calculate net values for.
    """
    # Calculate net values for datatype other than 'contracts_end' and 'sums_end'
    mask = ~pivot_df.index.get_level_values('datatype').isin(['contracts_end', 'sums_end'])
    pivot_df.loc[mask, 'net_1'] = pivot_df.loc[mask, 1]
    pivot_df.loc[mask, 'net_2'] = pivot_df.loc[mask, 2] - pivot_df.loc[mask, 1]
    pivot_df.loc[mask, 'net_3'] = pivot_df.loc[mask, 3] - pivot_df.loc[mask, 2]
    pivot_df.loc[mask, 'net_4'] = pivot_df.loc[mask, 4] - pivot_df.loc[mask, 3]

    # Calculate net values for 'contracts_end' and 'sums_end'
    mask = pivot_df.index.get_level_values('datatype').isin(['contracts_end', 'sums_end'])
    pivot_df.loc[mask, 'net_1'] = pivot_df.loc[mask, 1]
    pivot_df.loc[mask, 'net_2'] = pivot_df.loc[mask, 2]
    pivot_df.loc[mask, 'net_3'] = pivot_df.loc[mask, 3]
    pivot_df.loc[mask, 'net_4'] = pivot_df.loc[mask, 4]

    return pivot_df


def melt_pivot_table(pivot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Melt the pivot table and add a 'value_type' column.

    Args:
        pivot_df (pd.DataFrame): The pivot table DataFrame to melt.

    Returns:
        pd.DataFrame: The melted DataFrame.
    """
    logger.info("Starting melt_pivot_table function")

    melted_df = pd.melt(
        pivot_df.reset_index(),
        id_vars=['year', 'datatype', 'insurer', 'insurance_line'],
        var_name='quarter',
        value_name='value'
    )

    logger.info(f"Unique quarter values after melt: {melted_df['quarter'].unique()}")

    melted_df['value_type'] = np.where(
        melted_df['quarter'].isin([1, 2, 3, 4]),
        'value_ytd',
        'value_net'
    )

    logger.info(f"Unique value_type values: {melted_df['value_type'].unique()}")
    logger.info(f"Quarter values before replacement: {melted_df['quarter'].unique()}")

    melted_df['quarter'] = melted_df['quarter'].replace(
        {'net_1': 1, 'net_2': 2, 'net_3': 3, 'net_4': 4}
    ).astype(int)

    logger.info(f"Quarter values after replacement: {melted_df['quarter'].unique()}")
    logger.info("Finished melt_pivot_table function")

    return melted_df