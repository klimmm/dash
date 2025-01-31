from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AxisConfig:
    """Axis-related configuration settings"""
    show_grid: Dict[str, bool] = field(default_factory=lambda: {
        "x": True,
        "y": True,
        "y2": False
    })

    colors: Dict[str, str] = field(default_factory=lambda: {
        "grid": "#e0e0e0",
        "line": "#000000",
        "zero_line": "#000000"
    })

    features: Dict[str, bool] = field(default_factory=lambda: {
        "show_line": True,
        "show_zero_line": True,
        "show_tick_labels": True,  # Added this key
        "fixed_range": True,
        "mirror": False
    })

    defaults: Dict[str, str] = field(default_factory=lambda: {
        "type": "category",
        "primary_yaxis": "y",
        "secondary_yaxis": "y2",
    })

    tick_angle: int = 0


@dataclass
class ColorConfig:
    """Color and opacity configuration"""
    chart_colors: List[str] = field(default_factory=lambda: [
        '#FF6347', '#7F7F7F', '#1E90FF', '#1f77b4', '#ff7f0e',
        '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2',
        '#7f7f7f', '#bcbd22', '#17becf'
    ])
    used_random_colors: List[str] = field(default_factory=list)
    opacities: Dict[str, float] = field(default_factory=lambda: {
        "default": 0.8,
        "hover": 1.0,
        "fill": 0.5,
        "line": 0.7
    })
    background: Dict[str, str] = field(default_factory=lambda: {
        "plot": "#ffffff",
        "paper": "#ffffff"
    })

    def reset_used_colors(self) -> None:
        """Reset the list of used random colors"""
        self.used_random_colors.clear()


@dataclass
class LayoutConfig:
    """Layout configuration settings"""
    margin: Dict[str, int] = field(default_factory=lambda: {
        "l": 0,
        "r": 0,
        "t": 0,
        "b": 0
    })

    legend: Dict[str, Any] = field(default_factory=lambda: {
        "orientation": "v",
        "y_position": 1,
        "x_position": 0,
        "y_anchor": "top",
        "x_anchor": "right"
    })

    title: Dict[str, Any] = field(default_factory=lambda: {
        "x_position": 0.05,
        "y_position": 0.95,
        "x_anchor": "left",
        "y_anchor": "bottom"
    })

    legend_toggle: Dict[str, Any] = field(default_factory=lambda: {
        "pad_right": 10,
        "pad_top": 5,
        "x_position": 0.8,
        "y_position": 1,
        "x_anchor": "left",
        "y_anchor": "top",
        "border_width": 1
    })

    subplot: Dict[str, Any] = field(default_factory=lambda: {
        "specs": [[{"secondary_y": True}]]
    })


@dataclass
class BehaviorConfig:
    """Chart behavior configuration"""
    sorting: Dict[str, Any] = field(default_factory=lambda: {
        "priority_group": "1208",
        "ascending_defaults": {
            "group": True,
            "year_quarter": True,
            "year": False,
            "quarter": False,
            "series": True
        }
    })

    value_formatting: Dict[str, Any] = field(default_factory=lambda: {
        "percentage_decimal_places": 0,  # For ".0%" forma
        "hover_decimal_places": 2,       # For ".2%" forma
        "default_decimal_places": 1,     # For regular numbers
        "percentage_format": ".0%",
        "percentage_hover_format": ".2%"
    })

    hover: Dict[str, str] = field(default_factory=lambda: {
        "info": "x+y+text",
        "template": "%{x}<br>%{y}<br>%{text}<extra></extra>",
        "mode": "x unified"
    })
    stack: Dict[str, Any] = field(default_factory=lambda: {
        "group_name": "one",
        "mountain_fill_suffix": " (fill)"
    })
    trace_modes: Dict[str, str] = field(default_factory=lambda: {
        "fill": "none",
        "line": "lines",
        "scatter": "markers",
        "stacked": "lines",
        "base": "lines+markers"
    })

    text_formatting: Dict[str, str] = field(default_factory=lambda: {
        "percentage": "%{text}",
        "number": "%{text:.1f}"
    })
    features: Dict[str, bool] = field(default_factory=lambda: {
        "stacked": False,
        "show_percentage": False,
        "show_100_percent_bars": False
    })


