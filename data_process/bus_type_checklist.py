from typing import List, Optional, Tuple

from application.components.checklist import ChecklistComponent
from config.logging_config import get_logger
from constants.metrics import BUSINESS_TYPE_OPTIONS

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
