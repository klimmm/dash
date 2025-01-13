import pandas as pd
import numpy as np
import plotly.graph_objects as go
import logging
from typing import Any, Dict, List, Tuple, Union, Optional
from .color import ColorFormatter
from .layout_manager import ChartLayoutManager
from .config import ChartConfig
from .helpers import sort_dataframe
from constants.filter_options import METRICS
from data_process.data_utils import save_df_to_csv

logger = logging.getLogger(__name__)


class ChartTraceGenerator:
    def __init__(
        self,
        config: ChartConfig,
        layout_manager: ChartLayoutManager
    ):
        self.config = config
        self.layout_manager = layout_manager
        self.color_formatter = ColorFormatter(config.colors)

    def generate_traces(
        self,
        df,
        x_column,
        series_column,
        group_column,
        main_insurer,
        compare_insurers,
        primary_y_metrics,
        secondary_y_metrics,
        is_series_stacked,
        is_grouped_by_series,
        is_groups_stacked,
        primary_chart_type,
        secondary_chart_type,
        random_color,
        show_percentage,
        show_100_percent_bars

    ) -> Tuple[List[Union[go.Bar, go.Scatter]], Dict[str, List[float]]]:

        save_df_to_csv(df, "before_sort.csv")

        df = sort_dataframe(
            df, x_column, series_column, group_column,
            main_insurer, compare_insurers,
            primary_y_metrics, secondary_y_metrics
        )

        x_values = df[x_column].unique()

        # Handle series and groups properly - only use [None] if both are None
        if series_column is None and group_column is None:
            series = [None]
            groups = [None]

        else:
            # Get actual values for whichever column exists
            series = df[series_column].unique().tolist(
            ) if series_column is not None else [None]

            groups = df[group_column].unique().tolist(
            ) if group_column is not None else [None]
       
        # Determine loop order - simplified logic
        outer_loop = 'series' if (is_series_stacked or is_grouped_by_series) and not is_groups_stacked else 'group'

        traces = []

        # Pre-allocate base values
        base_values = {
            item: [0] *
            len(x_values) for item in (
                series if outer_loop == 'series' else groups)}

        # Generate traces efficiently
        for outer_idx, outer_item in enumerate(
                series if outer_loop == 'series' else groups):
            for inner_idx, inner_item in enumerate(
                    groups if outer_loop == 'series' else series):

                # Use regular trace generation with whatever columns we have
                new_trace = self._generate_single_trace(
                    df=df,
                    outer_item=outer_item,
                    inner_item=inner_item,
                    outer_loop=outer_loop,
                    is_grouped_by_series=is_grouped_by_series,
                    is_series_stacked=is_series_stacked,
                    is_groups_stacked=is_groups_stacked,
                    x_values=x_values,
                    x_column=x_column,
                    series_column=series_column,
                    group_column=group_column,
                    compare_insurers=compare_insurers,
                    primary_y_metrics=primary_y_metrics,
                    secondary_y_metrics=secondary_y_metrics,
                    secondary_chart_type=secondary_chart_type,
                    show_100_percent_bars=show_100_percent_bars,
                    show_percentage=show_percentage,
                    random_color=random_color,
                    primary_chart_type=primary_chart_type,
                    outer_idx=outer_idx,
                    inner_idx=inner_idx,
                    base_values=base_values[outer_item],
                    trace_count=len(traces),
                    num_series=len(series),
                    num_groups=len(groups)
                )

                # Handle stacking for bar charts
                if primary_chart_type.lower() == 'bar' and (
                    not is_series_stacked and not is_groups_stacked) or (
                        not is_groups_stacked and not is_series_stacked):
                    current_trace = new_trace if not isinstance(
                        new_trace, list) else new_trace[0]
                    if isinstance(current_trace, go.Bar):
                        base_values[outer_item] = [
                            base + y for base,
                            y in zip(
                                base_values[outer_item],
                                current_trace.y)]

                traces.append(new_trace)

        return traces, base_values

    def _generate_single_trace(
        self,
        df: pd.DataFrame,
        outer_item: str,
        inner_item: str,
        outer_loop: str,
        is_grouped_by_series: bool,
        is_series_stacked: bool,
        is_groups_stacked: bool,
        x_values: List[Any],
        x_column: str,
        series_column: str,
        group_column: str,
        compare_insurers,
        primary_y_metrics,
        secondary_y_metrics,
        secondary_chart_type,
        show_100_percent_bars,
        show_percentage,
        random_color,
        primary_chart_type,
        outer_idx: int,
        inner_idx: int,
        base_values: List[float],
        trace_count: int = 1,
        num_series: int = 1,
        num_groups: int = 1
    ) -> Union[go.Bar, go.Scatter]:
        """Generate a single trace with complete functionality"""
        # Set series and group values
        s = outer_item if outer_loop == 'series' else inner_item
        group = inner_item if outer_loop == 'series' else outer_item

        # Build filter conditions
        conditions = []
        if series_column:
            conditions.append(df[series_column] == s)
        if group_column:
            conditions.append(df[group_column] == group)

        filtered_df = df[np.logical_and.reduce(
            conditions)] if conditions else df

        # Determine metric and percentage status
        is_secondary_metric = False
        is_metric_percentage = False

        '''if series_column == 'metric':
            is_secondary_metric = s in (
                secondary_y_metrics or [])
            metric_type = METRICS[s]['type']
            is_metric_percentage = metric_type in [
                'percentage', 'market_share', 'q_to_q_change']
        elif group_column == 'metric':
            is_secondary_metric = group in (
                secondary_y_metrics or [])
            metric_type = METRICS[group]['type']
            is_metric_percentage = metric_type in [
                'percentage', 'market_share', 'q_to_q_change']'''
        is_metric_percentage = False
        is_secondary_metric = False
        # Check for compare insurer
        insurer = group if group_column == 'insurer' else s
        is_compare_insurer = insurer in compare_insurers

        # Determine final axis and percentage status
        '''is_secondary = is_secondary_metric or (
            is_compare_insurer and not secondary_y_metrics)'''
        is_secondary = False
        
        is_percentage = show_percentage or show_100_percent_bars or is_metric_percentage

        y_column = 'percent' if show_100_percent_bars else 'value'

        text_column = 'percent' if show_percentage else y_column

        decimals = (
            self.config.behavior.value_formatting["percentage_decimal_places"]
            if is_percentage
            else self.config.behavior.value_formatting["default_decimal_places"]
        )

        text = [
            f"{val * 100:.{decimals}f}%" if is_percentage else f"{val:.{decimals}f}"
            for val in filtered_df.set_index(x_column)[text_column].reindex(x_values).fillna(0)
        ]

        # Get y values
        y = filtered_df.set_index(x_column)[
            y_column].reindex(x_values).fillna(0).tolist()

        # Generate trace name and legend info
        trace_name, legend_group, legend_title = self.layout_manager.generate_trace_name_and_legend(
            s=s,
            group=group,
            series_column=series_column,
            group_column=group_column,
            x_column=x_column,
            outer_loop=outer_loop,
            num_series=num_series,
            num_groups=num_groups
        )
        logger.warning(f"primary_chart_type {primary_chart_type}")
        logger.warning(f"is_secondary {is_secondary}")
        # Determine chart type
        chart_type = (
            secondary_chart_type
            if is_secondary
            else primary_chart_type
        ).lower()

        # Get offsetgroup
        offsetgroup = (
            f"{outer_idx}"
            if is_series_stacked or is_groups_stacked
            else f"{outer_idx}_{inner_idx}"
        )
        logger.warning(f"trace_name {trace_name}")
        logger.warning(f"is_grouped_by_series {is_grouped_by_series}")
        # Get color
        color = self.color_formatter.get_rgba_color(
            outer_idx=outer_idx,
            inner_idx=inner_idx,
            num_groups=num_groups,
            num_series=num_series,
            outer_loop=outer_loop,
            is_grouped_by_series=is_grouped_by_series,
            is_series_stacked=is_series_stacked,
            is_groups_stacked=is_groups_stacked,
            x_column=x_column,
            group_column=group_column,
            series_column=series_column,
            chart_type=chart_type,
            random_color=random_color
        )

        # Determine if stacking should be applied
        is_stacked = False

        if chart_type == 'area':
            # For area charts, check both stacking conditions
            is_stacked = (
                (is_series_stacked and outer_loop == 'series') or
                (is_groups_stacked and outer_loop == 'group')
            )

        elif chart_type == 'bar':
            is_stacked = is_series_stacked or is_groups_stacked

        # Create base trace
        trace = go.Bar(
            x=x_values,
            y=y) if chart_type == 'bar' else go.Scatter(
            x=x_values,
            y=y)

        # Apply styling with corrected stacking parameter
        trace = self.apply_trace_styling(
            trace=trace,
            chart_type=chart_type,
            is_percentage=is_percentage,
            color=color,
            name=trace_name,
            legendgroup=legend_group,
            legendgrouptitle_text=legend_title,
            yaxis="y2" if is_secondary else "y",
            text=text,
            offsetgroup=offsetgroup,
            base=base_values if is_stacked and chart_type == 'bar' else None,
            is_stacked=is_stacked
        )
        #logger.warning(f"color {color}")
        
        # Apply hover template
        self.apply_hover_template(
            trace=trace,
            is_percentage=is_percentage,
            show_text=True
        )

        return trace

    def apply_hover_template(
        self,
        trace: Union[go.Bar, go.Scatter],
        is_percentage: bool,
        show_text: bool = True
    ) -> None:
        """Apply hover template to trace"""
        hover_template = self.config.behavior.hover["template"]
        if is_percentage:
            hover_template = hover_template.replace(
                "%{value}",
                "%{value:.2f}%"
            )

        if show_text:
            hover_template += "<br>%{text}"

        trace.update(hovertemplate=hover_template)

    def apply_trace_styling(
        self,
        trace: Union[go.Bar, go.Scatter],
        chart_type: str,
        is_percentage: bool,
        color: str,
        name: str = "",
        legendgroup: Optional[str] = None,
        legendgrouptitle_text: Optional[str] = None,
        yaxis: str = "y",
        text: Optional[List[str]] = None,
        base: Optional[List[float]] = None,
        offsetgroup: Optional[str] = None,
        is_stacked: bool = False
    ) -> Union[go.Bar, go.Scatter]:
        """Apply full styling to a trace including data labels"""
        # Base configuration
        trace_config = {
            "name": name,
            "legendgroup": legendgroup,
            "legendgrouptitle_text": legendgrouptitle_text,
            "yaxis": yaxis,
            "text": text
        }

        # Data label configuration for bar charts
        if chart_type == "bar":
            text_template = self.config.behavior.text_formatting[
                "percentage" if is_percentage else "number"]

            data_label_config = {
                "texttemplate": text_template,
                "textposition": self.config.chart_types.bar["text_position"],
                "textfont": dict(
                    # size=self.layout_manager._font_config['data_label']['size'],
                    color=self.config.chart_types.bar["inside_text_color"])}

            # Merge data label config with bar-specific styling
            trace.update(
                marker=dict(
                    color=color,
                    # line=dict(
                        # width=self.config.chart_types.bar["marker_line_width"])
                ),
                opacity=self.config.chart_types.bar["opacity"],
                base=base,
                offsetgroup=offsetgroup,
                **trace_config,
                **data_label_config)

        else:
            mode_map = {
                "line": "lines",
                "smoothed_line": "lines",
                "area": "lines",
                "scatter": "markers"
            }

            if chart_type == "scatter":
                trace.update(
                    mode=mode_map[chart_type],
                    marker=dict(
                        color=color,
                        size=self.config.chart_types.scatter["marker_size"],
                        line=dict(
                            width=self.config.chart_types.scatter["marker_line_width"],
                            color=color)),
                    **trace_config)
            else:
                line_config = {
                    "color": color,
                    # "width": self.config.chart_types.line["width"]
                }
                if chart_type == "smoothed_line":
                    line_config["shape"] = "spline"

                # Area-specific configuration
                if chart_type == "area":
                    area_config = {
                        "mode": mode_map[chart_type],
                        "line": line_config,
                        "fillcolor": self.color_formatter.adjust_color_opacity(
                            color,
                            self.config.chart_types.area["opacity"]
                        ),
                        **trace_config
                    }

                    if is_stacked:
                        area_config.update({
                            "stackgroup": "stack1",  # Use consistent stack group
                            # Add percentage normalization if needed
                            "groupnorm": "percent" if is_percentage else None,
                            "hovertemplate": "%{y:.1f}%<extra></extra>" if is_percentage else "%{y:.1f}<extra></extra>"
                        })
                    else:
                        area_config.update({
                            "fill": "tozeroy"
                        })

                    trace.update(**area_config)
                else:
                    trace.update(
                        mode=mode_map.get(chart_type, "lines"),
                        line=line_config,
                        **trace_config
                    )

        return trace