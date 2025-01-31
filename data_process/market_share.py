import pandas as pd
from typing import List
from config.logging_config import get_logger
logger = get_logger(__name__)


def calculate_market_share(
    df: pd.DataFrame,
    selected_insurers: List[str],
    selected_metrics: List[str],
    show_data_table: bool,
    total_insurer: str = 'total',
    suffix: str = '_market_share'
) -> pd.DataFrame:
    """
    Calculate market share metrics, skipping metrics that contain 'ratio',
    'average', or 'rate'.
    """
    if df.empty:
        logger.debug("Input DataFrame is empty, returning without calculations")
        return df

    logger.debug(f"Initial DataFrame shape: {df.shape}")
    logger.debug(f"Selected insurers: {selected_insurers}")
    logger.debug(f"Selected metrics: {selected_metrics}")
    logger.debug(f"Total insurer value: {total_insurer}")
    logger.debug(f"Input DataFrame head:\n{df.head()}")
    logger.debug(f"Metrics unique before: {df['metric'].unique()}")
    logger.debug(f"Insurers unique before: {df['insurer'].unique()}")

    # Get grouping columns
    group_cols = [col for col in df.columns if col not in {'insurer', 'value'}]
    logger.debug(f"Grouping columns: {group_cols}")

    # Calculate totals for each group
    total_insurer_data = df[df['insurer'] == total_insurer]
    logger.debug(f"Total insurer data shape: {total_insurer_data.shape}")
    logger.debug(f"Total insurer data head:\n{total_insurer_data.head()}")

    totals = (total_insurer_data
              .groupby(group_cols)['value']
              .first()
              .to_dict())

    if not totals:
        logger.debug(f"No totals calculated. Total insurer '{total_insurer}' might be missing from data")
        return df

    logger.debug(f"Calculated totals: {totals}")

    # Calculate market shares
    market_shares = []
    for group_key, group in df.groupby(group_cols):
        logger.debug(f"Processing group: {group_key}")

        # Skip if metric contains ratio, average, or rate
        metric_name = group['metric'].iloc[0].lower()
        if any(word in metric_name for word in ['ratio', 'average', 'rate']):
            logger.debug(f"Skipping market share calculation for metric '{metric_name}' as it contains excluded terms")
            continue

        if group_key not in totals:
            logger.debug(f"Group {group_key} not found in totals, skipping")
            continue

        if totals[group_key] == 0:
            logger.debug(f"Total for group {group_key} is 0, skipping to avoid division by zero")
            continue

        group = group.copy()
        original_values = group['value'].copy()
        group['value'] = (group['value'] / totals[group_key]).fillna(0)

        logger.debug(f"Group {group_key} calculation:")
        logger.debug(f"Original values: {original_values.tolist()}")
        logger.debug(f"Total value: {totals[group_key]}")
        logger.debug(f"Calculated market shares: {group['value'].tolist()}")

        group['metric'] = group['metric'] + suffix
        market_shares.append(group)

    if not market_shares:
        logger.debug("No market shares calculated")
        return df

    logger.debug(f"Number of market share groups calculated: {len(market_shares)}")

    result = pd.concat([df] + market_shares, ignore_index=True)
    logger.debug(f"Final DataFrame shape after concat: {result.shape}")

    if not show_data_table:
        filtered_result = result[result['insurer'].isin(selected_insurers)]
        logger.debug(f"Filtered DataFrame shape: {filtered_result.shape}")
        logger.debug(f"Final insurers: {filtered_result['insurer'].unique()}")
        return filtered_result

    logger.debug(f"Final metrics: {result['metric'].unique()}")
    return result