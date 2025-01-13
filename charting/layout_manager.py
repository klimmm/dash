import pandas as pd
import plotly.graph_objects as go
import logging
from typing import Optional, Tuple, Dict, Any, Union, List
from dataclasses import dataclass

from data_process.data_utils import map_insurer, map_line
from constants.translations import translate
from constants.filter_options import METRICS
from .color import ColorFormatter
from .config import ChartConfig

logger = logging.getLogger(__name__)


@dataclass
class ChartTextConfig:
    """Configuration for chart text formatting"""
    separator: str = " - "
    group_separator: str = ", "


class ChartLayoutManager:
    def __init__(
        self,
        config: ChartConfig
    ):
        self.config = config
        self._data_points = None
        self._width = None
        self._height = None
        self._num_traces = None
        self._font_config = self._initialize_font_config()
        self.text_config = ChartTextConfig()
        self.mapping_functions = {
            'linemain': map_line,
            'metric': translate,
            'insurer': map_insurer,
            'year_quarter': self._format_quarter_label
        }
        self.color_formatter = ColorFormatter(config.colors)

    def set_dimensions(
        self,
        width: int,
        height: int,
        chart_data: pd.DataFrame,
        x_column: str,
        traces: list,
        series_column: Optional[str] = None,
        is_grouped_by_series: bool = False
    ) -> None:        
        self._width = width
        self._height = height
        self._num_traces = len(traces)
        
        # Calculate data points
        self._data_points = self._calculate_data_points(
            chart_data=chart_data,
            x_column=x_column,
            series_column=series_column,
            is_grouped_by_series=is_grouped_by_series
        )
        
        logger.info(f"Data points for sizing: {self._data_points} (from {len(chart_data)} rows)")
    
    def _calculate_data_points(
        self,
        chart_data: pd.DataFrame,
        x_column: str,
        series_column: Optional[str],
        is_grouped_by_series: bool
    ) -> int:

        if is_grouped_by_series and series_column is not None:
            return len(chart_data.groupby([series_column, x_column]))
        return chart_data[x_column].nunique()
    
    def _initialize_font_config(self) -> Dict:
        """Initialize font configuration with defaults"""
        return {
            element: {
                'size': self.config.fonts.sizes[element],
                'color': self.config.fonts.colors[element],
                'family': self.config.fonts.family,
                'weight': self.config.fonts.weights.get(element, 'normal')
                if element in ['title', 'legend_group_title'] else None
            }
            for element in self.config.fonts.sizes.keys()
        }

    def _update_font_config(self) -> None:
        """Update font configuration using config's responsive font system"""
        if not (self._width and self._height):
            return

        try:
            self._font_config = self.config.fonts.get_font_config(
                width=self._width,
                height=self._height,
                data_points=self._data_points,
                num_traces=self._num_traces
            )
        except Exception as e:
            logger.error(f"Failed to update font config: {str(e)}")

    def apply_base_layout(
        self,
        fig: go.Figure,
        title: str,
        subtitle: str = None
    ) -> None:
        """Apply base layout with dynamic fonts"""

        if not self._font_config:
            self._update_font_config()

        if subtitle:
            title = (
                f"{title}<br>"
                f"<span style='font-size: {self._font_config['subtitle']['size']}px; "
                f"color: {self._font_config['subtitle']['color']};'>{subtitle}</span>")

        layout_config = {
            "autosize": True,
            "title": {
                'text': title,
                # 'font': self._font_config['title'],
                'x': self.config.layout.title['x_position'],
                'y': self.config.layout.title['y_position'],
                'xanchor': self.config.layout.title['x_anchor'],
                'yanchor': self.config.layout.title['y_anchor']
            },
            # "font": self._font_config['axis'],
            "plot_bgcolor": self.config.colors.background["plot"],
            "paper_bgcolor": self.config.colors.background["paper"],
            "margin": self.config.layout.margin,
            "hovermode": self.config.behavior.hover["mode"],
            "showlegend": True,
            "legend": {
                # 'font': self._font_config['legend'],
                # 'grouptitlefont': self._font_config['legend_group_title'],
                'orientation': self.config.layout.legend['orientation'],
                'y': self.config.layout.legend['y_position'],
                'x': self.config.layout.legend['x_position'],
                'yanchor': self.config.layout.legend['y_anchor'],
                'xanchor': self.config.layout.legend['x_anchor']
            },
            "updatemenus": [{
                'type': "buttons",
                'direction': "left",
                'buttons': [
                    {'args': [{"showlegend": True}], 'label': "", 'method': "relayout"},
                    {'args': [{"showlegend": False}], 'label': "", 'method': "relayout"}
                ],
                'pad': {
                    "r": self.config.layout.legend_toggle['pad_right'],
                    "t": self.config.layout.legend_toggle['pad_top']
                },
                'showactive': False,
                'x': self.config.layout.legend_toggle['x_position'],
                'y': self.config.layout.legend_toggle['y_position'],
                'xanchor': self.config.layout.legend_toggle['x_anchor'],
                'yanchor': self.config.layout.legend_toggle['y_anchor'],
                'borderwidth': self.config.layout.legend_toggle['border_width']
            }]
        }

        if self._width is not None:
            layout_config["width"] = self._width

        if self._height is not None:
            layout_config["height"] = self._height

        fig.update_layout(**layout_config)

    def apply_axis_styling(
        self,
        fig: go.Figure,
        x_column,
        period_type,
        start_quarter,
        compare_insurers,
        secondary_y_metrics,
        show_100_percent_bars,
        primary_y_metrics,
        y_range: Optional[tuple] = None,
        y2_range: Optional[tuple] = None
    ) -> None:
        """Apply axis styling with optimized configuration"""
        if not fig.data or not self._font_config:
            self._update_font_config()

        common_axis_config = {
            "title_text": "",
            "gridcolor": self.config.axes.colors["grid"],
            "linecolor": self.config.axes.colors["line"],
            "zeroline": self.config.axes.features["show_zero_line"],
            "zerolinecolor": self.config.axes.colors["zero_line"],
            "showline": self.config.axes.features["show_line"],
            "mirror": self.config.axes.features["mirror"],
            # "title_font": self._font_config['axis_title'],
            # "tickfont": self._font_config['axis_tick']
        }

        # X-axis optimization
        x_values = fig.data[0].x

        x_axis_config = {**common_axis_config,
                         "showgrid": self.config.axes.show_grid["x"]}

        # Simplified x-axis type handling
        if x_column in ['year_quarter', 'year']:
            tick_texts = {
                'year_quarter': lambda: self.create_custom_ticks(
                    x_values,
                    self.config,
                    period_type,
                    start_quarter)[1],
                'year': lambda: [
                    f"{x}Y" for x in x_values]}
            x_axis_config.update({
                "tickmode": "array",
                "type": self.config.axes.defaults["type"],
                "tickangle": self.config.axes.tick_angle,
                "ticktext": tick_texts[x_column](),
                "tickvals": x_values,
                "showticklabels": self.config.axes.features["show_tick_labels"],
                "fixedrange": self.config.axes.features["fixed_range"]
            })
        else:
            mapping_func = {
                'linemain': map_line,
                'metric': translate,
                'insurer': map_insurer
            }.get(x_column, str)

            unique_vals = list(dict.fromkeys(x_values))

            x_axis_config.update({
                "tickmode": "array",
                "type": "category",
                "tickangle": 0,
                "tickvals": unique_vals,
                "ticktext": [mapping_func(val) for val in unique_vals],
                "showticklabels": True
            })

        fig.update_xaxes(**x_axis_config)

        # Y-axis optimization
        has_compare = bool(compare_insurers)

        secondary_y = bool(secondary_y_metrics)

        y_config = {
            **common_axis_config,
            "showgrid": self.config.axes.show_grid["y"],
            "visible": not (has_compare and not secondary_y),
            **({"range": y_range} if y_range else {}),
            **({
                "tickformat": self.config.behavior.value_formatting["percentage_format"],
                "hoverformat": self.config.behavior.value_formatting["percentage_hover_format"]
            } if show_100_percent_bars else {})
        }

        fig.update_yaxes(y_config, secondary_y=False)

        if has_compare or secondary_y:
            metrics = (primary_y_metrics or []) + \
                (secondary_y_metrics or [])
            is_secondary_pct = any(
                metric in METRICS and METRICS[metric]['type'] in [
                    'percentage',
                    'market_share',
                    'q_to_q_change'] for metric in metrics)

            y2_config = {
                **common_axis_config,
                "showgrid": self.config.axes.show_grid["y2"],
                **({"range": y_range if has_compare and not secondary_y else y2_range} if y2_range else {}),
                **({
                    "tickformat": self.config.behavior.value_formatting["percentage_format"],
                    "hoverformat": self.config.behavior.value_formatting["percentage_hover_format"]
                } if is_secondary_pct else {})
            }

            fig.update_yaxes(y2_config, secondary_y=True)
    
    def _format_quarter_label(
        self,
        date: pd.Timestamp,
        period_type: str
    ) -> str:
        """Format quarter labels based on period type"""
        if isinstance(date, str):
            try:
                date = pd.to_datetime(date)
            except ValueError:
                return date

        year = date.year
        quarter = (date.month - 1) // 3 + 1

        if period_type in ['previous_quarter', 'same_q_last_year']:
            return f"{quarter}-й кв. {year} г."
        elif period_type == 'same_q_last_year_ytd':
            quarter_labels = {
                1: "1-й квартал",
                2: "1-е полугодие",
                3: "9 мес.",
                4: "Полный"
            }
            return f"{quarter_labels.get(quarter, str(quarter))} {year} г."
        elif period_type in ['same_q_last_year_mat', 'previous_q_mat']:
            start_date = date - pd.DateOffset(months=9)
            start_year = start_date.year
            start_quarter = (start_date.month - 1) // 3 + 1
            return f"{start_quarter} кв. {start_year} - {quarter} кв. {year}"
        elif period_type == 'cumulative_sum':
            return f"{quarter} кв. {year}"
        else:
            return f"Q{quarter}<br>{year}"

    def create_custom_ticks(
        self,
        dates: pd.Series,
        config: ChartConfig,
        period_type: str,
        start_quarter: Optional[str] = None
    ) -> Tuple[List[pd.Timestamp], List[str]]:

        ticks = []
        labels = []
        sorted_dates = sorted(pd.to_datetime(dates).unique())
        last_year = None

        for date in sorted_dates:
            year, quarter = date.year, (date.month - 1) // 3 + 1
            ticks.append(date)

            if period_type in [
                'previous_quarter',
                'same_q_last_year',
                'cumulative_sum',
                    'previous_q_mat']:
                label = f"{quarter}Q<br>{year}" if year != last_year else f"{quarter}Q<br>"
            elif period_type == 'same_q_last_year_ytd':
                quarter_labels = {1: "1Q", 2: "1H", 3: "9M", 4: "FY"}
                quarter_label = quarter_labels.get(quarter, f"{quarter}")
                label = f"{quarter_label}<br>{year}"
            elif period_type == 'same_q_last_year_mat':
                start_date = date - pd.DateOffset(months=9)
                start_year, start_quarter = start_date.year, (
                    start_date.month - 1) // 3 + 1
                label = f"{start_quarter}Q{start_year} -<br>{quarter}Q{year}"
            else:
                label = f"Q{quarter}<br>{year}"

            labels.append(label)
            last_year = year

        return ticks, labels

    def generate_chart_title(
        self,
        x_column: str,
        selected_linemains: Union[List[str], str],
        selected_metrics: Union[List[str], str],
        selected_insurers: Union[List[str], str],
        end_quarter: str,
        period_type: str,
        series_column: str,
        group_column: str
    ) -> Tuple[str, str]:
        """
        Generate title and subtitle for the chart based on series and group configurations.
        Fully self-contained processing including value retrieval, counting, and formatting.
        """
        def get_column_value(
                column: str) -> Union[str, List[str], pd.Timestamp, None]:
            """Internal helper to get the value for a specific column type"""
            if not column:
                return None

            if column == 'year_quarter':
                return end_quarter

            value_map = {
                'metric': selected_metrics,
                'linemain': selected_linemains,
                'insurer': selected_insurers
            }
            return value_map.get(column)

        def count_items(items: Union[List[str], str, None]) -> int:
            """Internal helper to count non-empty items"""
            if not items:
                return 0
            if isinstance(items, str):
                return 1 if items.strip() else 0
            return len([x for x in items if x and str(x).strip()])

        def get_column_data(column: str) -> Tuple[int, Optional[str]]:
            """Internal helper to get count and formatted value for a column"""
            if not column:
                return 0, None

            value = get_column_value(column)
            count = count_items(value)
            formatted = self._format_text(
                value, column, period_type=period_type) if value else ""
            return count, formatted

        def find_remaining_column() -> Optional[str]:
            """Internal helper to find the unused column"""
            all_columns = {'metric', 'linemain', 'insurer', 'year_quarter'}
            used_columns = {
                col for col in (
                    series_column,
                    group_column,
                    x_column) if col}
            remaining = all_columns - used_columns
            return next(iter(remaining), None) if remaining else None

        # Get counts and formatted values for series and groups
        num_series, series_formatted = get_column_data(series_column)

        num_groups, group_formatted = get_column_data(group_column)

        # Determine first part based on counts
        first_part = ""

        if num_groups == 1 and num_series > 1:
            first_part = group_formatted

        elif num_series == 1:  # Covers both cases: multiple groups or single group
            first_part = series_formatted

        elif num_series == 1 and num_groups == 1:
            first_part = group_formatted

        # Get second part from remaining column
        second_part = ""
        remaining_column = find_remaining_column()
        if remaining_column:
            _, remaining_formatted = get_column_data(remaining_column)
            second_part = remaining_formatted

        # Construct final title
        if first_part and second_part:
            title = f"{first_part}{self.text_config.separator}{second_part}"
        else:
            title = first_part or second_part

        # Generate subtitle
        subtitle = translate(period_type) if period_type else ""

        return title, subtitle

    def generate_trace_name_and_legend(
        self,
        s: str,
        group: str,
        series_column: str,
        group_column: str,
        x_column: str,
        outer_loop: str,
        num_series: int,
        num_groups: int,
        period_type: str = None
    ) -> Tuple[str, Optional[str], Optional[str]]:

        def format_value(value: Union[str, pd.Timestamp], column: str) -> str:
            """Helper to format a value using the specified column type"""
            return self._format_text(
                value, column, period_type=period_type) if value else ""

        # Determine which values to use based on counts and loop type
        
        use_series = False
        if num_groups == 1 and num_series > 1:
            use_series = True
        elif num_series == 1:  # Covers both single group and multiple groups
            use_series = False
        elif outer_loop == 'series':
            use_series = False
        elif outer_loop == 'group':
            use_series = True
        elif num_groups > num_series:
            use_series = False
        else:
            use_series = True

        # Format trace name
        trace_name = format_value(
            s if use_series else group,
            series_column if use_series else group_column)

        # Handle legend group and title
        legend_group = None

        legend_title = None

        if num_series > 1 and num_groups > 1:

            if outer_loop == 'series':
                legend_value = format_value(s, series_column)

            elif outer_loop == 'group':
                legend_value = format_value(group, group_column)

            elif num_series > num_groups:
                legend_value = format_value(group, group_column)

            elif num_groups > num_series:
                legend_value = format_value(s, series_column)
            else:
                legend_value = format_value(group, group_column)

            if legend_value:
                legend_group = legend_value
                legend_title = f" {legend_value}"

        logger.debug(f"trace_name {trace_name}")
        logger.debug(f"legend_group {legend_group}")
        logger.debug(f"legend_title {legend_title}")

        return trace_name, legend_group, legend_title

    def _format_text(
        self,
        value: Union[str, List[Any], pd.Timestamp, int, float],
        column_type: str,
        text_type: str = 'default',
        deduplicate: bool = True,
        period_type: str = None
    ) -> str:
        """Format text based on column type and configuration"""
        if value is None or (isinstance(value, (list, tuple)) and not value):
            return ""

        if isinstance(value, pd.Timestamp):
            mapping_func = self.mapping_functions.get(column_type)
            if column_type == 'year_quarter':
                return mapping_func(value, period_type)
            return str(value)

        values = [value] if isinstance(value, (str, int, float)) else value
        values = [v for v in values if v is not None]

        if deduplicate:
            values = list(dict.fromkeys(values))

        mapping_func = self.mapping_functions.get(column_type, str)
        if column_type == 'quarter':
            mapped_values = [f"{v}Q" for v in values]
        elif column_type == 'year_quarter':
            mapped_values = [mapping_func(val, period_type) for val in values]
        else:
            mapped_values = [mapping_func(val) for val in values]

        return self.text_config.group_separator.join(
            filter(None, mapped_values))