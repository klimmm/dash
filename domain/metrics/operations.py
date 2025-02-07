from typing import List, Set
import numpy as np
import pandas as pd

from config.logging_config import get_logger, timer, monitor_memory
from domain.metrics.definitions import METRICS

logger = get_logger(__name__)


@timer
def get_required_metrics(
    selected_metrics: List[str]
) -> List[str]:

    clean_metrics = []
    for metric in selected_metrics:
        logger.debug(f"metric {metric}")
        # Find all matching base metrics and get the longest one
        matches = [base for base in METRICS if metric.startswith(base)]
        base_metric = max(matches, key=len, default=metric) if matches else metric
        logger.debug(f"base_metric {base_metric}")
        clean_metrics.append(base_metric)

    ordered_metrics = []
    # First add selected metrics
    ordered_metrics.extend(clean_metrics)

    # Process each selected metric and its dependencies in order
    for metric in clean_metrics:
        if metric not in METRICS:
            continue

        # Get dependencies for current metric
        metric_deps = set(METRICS[metric][0])
        checked_deps = set()

        # Get nested dependencies
        while metric_deps - checked_deps:
            dep = (metric_deps - checked_deps).pop()
            checked_deps.add(dep)
            if dep in METRICS:
                new_deps = set(METRICS[dep][0])
                metric_deps.update(new_deps)

        # Add sorted dependencies for this metric while maintaining order
        for dep in sorted(metric_deps):
            if dep not in ordered_metrics:
                ordered_metrics.append(dep)

        logger.debug(f"metric {metric}")
        logger.debug(f"deps {metric_deps}")

    logger.debug(f"required_metrics {ordered_metrics}")

    return ordered_metrics


@timer
def get_calculation_order(metrics: Set[str]) -> List[str]:

    # Cache dependencies and reverse dependencies
    deps = {m: set(METRICS[m][0]) if m in METRICS else set() for m in metrics}
    rev_deps = {}
    for m in metrics:
        for dep in deps[m]:
            rev_deps.setdefault(dep, set()).add(m)

    ordered = []
    remaining = metrics.copy()
    ready = {m for m in remaining if not deps[m]}

    while ready:
        metric = min(ready)
        ordered.append(metric)
        remaining.remove(metric)

        # Update ready set
        if metric in rev_deps:
            for dep_metric in rev_deps[metric]:
                deps[dep_metric].remove(metric)
                if not deps[dep_metric] and dep_metric in remaining:
                    ready.add(dep_metric)
        ready.remove(metric)

    return ordered


@timer
@monitor_memory
def calculate_metrics(
    df: pd.DataFrame,
    selected_metrics: List[str],
    required_metrics: List[str]
) -> pd.DataFrame:

    selected_set = set(selected_metrics)
    required_set = set(required_metrics)

    # Early exit
    existing = df['metric'].unique()
    if all(m in existing for m in required_metrics):
        return df[df['metric'].isin(selected_set)]

    grouping_cols = [col for col in df.columns if col not in {'metric', 'value'}]
    calculation_order = get_calculation_order(required_set)

    # Pre-compute metric calculations - single dict comprehension
    metric_calcs = {
        m: METRICS[m][1]
        for m in calculation_order
        if m in METRICS and (
            m in selected_set or
            any(m in METRICS[dep][0] for dep in selected_set if dep in METRICS)
        )
    }

    # group processing
    all_groups = []
    grouped = df.groupby(grouping_cols)

    for idx, (name, group) in enumerate(grouped):
        base = dict(zip(grouping_cols,
                        name if isinstance(name, tuple) else [name]))
        metrics = dict(zip(group['metric'], group['value']))

        # Single loop through calculation order
        for metric in calculation_order:
            if metric not in metrics and metric in metric_calcs:
                try:
                    val = metric_calcs[metric](metrics)
                    metrics[metric] = val
                    if metric in selected_set:
                        all_groups.append({
                            **base,
                            'metric': metric,
                            'value': val
                        })
                except Exception:
                    continue

    # result combination
    if all_groups:
        new_df = pd.DataFrame(all_groups)
        df_filtered = df[df['metric'].isin(selected_set)]
        result = pd.concat([df_filtered, new_df], ignore_index=True)
        # Single operation for duplicates
        result.drop_duplicates(
            subset=grouping_cols + ['metric'],
            keep='last',
            inplace=True
        )
    else:
        result = df[df['metric'].isin(selected_set)]

    return result


