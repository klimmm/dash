import logging
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional, Tuple, Union
from .config import ChartConfig
from .trace_generator import ChartTraceGenerator
from .layout_manager import ChartLayoutManager
from .get_y_ranges import get_axis_ranges
from config.logging_config import get_logger

logger = get_logger(__name__)

def create_chart(
    chart_data: pd.DataFrame,
    primary_y_metric: Union[List[str], str],
    primary_chart_type: str = "bar",
    period_type: str = "",
    start_quarter: str = "",
    end_quarter: str = "",
    main_insurer: Union[List[str], str] = None,
    compare_insurers: Union[List[str], str] = None,
    secondary_y_metric: Optional[Union[List[str], str]] = None,
    secondary_chart_type: Optional[str] = None,
    is_groups_stacked: bool = False,
    is_series_stacked: bool = False,
    show_percentage: bool = False,
    show_100_percent_bars: bool = False,
    is_grouped_by_series: bool = True,
    x_column: str = 'year_quarter',
    series_column: str = 'metric',
    group_column: str = 'insurer',
    random_color: bool = False,
    selected_linemains: Union[List[str], str] = None,
    container_width: Optional[int] = 1200,
    container_height: Optional[int] = 900
) -> Tuple[go.Figure, Optional[str]]:
    """Create a chart with the given parameters"""

    def to_list(val: Union[List[str], str, None]) -> List[str]:
        return [] if val is None else [val] if isinstance(val, str) else val

    primary_y_metrics = to_list(primary_y_metric)
    main_insurer = to_list(main_insurer)
    compare_insurers = to_list(compare_insurers)
    secondary_y_metrics = to_list(secondary_y_metric)
    selected_linemains = to_list(selected_linemains)
    selected_metrics = primary_y_metrics + (secondary_y_metrics or [])
    selected_insurers = (main_insurer or []) + (compare_insurers or [])

    try:
        # Initialize configuration and managers
        chart_config = ChartConfig()
        layout_manager = ChartLayoutManager(chart_config)
        trace_generator = ChartTraceGenerator(chart_config, layout_manager)
        logger.warning(f"primary_chart_type {primary_chart_type}")
        fig = make_subplots(specs=chart_config.layout.subplot["specs"])

        traces, base_values = trace_generator.generate_traces(
            df=chart_data,
            x_column=x_column,
            series_column=series_column,
            group_column=group_column,
            main_insurer=main_insurer,
            compare_insurers=compare_insurers,
            primary_y_metrics=primary_y_metrics,
            secondary_y_metrics=secondary_y_metrics,
            is_series_stacked=is_series_stacked,
            is_grouped_by_series=is_grouped_by_series,
            is_groups_stacked=is_groups_stacked,
            primary_chart_type=primary_chart_type,
            secondary_chart_type=secondary_chart_type,
            random_color=random_color,
            show_percentage=show_percentage,
            show_100_percent_bars=show_100_percent_bars
        )

        for trace in traces:
            fig.add_trace(trace, secondary_y=getattr(trace, 'yaxis', 'y') == 'y2')

        '''layout_manager.set_dimensions(
            width=container_width,
            height=container_height,
            chart_data=chart_data,
            x_column=x_column,
            traces=traces,
            series_column=series_column,
            is_grouped_by_series=is_grouped_by_series
        )'''

        y_range, y2_range = get_axis_ranges(
            traces,
            base_values, 
            is_series_stacked, 
            primary_chart_type,
            compare_insurers, 
            secondary_y_metrics, 
            show_percentage, 
            show_100_percent_bars
        )

        '''title, subtitle = layout_manager.generate_chart_title(
            x_column=x_column,
            selected_linemains=selected_linemains,
            selected_metrics=selected_metrics,
            selected_insurers=selected_insurers,
            end_quarter=end_quarter,
            period_type=period_type,
            series_column=series_column,
            group_column=group_column
        )'''

        title, subtitle = None, None

        layout_manager.apply_base_layout(
            fig=fig, 
            title=title, 
            subtitle=subtitle)

        layout_manager.apply_axis_styling(
            fig=fig,
            x_column=x_column,
            period_type=period_type,
            start_quarter=start_quarter,
            compare_insurers=compare_insurers,
            secondary_y_metrics=secondary_y_metrics,
            show_100_percent_bars=show_100_percent_bars,
            primary_y_metrics=primary_y_metrics,
            y_range=y_range,
            y2_range=y2_range
        )

        return fig, None

    
    except Exception as e:
        logger.warning(f"Error generating chart: {str(e)}", exc_info=True)
        return go.Figure(), f"An error occurred: {str(e)}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.debug("Chart generation module loaded successfully")