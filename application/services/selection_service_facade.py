# SelectionServiceFacade.py
from typing import Dict, List, Optional
import pandas as pd

class SelectionServiceFacade:
    """
    Facade that provides simplified access to UI selection options and filtering criteria.
    Encapsulates functionality for insurer options and time period selections.
    """
    def __init__(
        self,
        domain_service
    ):
        insurers_service = domain_service.insurers_service
        metrics_service = domain_service.metrics_service
        period_service = domain_service.period_service
        self.config = insurers_service.config
        self.columns = self.config.columns
        self.value_types = self.config.value_types
        self.special_values = self.config.special_values
        self.view_modes = self.config.view_modes
        self.logger = self.config.logger
        self.insurers_service = insurers_service
        self.metrics_service = metrics_service
        self.period_service = period_service

    def __getattr__(self, name):
        return getattr(self.period_service, name)

    def get_insurer_options(
        self,
        df: pd.DataFrame,
        selected_insurers: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """Generate insurer options for UI dropdown."""
        ranked_insurers = self._get_ranked_insurers(df, metrics)

        self.logger.warning(f"selected_insurers in options {selected_insurers}")

        if ranked_insurers is None and selected_insurers:
            return [{'label': self.insurers_service.get_insurer_label(selected_insurers[0]),
                    'value': selected_insurers[0]}]

        if not selected_insurers:
            selected_insurers = [self.special_values.TOTAL_INSURER]

        # Case: Top-N selected - return no other options
        if selected_insurers[0].startswith('top-'):
            top_n = int(selected_insurers[0].split('-')[1])
            return [{"label": f"Топ-{top_n}", "value": f"top-{top_n}"}]

        return [{'label': self.insurers_service.get_insurer_label(ins), 'value': ins}
                for ins in ranked_insurers.index]

    def get_ordered_insurers(
        self,
        df: pd.DataFrame,
        selected_insurers: List[str],
        metrics: List[str]
    ) -> List[str]:
        """Get list of insurers required for display based on selection criteria."""
        ranked_insurers = self._get_ranked_insurers(df, metrics)

        if not selected_insurers:
            output = [ins for ins in ranked_insurers.index]
            output.extend([self.special_values.TOTAL_INSURER])
            return output

        # Case 1: Total insurer selected
        if self.special_values.TOTAL_INSURER in selected_insurers:
            output = [ins for ins in ranked_insurers.index]
            output.extend([self.special_values.TOTAL_INSURER])
            return output

        # Case 2: Top-N selection
        if selected_insurers[0].startswith('top-'):
            top_n = int(selected_insurers[0].split('-')[1])
            self.logger.debug(f"ranked_insurers {ranked_insurers}")
            ranked_insurers = pd.to_numeric(ranked_insurers, errors='coerce')
            output = ranked_insurers.nlargest(top_n).index.tolist()
            self.logger.debug(f"output {output}")
            output.extend([f"top-{top_n}"])
            self.logger.debug(f"output {output}")
            return output

        # Case 3: All available insurers - return in value order
        if self.special_values.ALL_INSURERS in selected_insurers:
            return [ins for ins in ranked_insurers.index]

        # Case 4: Specific insurers selected - return them in value order
        return [ins for ins in ranked_insurers.index if ins in selected_insurers]

    def _get_ranked_insurers(
        self,
        df: pd.DataFrame,
        metrics: Optional[List[str]]
    ) -> pd.Series:
        """Get ranked insurers based on metrics."""
        ordered_metrics = self.metrics_service.get_ordered_nodes(metrics, df)
        base_filter = (
            (df[self.config.columns.METRIC] == ordered_metrics[0]) &
            (df[self.config.columns.VALUE_TYPE] == self.config.value_types.BASE)
        )
        latest_period = df[base_filter][self.config.columns.YEAR_QUARTER].max()
        ranking_df = df[
            base_filter &
            (df[self.config.columns.YEAR_QUARTER] == latest_period) &
            (~df[self.config.columns.INSURER].isin(
                self.config.special_values.NON_INSURERS))
        ]
        ranked_insurers = ranking_df.groupby(
            self.config.columns.INSURER
        )[
            self.config.columns.VALUE
        ].sum().sort_values(ascending=False)
        return ranked_insurers