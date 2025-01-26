from config.logging_config import get_logger
from typing import List, Optional, Tuple
logger = get_logger(__name__)


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
        ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses', 
         'ceded_premiums', 'ceded_losses'],
        lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)) - 
                 (d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0))
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


def get_checklist_config(selected_metrics: List[str], reporting_form: str) -> Tuple[bool, Optional[List[str]]]:
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

    return checklist_mode, sorted(list(allowed_types))