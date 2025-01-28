from typing import List, Dict, Optional, Any
from callbacks.get_available_metrics import get_available_metrics
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158
from constants.filter_options import METRICS_OPTIONS
from config.logging_config import get_logger
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
    """
    Get metric options based on reporting form and selected metrics.
    """
    logger.info(f"Starting get_metric_options with reporting_form={reporting_form}")
    logger.debug(f"Input parameters: selected_primary_metrics={selected_primary_metrics}, "
                f"selected_secondary_metrics={selected_secondary_metrics}")

    # 1. Initialize and normalize inputs
    allowed_basic_metrics = FORM_METRICS.get(reporting_form, set())
    logger.debug(f"Allowed basic metrics for form {reporting_form}: {allowed_basic_metrics}")

    available_calculated_metrics = set(get_available_metrics(allowed_basic_metrics))
    logger.debug(f"Available calculated metrics: {available_calculated_metrics}")

    # Normalize input lists
    selected_primary_metrics = [selected_primary_metrics] if isinstance(selected_primary_metrics, str) else (selected_primary_metrics or [])
    selected_secondary_metrics = [selected_secondary_metrics] if isinstance(selected_secondary_metrics, str) else (selected_secondary_metrics or [])
    logger.debug(f"Normalized selected primary metrics: {selected_primary_metrics}")
    logger.debug(f"Normalized selected secondary metrics: {selected_secondary_metrics}")

    # 2. Determine default metrics sets
    primary_metric_set = allowed_basic_metrics.copy()
    secondary_metric_set = available_calculated_metrics.copy()
    logger.debug(f"Initial primary metric set: {primary_metric_set}")
    logger.debug(f"Initial secondary metric set: {secondary_metric_set}")

    # 3. Handle selected primary metrics that are in secondary set
    for metric in selected_primary_metrics:
        if metric in secondary_metric_set:
            logger.info(f"Moving metric '{metric}' from secondary to primary set")
            primary_metric_set.add(metric)
            secondary_metric_set.remove(metric)

    # 4. Validate primary metrics
    valid_primary_metrics = [
        metric for metric in selected_primary_metrics 
        if metric in primary_metric_set
    ] or None
    logger.info(f"Valid primary metrics after validation: {valid_primary_metrics}")
    
    # 5. Handle selected secondary metrics based on primary validation
    if not valid_primary_metrics and selected_secondary_metrics:
        logger.info("No valid primary metrics found, attempting to use secondary metrics as primary")
        valid_primary_metrics = []
        metrics_to_remove = []

        for metric in selected_secondary_metrics:
            if metric in primary_metric_set or metric in secondary_metric_set:
                logger.info(f"Converting secondary metric '{metric}' to primary metric")
                valid_primary_metrics.append(metric)
                metrics_to_remove.append(metric)
                primary_metric_set.add(metric)
                secondary_metric_set.discard(metric)

        # Remove processed metrics from selected_secondary_metrics
        for metric in metrics_to_remove:
            selected_secondary_metrics.remove(metric)
            logger.debug(f"Removed processed metric '{metric}' from selected secondary metrics")
    else:
        logger.debug("Processing secondary metrics with valid primary metrics present")
        for metric in selected_secondary_metrics:
            if metric in primary_metric_set:
                logger.info(f"Moving metric '{metric}' from primary to secondary set")
                primary_metric_set.remove(metric)
                secondary_metric_set.add(metric)

    # Determine primary metric value based on validation results
    if valid_primary_metrics is not None and len(valid_primary_metrics) > 0:
        primary_metric_value = valid_primary_metrics
    else:
        primary_metric_value = DEFAULT_PRIMARY_METRICS if reporting_form == '0420162' else DEFAULT_PRIMARY_METRICS_158
    logger.info(f"Final primary metric value: {primary_metric_value}")

    # 6. Validate secondary metrics
    valid_secondary_metrics = [
        metric for metric in selected_secondary_metrics 
        if metric in secondary_metric_set
    ] or None
    logger.info(f"Valid secondary metrics after validation: {valid_secondary_metrics}")

    secondary_metric_value = valid_secondary_metrics if valid_secondary_metrics is not None else []
    logger.debug(f"Final secondary metric value: {secondary_metric_value}")

    # 7. Create options based on the metric sets
    primary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in primary_metric_set
    ]
    logger.debug(f"Generated primary metric options: {len(primary_metric_options)} options")

    secondary_metric_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in secondary_metric_set
    ]
    logger.debug(f"Generated secondary metric options: {len(secondary_metric_options)} options")

    logger.info("Successfully completed get_metric_options")
    
    return primary_metric_options, secondary_metric_options, primary_metric_value, secondary_metric_value