@dataclass
class ChartTypeConfig:
    """Simplified configuration for different chart types with dynamic scaling"""
    # Size limits for various properties
    size_limits: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "bar": {
            "min_gap": 0.1,
            "max_gap": 0.4
        },
        "line": {
            "min_width": 1,
            "max_width": 4,
            "min_marker": 4,
            "max_marker": 15
        },
        "text": {
            "min_size": 8,
            "max_size": 16
        }
    })

    # Base values that will be scaled
    base_values: Dict[str, float] = field(default_factory=lambda: {
        "line_width": 4.0,
        "marker_size": 8,
        "marker_line_width": 2,
        "text_font_size": 12,
        "bar_gap": 0.15
    })

    def __post_init__(self):
        """Initialize all chart type configurations with default values"""
        self.update_configs(width=400, data_points=5)  # Default medium size

    def get_scale_coefficient(
            self,
            width: Optional[int] = None,
            data_points: Optional[int] = None) -> float:
        """Calculate a single scaling coefficient based on width and data density"""
        # Base scale based on width
        if width is None:
            width = 400  # Default medium width

        if width <= 300:
            base_scale = 0.7
        elif width <= 500:
            base_scale = 1.0
        else:
            base_scale = 1.3

        # Adjust for data density if provided
        if data_points is not None:
            if data_points <= 3:
                base_scale *= 1.2
            elif data_points > 10:
                density_factor = max(0.7, 1 - (data_points - 10) * 0.02)
                base_scale *= density_factor

        return base_scale

    def get_scaled_value(self, base_value: float, property_type: str,
                         constraint_type: str, scale: float) -> float:
        """Scale a value and apply constraints"""
        scaled_value = base_value * scale

        limits = self.size_limits.get(property_type, {})
        min_val = limits.get(f"min_{constraint_type}", scaled_value)
        max_val = limits.get(f"max_{constraint_type}", scaled_value)

        return max(min_val, min(scaled_value, max_val))

    def update_configs(self, width: Optional[int] = None,
                       data_points: Optional[int] = None) -> None:
        """Update all chart type configurations based on scaling coefficient"""
        scale = self.get_scale_coefficient(width, data_points)

        # Update bar configuration
        self.bar = {
            "opacity": 1,
            "gap": self.get_scaled_value(
                self.base_values["bar_gap"],
                "bar", "gap", scale
            ),
            "marker_line_width": self.get_scaled_value(
                self.base_values["marker_line_width"],
                "line", "width", scale
            ),
            "text_position": "inside",
            "text_font_size": self.get_scaled_value(
                self.base_values["text_font_size"],
                "text", "size", scale
            ),
            "text_color": "black",
            "inside_text_color": "white"
        }

        # Update line configuration
        self.line = {
            "width": self.get_scaled_value(
                self.base_values["line_width"],
                "line", "width", scale
            ),
            "show_markers": True,
            "marker_size": self.get_scaled_value(
                self.base_values["marker_size"],
                "line", "marker", scale
            ),
            "shape": "linear",
            "text_position": "top center",
            "text_font_size": self.bar["text_font_size"]
        }

        # Update scatter configuration (shares properties with line)
        self.scatter = {
            "marker_size": self.line["marker_size"],
            "marker_line_width": 1,
            "marker_line_opacity": 0.7
        }

        # Update area configuration
        self.area = {
            "opacity": 0.5,
            "line_width": self.line["width"]
        }

        # Update gradient mountain configuration
        self.gradient_mountain = {
            "line_width": self.line["width"],
            "colorscale": [
                [0, "rgba(220,220,220,0.8)"],
                [0.5, "rgba(140,140,140,0.5)"],
                [1, "rgba(60,60,60,0.3)"]
            ]
        }


