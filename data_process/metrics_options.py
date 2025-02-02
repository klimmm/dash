from typing import List, Dict, Optional, Any, Tuple

from config.default_values import DEFAULT_METRICS, DEFAULT_METRICS_158
from config.logging_config import get_logger
from constants.metrics import METRICS_OPTIONS, BUSINESS_TYPE_OPTIONS
from application.components.checklist import ChecklistComponent

logger = get_logger(__name__)


def get_base_metrics(reporting_form):
    if reporting_form == '0420162':
        base_metrics = {'new_sums', 'ceded_premiums', 'commissions_interm',
                        'claims_reported', 'direct_losses', 'sums_end',
                        'ceded_losses', 'new_contracts', 'claims_settled',
                        'contracts_end', 'premiums_interm', 'inward_losses',
                        'inward_premiums', 'direct_premiums'}
    else:
        base_metrics = {'ceded_premiums', 'total_losses',
                        'ceded_losses', 'total_premiums'}
    return base_metrics


def get_additional_metrics(reporting_form):
    if reporting_form == '0420162':
        additional_metrics = {'net_loss_ratio', 'ceded_premiums_ratio',
                              'inward_loss_ratio', 'average_loss', 'net_result',
                              'average_sum_insured', 'direct_loss_ratio',
                              'ceded_losses_to_ceded_premiums_ratio',
                              'net_premiums', 'average_new_sum_insured',
                              'net_balance', 'total_losses', 
                              'average_new_premium', 'ceded_ratio_diff',
                              'commissions_rate', 'net_losses',
                              'gross_loss_ratio', 'total_premiums',
                              'gross_result', 'ceded_losses_ratio',
                              'effect_on_loss_ratio', 'average_rate',
                              'premiums_interm_ratio'}
    else:
        additional_metrics = {'net_premiums', 'net_loss_ratio',
                              'ceded_premiums_ratio', 'gross_loss_ratio',
                              'net_result', 'ceded_ratio_diff', 'gross_result',
                              'ceded_losses_ratio', 'effect_on_loss_ratio',
                              'net_losses', 'net_balance',
                              'ceded_losses_to_ceded_premiums_ratio'}
    return additional_metrics


def get_metric_options(
    reporting_form: str,
    selected_metrics: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Any]:
    """
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    """
    logger.info(f"Entering get_metric_options with reporting_form={reporting_form}, "
                f"selected_metrics={selected_metrics}")
    try:

        base_metrics = set(get_base_metrics(reporting_form))
        logger.debug(f"Allowed basic metrics for form '{reporting_form}': {base_metrics}")
        additional_metrics = set(get_additional_metrics(reporting_form))
        base_metrics.update(additional_metrics)

        if isinstance(selected_metrics, str):
            selected_metrics = [selected_metrics]
        else:
            selected_metrics = selected_metrics or []
        logger.debug(f"Normalized selected metrics: {selected_metrics}")

        metrics_set = base_metrics.copy()
        logger.debug(f"Combined metrics set: {metrics_set}")

        valid_metrics = [metric for metric in selected_metrics if metric in metrics_set] or None
        logger.info(f"Valid metrics after validation: {valid_metrics}")

        if valid_metrics:
            metric_value = valid_metrics
        else:
            metric_value = DEFAULT_METRICS if reporting_form == '0420162' else DEFAULT_METRICS_158
        logger.info(f"Final metric value selected: {metric_value}")

        metric_options = [opt for opt in METRICS_OPTIONS if opt['value'] in metrics_set]
        logger.debug(f"Generated {len(metric_options)} metric option(s).")

        logger.info("Exiting get_metric_options successfully.")
        return metric_options, metric_value

    except Exception as exc:
        logger.exception("Error occurred in get_metric_options")
        raise


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