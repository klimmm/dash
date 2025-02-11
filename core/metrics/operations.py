from typing import Dict, List, Set

import numpy as np
import pandas as pd

from config.logging import get_logger, timer, monitor_memory
from core.metrics.definitions import METRICS

logger = get_logger(__name__)


@timer
def get_required_metrics(
    selected_metrics: List[str]
) -> List[str]:
    clean_metrics: List[str] = []
    for metric in selected_metrics:
        logger.debug(f"metric {metric}")
        # Find all matching base metrics and get the longest one
        matches = [base for base in METRICS if metric.startswith(base)]
        base_metric = max(
            matches, key=len, default=metric
        ) if matches else metric
        logger.debug(f"base_metric {base_metric}")
        clean_metrics.append(base_metric)

    ordered_metrics: List[str] = []
    # First add selected metrics
    ordered_metrics.extend(clean_metrics)
    # Process each selected metric and its dependencies in order
    for metric in clean_metrics:
        if metric not in METRICS:
            continue
        # Get dependencies for current metric
        metric_deps: Set[str] = set(METRICS[metric][0])
        checked_deps: Set[str] = set()
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
    deps: Dict[str, Set[str]] = {
        m: set(METRICS[m][0]) if m in METRICS else set() for m in metrics
    }
    rev_deps: Dict[str, Set[str]] = {}
    for m in metrics:
        for dep in deps[m]:
            rev_deps.setdefault(dep, set()).add(m)

    ordered: List[str] = []
    remaining = metrics.copy()
    ready: Set[str] = {m for m in remaining if not deps[m]}

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

    grouping_cols = [
        col for col in df.columns if col not in {'metric', 'value'}
    ]
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
def add_top_n_rows(df: pd.DataFrame, top_n_list: List[int] = [5, 10, 20]
                   ) -> pd.DataFrame:
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
    """Calculate market share metrics for insurance data.

    Args:
        df: Input DataFrame with insurer and value columns
        selected_insurers: List of insurers to process
        selected_metrics: List of metrics to calculate shares for
        total_insurer: Name of insurer representing total market
        suffix: Suffix to append to market share metric names

    Returns:
        DataFrame with original data and market share calculations
    """
    if df.empty:
        return df

    # Get grouping columns and calculate totals
    group_cols = [col for col in df.columns if col not in {'insurer', 'value'}]
    totals = (df[df['insurer'] == total_insurer]
              .groupby(group_cols)['value']
              .first()
              .to_dict())

    if not totals:
        return df

    # Calculate market shares for valid metrics
    market_shares = []
    skip_words = {'ratio', 'average', 'rate'}

    for group_key, group in df.groupby(group_cols):
        metric_name = group['metric'].iloc[0].lower()

        # Skip invalid metrics or groups
        if (any(word in metric_name for word in skip_words) or
            group_key not in totals or
                totals[group_key] == 0):
            continue

        # Calculate market share
        share_group = group.copy()
        share_group['value'] = (share_group['value'] /
                                totals[group_key]).fillna(0)
        share_group['metric'] += suffix
        market_shares.append(share_group)

    return (pd.concat([df] + market_shares, ignore_index=True)
            if market_shares else df)


@timer
@monitor_memory
def calculate_growth(
    df: pd.DataFrame,
    selected_insurers: List[str],
    num_periods_selected: int = 2,
    period_type: str = 'qoq'
) -> pd.DataFrame:
    """Calculate growth metrics for insurance data."""
    if df.empty:
        return df

    # Create a single copy of input DataFrame
    #df = df.copy()
    df.loc[:, 'year_quarter'] = pd.to_datetime(df['year_quarter'],
                                               errors='coerce')

    # Get grouping columns and sort
    group_cols = [col for col in df.columns if col not in [
        'year_quarter', 'metric', 'value'
    ]]
    df = df.sort_values(by=group_cols + ['year_quarter'])

    # Split data based on metric type
    market_share_mask = df['metric'].str.endswith('market_share')
    results = []

    # Regular metrics
    regular_mask = ~market_share_mask
    if regular_mask.any():
        regular = df[regular_mask]
        grouped = regular.groupby(group_cols + ['metric'], observed=True)
        shifted = grouped['value'].shift(1)

        # Create growth DataFrame
        growth_regular = pd.DataFrame(index=regular.index)
        growth_regular['metric'] = regular['metric'] + '_change'
        growth_regular['value'] = np.where(
            shifted > 1e-9,
            (regular['value'] - shifted) / shifted,
            np.nan
        )

        # Copy only necessary columns
        for col in group_cols + ['year_quarter']:
            growth_regular[col] = regular[col]

        results.append(growth_regular)

    # Market share metrics
    if market_share_mask.any():
        market_share = df[market_share_mask]

        # Create growth DataFrame
        growth_market = pd.DataFrame(index=market_share.index)
        growth_market['metric'] = market_share['metric'] + '_change'
        growth_market['value'] = market_share.groupby(
            group_cols + ['metric'],
            observed=True
        )['value'].diff()

        # Copy only necessary columns
        for col in group_cols + ['year_quarter']:
            growth_market[col] = market_share[col]

        results.append(growth_market)

    # Combine results and filter periods
    if not results:
        growth_df = pd.DataFrame(columns=df.columns)
    else:
        growth_df = pd.concat(results, ignore_index=True)

    # Calculate periods using efficient operations
    unique_periods = df['year_quarter'].unique()
    num_periods = min(num_periods_selected, len(unique_periods))
    recent_periods = pd.Series(unique_periods).nlargest(num_periods)
    growth_periods = recent_periods.iloc[:max(num_periods - 1, 1)]

    # Final concatenation
    result = pd.concat([
        df,
        growth_df[growth_df['year_quarter'].isin(growth_periods)]
    ], ignore_index=True)

    return result.sort_values(
        by=group_cols + ['year_quarter']
    ).reset_index(drop=True)