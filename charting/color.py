import random
import re
from typing import Optional
from .config import ColorConfig
from config.logging_config import get_logger

logger = get_logger(__name__)


class ColorFormatter:
    """Handles color selection and formatting for charts"""

    def __init__(self, config: Optional[ColorConfig] = None):
        self.config = config or ColorConfig()

    def get_rgba_color(
        self,
        outer_idx: int,
        inner_idx: int,
        num_groups: int,
        num_series: int,
        outer_loop: str,
        is_grouped_by_series: bool,
        is_series_stacked: bool,
        is_groups_stacked: bool,
        x_column: str,
        group_column: str,
        series_column: str,
        chart_type: str,
        random_color: bool = False
    ) -> str:
        """
        Get RGBA color with opacity optimized for maximum contrast between items.

        Color logic:
        - Each main category (outer_loop) gets a distinct color
        - Items within each category get evenly distributed opacity values
          between 1.0 and 0.3 for maximum visual distinction
        """
        # Get base color using outer_idx for distinct colors per category

        num_inner = num_groups if is_grouped_by_series and (is_series_stacked or is_groups_stacked) else num_series
        num_outer = num_series if is_grouped_by_series and (is_series_stacked or is_groups_stacked) else num_groups
        chart_columns = [x_column, series_column, group_column]
        if random_color:
            if not hasattr(self, '_random_color_map'):
                self._random_color_map = {}

            # Assign colors per item when num_inner == 1 or num_outer == 1
            if num_inner == 1 or num_outer == 1:
                item_key = (outer_idx, inner_idx)
                if item_key not in self._random_color_map:
                    available_colors = [
                        c for c in self.config.chart_colors if c not in self.config.used_random_colors]
                    if not available_colors:
                        self.config.reset_used_colors()
                        self._random_color_map.clear()  # Reset stored colors
                        available_colors = self.config.chart_colors

                    color = random.choice(available_colors)
                    self.config.used_random_colors.append(color)
                    self._random_color_map[item_key] = color
                color = self._random_color_map[item_key]
            else:
                # Assign colors per outer_idx as before
                if outer_idx not in self._random_color_map:
                    available_colors = [
                        c for c in self.config.chart_colors if c not in self.config.used_random_colors]
                    if not available_colors:
                        self.config.reset_used_colors()
                        self._random_color_map.clear()  # Reset stored colors
                        available_colors = self.config.chart_colors

                    color = random.choice(available_colors)
                    self.config.used_random_colors.append(color)
                    self._random_color_map[outer_idx] = color
                color = self._random_color_map[outer_idx]

        elif num_outer == 1 and num_inner > 1 and 'quarter' not in chart_columns:
            color = self.config.chart_colors[inner_idx % len(
                self.config.chart_colors)]

        elif is_grouped_by_series and (is_series_stacked or is_groups_stacked):
            color = self.config.chart_colors[outer_idx % len(self.config.chart_colors)]
        
        else:
            color = self.config.chart_colors[inner_idx % len(self.config.chart_colors)]

        '''elif is_grouped_by_series:
            color = self.config.chart_colors[outer_idx % len(self.config.chart_colors)]'''        
        logger.debug(f"color {color}")
        # Calculate number of items in inner loop
        if (num_inner == 1 or num_outer == 1):
            
            
            if 'quarter' not in chart_columns and not is_grouped_by_series and not (is_series_stacked or is_groups_stacked):
                opacity = 1.0
            else:
                opacity = 1.0 - (outer_idx * (0.3 / (num_outer)))

        elif num_inner == 2:
            # Calculate step size for even distribution between 1.0 and 0.3
            if is_grouped_by_series and (is_series_stacked or is_groups_stacked):
                opacity = 1.0 - (inner_idx * (0.4 / (num_inner - 1)))
            else:
                opacity = 1.0 - (outer_idx * (0.4 / (num_outer - 1)))

        
        elif num_inner == 3:
            # Calculate step size for even distribution between 1.0 and 0.3
            opacity = 1.0 - (inner_idx * (0.5 / (num_inner - 1)))
        else:

            opacity = 1.0 - (inner_idx * (0.7 / (num_inner - 1)))

        logger.debug(f"opacity {opacity}")
        return self.adjust_color_opacity(color, opacity)

    def get_color(
            self,
            index: int,
            total: int,
            random_color: bool = False) -> str:
        """Get a color from the color palette."""
        if random_color:
            available_colors = [c for c in self.config.chart_colors
                                if c not in self.config.used_random_colors]
            if not available_colors:
                self.config.reset_used_colors()
                available_colors = self.config.chart_colors

            chosen_color = random.choice(available_colors)
            self.config.used_random_colors.append(chosen_color)
            return chosen_color

        return self.config.chart_colors[index % len(self.config.chart_colors)]

    def adjust_color_opacity(self, color: str, opacity: float) -> str:

        try:
            if color.startswith('rgba'):
                r, g, b, _ = map(float, re.findall(r"[\d.]+", color))
                return f'rgba({int(r)},{int(g)},{int(b)},{opacity})'

            elif color.startswith('rgb'):
                r, g, b = map(int, re.findall(r'\d+', color))
                return f'rgba({r},{g},{b},{opacity})'

            elif color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                return f'rgba({r},{g},{b},{opacity})'

            else:
                return f'rgba({color},{opacity})'

        except Exception as e:
            logger.error(
                f"Error adjusting color opacity for color '{color}': {str(e)}")
            return f'rgba(128,128,128,{opacity})'