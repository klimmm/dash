from typing import List, Tuple

from config.logging import get_logger

logger = get_logger(__name__)

BUSINESS_TYPE_OPTIONS = [
    {'label': 'Прям.', 'value': 'direct'},
    {'label': 'Входящ.', 'value': 'inward'}
]


def get_checklist_config(
    selected_metrics: List[str],
    reporting_form: str,
    current_checklist_values: List[str]
) -> Tuple[bool, List[str]]:

    logger.debug(f"Input - selected_metrics: {selected_metrics}")
    logger.debug(f"Input - reporting_form: {reporting_form}")
    logger.debug(f"Input - current values: {current_checklist_values}")

    if not selected_metrics:
        logger.debug("No metrics selected, returning default")
        return False, ['direct']

    config = {
        ('total_premiums', 'total_losses'):
            (reporting_form == '0420158', ['direct', 'inward']),
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
    required_all_types = False

    # Process metrics to collect allowed types and check requirements
    for metric in selected_metrics:
        logger.debug(f"Processing metric: {metric}")

        for metric_group, (is_readonly, type_list) in config.items():
            if metric in metric_group:
                checklist_mode |= is_readonly
                allowed_types.update(type_list)

                # Check if this metric requires specific types
                if len(type_list) == 1:
                    required_all_types = True
                    logger.debug(
                        f"Single-type metric found: {metric}, requiring all")
                break

    if not allowed_types:
        logger.debug("No allowed types found, defaulting to {'direct'}")
        allowed_types = {'direct'}

    # If we have metrics requiring specific types or current selection invalid,
    # return all allowed types
    valid_current = [v for v in current_checklist_values if v in allowed_types]

    if required_all_types:
        logger.debug("Metrics require specific types, returning all allowed")
        result = (checklist_mode, sorted(allowed_types))
    elif valid_current:
        logger.debug(f"Using current valid selection: {valid_current}")
        result = (checklist_mode, valid_current)
    else:
        logger.debug("No valid current selection, using all allowed types")
        result = (checklist_mode, sorted(allowed_types))

    logger.debug(f"Final result: {result}")
    return result