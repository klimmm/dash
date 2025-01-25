import pandas as pd
from typing import List, Optional, Set
from config.logging_config import get_logger

logger = get_logger(__name__)

# Base metrics that form the foundation for calculations
BASE_METRICS = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end',
    'premiums_interm', 'commissions_interm'
}

# Combined metric calculations dictionary with clear separation of basic and ratio metrics
METRIC_CALCULATIONS = {
    # Basic metrics (calculated first)
    'net_balance': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0)
    ),
    'total_premiums': (
        ['direct_premiums', 'inward_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0)
    ),
    'net_premiums': (
        ['total_premiums', 'ceded_premiums'],
        lambda d: d.get('total_premiums', 0) - d.get('ceded_premiums', 0)
    ),
    'total_losses': (
        ['direct_losses', 'inward_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0)
    ),
    'net_losses': (
        ['total_losses', 'ceded_losses'],
        lambda d: d.get('total_losses', 0) - d.get('ceded_losses', 0)
    ),
    'gross_result': (
        ['total_premiums', 'total_losses'],
        lambda d: (d.get('total_premiums', 0)) - 
                 (d.get('total_losses', 0))
    ),
    'net_result': (
        ['total_premiums', 'total_losses', 
         'ceded_premiums', 'ceded_losses'],
        lambda d: (d.get('total_premiums', 0) - d.get('ceded_premiums', 0)) - 
                 (d.get('total_losses', 0) - d.get('ceded_losses', 0))
    ),
    # Ratio metrics (calculated after basic metrics)
    'average_sum_insured': (
        ['sums_end', 'contracts_end'],
        lambda d: (d.get('sums_end', 0) / 10) / (d.get('contracts_end', 1) * 1000) / 1000
    ),
    'average_new_sum_insured': (
        ['new_sums', 'new_contracts'],
        lambda d: (d.get('new_sums', 0) / 10) / (d.get('new_contracts', 1) * 1000) / 1000
    ),
    'average_new_premium': (
        ['direct_premiums', 'new_contracts'],
        lambda d: d.get('direct_premiums', 0) / (d.get('new_contracts', 1) * 1000)
    ),
    'average_loss': (
        ['direct_losses', 'claims_settled'],
        lambda d: d.get('direct_losses', 0) / (d.get('claims_settled', 1) * 1000)
    ),
    'average_rate': (
        ['new_sums', 'direct_premiums'],
        lambda d: d.get('direct_premiums', 0) / d.get('new_sums', 1)
    ),
    'ceded_premiums_ratio': (
        ['ceded_premiums', 'total_premiums'],
        lambda d: d.get('ceded_premiums', 0) / d.get('total_premiums', 1)
    ),
    'ceded_losses_ratio': (
        ['ceded_losses', 'total_losses'],
        lambda d: d.get('ceded_losses', 0) / d.get('total_losses', 1)
    ),
    'ceded_losses_to_ceded_premiums_ratio': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) / d.get('ceded_premiums', 1)
    ),
    'direct_loss_ratio': (
        ['direct_losses', 'direct_premiums'],
        lambda d: d.get('direct_losses', 0) / d.get('direct_premiums', 1)
    ),
    'inward_loss_ratio': (
        ['inward_losses', 'inward_premiums'],
        lambda d: d.get('inward_losses', 0) / d.get('inward_premiums', 1)
    ),
    'gross_loss_ratio': (
        ['total_losses', 'total_premiums'],
        lambda d: d.get('total_losses', 0) / d.get('total_premiums', 1)
    ),
    'net_loss_ratio': (
        ['net_losses', 'net_premiums'],
        lambda d: d.get('net_losses', 0) / d.get('net_premiums', 1)
    ),
    'effect_on_loss_ratio': (
        ['total_losses', 'net_losses', 'total_premiums', 'net_premiums'],
        lambda d: (d.get('total_losses', 0) / d.get('total_premiums', 1)) -
                 (d.get('net_losses', 0) / d.get('net_premiums', 1))
    ),
    'ceded_ratio_diff': (
        ['ceded_losses', 'total_losses', 'ceded_premiums', 'total_premiums'],
        lambda d: (d.get('ceded_losses', 0) / d.get('total_losses', 1)) -
                 (d.get('ceded_premiums', 0) / d.get('total_premiums', 1))
    ),
    'premiums_interm_ratio': (
        ['direct_premiums', 'premiums_interm'],
        lambda d: d.get('premiums_interm', 0) / d.get('direct_premiums', 1)
    ),
    'commissions_rate': (
        ['premiums_interm', 'commissions_interm'],
        lambda d: d.get('commissions_interm', 0) / d.get('premiums_interm', 1)
    )
}

def get_metric_dependencies(metric: str) -> Set[str]:
    """
    Get all dependencies for a metric, including dependencies of dependencies.
    
    Args:
        metric: Name of the metric
    Returns:
        Set of all required metrics including nested dependencies
    """
    if metric not in METRIC_CALCULATIONS:
        return set()

    deps = set(METRIC_CALCULATIONS[metric][0])
    for dep in list(deps):  # Convert to list to avoid modifying set during iteration
        deps.update(get_metric_dependencies(dep))
    logger.debug(f"metric {metric}")
    logger.debug(f"deps {deps}")
    return deps

def get_required_metrics(selected_metrics: List[str], premium_loss_selection: Optional[List[str]] = None) -> List[str]:
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
        metric[:-len(suffix)] if any(metric.endswith(s) for s in suffix_list) else metric
        for metric in selected_metrics
    ]

    ordered_metrics = []
    # First add selected metrics
    ordered_metrics.extend(clean_metrics)
    
    # Then add dependencies for each selected metric in order
    for metric in clean_metrics:
        deps = sorted(get_metric_dependencies(metric))
        for dep in deps:
            if dep not in ordered_metrics:
                ordered_metrics.append(dep)
    
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
                    if m not in METRIC_CALCULATIONS or 
                    all(dep not in metrics_set for dep in METRIC_CALCULATIONS[m][0])}

        if not available:
            logger.debug(f"Circular dependency detected in remaining metrics: {metrics_set}")
            break

        ordered.extend(sorted(available))  # Sort for deterministic ordering
        metrics_set -= available

    return ordered

def calculate_metrics(
    df: pd.DataFrame,
    selected_metrics: List[str],
    premium_loss_selection: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE
    Calculate insurance metrics based on selected metrics and premium/loss selection.
    
    Args:
        df: Input DataFrame with metrics and values
        selected_metrics: List of metrics to calculate
        premium_loss_selection: Optional list to filter premium/loss metrics
    Returns:
        DataFrame with calculated metrics added
    """
    logger.debug(f"Starting calculation for {len(selected_metrics)} selected metrics")

    # Get all required metrics including dependencies
    required_metrics = set(get_required_metrics(selected_metrics))

    # Filter based on premium_loss_selection if provided
    if premium_loss_selection:
        if 'direct' not in premium_loss_selection:
            required_metrics.discard('direct_premiums')
            required_metrics.discard('direct_losses')
        if 'inward' not in premium_loss_selection:
            required_metrics.discard('inward_premiums')
            required_metrics.discard('inward_losses')

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

            if metric not in METRIC_CALCULATIONS:
                continue

            deps, calculation = METRIC_CALCULATIONS[metric]
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
    return df