import pandas as pd
from typing import List, Dict, Optional, Set
from config.logging_config import get_logger
# from data_process.data_utils import save_df_to_csv


logger = get_logger(__name__)


# Simplified base metrics set
BASE_METRICS = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end',
    'premiums_interm', 'commissions_interm'
}

# Separate dictionaries for basic metrics and ratios to ensure proper calculation order
BASIC_METRIC_CALCULATIONS = {
    'net_balance': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0)
    ),
    'total_premiums': (
        ['direct_premiums', 'inward_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0)
    ),
    'net_premiums': (
        ['direct_premiums', 'inward_premiums', 'ceded_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)
    ),
    'total_losses': (
        ['direct_losses', 'inward_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0)
    ),
    'net_losses': (
        ['direct_losses', 'inward_losses', 'ceded_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0)
    ),
    'gross_result': (
        ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses'],
        lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0)) - 
                 (d.get('direct_losses', 0) + d.get('inward_losses', 0))
    ),
    'net_result': (
        ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses', 'ceded_premiums', 'ceded_losses'],
        lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)) - 
                 (d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0))
    ),
}

RATIO_CALCULATIONS = {
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

def get_required_metrics(
    selected_metrics: List[str],
    premium_loss_selection: Optional[List[str]] = None,
    metric_calculations: Dict[str, tuple] = {**BASIC_METRIC_CALCULATIONS, **RATIO_CALCULATIONS},
    base_metrics: Optional[Set[str]] = BASE_METRICS
) -> Set[str]:
    """
    Determine required metrics based on selected metrics and their dependencies.
    Handles both basic metrics and ratio calculations.
    """
    # Strip metric suffixes for processing
    suffix_list = ['_market_share_q_to_q_change', '_q_to_q_change', '_market_share']
    clean_metrics = [
        metric[:-len(suffix)] if any(metric.endswith(s) for s in suffix_list) else metric
        for metric in selected_metrics
    ]

    # Get all required metrics including dependencies
    required = set(clean_metrics)
    to_process = list(clean_metrics)
    processed = set()
    
    while to_process:
        metric = to_process.pop(0)
        if metric in processed:
            continue
            
        processed.add(metric)
        if metric in metric_calculations:
            deps = metric_calculations[metric][0]
            new_deps = set(deps) - required
            required.update(new_deps)
            to_process.extend(new_deps)
        
        # Check for dependencies in both calculation dictionaries
        if metric in BASIC_METRIC_CALCULATIONS:
            deps = BASIC_METRIC_CALCULATIONS[metric][0]
            new_deps = set(deps) - required
            required.update(new_deps)
            to_process.extend(new_deps)
        
        if metric in RATIO_CALCULATIONS:
            deps = RATIO_CALCULATIONS[metric][0]
            new_deps = set(deps) - required
            required.update(new_deps)
            to_process.extend(new_deps)
    
    # Filter based on premium_loss_selection if provided
    if premium_loss_selection:
        if 'direct' not in premium_loss_selection:
            required.discard('direct_premiums')
            required.discard('direct_losses')
        if 'inward' not in premium_loss_selection:
            required.discard('inward_premiums')
            required.discard('inward_losses')
            
    return required

def calculate_metrics(
    df: pd.DataFrame,
    selected_metrics: List[str],
    premium_loss_selection: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE
    Calculate insurance metrics based on selected metrics and premium/loss selection.
    """
    logger.debug(f"Initial dataframe metrics and values:")
    for _, row in df.iterrows():
        logger.debug(f"Metric: {row['metric']}, Value: {row['value']}")
    
    # Get required metrics for both basic and ratio calculations
    required_basic = get_required_metrics(
        selected_metrics,
        premium_loss_selection,
        BASIC_METRIC_CALCULATIONS,
        BASE_METRICS
    )
    required_ratios = get_required_metrics(
        selected_metrics,
        premium_loss_selection,
        RATIO_CALCULATIONS,
        BASE_METRICS
    )

    logger.debug(f"selected_metrics {selected_metrics}")
    logger.debug(f"required_basic {required_basic}")
    logger.debug(f"required_ratios {required_ratios}")
    logger.debug(f"_metrics unique before {df['metric'].unique()}")        
    # Prepare data for calculations
    grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]
    result_frames = []
    
    # Process each group separately
    for _, group in df.groupby(grouping_cols):
        metrics_dict = dict(zip(group['metric'], group['value']))
        logger.debug(f"Initial metrics_dict for group: {metrics_dict}")
        base_dict = {col: group[col].iloc[0] for col in grouping_cols}
        new_rows = []

        # Step 1: Calculate basic metrics first
        for metric in required_basic:

            
            if metric in BASIC_METRIC_CALCULATIONS:


                if metric in metrics_dict:
                    logger.debug(f"Skipping calculation for existing metric {metric} with value {metrics_dict[metric]}")
                    continue                
                try:
                    _, calculation = BASIC_METRIC_CALCULATIONS[metric]
                    value = calculation(metrics_dict)
                    logger.debug(f"Calculated basic metric {metric} = {value}")
                    new_row = {
                        **base_dict,
                        'metric': metric,
                        'value': value
                    }
                    new_rows.append(new_row)
                    # Update metrics_dict with the new calculated value for ratio calculations
                    logger.debug(f"Before updating metrics_dict[{metric}]: {metrics_dict.get(metric, 'Not present')}")
                    metrics_dict[metric] = value
                    logger.debug(f"After updating metrics_dict[{metric}]: {metrics_dict[metric]}")
                except Exception as e:
                    logger.debug(f"Error calculating basic metric {metric}: {str(e)}")
                    logger.debug(f"Current metrics_dict state: {metrics_dict}")
                    continue

        # Step 2: Calculate ratios using updated metrics_dict
        for metric in required_ratios:
          
            if metric in RATIO_CALCULATIONS:

                if metric in metrics_dict:
                    logger.debug(f"Skipping calculation for existing metric {metric} with value {metrics_dict[metric]}")
                    continue  
                
                try:
                    deps, calculation = RATIO_CALCULATIONS[metric]
                    logger.debug(f"Required dependencies for {metric}: {deps}")
                    missing_deps = [dep for dep in deps if dep not in metrics_dict]
                    if missing_deps:
                        logger.debug(f"Missing dependencies for {metric}: {missing_deps}")
                        continue
                    
                    # Check if all required basic metrics are calculated
                    if all(dep in metrics_dict for dep in deps):
                        logger.debug(f"All dependencies present for {metric}, calculating...")
                        dep_values = {dep: metrics_dict[dep] for dep in deps}
                        logger.debug(f"Input values for {metric}: {dep_values}")
                        value = calculation(metrics_dict)
                        logger.info(f"Successfully calculated {metric} = {value}")
                        new_rows.append({
                            **base_dict,
                            'metric': metric,
                            'value': value
                        })
                except Exception as e:
                    logger.debug(f"Error calculating ratio {metric}: {str(e)}")
                    logger.debug(f"Metrics dict state when error occurred: {metrics_dict}")
                    continue

        if new_rows:
            result_frames.append(pd.DataFrame(new_rows))

    # Combine results
    if result_frames:
        result_df = pd.concat([df] + result_frames, ignore_index=True)
        # Remove any duplicate metrics that might have been calculated
        logger.debug(f"_metrics unique result_df df {result_df['metric'].unique()}")
        return result_df.drop_duplicates(subset=grouping_cols + ['metric'], keep='last')

    logger.debug(f"_metrics unique return df {df['metric'].unique()}")

    return df