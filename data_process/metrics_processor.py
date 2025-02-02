from typing import List, Optional, Set
import pandas as pd

from config.default_values import DEFAULT_METRICS, DEFAULT_METRICS_158
from config.logging_config import get_logger
from constants.metrics import METRICS 


class MetricsProcessor:
    logger = get_logger(__name__)

    DEFAULT_METRICS = DEFAULT_METRICS 
    DEFAULT_METRICS_158 = DEFAULT_METRICS_158
    valid_metrics = [
        'direct_premiums',
        'direct_losses',
        'inward_premiums',
        'inward_losses',
        'ceded_premiums',
        'ceded_losses',
        'new_contracts',
        'contracts_end',
        'premiums_interm',
        'commissions_interm',
        'total_premiums',
        'total_losses',
        'net_premiums',
        'net_losses',
        'average_new_premium',
        'average_loss',
        'average_rate',
        'ceded_premiums_ratio',
        'ceded_losses_ratio',
        'premiums_interm_ratio',
        'commissions_rate'
    ]

    @staticmethod
    def timer(func):
        """A simple decorator to time function execution."""
        import time
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(f"{func.__name__} took {(end - start) * 1000:.2f}ms to execute")
            return result
        return wrapper

    # Local alias for the timer decorator for ease of use.
    _timer = timer

    @staticmethod
    def get_base_metrics(reporting_form: str) -> Set[str]:
        if reporting_form == '0420162':
            base_metrics = {
                'new_sums', 'ceded_premiums', 'commissions_interm',
                'claims_reported', 'direct_losses', 'sums_end',
                'ceded_losses', 'new_contracts', 'claims_settled',
                'contracts_end', 'premiums_interm', 'inward_losses',
                'inward_premiums', 'direct_premiums'
            }
        else:
            base_metrics = {
                'ceded_premiums', 'total_losses',
                'ceded_losses', 'total_premiums'
            }
        return base_metrics

    @staticmethod
    def get_additional_metrics(reporting_form: str) -> Set[str]:
        if reporting_form == '0420162':
            additional_metrics = {
                'net_loss_ratio', 'ceded_premiums_ratio',
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
                'premiums_interm_ratio'
            }
        else:
            additional_metrics = {
                'net_premiums', 'net_loss_ratio',
                'ceded_premiums_ratio', 'gross_loss_ratio',
                'net_result', 'ceded_ratio_diff', 'gross_result',
                'ceded_losses_ratio', 'effect_on_loss_ratio',
                'net_losses', 'net_balance',
                'ceded_losses_to_ceded_premiums_ratio'
            }
        return additional_metrics

    @staticmethod
    def get_metrics_options(form_ids=None, metric_types=None, valid_metrics=None, metrics_dict=METRICS):
        """
        Generate dropdown options from the metrics definitions with optional filtering by forms,
        types and metric names.
        """
        if valid_metrics is None:
            valid_metrics = MetricsProcessor.valid_metrics

        # If form_ids is a string, convert it to a list
        if isinstance(form_ids, str):
            form_ids = [form_ids]

        return [
            {'label': metrics_dict[metric][4], 'value': metric}
            for metric in valid_metrics
            if (metric in metrics_dict and
                (form_ids is None or any(form_id in metrics_dict[metric][3] for form_id in form_ids)) and
                (metric_types is None or metrics_dict[metric][2] in metric_types))
        ]

    @staticmethod
    def validate_metric_values(
        reporting_form: str,
        selected_metrics: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Validate the provided selected metrics against the allowed metrics for the given form,
        and return the validated metric value list.
        If no valid metrics are provided, default values are returned.
        """
        MetricsProcessor.logger.info(
            f"Entering get_metric_options with reporting_form={reporting_form}, "
            f"selected_metrics={selected_metrics}"
        )
        try:
            base_metrics = MetricsProcessor.get_base_metrics(reporting_form)
            additional_metrics = MetricsProcessor.get_additional_metrics(reporting_form)
            allowed_metrics = base_metrics.union(additional_metrics)

            if isinstance(selected_metrics, str):
                selected_metrics = [selected_metrics]
            else:
                selected_metrics = selected_metrics or []

            valid_metrics_list = [metric for metric in selected_metrics if metric in allowed_metrics]
            if valid_metrics_list:
                metric_value = valid_metrics_list
            else:
                metric_value = (MetricsProcessor.DEFAULT_METRICS
                                if reporting_form == '0420162'
                                else MetricsProcessor.DEFAULT_METRICS_158)
            MetricsProcessor.logger.info(f"Final metric value selected: {metric_value}")
            return metric_value

        except Exception:
            MetricsProcessor.logger.exception("Error occurred in get_metric_options")
            raise

    @staticmethod
    @_timer
    def get_required_metrics(
        selected_metrics: List[str],
        business_type_selection: Optional[List[str]] = None
    ) -> List[str]:
        """
        Returns an ordered list of required metrics by grouping each selected metric
        with its dependencies. For each selected metric, its dependencies (and nested
        dependencies) are added immediately after it. For example, if the selected
        metrics are ['total_premiums', 'total_losses'] and:
            - total_premiums depends on direct_premiums and inward_premiums
            - total_losses depends on direct_losses and inward_losses
        the output will be:
            ['total_premiums', 'direct_premiums', 'inward_premiums',
             'total_losses', 'direct_losses', 'inward_losses']
        """
        # Remove known suffixes (if any) from selected metrics.
        suffix_list = ['_market_share_q_to_q_change', '_q_to_q_change', '_market_share']
        clean_metrics = [
            metric[:-len(matched_suffix)]
            if (matched_suffix := next((s for s in suffix_list if metric.endswith(s)), None))
            else metric
            for metric in selected_metrics
        ]

        result = []
        visited = set()

        def dfs(metric: str) -> List[str]:
            """
            Recursively collect dependencies for a given metric.
            Dependencies are processed in sorted order.
            """
            deps_order = []
            if metric not in METRICS:
                return deps_order
            for dep in sorted(METRICS[metric][0]):
                # Filter out dependencies based on business type if specified.
                if business_type_selection:
                    if 'direct' not in business_type_selection and dep in ('direct_premiums', 'direct_losses'):
                        continue
                    if 'inward' not in business_type_selection and dep in ('inward_premiums', 'inward_losses'):
                        continue
                if dep not in visited:
                    visited.add(dep)
                    deps_order.append(dep)
                    deps_order.extend(dfs(dep))
            return deps_order

        for metric in clean_metrics:
            if metric not in visited:
                visited.add(metric)
                result.append(metric)
                result.extend(dfs(metric))

        MetricsProcessor.logger.debug(f"Grouped required metrics: {result}")
        return result

    @staticmethod
    def get_calculation_order(metrics: Set[str]) -> List[str]:
        """Fast calculation order with minimal operations."""
        ordered = []
        remaining = metrics.copy()
        deps_cache = {m: set(METRICS[m][0]) if m in METRICS else set() for m in metrics}

        while remaining:
            available = remaining - {m for m in remaining if deps_cache[m] & remaining}
            if not available:
                break
            ordered.extend(sorted(available))
            remaining -= available
        return ordered

    @staticmethod
    @_timer
    def calculate_metrics(
        df: pd.DataFrame,
        selected_metrics: List[str],
        required_metrics: List[str]
    ) -> pd.DataFrame:
        """
        Optimized metric calculation minimizing DataFrame operations.
        If the required metrics are already in the DataFrame then no calculations are performed.
        Otherwise, metrics are computed in a dependency order.
        """
        existing = df['metric'].unique()
        selected_set = set(selected_metrics)

        if all(m in existing for m in required_metrics):
            return df.loc[df['metric'].isin(selected_set)]

        calculation_order = MetricsProcessor.get_calculation_order(set(required_metrics))
        MetricsProcessor.logger.warning(f"calculation_order {calculation_order}")
        grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]

        metric_calcs = {
            m: METRICS[m][1]
            for m in calculation_order
            if m in METRICS and (
                m in selected_set or
                any(m in METRICS[dep][0] for dep in selected_set if dep in METRICS)
            )
        }

        all_groups = []
        for _, group in df.groupby(grouping_cols):
            metrics = dict(zip(group['metric'], group['value']))
            base = {col: group[col].iloc[0] for col in grouping_cols}

            new_metrics = []
            for metric in calculation_order:
                if metric not in metrics and metric in metric_calcs:
                    try:
                        val = metric_calcs[metric](metrics)
                        metrics[metric] = val
                        if metric in selected_set:
                            new_metrics.append({
                                'metric': metric,
                                'value': val,
                                **base
                            })
                    except Exception:
                        continue

            if new_metrics:
                all_groups.extend(new_metrics)

        if all_groups:
            new_df = pd.DataFrame(all_groups)
            df_filtered = df.loc[df['metric'].isin(selected_set)]
            result = pd.concat([df_filtered, new_df], ignore_index=True)
            result.drop_duplicates(subset=grouping_cols + ['metric'], keep='last', inplace=True)
        else:
            result = df.loc[df['metric'].isin(selected_set)]
        return result