@dataclass
class FontConfig:
    """Font-related configuration settings with advanced scaling based on traces and data density"""
    family: str = "Arial, sans-serif"
    sizes: Dict[str, int] = field(default_factory=lambda: {
        "title": 14,
        "subtitle": 12,
        "axis_title": 12,
        "axis": 20,
        "axis_tick": 20,
        "legend": 14,
        "legend_group_title": 20,
        "data_label": 20
    })
    colors: Dict[str, str] = field(default_factory=lambda: {
        "title": "#000000",
        "subtitle": "#000000",
        "axis_title": "#000000",
        "axis_tick": "#000000",
        "axis": "#000000",
        "legend": "#000000",
        "legend_group_title": "#000000",
        "data_label": "black"
    })
    weights: Dict[str, str] = field(default_factory=lambda: {
        "legend_group_title": "normal",
        "title": "bold"
    })

    def get_scale_coefficient(
            self,
            width: int,
            data_points: Optional[int] = None,
            num_traces: Optional[int] = None,
            element_type: str = 'default') -> float:
        """
        Calculate scaling coefficient based on width, data density, and number of traces

        Args:
            width: Chart width in pixels
            data_points: Number of data points (optional)
            num_traces: Number of traces/series in the chart (optional)
            element_type: Type of element being scaled ('legend', 'legend_group', 'data_label', or 'default')

        Returns:
            float: Scaling coefficient for font size
        """
        # Base scaling based on width
        if width <= 300:
            base_scale = 0.7
        elif width <= 600:
            base_scale = 1.0
        else:
            base_scale = 1.3

        # Adjust for data density if provided
        if data_points is not None:
            density = data_points / width
            if density > 0.5:
                density_factor = max(0.7, 1 - (density - 0.5) * 0.2)
                base_scale *= density_factor

        # Apply trace-specific scaling for legend-related elements
        if num_traces is not None and element_type in [
                'legend', 'legend_group', 'data_label']:
            # Define trace thresholds and their scaling impacts
            if num_traces <= 5:
                trace_factor = 1.0
            elif num_traces <= 10:
                trace_factor = 0.8
            elif num_traces <= 15:
                trace_factor = 0.7
            else:
                trace_factor = 0.6

            # Additional adjustments based on element type
            if element_type == 'legend':
                # Legend entries need to be readable but can be smaller with
                # many traces
                base_scale *= trace_factor
            elif element_type == 'legend_group':
                # Group titles should remain slightly larger than regular
                # legend entries
                base_scale *= min(1.0, trace_factor * 1.1)
            elif element_type == 'data_label':
                # Data labels should be reduced more aggressively with many
                # traces
                base_scale *= trace_factor * 0.9

        return base_scale

    def get_font_config(self, width: int, height: int,
                        data_points: Optional[int] = None,
                        num_traces: Optional[int] = None) -> Dict[str, Dict[str, any]]:
        """
        Generate font configuration with scaling based on dimensions, data density, and number of traces

        Args:
            width: Chart width in pixels
            height: Chart height in pixels
            data_points: Number of data points (optional)
            num_traces: Number of traces/series in the chart (optional)

        Returns:
            Dict containing font configurations for each element
        """
        font_config = {}

        for element, size in self.sizes.items():
            # Determine appropriate element type for scaling
            if element in ['legend', 'legend_group_title', 'data_label']:
                element_type = 'legend' if element == 'legend' else \
                    'legend_group' if element == 'legend_group_title' else 'data_label'
                scale = self.get_scale_coefficient(
                    width, data_points, num_traces, element_type)
            else:
                scale = self.get_scale_coefficient(width, data_points)

            font_config[element] = {
                'size': round(size * scale),
                'color': self.colors[element],
                'family': self.family,
                'weight': self.weights.get(element, 'normal')
            }

        return font_config


@dataclass
class ChartConfig:
    fonts: FontConfig = field(default_factory=FontConfig)
    axes: AxisConfig = field(default_factory=AxisConfig)
    colors: ColorConfig = field(default_factory=ColorConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    chart_types: ChartTypeConfig = field(default_factory=ChartTypeConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)


# Create default configuration
default_config = ChartConfig()