import pandas as pd
from typing import List, Optional, Set
from constants.metrics import METRICS
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_required_metrics(selected_metrics: List[str], business_type_selection: Optional[List[str]] = None) -> List[str]:
    """
    Determine all required metrics based on selected metrics and their dependencies.
    Returns them with selected metrics first, followed by their dependencies grouped by parent metric.
    Args:
        selected_metrics: List of metrics to calculate
    Returns:
        List of all required metrics with selected metrics first, then grouped dependencies
    """
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
    """
    Determine the correct order of calculation based on dependencies.

    Args:
        metrics: Set of metrics to be calculated
    Returns:
        List of metrics in correct calculation order
    """
    ordered = []
    metrics_set = set(metrics)

    while metrics_set:
        # Find metrics with no remaining dependencies or base metrics
        available = {m for m in metrics_set 
                     if m not in METRICS or
                     all(dep not in metrics_set for dep in METRICS[m][0])}

        if not available:
            logger.debug(f"Circular dependency detected in remaining metrics: {metrics_set}")
            break

        ordered.extend(sorted(available))  # Sort for deterministic ordering
        metrics_set -= available

    return ordered


def calculate_metrics(
    df: pd.DataFrame,
    selected_metrics: List[str],
    required_metrics: List[str]
) -> pd.DataFrame:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE
    Calculate insurance metrics based on selected metrics and premium/loss selection.

    Args:
        df: Input DataFrame with metrics and values
        selected_metrics: List of metrics to calculate
    Returns:
        DataFrame with calculated metrics added
    """
    logger.debug(f"Starting calculation for {len(selected_metrics)} selected metrics")

    # Get all required metrics including dependencies
    required_metrics = set(required_metrics)

    existing_metrics = set(df['metric'].unique())
    if required_metrics.issubset(existing_metrics):
        logger.debug("All required metrics already present in DataFrame")
        df = df[df['metric'].isin(selected_metrics)]

        df['metric'] = pd.Categorical(
            df['metric'], 
            categories=selected_metrics, 
            ordered=True
        )
        grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
        df = df.sort_values(by=grouping_cols + ['metric'])

        return df

    # Get proper calculation order
    calculation_order = get_calculation_order(required_metrics)
    logger.debug(f"Calculation order determined: {calculation_order}")

    # Process each group separately
    grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
    result_frames = []

    for _, group in df.groupby(grouping_cols):
        metrics_dict = dict(zip(group['metric'], group['value']))
        base_dict = {col: group[col].iloc[0] for col in grouping_cols}
        new_rows = []
        logger.debug(f"metrics_dict: {metrics_dict}")
        # Calculate metrics in determined order
        for metric in calculation_order:

            if metric in metrics_dict:
                logger.debug(f"Skipping existing metric: {metric}")
                continue

            if metric not in METRICS:
                continue

            deps, calculation, *_ = METRICS[metric]
            try:
                value = calculation(metrics_dict)
                logger.debug(f"Calculated {metric} = {value}")
                new_rows.append({
                    **base_dict,
                    'metric': metric,
                    'value': value
                })
                metrics_dict[metric] = value  # Update for dependent calculations
            except Exception as e:
                logger.debug(f"Error calculating {metric}: {str(e)}")
                continue

        if new_rows:
            result_frames.append(pd.DataFrame(new_rows))

    # Combine results
    if result_frames:
        result_df = pd.concat([df] + result_frames, ignore_index=True)
        result_df = result_df.drop_duplicates(subset=grouping_cols + ['metric'], keep='last')
        result_df = result_df[result_df['metric'].isin(selected_metrics)]
        return result_df

    df = df[df['metric'].isin(selected_metrics)]

    # Apply the same sorting logic to the original df
    df['metric'] = pd.Categorical(
        df['metric'], 
        categories=selected_metrics, 
        ordered=True
    )
    df = df.sort_values(by=grouping_cols + ['metric'])
    logger.debug(f"df sorted: {df}")
    logger.debug(f"selected_metrics: {selected_metrics}")

    return df