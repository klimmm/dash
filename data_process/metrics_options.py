from typing import List, Dict, Optional, Tuple, Any
from application.components.checklist import ChecklistComponent
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158
from config.logging_config import get_logger
from constants.metrics import METRICS, METRICS_OPTIONS, BUSINESS_TYPE_OPTIONS

logger = get_logger(__name__)


def get_checklist_config(
    selected_metrics: List[str],
    reporting_form: str, 
    current_checklist_values: List[str]
) -> Tuple[bool, Optional[List[str]]]:

    if not selected_metrics:
        return True, ['direct']

    is_form_158 = reporting_form == '0420158'

    metric_configs = {
        ('total_premiums', 'total_losses'): 
            (True, ['direct', 'inward']) if is_form_158 else (False, ['direct', 'inward']),
        ('ceded_premiums', 'ceded_losses', 'ceded_premiums_ratio',
         'ceded_losses_to_ceded_premiums_ratio', 'net_premiums', 'net_losses'):
            (True, ['direct', 'inward']),
        ('inward_premiums', 'inward_losses'): 
            (True, ['inward']),
        ('direct_premiums', 'direct_losses'): 
            (True, ['direct'])
    }

    checklist_mode = False
    allowed_types = set()

    for metric in selected_metrics:
        metric_found = False
        for metric_group, (is_readonly, type_list) in metric_configs.items():
            if metric in metric_group:
                metric_found = True
                checklist_mode = checklist_mode or is_readonly
                allowed_types.update(type_list)
                break
        if not metric_found:
            allowed_types.add('direct')

    if not allowed_types:
        allowed_types.add('direct')

    logger.debug(f"metric: {metric}")
    logger.debug(f"readonly: {checklist_mode}")
    logger.debug(f"values: {sorted(list(allowed_types))}")

    allowed_types = sorted(list(allowed_types))

    checklist_values = allowed_types or current_checklist_values
    business_type_checklist = checklist_values or []
    checklist_component = ChecklistComponent.create_checklist(
        id='business-type-checklist',
        options=BUSINESS_TYPE_OPTIONS,
        value=checklist_values,
        readonly=checklist_mode
    )

    return checklist_component, business_type_checklist


def can_calculate_metric(metric_name, base_metrics, metrics_dict=METRICS, depth=0):
    """
    Recursively check if a metric can be calculated given available fields and other calculable metrics.
    Returns False if all optional metrics are unavailable.
    """
    indent = "  " * depth
    logger.debug(f"{indent}Analyzing metric: {metric_name}")

    is_ratio = metric_name.endswith('_ratio') or metric_name.endswith('_rate') or metric_name.endswith('_diff') or metric_name.startswith('average_')
    logger.debug(f"{indent}Is ratio metric: {is_ratio}")

    metric_info = metrics_dict[metric_name]
    required_fields = set(metric_info[0])
    calc_lambda = metric_info[1]

    logger.debug(f"{indent}Required fields for {metric_name}: {required_fields}")

    if is_ratio:
        logger.debug(f"{indent}Checking fields for ratio metric...")
        # Track available ratio fields
        available_ratio_fields = True

        for field in required_fields:
            logger.debug(f"{indent}Checking ratio field: {field}")

            if field not in base_metrics:
                if field in metrics_dict:
                    logger.debug(f"{indent}➜ {field} is a calculated metric, checking recursively...")
                    if not can_calculate_metric(field, base_metrics, metrics_dict, depth + 1):
                        logger.debug(f"{indent}✗ Cannot calculate ratio field {field}")
                        available_ratio_fields = False
                        break
                else:
                    logger.debug(f"{indent}✗ Ratio field {field} is not available")
                    available_ratio_fields = False
                    break
            else:
                logger.debug(f"{indent}✓ {field} is available")

        if not available_ratio_fields:
            logger.debug(f"{indent}✗ Cannot calculate ratio metric {metric_name}")
            return False
    else:
        # Track if we have at least one available field
        has_available_field = False

        # Check each required field
        for field in required_fields:
            logger.debug(f"{indent}Checking field: {field}")

            # Test if this specific field is optional
            test_dict = {f: 1 for f in required_fields if f != field}
            try:
                calc_lambda(test_dict)
                logger.debug(f"{indent}Field {field} is optional (works without it)")
                is_optional = True
            except:
                logger.debug(f"{indent}Field {field} is required (fails without it)")
                is_optional = False

            # If field is directly available
            if field in base_metrics:
                logger.debug(f"{indent}✓ {field} is available directly")
                has_available_field = True
                continue

            # If field is a calculated metric
            if field in metrics_dict:
                logger.debug(f"{indent}➜ {field} is a calculated metric, checking recursively...")
                if can_calculate_metric(field, base_metrics, metrics_dict, depth + 1):
                    logger.debug(f"{indent}✓ Can calculate dependency: {field}")
                    has_available_field = True
                    continue
                elif not is_optional:
                    logger.debug(f"{indent}✗ Cannot calculate required dependency: {field}")
                    return False
                continue

            # If field is required but not available
            if not is_optional:
                logger.debug(f"{indent}✗ {field} is required but not available")
                return False

        # Return false if no fields are available, even if they're all optional
        if not has_available_field:
            logger.debug(f"{indent}✗ No fields are available for {metric_name}")
            return False

    logger.debug(f"{indent}✓ Can calculate: {metric_name}")
    return True


def get_available_metrics(base_metrics, metrics_dict=METRICS):
    """
    Determine which metrics can be calculated based on available fields,
    accounting for metric dependencies and optional fields.
    """
    logger.debug(f"\nStarting metric analysis with available fields: {base_metrics}")
    available_metrics = {}
    calculated_metrics = set()

    iteration = 1
    # Keep trying to find new calculable metrics until no more can be found
    while True:
        logger.debug(f"\nIteration {iteration}")
        metrics_added = False

        for metric_name, (required_fields, calc_function, *_) in metrics_dict.items():
            if metric_name not in available_metrics:
                logger.debug(f"\nAnalyzing metric: {metric_name}")
                if can_calculate_metric(metric_name, base_metrics, metrics_dict):
                    logger.debug(f"✓ Adding {metric_name} to available metrics")
                    available_metrics[metric_name] = calc_function
                    calculated_metrics.add(metric_name)
                    metrics_added = True
                else:
                    logger.debug(f"✗ Cannot calculate {metric_name} yet")

        if not metrics_added:
            logger.debug(f"\nNo new metrics added in iteration {iteration}, stopping")
            break

        iteration += 1

    logger.debug(f"available_metrics:, {list(available_metrics.keys())}")
    available_metrics = list(available_metrics.keys())

    return available_metrics


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
    allowed_basic_metrics = {metric for metric, (_, _, _, forms, _) in METRICS.items() if reporting_form in forms}

    logger.debug(f"Allowed basic metrics for form {reporting_form}: {allowed_basic_metrics}")

    available_calculated_metrics = set(get_available_metrics(allowed_basic_metrics))
    logger.debug(f"Available calculated metrics: {available_calculated_metrics}")
    allowed_basic_metrics.update(available_calculated_metrics)


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
    logger.debug(f"METRICS_OPTIONS: {METRICS_OPTIONS}")
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