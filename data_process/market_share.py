from typing import List

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


def timer(func):
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


@timer
def calculate_market_share(
    df: pd.DataFrame,
    selected_insurers: List[str],
    selected_metrics: List[str],
    total_insurer: str = 'total',
    suffix: str = '_market_share'
) -> pd.DataFrame:
    """
    Calculate market share metrics, skipping metrics that contain 'ratio',
    'average', or 'rate'.
    """

    group_cols = [col for col in df.columns if col not in {'insurer', 'value'}]
    logger.debug(f"Grouping columns: {group_cols}")

    # Calculate totals for each group
    total_insurer_data = df[df['insurer'] == total_insurer]

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

        group['metric'] = group['metric'] + suffix
        market_shares.append(group)

    if not market_shares:
        logger.debug("No market shares calculated")
        return df

    result = pd.concat([df] + market_shares, ignore_index=True)

    return result