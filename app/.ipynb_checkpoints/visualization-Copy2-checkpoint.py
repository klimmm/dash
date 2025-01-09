import logging
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import dash_bootstrap_components as dbc

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from mapping import map_insurer, map_line
from translations import translate, METRICS

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
#logger.setLevel(logging.CRITICAL)

# Application configuration
DATE_COLUMN: str = 'year_quarter'
DEFAULT_CHART_TYPE: str = 'line'
EXTERNAL_STYLESHEETS: List[Any] = [dbc.themes.CYBORG]

# Chart configuration
CHART_ELEMENT_COLORS: Dict[str, str] = {
    "title": "black",
    "axis_line": "#bbb",
    "grid": "#eee",
    "legend_bg": "rgba(255,255,255,0.8)",
    "legend_border": "#ddd",
    "button_bg": "lightgray",  # Add this line
    "button_active": "gray"  # Add this line
}
# Constants
INSURER_COL = 'insurer'
TOP_INSURER_COUNTS = [5, 10, 20]

CHART_COLORS = [

    '#56B4E9',  # Light blue
    '#009E73',  # Green
    '#E69F00',  # Orange
    '#F0E442',  # Light yellow
    '#CC79A7',  # Pink
    '#0072B2',  # Dark blue
    '#D55E00',  # Red-orange
    '#999999',  # Gray
    '#7A4DAB',  # Purple
    '#636EFA',   # Bright blue
    '#E69F00', '#D55E00', '#9467bd', '#8c564b', '#e377c2',
    '#7f7f7f', '#bcbd22', '#17becf', '#EF553B', '#00cc96',
    '#ab63fa', '#FFA15A', '#19d3f3', '#FF6692', '#B6E880',
    '#FF97FF', '#FECB52', '#636efa', '#5D4037', '#26A69A',
    '#EC407A', '#7CB342', '#FFA000', '#5E35B1', '#00BFA5',
    '#D81B60', '#64DD17', '#F57F17', '#0072B2', '#009E73',
    '#CC79A7', '#56B4E9', '#F0E442', '#999999', '#7A4DAB', '#d62728'

    ]
FONT_FAMILY = "Arial"
FONT_SIZES = {
    "axis": 20,
    "title": 30,
    "legend": 25,
    "tick": 20,
    "hover": 20
}

# Default chart options
DEFAULT_CHART_OPTIONS = {
    'combined': {
        'title': translate(""),
        'x_title': translate("Quarter"),
        'y_title': translate("Value"),
        'y_title_secondary': translate("Percentage / Ratio")
    },
    'market': {
        'title': translate("по видам страхования, млрд руб."),
        'x_title': translate(""),
        'y_title': translate(""),
        'legend_title': translate("Line of Business")
    }
}

CHART_LAYOUT: Dict[str, Any] = {
    'font': {
        'family': "Arial, sans-serif",
        'size': 16
    },
    'margin': {
        'l': 50, 'r': 50, 't': 50, 'b': 50
    },
    'hovermode': "x unified"
}


def format_metric_name(metric: str) -> str:
    """
    Format and translate the metric name for display.

    Args:
        metric (str): The metric name to format and translate.

    Returns:
        str: The formatted and translated metric name.
    """
    if metric in METRICS:
        return translate(METRICS[metric]['label'])

    formatted = metric.replace('_', ' ').title()
    return translate(formatted)





@dataclass
class ChartConfig:
    title: str
    x_title: str
    y_title: str
    y2_title: Optional[str] = None
    y_range: Optional[List[float]] = None
    y2_range: Optional[List[float]] = None
    add_range_selector: bool = False
    x_axis_type: str = "date"
    range_selector_buttons: Optional[List[Dict[str, Any]]] = None
    show_rangeslider: bool = False
    legend_position: Optional[Dict[str, Any]] = None
    margins: Optional[Dict[str, int]] = None
    button_colors: Optional[Dict[str, str]] = None
    padding: Optional[Dict[str, int]] = None


