from typing import Any, Dict, List, Optional, Tuple

from config.logging_config import get_logger, timer
from config.default_values import DEFAULT_METRICS, DEFAULT_METRICS_158
from core.metrics.definitions import METRICS, VALID_METRICS

logger = get_logger(__name__)


@timer
def get_metric_options(
    reporting_form: str,
    selected_metrics: Optional[List[str]] = None,
    metric_types: Optional[List[str]] = None,
    metrics_dict: Dict = METRICS
) -> Tuple[List[Dict[str, Any]], List[str]]:

    logger.info(
        f"Getting metric options: "
        f"form={reporting_form}, "
        f"selected={selected_metrics}"
    )

    try:
        # Handle single string metric input
        if isinstance(selected_metrics, str):
            selected_metrics = [selected_metrics]
        elif selected_metrics is None:
            selected_metrics = []

        # Get metrics valid for this form
        metrics_set = {
            metric_id for metric_id, metric_info in metrics_dict.items()
            if reporting_form in metric_info[3]
        }

        # Generate metric options
        metric_options = [
            {'label': metrics_dict[metric_id][4], 'value': metric_id}
            for metric_id in (VALID_METRICS or metrics_dict.keys())
            if metric_id in metrics_dict
            and metric_id in metrics_set
            and (
                not metric_types or metrics_dict[metric_id][2] in metric_types
            )
        ]

        # Filter and set selected metrics
        valid_selected = [m for m in selected_metrics if m in metrics_set]
        metric_values = valid_selected or (
            DEFAULT_METRICS if reporting_form == '0420162'
            else DEFAULT_METRICS_158
        )

        return metric_options, metric_values

    except Exception:
        logger.exception("Error in get_metric_options")
        raise