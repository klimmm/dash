from typing import List, Dict, Optional, Any
from callbacks.get_available_metrics import get_available_metrics
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158
from constants.filter_options import METRICS_OPTIONS
from config.logging_config import get_logger, track_callback, track_callback_end
logger = get_logger(__name__)


FORM_METRICS = {
    '0420158': {'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
                'net_premiums', 'net_losses'
               },
    '0420162': {'direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses', 
                'ceded_premiums', 'ceded_losses',
                'new_sums', 'sums_end',
                'new_contracts', 'contracts_end',
                'premiums_interm', 'commissions_interm', 
                'claims_settled', 'claims_reported'
               }
}


def get_metric_options(
    reporting_form: str,
    selected_primary_metrics: Optional[List[str]] = None,
    selected_secondary_metrics: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    # 1. Initialize and normalize inputs
    allowed_basic_metrics = FORM_METRICS.get(reporting_form, set())
    available_calculated_metrics = set(get_available_metrics(allowed_basic_metrics))  # Convert to set explicitly
    selected_primary_metrics = [selected_primary_metrics] if isinstance(selected_primary_metrics, str) else (selected_primary_metrics or [])
    selected_secondary_metrics = [selected_secondary_metrics] if isinstance(selected_secondary_metrics, str) else (selected_secondary_metrics or [])

    logger.debug(f"selected_primary_metrics{selected_primary_metrics}")

    # 2. Determine default metrics sets
    primary_metric_set = allowed_basic_metrics.copy()
    secondary_metric_set = available_calculated_metrics.copy()
    logger.debug(f"allowed_basic_metrics{primary_metric_set}")
    # 3. Handle selected primary metrics that are in secondary set
    for metric in selected_primary_metrics:
        if metric in secondary_metric_set:
            primary_metric_set.add(metric)
            secondary_metric_set.remove(metric)
    logger.debug(f"primary_metric_set{primary_metric_set}")
    
    # 4. Validate primary metrics
    valid_primary_metrics = [
        metric for metric in selected_primary_metrics 
        if metric in primary_metric_set
    ] or None
    logger.debug(f"valid_primary_metrics{valid_primary_metrics}")
    
    # 5. Handle selected secondary metrics based on primary validation
    if not valid_primary_metrics and selected_secondary_metrics:
        # If no valid primary metrics, collect eligible secondary metrics
        valid_primary_metrics = []
        metrics_to_remove = []

        for metric in selected_secondary_metrics:
            if metric in primary_metric_set or metric in secondary_metric_set:
                valid_primary_metrics.append(metric)
                metrics_to_remove.append(metric)
                primary_metric_set.add(metric)
                secondary_metric_set.discard(metric)

        # Remove processed metrics from selected_secondary_metrics
        for metric in metrics_to_remove:
            selected_secondary_metrics.remove(metric)
    else:
        # If we have valid primary metrics, move appropriate metrics to secondary
        for metric in selected_secondary_metrics:
            if metric in primary_metric_set:
                primary_metric_set.remove(metric)
                secondary_metric_set.add(metric)

    primary_metric_value = valid_primary_metrics if valid_primary_metrics is not None else DEFAULT_PRIMARY_METRICS if reporting_form == '0420162' else DEFAULT_PRIMARY_METRICS_158

    # 6. Validate secondary metrics
    valid_secondary_metrics = [
        metric for metric in selected_secondary_metrics 
        if metric in secondary_metric_set
    ] or None

    secondary_metric_value = valid_secondary_metrics if valid_secondary_metrics is not None else []

    # 7. Create options based on the metric sets
    primary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in primary_metric_set
    ]

    secondary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in secondary_metric_set
    ]

    return primary_metric_options, secondary_metric_options, primary_metric_value, secondary_metric_value