def create_font_dict(size: int, color: Optional[str] = None) -> Dict[str, Any]:
    """Create a font dictionary with consistent family and given size."""
    font_dict = {"family": FONT_FAMILY, "size": size}
    if color:
        font_dict["color"] = color
    return font_dic


def get_plotly_chart_function(chart_type: str) -> Callable:
    """Get the appropriate Plotly chart function based on the chart type."""
    chart_type_map = {
        "line": px.line,
        "bar": px.bar,
        "area": px.area,
        "scatter": px.scatter,
    }
    return chart_type_map.get(chart_type, px.line)


def create_custom_ticks(dates: pd.Series) -> Tuple[List[pd.Timestamp], List[str]]:
    """Create custom ticks for date axis with year centered below quarters."""
    ticks = []
    labels = []
    years = set()
    sorted_dates = sorted(pd.to_datetime(dates).unique())

    for date in sorted_dates:
        year = date.year
        quarter = (date.month - 1) // 3 + 1
        ticks.append(date)

        if year not in years:
            labels.append(f"Q{quarter}<br>{year}")
            years.add(year)
        else:
            labels.append(f"Q{quarter}")

    return ticks, labels


def apply_axis_styling(
    fig: go.Figure,
    axis: str,
    title: str,
    is_date: bool = False,
    is_percentage: bool = False,
    dates: Optional[pd.Series] = None,
    is_secondary: bool = False,
    range_vals: Optional[List[float]] = None,
) -> None:
    """Apply consistent styling to chart axes."""
    axis_dict = {
        "title_text": title if axis != "xaxis" else "",
        "title_font": create_font_dict(FONT_SIZES["axis"]),
        "tickfont": create_font_dict(FONT_SIZES["tick"]),
        "showgrid": True,
        "gridcolor": CHART_ELEMENT_COLORS.get("grid", "#E5ECF6"),
        "linecolor": CHART_ELEMENT_COLORS.get("axis_line", "#000"),
        "zeroline": False,
        "showline": True,
        "mirror": True,
    }

    if is_date and dates is not None:
        ticks, labels = create_custom_ticks(dates)
        axis_dict.update(
            {
                "tickmode": "array",
                "tickvals": ticks,
                "ticktext": labels,
                "tickangle": 0,
            }
        )
    elif is_percentage:
        axis_dict.update({"tickformat": ".1%", "hoverformat": ".2%"})
    else:
        axis_dict.update({"tickformat": ",", "hoverformat": ","})

    if range_vals:
        axis_dict["range"] = range_vals

    fig.update_layout(**{axis: axis_dict})


