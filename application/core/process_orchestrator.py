from typing import List, Optional, Any, Dict
from dash import dash_table
import pandas as pd
import itertools
from application.processors.helpers import filter_by_column

class ProcessOrchestrator:
    """Orchestrates data processing and visualization pipeline.

    Coordinates analytics flow from data loading through processing to visualization,
    integrating processors and visualization services for insurance data analytics.
    """

    def __init__(
        self,
        config,
        data_processing,
        visualization,
        selection_facade,
        context
    ):
        self.config = config
        self.logger = config.logger
        self.log_pipe = config.pipe_with_logging

        self.data_processing = data_processing
        self.visualization = visualization
        self.selection_facade = selection_facade
        self.context = context

    def process_dashboard_data(self):
        """Process dashboard data through pipeline."""

        required_metrics = self.data_processing.get_required_metrics(self.context.metrics)
        df = self.context.get_dataframe(self.context.reporting_form)
        processed_df = (
            df
            .pipe(self.log_pipe, filter_by_column,
                  self.context.columns.LINE, self.context.lines)
            .pipe(self.log_pipe, filter_by_column,
                  self.context.columns.METRIC, required_metrics)
            .pipe(self.log_pipe, self.data_processing.calculate_period_type,
                  self.context.end_q, self.context.period_type)
            .pipe(self.log_pipe, self.data_processing.add_top_n_rows)
            .pipe(self.log_pipe, self.data_processing.calculate_metrics,
                  self.context.metrics, required_metrics)
            .pipe(self.log_pipe, filter_by_column,
                  self.context.columns.YEAR_QUARTER, self.context.end_q, 'lte')
            .pipe(lambda df: self.context.update_state(filtered_quarters_df=df))
            .pipe(self.log_pipe, self.data_processing.add_rank_column,
                  self.context.value_types, self.context.num_periods)
            .pipe(self.log_pipe, self.data_processing.calculate_market_share,
                  self.context.value_types)
            .pipe(self.log_pipe, self.data_processing.calculate_growth,
                  self.context.value_types, self.context.num_periods)
            .pipe(self.log_pipe, self.data_processing.format_ranks)
        )
        self.context.update_state(processed_df=processed_df)
        return self.context.filtered_quarters

    def prepare_visualization_data(self):
        """Generate segmented dimensional results."""
        if not self.context.is_processing_ready():
            self.logger.error("No processed dataframe available")
            return None
        result_dfs = self.visualization.process_dimensional_data(
            self.context.processed_df, self.context.insurers, self.context.lines,
            self.context.metrics, self.context.value_types, self.context.quarters,
            self.context.split_cols, 10
        )
        self.context.update_state(result_dfs=result_dfs)
        return self.context.filtered_quarters

    def create_visualizations(
        self,
        viewport_size: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Create visualizations based on parameters."""
        if not self.context.is_visualization_ready():
            self.logger.warning("No result dataframes available")
            return []
        visualization_sections = []
        try:
            for i, (df, split_cols, split_vals) in enumerate(self.context.result_dfs):
                section = {'table': None, 'charts': []}
                if 'table' in self.context.view_mode:
                    section['table'] = self._create_table(
                        df, split_cols, split_vals)
                if 'chart' in self.context.view_mode:
                    section['charts'] = self._create_charts(
                        df, split_cols, split_vals, viewport_size or 'desktop', i)
                visualization_sections.append(section)
            return visualization_sections
        except Exception as e:
            self.logger.error(f"Visualization error: {str(e)}", exc_info=True)
            raise

    def _create_table(self, df: pd.DataFrame, split_cols: List[str],
                     split_vals: List[Any]) -> dash_table.DataTable:
        """Create data table visualization."""
        pivot = self.visualization.create_pivot(df, self.context.pivot_cols, self.context.index_cols)
        table_props = self.visualization.create_datatable(
            pivot, 
            self.context.pivot_cols,
            self.context.index_cols,
            self.context.period_type,
            self.context.value_types,
            split_cols=split_cols,
            split_vals=split_vals
        )
        return dash_table.DataTable(**table_props)

    def _create_charts(self, df: pd.DataFrame, split_cols: List[str],
                       split_vals: List[Any], viewport_size: str,
                       section_index: int) -> List[Any]:
        """Create chart visualizations."""
        other_cols = [col for col
                      in self.context.pivot_cols + self.context.index_cols
                      if col not in [self.context.index_cols[0],
                                     self.context.pivot_cols[0],
                                     self.context.columns.VALUE]]

        combinations = [dict(combo) for combo in itertools.product(
            *[[(col, val) for val in df[col].unique()] for col in other_cols]
        )]

        charts = []
        for i, combo in enumerate(combinations):
            chart_df = df.copy()
            for col, val in combo.items():
                chart_df = chart_df[chart_df[col] == val]

            if not chart_df.empty:
                chart = self.visualization.create_bar_chart(
                    chart_df, 
                    index_cols=self.context.index_cols,
                    values_col=self.context.columns.VALUE,
                    period_type=self.context.period_type,
                    series_col=self.context.pivot_cols[0],
                    split_cols=split_cols,
                    split_vals=split_vals,
                    other_cols=list(combo.keys()),
                    other_vals=list(combo.values()),
                    viewport_size=viewport_size,
                    chart_n=i
                )
                charts.append(chart)

        return charts