@timer
@monitor_memory
def add_top_n_rows(df, top_n_list=[5, 10, 20]):
    """
    Performance-optimized version that still avoids SettingWithCopyWarning
    """
    # Pre-filter excluded insurers once - use loc for boolean indexing
    group_by_cols = [
        col for col in df.columns if col not in ['insurer', 'value']]
    filtered_df = df.loc[df['insurer'] != 'total'].copy()

    # Store the original df in the list
    dfs = [df]

    for n in top_n_list:
        if n == 999:
            continue

        # Compute ranks directly and create new DataFrame in one step
        ranked_df = filtered_df.assign(
            rank=lambda x: x.groupby(group_by_cols)['value'].rank(
                method='first',
                ascending=False
            )
        )

        # Filter and aggregate in one step
        top_n_df = (ranked_df[ranked_df['rank'] <= n]
                    .groupby(group_by_cols, observed=True)
                    .agg({'value': 'sum'})
                    .assign(insurer=f'top-{n}')
                    .reset_index())

        dfs.append(top_n_df)

    return pd.concat(dfs, ignore_index=True)


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
        logger.debug(
            f"No totals calculated. Total insurer '{total_insurer}'")
        return df

    logger.debug(f"Calculated totals: {totals}")

    # Calculate market shares
    market_shares = []
    for group_key, group in df.groupby(group_cols):
        logger.debug(f"Processing group: {group_key}")

        # Skip if metric contains ratio, average, or rate
        metric_name = group['metric'].iloc[0].lower()
        if any(word in metric_name for word in ['ratio', 'average', 'rate']):
            logger.debug(
                f"Skipping market share calc for metric '{metric_name}'")
            continue

        if group_key not in totals:
            logger.debug(f"Group {group_key} not found in totals, skipping")
            continue

        if totals[group_key] == 0:
            logger.debug(
                f"Total for group {group_key} is 0, skip to avoid div by zero")
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

    logger.debug(
        f"Number of market share groups calculated: {len(market_shares)}")

    result = pd.concat([df] + market_shares, ignore_index=True)
    logger.debug(f"Final DataFrame shape after concat: {result.shape}")

    logger.debug(f"Final metrics: {result['metric'].unique()}")

    return result


@timer
@monitor_memory
def calculate_growth(
    df: pd.DataFrame,
    selected_insurers: List[str],
    num_periods_selected: int = 2,
    period_type: str = 'qoq'
) -> pd.DataFrame:
    """Calculate growth metrics with improved performance."""
    try:
        if df.empty:
            return df

        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(df['year_quarter']):
            df['year_quarter'] = pd.to_datetime(df['year_quarter'],
                                                errors='coerce')
        group_cols = [
            col for col in df.columns if col not in [
                'year_quarter', 'metric', 'value']]
        df_sorted = df.sort_values(by=group_cols + ['year_quarter']).copy()
        # save_df_to_csv(df_sorted, "df_sorted_growth.csv")
        # Split processing by metric type
        market_share_mask = df_sorted['metric'].str.endswith('market_share')
        regular_metrics = df_sorted[~market_share_mask].copy()
        market_share_metrics = df_sorted[market_share_mask].copy()

        processed_dfs = []

        # Process regular metrics
        if len(regular_metrics) > 0:
            grouped = regular_metrics.groupby(group_cols + ['metric'],
                                              observed=True)
            regular_metrics['previous'] = grouped['value'].shift(1)

            mask = regular_metrics['previous'] > 1e-9
            regular_metrics['growth'] = np.where(
                mask,
                (regular_metrics['value'] - regular_metrics['previous']) /
                regular_metrics['previous'],
                np.nan
            )

            growth_regular = regular_metrics.copy()
            growth_regular['metric'] += '_change'
            growth_regular['value'] = growth_regular['growth']
            processed_dfs.append(growth_regular.drop(columns=[
                'growth', 'previous']))

        # Process market share metrics
        if len(market_share_metrics) > 0:
            grouped = market_share_metrics.groupby(group_cols + ['metric'],
                                                   observed=True)
            market_share_metrics['growth'] = grouped['value'].diff().fillna(0)

            growth_market = market_share_metrics.copy()
            growth_market['metric'] += '_change'
            growth_market['value'] = growth_market['growth']
            processed_dfs.append(growth_market.drop(columns=['growth']))

        growth_df = pd.concat(
            processed_dfs,
            ignore_index=True) if processed_dfs else pd.DataFrame(columns=df.
                                                                  columns)

        logger.debug(f" num_periods_selected {num_periods_selected}")
        num_periods_growth = num_periods_selected - 1
        logger.debug(f" num_periods_growth {num_periods_growth}")
        recent_periods = (df_sorted['year_quarter']
                          .drop_duplicates()
                          .sort_values(ascending=False)
                          .iloc[:num_periods_selected])
        logger.debug(f" recent_periods {recent_periods}")
        recent_growth_periods = (df_sorted['year_quarter']
                                 .drop_duplicates()
                                 .sort_values(ascending=False)
                                 .iloc[:max(num_periods_growth, 1)])
        logger.debug(f" recent_growth_periods {recent_growth_periods}")

        df_filtered = df_sorted[
            df_sorted['year_quarter'].isin(recent_periods)].copy()
        logger.debug(
            f" df_filtered periods {df_filtered['year_quarter'].unique()}")
        growth_filtered = growth_df[
            growth_df['year_quarter'].isin(recent_growth_periods)].copy()
        logger.debug(
            f" df_growth_periods {growth_filtered['year_quarter'].unique()}")
        result = pd.concat([df_filtered, growth_filtered], ignore_index=True)
        logger.debug(f" result_periods {result['year_quarter'].unique()}")

        # save_df_to_csv(result, "result_growth_before_sort.csv")

        result.sort_values(by=group_cols + ['year_quarter'], inplace=True)
        # save_df_to_csv(result, "result_growth_after_sort.csv")

        result.reset_index(drop=True, inplace=True)

        return result

    except Exception as e:
        logger.error(f"Error in growth calculation: {str(e)}")
        raise