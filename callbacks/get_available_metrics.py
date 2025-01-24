from config.logging_config import get_logger
from callbacks.metrics import METRIC_CALCULATIONS, FORM_METRICS
from constants.filter_options import METRICS_OPTIONS
from typing import List, Dict, Any, Optional, Tuple
import json
from dataclasses import dataclass
from config.default_values import DEFAULT_PRIMARY_METRICS, DEFAULT_PRIMARY_METRICS_158


logger = get_logger(__name__)

def can_calculate_metric(metric_name, available_fields, metrics_dict, calculated_metrics=None, depth=0):
    """
    Recursively check if a metric can be calculated given available fields and other calculable metrics.
    Returns False if all optional metrics are unavailable.
    """
    indent = "  " * depth
    logger.debug(f"{indent}Analyzing metric: {metric_name}")
    
    if calculated_metrics is None:
        calculated_metrics = set()
        
    if metric_name in calculated_metrics:
        logger.debug(f"{indent}✓ {metric_name} was already calculated")
        return True
        
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
            
            if field not in available_fields and field not in calculated_metrics:
                if field in metrics_dict:
                    logger.debug(f"{indent}➜ {field} is a calculated metric, checking recursively...")
                    if not can_calculate_metric(field, available_fields, metrics_dict, calculated_metrics.copy(), depth + 1):
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
            if field in available_fields:
                logger.debug(f"{indent}✓ {field} is available directly")
                has_available_field = True
                continue
                
            # If field is a calculated metric
            if field in metrics_dict:
                logger.debug(f"{indent}➜ {field} is a calculated metric, checking recursively...")
                if can_calculate_metric(field, available_fields, metrics_dict, calculated_metrics, depth + 1):
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


def get_available_metrics(available_fields, metrics_dict=METRIC_CALCULATIONS):
    """
    Determine which metrics can be calculated based on available fields,
    accounting for metric dependencies and optional fields.
    """
    logger.debug(f"\nStarting metric analysis with available fields: {available_fields}")
    available_metrics = {}
    calculated_metrics = set()
    
    iteration = 1
    # Keep trying to find new calculable metrics until no more can be found
    while True:
        logger.debug(f"\nIteration {iteration}")
        metrics_added = False
        
        for metric_name, (required_fields, calc_function) in metrics_dict.items():
            if metric_name not in available_metrics:
                logger.debug(f"\nAnalyzing metric: {metric_name}")
                if can_calculate_metric(metric_name, available_fields, metrics_dict, calculated_metrics):
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


def explain_metric_calculation(metric_name, available_fields, metrics_dict=METRIC_CALCULATIONS):
    """
    Explain how a metric can be calculated, showing the dependency chain
    and which fields are optional.
    """
    logger.debug(f"\nExplaining calculation path for: {metric_name}")
    
    def _explain_recursive(metric_name, depth=0):
        indent = "  " * depth
        logger.debug(f"{indent}Analyzing {metric_name}")
        
        if metric_name not in metrics_dict:
            if metric_name in available_fields:
                logger.debug(f"{indent}✓ Field available directly")
                return f"{indent}✓ {metric_name} (available directly)"
            logger.debug(f"{indent}✗ Field not available")
            return f"{indent}✗ {metric_name} (not available)"
            
        required_fields = metrics_dict[metric_name][0]
        calc_function = metrics_dict[metric_name][1]
        calc_str = str(calc_function)
        
        logger.debug(f"{indent}Checking dependencies for {metric_name}")
        explanation = [f"{indent}{metric_name} requires:"]
        
        for field in required_fields:
            logger.debug(f"{indent}Checking field: {field}")
            if f"get('{field}', 0)" in calc_str:
                if field in available_fields:
                    logger.debug(f"{indent}✓ Optional field available")
                    explanation.append(f"{indent}  ✓ {field} (available, optional)")
                else:
                    logger.debug(f"{indent}○ Optional field missing, will use 0")
                    explanation.append(f"{indent}  ○ {field} (missing but optional, will use 0)")
            else:
                explanation.append(_explain_recursive(field, depth + 1))
                
        return '\n'.join(explanation)
    
    return _explain_recursive(metric_name)

def get_premium_loss_state(metrics: List[str], reporting_form: str) -> Tuple[bool, Optional[List[str]]]:
    if not metrics:
        return True, ['direct']

    is_form_158 = reporting_form == '0420158'
    states = {
        ('total_premiums', 'total_losses'): 
            (True, ['direct', 'inward']) if is_form_158 else (False, ['direct', 'inward']),
        ('ceded_premiums', 'ceded_losses', 'ceded_premiums_ratio',
         'ceded_losses_to_ceded_premiums_ratio', 'net_premiums', 'net_losses'):
            (True, ['direct', 'inward']),
        ('inward_premiums', 'inward_losses'): 
            (True, ['inward']),
        ('direct_premiums', 'direct_losses'): (True, ['direct'])
    }
    
    result_bool = False  # Change initial value to False
    result_states = set()
    
    # Check each metric in the input list
    for metric in metrics:
        found = False
        for metrics_group, (bool_state, state_list) in states.items():
            if metric in metrics_group:
                found = True
                # Update the boolean state
                result_bool = result_bool or bool_state
                # Always add states to the result set if they exist
                if state_list:
                    result_states.update(state_list)
                break
        if not found:
            result_states.add('direct')
    
    # If no states were collected, use default
    if not result_states:
        result_states.add('direct')

    logger.debug(f"metric: {metric}")
    logger.debug(f"readonly: {result_bool}")
    logger.debug(f"values: {sorted(list(result_states))}")
    return result_bool, sorted(list(result_states))


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


    # 2. Determine default metrics sets
    primary_metric_set = allowed_basic_metrics.copy()
    secondary_metric_set = available_calculated_metrics.copy()

    # 3. Handle selected primary metrics that are in secondary set
    for metric in selected_primary_metrics:
        if metric in secondary_metric_set:
            primary_metric_set.add(metric)
            secondary_metric_set.remove(metric)
            
    # 4. Validate primary metrics
    valid_primary_metrics = [
        metric for metric in selected_primary_metrics 
        if metric in primary_metric_set
    ] or None

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

    valid_primary_metrics = valid_primary_metrics if valid_primary_metrics is not None else DEFAULT_PRIMARY_METRICS if reporting_form == '0420162' else DEFAULT_PRIMARY_METRICS_158

    # 6. Validate secondary metrics
    valid_secondary_metrics = [
        metric for metric in selected_secondary_metrics 
        if metric in secondary_metric_set
    ] or None

    valid_secondary_metrics = valid_secondary_metrics if valid_secondary_metrics is not None else []

    # 7. Create options based on the metric sets
    primary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in primary_metric_set
    ]

    secondary_options = [
        opt for opt in METRICS_OPTIONS 
        if opt['value'] in secondary_metric_set
    ]

    return {
        'primary_y_metric_options': primary_options,
        'secondary_y_metric_options': secondary_options,
        'primary_metric': valid_primary_metrics,
        'secondary_metric': valid_secondary_metrics
    }
