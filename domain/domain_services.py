# InsurersService.py
import re
from functools import lru_cache
from typing import Dict, List, Union
import pandas as pd


class InsurersService:
    """Service for handling insurer-specific operations without metrics dependency."""

    def __init__(
        self,
        data_structure
    ):
        self.config = data_structure.config
        self.logger = self.config.logger
        self.data_structure = data_structure
        self.special_values = data_structure.config.special_values

    @lru_cache(maxsize=1024)
    def get_node_label(self, insurer_code: str) -> str:
        """Maps insurer code to display name."""
        top_match = re.match(r'^top-(\d+)$', insurer_code)
        if top_match:
            return f"Топ-{top_match.group(1)}"
        if insurer_code == self.special_values.TOTAL_INSURER:
            return "Все компании"
        return self.data_structure.get_node_label(insurer_code)


class MetricsService:
    """Specialized service for metrics that uses TreeService."""

    def __init__(self, tree_service):
        self.tree_service = tree_service

    def __getattr__(self, name):
        return getattr(self.tree_service, name)


class LinesService:
    """Specialized service for lines that uses TreeService."""

    def __init__(self, tree_service):
        self.tree_service = tree_service
        self.config = self.tree_service.config
        self.logger = self.config.logger
        self.special_values = self.config.special_values

    def get_node_label(
        self,
        code: Union[str, List[str]]
    ) -> Union[str, List[str]]:
        if code == self.special_values.TOTAL_LINES:
            return 'Всего по указанным видам'
        return self.tree_service.get_node_label(code)

    def get_ordered_nodes(
        self,
        selected_nodes: List[str],
        df: pd.DataFrame = None
    ) -> List[str]:

        output = self.tree_service(selected_nodes, df)
        if self.special_values.TOTAL_LINES in selected_nodes:
            output.append(self.special_values.TOTAL_LINES)
        return output

    def __getattr__(self, name):
        return getattr(self.tree_service, name)


class PeriodService:

    def __init__(self, config):
        self.config = config
        self.logger = self.config.logger
        self.available_quarters = {}
        self.quarter_options = {}

    def setup_period_options(self, df_158: pd.DataFrame, df_162: pd.DataFrame) -> None:
        """Initialize period options and available quarters."""
        for form_type, df in [("0420158", df_158), ("0420162", df_162)]:
            quarters = self._get_quarters_from_df(df)
            self.available_quarters[form_type] = quarters
            self.quarter_options[form_type] = [
                {'label': q, 'value': q} for q in quarters
            ]

    def _get_quarters_from_df(self, df: pd.DataFrame) -> List[str]:
        """Extract and sort available quarters from dataframe."""
        if 'year_quarter' not in df.columns:
            self.logger.warning("Missing 'year_quarter' column in dataframe")
            return []
        quarters = sorted({
            f"{dt.year}Q{dt.quarter}" for dt in df['year_quarter']
        })
        self.logger.debug(f"Available quarters: {quarters}")
        return quarters

    def get_period_options(self, reporting_form: List[str]) -> List[Dict[str, str]]:
        """Get quarter options for given form."""
        return self.quarter_options.get(reporting_form, [])