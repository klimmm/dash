import math
import plotly.graph_objects as go
from typing import List, Optional, Tuple, Union
from config.logging_config import get_logger

logger = get_logger(__name__)


def get_axis_ranges(
    traces: List[Union[go.Bar, go.Scatter]],
    base_values,
    is_series_stacked, 
    primary_chart_type,
    compare_insurers, 
    secondary_y_metrics,
    show_percentage,
    show_100_percent
    
) -> Tuple[List[float], Optional[List[float]]]:

    y_range, y2_range = None, None
    
    if is_series_stacked and primary_chart_type.lower() != 'bar':
        return None, None
        
    y_min, y_max = float('inf'), float('-inf')
    y2_min, y2_max = float('inf'), float('-inf')

    for trace in traces:
        y_data = trace.y
        base = trace.base if isinstance(
            trace, go.Bar) and trace.base is not None else [0] * len(y_data)

        if getattr(trace, 'yaxis', 'y') == 'y':
            y_min = min(y_min, min(y_data), min(base))
            y_max = max(y_max, max([y + b for y, b in zip(y_data, base)]))
        else:  # 'y2' axis
            y2_min = min(y2_min, min(y_data), min(base))
            y2_max = max(y2_max, max([y + b for y, b in zip(y_data, base)]))

    if y2_min == float('inf') or y2_max == float('-inf'):
        y_range, y2_range = [y_min, y_max], None
    else:
        y_range, y2_range = [y_min, y_max], [y2_min, y2_max]

    if compare_insurers and not secondary_y_metrics:
        min_y = min(y_range[0], y2_range[0] if y2_range else y_range[0])
        max_y = max(y_range[1], y2_range[1] if y2_range else y_range[1])
        y_range = y2_range = [min_y, max_y]

    else:
        y_range, y2_range = calculate_and_align_axis_ranges(
            y_range=y_range,
            y2_range=y2_range,
            show_percentage=show_percentage,
            show_100_percent_bars=show_100_percent
        )

    return y_range, y2_range


def calculate_and_align_axis_ranges(
    y_range: List[float],
    y2_range: Optional[List[float]],
    show_percentage: bool,
    show_100_percent_bars: bool,
    padding: float = 0.15
) -> Tuple[List[float], Optional[List[float]]]:
    logger.info("Starting calculate_and_align_axis_ranges")
    logger.info(
        f"Input parameters: y_range={y_range}, y2_range={y2_range}, "
        f"show_percentage={show_percentage}, show_100_percent_bars={show_100_percent_bars}, "
        f"padding={padding}")

    def adjust_range(range_: List[float]) -> List[float]:
        logger.info(f"Adjusting range: {range_}")
        min_, max_ = range_
        if min_ > 0:
            logger.info(
                f"Adjusting minimum from {min_} to 0 as it was positive")
            min_ = 0
        if max_ < 0:
            logger.info(f"Adjusting maximum to {-min_} as it was negative")
            max_ = -min_
        span = max_ - min_
        logger.info(f"Range span: {span}")

        max_ += span * padding
        if min_ < 0:
            min_ -= span * (padding / 2)

        logger.info(f"Adjusted range: [{min_}, {max_}]")
        return [min_, max_]

    # Case 1: Only y_range exists
    if y2_range is None and y_range is not None:
        logger.info("Processing case: only y_range exists")
        result = adjust_range(y_range), None
        logger.info(f"Returning result: {result}")
        return result

    # Case 2: Only y2_range exists or y_range is invalid
    elif y_range is None or (len(y_range) == 2 and all(math.isinf(x) for x in y_range)) and y2_range is not None:
        logger.info(
            "Processing case: only y2_range exists or y_range is invalid")
        result = None, adjust_range(y2_range)
        logger.info(f"Returning result: {result}")
        return result

    # Case 3: Both ranges exis
    elif y_range is not None and y2_range is not None:
        logger.info("Processing case: both ranges exist")
        y_min, y_max = y_range
        y2_min, y2_max = y2_range
        logger.info(
            f"Initial ranges - y: [{y_min}, {y_max}], y2: [{y2_min}, {y2_max}]")

        # Calculate zero positions
        y_zero_pos = -y_min / (y_max - y_min) if y_min < 0 and y_max > 0 else 0
        y2_zero_pos = abs(y2_min) / (y2_max -
                                     y2_min) if y2_min < 0 and y2_max > 0 else 0
        logger.info(f"Zero positions - y: {y_zero_pos}, y2: {y2_zero_pos}")

        if y_min > 0 and y2_min > 0:
            y_min = 0
            y2_min = 0
            logger.info(f"y_min > 0 and y2_min > 0:")

        elif y_max < 0 and y2_max < 0:
            y_max = 0
            y2_max = 0
            logger.info(f"y_max < 0 and y2_max <0")

        elif y_max > 0 and y_min < 0 and y2_max < 0:
            y2_max = y2_min * (1 - y_zero_pos) / (-y_zero_pos)
            logger.info(f"y_max > 0 and y_min < 0 and y2_max < 0")

        elif y2_max > 0 and y2_min < 0 and y_max < 0:
            y_max = y_min * (1 - y2_zero_pos) / (-y2_zero_pos)
            logger.info(f"yy2_max > 0 and y2_min < 0 and y_max < 0")

        elif y_min >= 0 and y2_max <= 0:
            y_min = -y_max
            y2_max = -y2_min
            logger.info(f"yy_min >= 0 and y2_max <= 0:")

        elif y2_min >= 0 and y_max <= 0:
            y2_min = -y2_max
            y_max = -y_min
            logger.info(f"y2_min >= 0 and y_max <= 0")

        else:
            target_zero_pos = max(y_zero_pos, y2_zero_pos)
            logger.info(f"Target zero position: {target_zero_pos}")

            # Adjust minimums if necessary
            if target_zero_pos > y_zero_pos:
                y_min = (target_zero_pos * y_max) / (target_zero_pos - 1)
                logger.info(f" target_zero_pos  {target_zero_pos}")
                logger.info(f" y_max  {y_max}")
                logger.info(f"Adjusted y_min to {y_min}")

            if target_zero_pos > y2_zero_pos:
                y2_min = (-target_zero_pos * y2_max) / (1 - target_zero_pos)
                logger.info(f"Adjusted y2_min to {y2_min}")

        # Apply final adjustments
        y_range = adjust_range([y_min, y_max])
        y2_range = adjust_range([y2_min, y2_max])

        logger.info(f"Final ranges - y: {y_range}, y2: {y2_range}")

        return y_range, y2_range

    else:
        logger.warning("No valid ranges provided")
        return None, None
