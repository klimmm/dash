from concurrent.futures import ThreadPoolExecutor
import numpy as np
from functools import lru_cache
from typing import List, Optional, Set

import pandas as pd

from config.logging_config import get_logger
from constants.metrics import METRICS

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
def get_required_metrics(
    selected_metrics: List[str],
    business_type_selection: Optional[List[str]] = None
) -> List[str]:

    # Strip metric suffixes for processing
    suffix_list = ['_market_share_q_to_q_change', '_q_to_q_change', '_market_share']
    clean_metrics = [
        metric[:-len(matched_suffix)] if (matched_suffix := next((s for s in suffix_list if metric.endswith(s)), None)) else metric
        for metric in selected_metrics
    ]

    ordered_metrics = []
    # First add selected metrics
    ordered_metrics.extend(clean_metrics)

    # Filter based on business_type_selection if provided
    if business_type_selection:
        if 'direct' not in business_type_selection:
            ordered_metrics = [x for x in ordered_metrics if x not in ('direct_premiums', 'direct_losses')]
        if 'inward' not in business_type_selection:
            ordered_metrics = [x for x in ordered_metrics if x not in ('inward_premiums', 'inward_losses')]

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


def get_calculation_order(metrics: Set[str]) -> List[str]:
    """Fast calculation order with minimal operations"""
    ordered = []
    remaining = metrics.copy()
    deps_cache = {m: set(METRICS[m][0]) if m in METRICS else set() for m in metrics}

    while remaining:
        available = remaining - {m for m in remaining if deps_cache[m] & remaining}
        if not available:
            break
        ordered.extend(sorted(available))
        remaining -= available
    return ordered


@timer
def calculate_metrics(
    df: pd.DataFrame,
    selected_metrics: List[str],
    required_metrics: List[str]
) -> pd.DataFrame:
    """Optimized metric calculation minimizing DataFrame operations"""
    existing = df['metric'].unique()
    selected_set = set(selected_metrics)


    if all(m in existing for m in required_metrics):
        result = df.loc[df['metric'].isin(selected_set)]
        return result

    calculation_order = get_calculation_order(set(required_metrics))
    grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]

    metric_calcs = {
        m: METRICS[m][1] 
        for m in calculation_order 
        if m in METRICS and (
            m in selected_set or 
            any(m in METRICS[dep][0] for dep in selected_set if dep in METRICS)
        )
    }

    all_groups = []

    for _, group in df.groupby(grouping_cols):
        metrics = dict(zip(group['metric'], group['value']))
        base = {col: group[col].iloc[0] for col in grouping_cols}

        new_metrics = []
        for metric in calculation_order:
            if metric not in metrics and metric in metric_calcs:
                try:
                    val = metric_calcs[metric](metrics)
                    metrics[metric] = val
                    if metric in selected_set:
                        new_metrics.append({
                            'metric': metric,
                            'value': val,
                            **base
                        })
                except Exception:
                    continue

        if new_metrics:
            all_groups.extend(new_metrics)

    if all_groups:
        new_df = pd.DataFrame(all_groups)
        df_filtered = df.loc[df['metric'].isin(selected_set)]
        result = pd.concat([df_filtered, new_df], ignore_index=True)
        result.drop_duplicates(
            subset=grouping_cols + ['metric'], 
            keep='last', 
            inplace=True
        )
    else:
        result = df.loc[df['metric'].isin(selected_set)]

    return result