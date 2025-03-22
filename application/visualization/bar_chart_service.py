# application/services/bar_chart_service.py

from typing import List, Optional, Union, Dict, Any, Tuple
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from infrastructure.logger import timer


class BarChartService:

    def __init__(self, formatting_service):
        self.logger = formatting_service.logger
        self.formatting_service = formatting_service


    """Service class for creating bar chart visualizations."""

    # Predefined constants
    COLORS: List[str] = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#76B7B2',
                         '#EDC948', '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC']

    VIEWPORT_FONTS: Dict[str, Dict[str, float]] = {
        'xs': {'title': 6, 'legend': 6, 'axis': 6, 'tick': 5.5},
        'sm': {'title': 6.5, 'legend': 6.5, 'axis': 6.5, 'tick': 6},
        'md': {'title': 7.5, 'legend': 7.5, 'axis': 7.5, 'tick': 6.5},
        'lg': {'title': 7.5, 'legend': 7.5, 'axis': 7.5, 'tick': 7},
        'xl': {'title': 8, 'legend': 8, 'axis': 8, 'tick': 7},
        'xxl': {'title': 8, 'legend': 8, 'axis': 8, 'tick': 7},
        'xxxl': {'title': 8.5, 'legend': 8.5, 'axis': 8.5, 'tick': 7.5},
        'desktop': {'title': 10, 'legend': 8.5, 'axis': 8.5, 'tick': 7.5}
    }

    @timer
    def create_bar_chart(
        self,
        df: pd.DataFrame,
        index_cols: List[str],
        values_col: str,
        period_type: str,
        series_col: Optional[str] = None,
        split_cols: Optional[List[str]] = None,
        split_vals: Optional[List[Any]] = None,
        other_cols: Optional[List[str]] = None,
        other_vals: Optional[List[Any]] = None,
        val_type: Optional[str] = 'base',
        viewport_size: str = 'desktop',
        chart_n: int = 1,
        orientation: str = 'v'  # 'v' for vertical, 'h' for horizontal
    ) -> Union[dcc.Graph, html.Div]:
        """
        Create a responsive bar chart visualization.
        
        Args:
            df: Input DataFrame containing the data
            index_cols: Columns to use as index (category axis)
            values_col: Column containing values to plot
            period_type: Type of time period for formatting
            series_col: Column to use for generating series
            split_cols: Columns used for splitting/filtering
            split_vals: Values of split columns for filtering
            other_cols: Additional columns for filtering
            other_vals: Values of additional columns for filtering
            val_type: Type of value
            viewport_size: Size of the viewport for responsive design
            chart_n: Chart number for ID generation
            orientation: 'v' for vertical bars, 'h' for horizontal bars
            
        Returns:
            A Dash component containing the chart or error message
        """
        self.logger.debug(f"Creating bar chart for viewport {viewport_size}")
        self.logger.debug(f"other_vals {other_vals}")

        # Filter and prepare data
        base_df = df.copy()
        if other_cols and other_vals:
            mask = pd.Series(True, index=df.index)
            for col, val in zip(other_cols, other_vals):
                mask &= df[col] == val
            base_df = base_df[mask]

        # Check if filtered dataframe is empty
        if base_df.empty:
            self.logger.debug("No data available after filtering")
            return html.Div(
                "No data available",
                style={
                    'text-align': 'center',
                    'padding': '20px',
                    'color': '#666',
                    'font-family': 'Arial, sans-serif'
                }
            )

        x_col = index_cols[0]

        # Get ordered unique values while preserving DataFrame order from first occurrence
        df_order = pd.DataFrame({'val': base_df[x_col], 'idx': range(len(base_df))})
        first_occurrence = df_order.drop_duplicates('val').sort_values('idx')
        x_values = first_occurrence['val'].tolist()
        original_order = x_values.copy()  # Same order for both orientations

        series_values: List[Any] = []
        if series_col is not None:
            series_values = base_df[series_col].unique().tolist()
            series_order = {val: idx for idx, val in enumerate(base_df[series_col])}
            series_values.sort(key=lambda x: series_order[x])

        # Get metric value if applicable
        metric_value: Any = None
        if series_col == 'metric' and series_values:
            metric_value = series_values[0]
        elif other_cols and 'metric' in other_cols:
            idx = other_cols.index('metric')
            metric_value = other_vals[idx] if other_vals and idx < len(other_vals) else None

        # Generate chart title
        chart_title = self._generate_chart_title(split_cols, split_vals, other_cols,
                                                other_vals, period_type, metric_value)

        # Create figure and add traces
        fig = go.Figure()
        has_valid_data = False

        # Handle series values properly
        series_to_plot: List[Any] = [None] if series_col is None or len(series_values) == 0 else series_values

        for i, series_val in enumerate(series_to_plot):
            series_df = base_df[base_df[series_col] == series_val] if series_col is not None else base_df

            # Prepare data points maintaining DataFrame order
            data = self._prepare_data_points(series_df, x_col, values_col, original_order)
            if data:
                has_valid_data = True
                self._add_bar_trace(fig, data, series_col, series_val, values_col,
                                   x_col, period_type, metric_value, i, orientation)

        # Check if we have any valid data points
        if not has_valid_data:
            self.logger.debug("No valid data points found for plotting")
            return html.Div(
                "No valid data points available for visualization",
                style={
                    'text-align': 'center',
                    'padding': '20px',
                    'color': '#666',
                    'font-family': 'Arial, sans-serif'
                }
            )

        # Get font sizes for current viewport
        fonts = self.VIEWPORT_FONTS.get(viewport_size, self.VIEWPORT_FONTS['desktop'])

        # Calculate max Y value
        max_y = pd.to_numeric(base_df[values_col], errors='coerce').max() or 10
        max_y = float(max_y) * 1.1

        # Prepare tick texts
        tick_texts = [self.formatting_service.format_value(
            val, x_col, period_type, metric_value) for val in x_values]

        # Configure layout based on orientation
        axis_config, margin, legend_config = self._configure_layout(
            orientation, fonts, max_y, x_values, tick_texts, values_col
        )

        # Update layout
        fig.update_layout(
            title=chart_title,
            title_font=dict(size=fonts['title'], family="Arial, sans-serif"),
            template="plotly_white",
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1,
            legend=legend_config,
            margin=margin,
            autosize=True,
            font=dict(family="Arial, sans-serif", size=fonts['axis']),
            xaxis=axis_config['x_axis'],
            yaxis=axis_config['y_axis'],
            plot_bgcolor='white',
            yaxis_gridcolor='#E8E8E8',
            yaxis_zerolinecolor='#AAAAAA'
        )

        return dcc.Graph(
            id=f"bar-chart-{chart_n}",
            figure=fig,
            config={
                'displayModeBar': False,
                'responsive': True,
                'autosizable': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': f'bar_chart_{chart_n}',
                    'scale': 2
                }
            },
            style={
                'width': '100%',
            },
            className='responsive-chart'
        )

    def _generate_chart_title(
        self,
        split_cols: Optional[List[str]],
        split_vals: Optional[List[Any]],
        other_cols: Optional[List[str]],
        other_vals: Optional[List[Any]],
        period_type: str,
        metric_value: Any
    ) -> str:
        """Generate a formatted chart title based on filter values."""
        title_parts: List[str] = []

        # Add split_cols/split_vals pairs at the beginning if they exist
        if split_cols and split_vals:
            for i, (col, val) in enumerate(zip(split_cols, split_vals)):
                if col and val is not None:
                    title_parts.append(self.formatting_service.format_value(
                        val, col, period_type, metric_value))

        # Add other_cols/other_vals pairs
        if other_cols and other_vals:
            for col, val in zip(other_cols, other_vals):
                if col and val is not None:
                    title_parts.append(self.formatting_service.format_value(
                        val, col, period_type, metric_value))

        return " | ".join(title_parts)

    def _prepare_data_points(
        self,
        df: pd.DataFrame,
        x_col: str,
        values_col: str,
        original_order: List[Any]
    ) -> List[Tuple[Any, float]]:
        """Prepare data points for plotting, maintaining original order."""
        data: List[Tuple[Any, float]] = []
        for x_val in original_order:
            matches = df[df[x_col] == x_val]
            if not matches.empty:
                value = matches.iloc[0][values_col]  # Take first occurrence value
                if pd.isna(value) or value is None:
                    continue
                try:
                    y_value = float(value)
                    data.append((x_val, y_value))
                except (ValueError, TypeError) as e:
                    self.logger.debug(
                        f"Could not convert value '{value}' to float for {x_col}={x_val}: {e}")
        return data

    def _add_bar_trace(
        self,
        fig: go.Figure,
        data: List[Tuple[Any, float]],
        series_col: Optional[str],
        series_val: Any,
        values_col: str,
        x_col: str,
        period_type: str,
        metric_value: Any,
        color_idx: int,
        orientation: str
    ) -> None:
        """Add a bar trace to the figure."""
        x_data, y_data = zip(*data) if data else ([], [])

        series_name = self.formatting_service.format_value(
            series_val, series_col, period_type, metric_value) if series_col is not None else ''

        trace_data: Dict[str, Any] = {
            'name': series_name,
            'marker_color': self.COLORS[color_idx % len(self.COLORS)],
            'orientation': orientation
        }

        if orientation == 'h':
            trace_data.update({
                'x': y_data,
                'y': x_data,
                'hovertemplate': (f"{self.formatting_service.format_value(series_col) if series_col is not None else ''}: {series_name}<br>"
                                f"{self.formatting_service.format_value(x_col)}: %{{y}}<br>"
                                f"{self.formatting_service.format_value(values_col)}: %{{x:.2f}}<extra></extra>")
            })
        else:
            trace_data.update({
                'x': x_data,
                'y': y_data,
                'hovertemplate': (
                    f"{self.formatting_service.format_value(series_col) if series_col is not None else ''}: {series_name}<br>"
                    f"{self.formatting_service.format_value(x_col)}: %{{x}}<br>"
                    f"{self.formatting_service.format_value(values_col)}: %{{y:.2f}}<extra></extra>")
            })

        fig.add_trace(go.Bar(**trace_data))

    def _configure_layout(
        self,
        orientation: str,
        fonts: Dict[str, float],
        max_y: float,
        x_values: List[Any],
        tick_texts: List[str],
        values_col: str
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int], Dict[str, Any]]:
        """Configure the chart layout based on orientation."""
        x_axis_config: Dict[str, Any]
        y_axis_config: Dict[str, Any]
        margin: Dict[str, int]

        if orientation == 'h':
            x_axis_config = dict(
                range=[0, max_y],
                tickfont=dict(size=fonts['tick']),
                fixedrange=True,
                dtick=max_y / 5,
                title=self.formatting_service.format_value(values_col)
            )
            y_axis_config = dict(
                ticktext=tick_texts,
                tickvals=list(x_values),
                tickfont=dict(size=fonts['tick']),
                fixedrange=True,
                automargin=True,  # Ensure labels are visible
                # Force category order from top to bottom
                categoryorder='array',
                categoryarray=list(reversed(x_values))  # Reverse here to get top-to-bottom order
            )
            # Reduced right margin since legend is inside the plot
            margin = dict(l=150, r=50, t=50, b=50)
        else:
            x_axis_config = dict(
                tickangle=-60,
                ticktext=tick_texts,
                tickvals=list(x_values),
                tickfont=dict(size=fonts['tick']),
                nticks=min(len(x_values), 8),
                fixedrange=True
            )
            y_axis_config = dict(
                range=[0, max_y],
                tickfont=dict(size=fonts['tick']),
                fixedrange=True,
                dtick=max_y / 5,
                title=self.formatting_service.format_value(values_col)
            )
            margin = dict(l=50, r=50, t=50, b=70)

        # Configure legend position based on orientation
        legend_config: Dict[str, Any] = dict(
            font=dict(size=fonts['legend']),
            itemsizing='constant'
        )

        if orientation == 'h':
            legend_config.update(dict(
                # Set orientation to horizontal for better space utilization below chart
                orientation="h",
                # Position below the chart
                yanchor="top",
                y=-0.15,  # Negative value places it below the chart
                xanchor="center",
                x=0.5     # Center horizontally
            ))
        else:
            legend_config.update(dict(
                orientation="h",
                y=0.9,
                yanchor="bottom",
                x=0.7,
                xanchor="center"
            ))

        return {
            'x_axis': x_axis_config,
            'y_axis': y_axis_config
        }, margin, legend_config