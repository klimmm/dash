from typing import List, Dict, Callable, Tuple
import pandas as pd

MetricName = str
MetricComputation = Callable[[Dict[str, float]], float]
MetricDependencies = List[str]
MetricFormula = Tuple[MetricDependencies, MetricComputation]

class MetricsProcessor:
    def __init__(
        self,
        metrics_formulas=None
    ):
        self.metrics_formulas = metrics_formulas
        self._validate_formulas()

    def _validate_formulas(self):
        """Validate that formulas have the expected structure."""
        if not isinstance(self.metrics_formulas, dict):
            raise TypeError("metrics_formulas must be a dictionary")

        for metric, formula in self.metrics_formulas.items():
            if not isinstance(formula, tuple) or len(formula) != 2:
                raise ValueError(f"Formula for {metric} must be a tuple of (dependencies, computation_function)")

            deps, func = formula
            if not isinstance(deps, list):
                raise TypeError(f"Dependencies for {metric} must be a list")

            if not callable(func):
                raise TypeError(f"Computation for {metric} must be a callable function")

    def get_required_metrics(self, metrics: List[str], logger, config) -> List[str]:
        """Determine required metrics including dependencies."""
        self.columns = config.columns
        self.value_types = config.value_types
        self.special_values = config.special_values
        self.logger = logger




        ordered = []
        visited = set()

        def add_metric_with_deps(metric):
            # Skip if already processed or not in definitions
            if metric in visited or metric not in self.metrics_formulas:
                return

            # Mark as visited to prevent cycles
            visited.add(metric)

            # Process all dependencies first (recursive DFS)
            for dep in self.metrics_formulas[metric][0]:
                add_metric_with_deps(dep)

            # Add this metric after all its dependencies
            ordered.append(metric)

        # Process each selected metric
        for metric in metrics:
            add_metric_with_deps(metric)

        self.logger.debug(f"required_metrics {ordered}")
        return ordered

    def calculate_metrics(
        self,
        df: pd.DataFrame,
        selected_metrics: List[str],
        required_metrics: List[str],
        logger,
        config
    ) -> pd.DataFrame:
        """Calculate derived metrics based on base metrics in the data."""
        self.columns = config.columns
        self.value_types = config.value_types
        self.special_values = config.special_values
        self.logger = logger

        selected_set = set(selected_metrics)

        # Check which required metrics are not in base and need calculation
        metrics_to_calculate = [m for m in selected_metrics
                                if self.metrics_formulas[m][0] != []]
        # Early exit if all metrics are in base
        if not metrics_to_calculate:
            result = df[df[self.columns.METRIC].isin(selected_set)]
            result[self.columns.VALUE_TYPE] = self.value_types.BASE
            return result

        grouping_cols = [col for col in df.columns
                         if col not in {self.columns.METRIC, self.columns.VALUE}]

        # Pre-compute metric calculations - single dict comprehension
        metric_calcs = {m: self.metrics_formulas[m][1] for m in required_metrics}

        self.logger.debug(f"metric_calcs {metric_calcs}")
        all_groups = []
        grouped = df.groupby(grouping_cols)

        for idx, (name, group) in enumerate(grouped):
            base = dict(zip(grouping_cols,
                            name if isinstance(name, tuple) else [name]))
            metrics = dict(zip(group[self.columns.METRIC], group[self.columns.VALUE]))

            # Single loop through calculation order
            for metric in required_metrics:
                if metric not in metrics and metric in metric_calcs:
                    try:
                        val = metric_calcs[metric](metrics)
                        metrics[metric] = val
                        if metric in selected_set:
                            all_groups.append({
                                **base,
                                self.columns.METRIC: metric,
                                self.columns.VALUE: val
                            })
                    except Exception:
                        continue

        if all_groups:
            new_df = pd.DataFrame(all_groups)
            df_filtered = df[df[self.columns.METRIC].isin(selected_set)]
            result = pd.concat([df_filtered, new_df], ignore_index=True)
            # Single operation for duplicates
            result.drop_duplicates(
                subset=grouping_cols + [self.columns.METRIC],
                keep='last',
                inplace=True
            )
        else:
            result = df[df[self.columns.METRIC].isin(selected_set)]
        result[self.columns.VALUE_TYPE] = self.value_types.BASE

        return result

    def add_custom_formula(self, metric_name: str, formula: MetricFormula) -> None:
        """Add or update a custom metric formula."""
        # Validate the formula structure
        if not isinstance(formula, tuple) or len(formula) != 2:
            raise ValueError(f"Formula for {metric_name} must be a tuple of (dependencies, computation_function)")

        deps, func = formula
        if not isinstance(deps, list):
            raise TypeError(f"Dependencies for {metric_name} must be a list")

        if not callable(func):
            raise TypeError(f"Computation for {metric_name} must be a callable function")

        # Add or update the formula
        self.metrics_formulas[metric_name] = formula
        self.logger.debug(f"Added custom formula for {metric_name}")

    def get_available_metrics(self) -> List[str]:
        """Get a list of all available metrics."""
        return list(self.metrics_formulas.keys())