def apply_consistent_styling(fig: go.Figure, config: ChartConfig) -> go.Figure:
    """Apply consistent styling to the entire chart."""
    if not isinstance(fig, go.Figure):
        raise TypeError("fig must be a plotly.graph_objs.Figure object")

    default_legend_position = {
        "orientation": "h",
        "yanchor": "bottom",
        "y": -0.2,
        "xanchor": "left",
        "x": 0.01,
    }
    legend_position = config.legend_position or default_legend_position
    margins = config.margins or {"l": 50, "r": 50, "t": 100, "b": 100}
    button_colors = config.button_colors or {
        "bgcolor": CHART_ELEMENT_COLORS.get("button_bg", "lightgray"),
        "activecolor": CHART_ELEMENT_COLORS.get("button_active", "gray"),
    }

    # Apply padding if provided
    if config.padding:
        margins.update(config.padding)

    fig.update_layout(
        title={
            "text": translate(config.title),
            "font": create_font_dict(FONT_SIZES["title"], CHART_ELEMENT_COLORS.get("title", "#000")),
        },
        font=create_font_dict(FONT_SIZES["axis"]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend={
            "font": create_font_dict(FONT_SIZES["legend"]),
            "bgcolor": CHART_ELEMENT_COLORS.get("legend_bg", "rgba(0,0,0,0)"),
            "bordercolor": CHART_ELEMENT_COLORS.get("legend_border", "#000"),
            "borderwidth": 1,
            "traceorder": "normal",
            "itemsizing": "constant",
            "title_text": "",
            "itemwidth": 30,
            **legend_position,
        },
        margin=margins,
        hovermode="x unified",
    )

    return fig


def calculate_and_align_axis_ranges(
    df: pd.DataFrame,
    primary_metrics: List[str],
    secondary_metrics: List[str],
    padding: float = 0.25,
) -> Tuple[Optional[List[float]], Optional[List[float]]]:
    """Calculate and align axis ranges for primary and secondary metrics."""
    if padding < 0:
        raise ValueError("Padding must be non-negative")

    all_metrics = primary_metrics + secondary_metrics
    missing_columns = set(all_metrics) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Columns {missing_columns} not found in DataFrame")

    y_range = y2_range = None
    y_span = y2_span = 0

    if primary_metrics:
        primary_data = df[primary_metrics].values.flatten()
        primary_data = np.nan_to_num(primary_data, nan=0, posinf=0, neginf=0)
        y_min, y_max = primary_data.min(), primary_data.max()
        if y_min == y_max:
            y_min -= 1
            y_max += 1
        y_range = [y_min, y_max]
        y_span = y_max - y_min

    if secondary_metrics:
        secondary_data = df[secondary_metrics].values.flatten()
        secondary_data = np.nan_to_num(secondary_data, nan=0, posinf=0, neginf=0)
        y2_min, y2_max = secondary_data.min(), secondary_data.max()
        if y2_min == y2_max:
            y2_min -= 1
            y2_max += 1
        y2_range = [y2_min, y2_max]
        y2_span = y2_max - y2_min

    if y_range:
        if y_range[0] > 0:
            y_range[0] = 0
        y_range[1] += y_span * padding

    if y2_range:
        if y2_range[0] > 0:
            y2_range[0] = 0
        y2_range[1] += y2_span * padding

    return y_range, y2_range


def get_color_for_metric(
    metric: str, index: int, num_metrics: int, num_insurers: in
) -> str:
    """Assign a consistent color for each metric or insurer."""
    if num_metrics == 1:
        return CHART_COLORS[index % len(CHART_COLORS)]
    else:
        return CHART_COLORS[(index // num_insurers) % len(CHART_COLORS)]


def generate_color_shades(base_color: str, num_shades: int) -> List[str]:
    """Generate color shades for comparison insurers and benchmarks."""
    import colorsys

    try:
        rgb = tuple(int(base_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        logger.warning(f"Invalid base_color '{base_color}'. Defaulting to '#000000'.")
        rgb = (0, 0, 0)  # Default to black if invalid

    hsv = colorsys.rgb_to_hsv(*(x / 255.0 for x in rgb))
    shades = []
    for i in range(num_shades):
        factor = 1 - i / num_shades
        new_hsv = (hsv[0], hsv[1] * factor, hsv[2] * factor)
        new_rgb = colorsys.hsv_to_rgb(*new_hsv)
        shade = "#" + "".join(f"{int(x * 255):02x}" for x in new_rgb)
        shades.append(shade)
    return shades


def add_data_labels(
    trace: go.Figure,
    chart_type: str,
    is_secondary: bool,
    num_traces: int = 1,
    is_main_insurer: bool = True,
    is_market_chart: bool = False,
    show_comparison_labels: bool = True,
    num_x_points: int = 1,
) -> go.Figure:
    """Add data labels to the chart trace."""
    base_size = 25
    trace_factor = max(0.8, 1 - (num_traces - 1) * 0.1)  # Reduce size as number of traces increases
    x_factor = max(1, 1 - (num_x_points - 1) * 0.02)  # Reduce size as number of x-axis points increases
    adjusted_size = max(15, int(base_size * trace_factor * x_factor))

    trace.update_traces(showlegend=True)

    if is_main_insurer or is_market_chart or (not is_main_insurer and show_comparison_labels):
        text_template = "%{y:.0%}" if is_secondary else "%{y:.0f}"
        if chart_type == "bar":
            text_position = "inside" if is_market_chart else "outside"
            trace.update_traces(
                textposition=text_position,
                texttemplate=text_template,
                textfont=dict(size=adjusted_size),
                marker_line_width=0,
            )
        elif chart_type == "scatter":
            trace.update_traces(
                mode="markers+text",
                textposition="top center",
                texttemplate=text_template,
                textfont=dict(size=adjusted_size),
                marker=dict(size=10),
            )
        else:  # line and area
            trace.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                texttemplate=text_template,
                textfont=dict(size=adjusted_size),
            )

    if chart_type == "area":
        trace.update_traces(fill="tozeroy")

    return trace


def get_chart_properties(
    chart_type: str, color: str, is_comparison: bool
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return appropriate properties based on chart type."""
    px_props = {"color_discrete_sequence": [color]}
    go_props = {}

    if chart_type == "bar":
        px_props["opacity"] = 0.7 if is_comparison else 1
    elif chart_type in ["line", "area"]:
        go_props["line"] = {"dash": "dash" if is_comparison else "solid"}

    return px_props, go_props


def create_chart(
    chart_type: str, df: pd.DataFrame, x: str, y: str, **kwargs
) -> go.Figure:
    """Create a chart based on the specified type."""
    chart_func = get_plotly_chart_function(chart_type)
    try:
        fig = chart_func(df, x=x, y=y, **kwargs)
        return fig
    except Exception as e:
        logger.error(f"Error in create_chart: {str(e)}")
        logger.debug(traceback.format_exc())
        raise


def apply_chart_styles(
    fig: go.Figure, chart_type: str, go_props: Dict[str, Any]
) -> go.Figure:
    """Apply additional styles to the chart."""
    if chart_type in ["line", "area"] and "line" in go_props:
        fig.update_traces(line=go_props["line"])
    return fig


def process_metric(
    df: pd.DataFrame,
    metric: str,
    chart_type: str,
    is_secondary: bool,
    insurers: List[str],
    num_metrics: int,
    main_insurer: str,
    metric_index: int,
) -> List[go.Trace]:
    """Process a single metric for all insurers and return traces."""
    traces = []
    show_comparison_labels = len(insurers) <= 3 and num_metrics == 1

    for i, insurer in enumerate(insurers):
        color = get_color_for_metric(
            metric, i + metric_index * len(insurers), num_metrics, len(insurers)
        )
        formatted_metric_name = format_metric_name(metric)

        insurer_df = df[df[INSURER_COL] == insurer]
        px_props, go_props = get_chart_properties(chart_type, color, insurer != main_insurer)

        try:
            trace_fig = create_chart(
                chart_type,
                insurer_df,
                x=DATE_COLUMN,
                y=metric,
                labels={DATE_COLUMN: translate("Quarter"), metric: formatted_metric_name},
                hover_data={metric: ":.2%" if is_secondary else ":.2f"},
                **px_props,
            )
        except Exception as e:
            logger.error(f"Failed to create chart for {insurer} - {metric}: {e}")
            continue  # Skip this trace and continue with others

        trace_fig = apply_chart_styles(trace_fig, chart_type, go_props)
        trace_fig.update_traces(name=f"{insurer} - {formatted_metric_name}")

        if chart_type == "area":
            trace_fig.update_traces(fill="tozeroy", stackgroup=None)  # Remove stacking for area charts

        trace_fig = add_data_labels(
            trace_fig,
            chart_type,
            is_secondary,
            num_metrics,
            is_main_insurer=(insurer == main_insurer),
            is_market_chart=False,
            show_comparison_labels=show_comparison_labels,
            num_x_points=len(insurer_df[DATE_COLUMN].unique()),
        )
        traces.append(trace_fig.data[0])

    return traces


def generate_combined_figure(
    df: pd.DataFrame,
    primary_metrics: List[str],
    secondary_metrics: List[str],
    primary_chart_type: str,
    secondary_chart_type: str,
    main_insurer: str,
    selected_linemains: Any,
    comparison_insurers: Optional[List[str]] = None,
    benchmark: Optional[List[str]] = None,
) -> Tuple[go.Figure, str]:
    """Generate a combined figure with primary and secondary metrics."""
    try:
        comparison_insurers = comparison_insurers or []
        benchmark = benchmark or []
        insurers = [main_insurer] + comparison_insurers + benchmark
        logger.debug(f"Generating combined figure for insurers: {insurers}")
        logger.debug(f"Primary chart type: {primary_chart_type}, Secondary chart type: {secondary_chart_type}")
        logger.debug(f"Primary metrics: {primary_metrics}")
        logger.debug(f"Secondary metrics: {secondary_metrics}")
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"DataFrame columns: {df.columns}")
        logger.debug(f"Date column values: {df[DATE_COLUMN].tolist()}")

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        metric_index = 0
        total_metrics = len(primary_metrics) + len(secondary_metrics)
        for metrics, chart_type, is_secondary in [
            (primary_metrics, primary_chart_type, False),
            (secondary_metrics, secondary_chart_type, True),
        ]:
            logger.debug(f"Processing {'secondary' if is_secondary else 'primary'} metrics: {metrics}")
            for metric in metrics:
                traces = process_metric(
                    df,
                    metric,
                    chart_type,
                    is_secondary,
                    insurers,
                    total_metrics,
                    main_insurer,
                    metric_index,
                )
                for trace in traces:
                    fig.add_trace(trace, secondary_y=is_secondary)
                metric_index += 1

        primary_y_title = ", ".join(format_metric_name(m) for m in primary_metrics) or translate(
            DEFAULT_CHART_OPTIONS["combined"]["y_title"]
        )
        secondary_y_title = ", ".join(format_metric_name(m) for m in secondary_metrics) or translate(
            DEFAULT_CHART_OPTIONS["combined"]["y_title_secondary"]
        )
        logger.debug("Calculating axis ranges")

        y_range, y2_range = calculate_and_align_axis_ranges(df, primary_metrics, secondary_metrics)
        logger.debug(f"Calculated y_range: {y_range}, y2_range: {y2_range}")

        mapped_lines = map_line(selected_linemains)
        if isinstance(mapped_lines, list):
            line_title = ", ".join(mapped_lines)
        else:
            line_title = mapped_lines

        config = ChartConfig(
            title=f"{line_title} - {map_insurer(main_insurer)}",
            x_title=translate("Quarter"),
            y_title=primary_y_title,
            y2_title=secondary_y_title,
            y_range=y_range,
            y2_range=y2_range,
            add_range_selector=False,
            legend_position={
                "orientation": "h",
                "yanchor": "top",
                "y": 0.99,
                "xanchor": "left",
                "x": 0.01,
            },
            padding={"t": 30, "r": 30, "b": 40, "l": 50},
        )
        fig = apply_consistent_styling(fig, config)

        apply_axis_styling(
            fig,
            "xaxis",
            translate("Quarter"),
            is_date=True,
            dates=df[DATE_COLUMN],
        )
        apply_axis_styling(
            fig,
            "yaxis",
            primary_y_title,
            is_percentage=False,
            range_vals=y_range,
        )
        if secondary_metrics:
            apply_axis_styling(
                fig,
                "yaxis2",
                secondary_y_title,
                is_percentage=True,
                range_vals=y2_range,
            )

        fig.update_traces(hoverlabel=dict(font=create_font_dict(FONT_SIZES["hover"])))

        return fig, "Combined figure generated successfully."

    except Exception as e:
        logger.error(f"Error in generate_combined_figure: {str(e)}")
        logger.debug(traceback.format_exc())
        return go.Figure(), f"Error generating combined figure: {str(e)}"


def generate_market_figure(
    df: pd.DataFrame,
    chart_type: str = DEFAULT_CHART_TYPE,
    selected_metric: str = "total_premiums",
    stacked: bool = True,
    show_labels: bool = True,
    padding: Optional[Dict[str, int]] = None,
) -> go.Figure:
    """Generate a market share figure."""
    try:
        logger.debug("Entering generate_market_figure function")
        logger.debug(f"Input DataFrame shape: {df.shape}")
        logger.debug(f"Chart type: {chart_type}, Stacked: {stacked}, Show labels: {show_labels}")
        logger.debug(f"Columns in DataFrame: {df.columns.tolist()}")
        logger.debug(f"Date column values: {df[DATE_COLUMN].tolist()}")

        if df.empty:
            logger.warning("Input DataFrame is empty. Returning empty figure.")
            return go.Figure()

        fig = make_subplots()

        is_percentage = "share" in selected_metric.lower() or "ratio" in selected_metric.lower()
        logger.debug(f"Is percentage data: {is_percentage}")

        num_traces = len(df.columns) - 1  # Excluding DATE_COLUMN
        num_x_points = len(df[DATE_COLUMN].unique())
        logger.debug(f"Number of traces: {num_traces}")
        logger.debug(f"Number of x-axis points: {num_x_points}")

        for i, column in enumerate(df.columns):
            if column != DATE_COLUMN:
                logger.debug(f"Processing column: {column}")
                color = CHART_COLORS[i % len(CHART_COLORS)]

                px_props, go_props = get_chart_properties(chart_type, color, False)

                try:
                    trace_fig = create_chart(
                        chart_type,
                        df,
                        x=DATE_COLUMN,
                        y=column,
                        labels={DATE_COLUMN: translate("Quarter"), column: column},
                        hover_data={column: ":.2%" if is_percentage else ":.2f"},
                        **px_props,
                    )
                except Exception as e:
                    logger.error(f"Failed to create chart for {column}: {e}")
                    continue  # Skip this trace and continue with others

                trace_fig = apply_chart_styles(trace_fig, chart_type, go_props)
                trace = trace_fig.data[0]
                trace.update(name=map_line(column))  # Ensure the legend label is se

                if show_labels:
                    trace = add_data_labels(
                        go.Figure(data=[trace]),
                        chart_type,
                        is_secondary=is_percentage,
                        num_traces=num_traces,
                        is_main_insurer=False,
                        is_market_chart=True,
                        show_comparison_labels=True,
                        num_x_points=num_x_points,
                    ).data[0]

                fig.add_trace(trace)

        # Apply stacking
        if stacked:
            if chart_type == "bar":
                fig.update_layout(barmode="relative")
            elif chart_type == "area":
                for trace in fig.data:
                    trace.update(stackgroup="one")
        else:
            if chart_type == "bar":
                fig.update_layout(barmode="group")
            elif chart_type == "area":
                for trace in fig.data:
                    trace.update(stackgroup=None)

        chart_options = DEFAULT_CHART_OPTIONS.get("market", {})
        title = chart_options.get("title", "Market Share")
        y_title = chart_options.get("y_title", "Value")

        config = ChartConfig(
            title=f"{format_metric_name(selected_metric)} - {translate(title)}",
            x_title=translate("Quarter"),
            y_title=translate(y_title),
            add_range_selector=False,
            padding={
                "t": 80,
                "r": 30,
                "b": 40,
                "l": 50,
            },
        )
        fig = apply_consistent_styling(fig, config)

        apply_axis_styling(
            fig,
            "xaxis",
            translate("Quarter"),
            is_date=True,
            dates=df[DATE_COLUMN],
        )
        apply_axis_styling(
            fig,
            "yaxis",
            translate(y_title),
            is_percentage=is_percentage,
            range_vals=None,  # Range is handled in apply_consistent_styling
        )

        if "xaxis" in fig.layout:
            logger.debug(f"X-axis type: {fig.layout.xaxis.type}")
            logger.debug(f"X-axis range: {fig.layout.xaxis.range}")
            if hasattr(fig.layout.xaxis, "tickvals"):
                logger.debug(f"X-axis tick values: {fig.layout.xaxis.tickvals}")
            if hasattr(fig.layout.xaxis, "ticktext"):
                logger.debug(f"X-axis tick labels: {fig.layout.xaxis.ticktext}")

        logger.debug("Finished generating market figure")
        return fig

    except Exception as e:
        logger.error(f"Error in generate_market_figure: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
