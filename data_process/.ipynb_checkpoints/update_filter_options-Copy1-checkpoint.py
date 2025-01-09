import pandas as pd
from typing import Optional, List, Any, Se
import logging
import json
from constants.mapping import map_insurer
from data_process.data_utils import default_insurer_options
from logging_config import setup_logging, set_debug_level, DebugLevels, get_logger, custom_profile

from constants.filter_options import (
    VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS, RATIO_METRICS_OPTIONS,
    MARKET_SHARE_METRICS_OPTIONS, Q_TO_Q_CHANGE_METRICS_OPTIONS,
    Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE, VALUE_METRICS_OPTIONS_REINSURANCE, VALUE_METRICS_OPTIONS_DIRECT,
    AVERAGE_VALUE_METRICS_OPTIONS_DIRECT, RATIO_METRICS_OPTIONS_DIRECT, MARKET_SHARE_METRICS_OPTIONS_DIRECT,
    Q_TO_Q_CHANGE_METRICS_OPTIONS_DIRECT
)
from memory_profiler import LogFile, profile

from default_values import *

from typing import List, Dict, Tuple
logger = get_logger(__name__)

def get_filter_options(
    df: pd.DataFrame,
    primary_y_metric: List[str],
    secondary_y_metric: List[str],
    show_reinsurance_chart: bool,
    x_column_selected: str,
    series_column_selected: str,
    group_column_selected: str,
    main_insurer: List[str],
    top_n_list: List[int],
    selected_metrics: List[str],
    base_metrics: Set[str],
    number_of_insurers: int,
    premium_loss_selection: List[str]
):
    primary_y_metric_options, secondary_y_metric_options, table_metric_options = get_metric_options(
        primary_y_metric, secondary_y_metric,
        show_reinsurance_chart, premium_loss_selection
    )

    x_column_options, series_column_options, group_column_options = get_column_options(
        x_column_selected, series_column_selected, group_column_selected,
        show_reinsurance_char
    )

    return (primary_y_metric_options, secondary_y_metric_options, table_metric_options,
            x_column_options, series_column_options, group_column_options)
import pandas as pd
from typing import Dict, List, Set, Any, Optional
import logging
from constants.filter_options import (
    VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS, RATIO_METRICS_OPTIONS,
    MARKET_SHARE_METRICS_OPTIONS, Q_TO_Q_CHANGE_METRICS_OPTIONS,
    Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE, VALUE_METRICS_OPTIONS_REINSURANCE, VALUE_METRICS_OPTIONS_DIRECT,
    AVERAGE_VALUE_METRICS_OPTIONS_DIRECT, RATIO_METRICS_OPTIONS_DIRECT, MARKET_SHARE_METRICS_OPTIONS_DIRECT,
    Q_TO_Q_CHANGE_METRICS_OPTIONS_DIRECT
)
from logging_config import get_logger

logger = get_logger(__name__)

def _get_metric_sets(show_reinsurance: bool, premium_loss_selection: List[str]) -> tuple[list, list]:
    """Helper function to determine metric option sets based on configuration."""
    if show_reinsurance:
        primary_options = [
            VALUE_METRICS_OPTIONS_REINSURANCE,
            Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE
        ]
        return primary_options, primary_options

    if not premium_loss_selection:
        return (
            [VALUE_METRICS_OPTIONS_INWARD, AVERAGE_VALUE_METRICS_OPTIONS_INWARD],
            [VALUE_METRICS_OPTIONS_INWARD, AVERAGE_VALUE_METRICS_OPTIONS_INWARD,
             RATIO_METRICS_OPTIONS_INWARD, MARKET_SHARE_METRICS_OPTIONS_INWARD,
             Q_TO_Q_CHANGE_METRICS_OPTIONS_INWARD]
        )

    if 'direct' in premium_loss_selection and 'inward' in premium_loss_selection:
        return (
            [VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS],
            [VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS,
             RATIO_METRICS_OPTIONS, MARKET_SHARE_METRICS_OPTIONS,
             Q_TO_Q_CHANGE_METRICS_OPTIONS]
        )

    if 'inward' not in premium_loss_selection:
        return (
            [VALUE_METRICS_OPTIONS_DIRECT, AVERAGE_VALUE_METRICS_OPTIONS_DIRECT],
            [VALUE_METRICS_OPTIONS_DIRECT, AVERAGE_VALUE_METRICS_OPTIONS_DIRECT,
             RATIO_METRICS_OPTIONS_DIRECT, MARKET_SHARE_METRICS_OPTIONS_DIRECT,
             Q_TO_Q_CHANGE_METRICS_OPTIONS_DIRECT]
        )

    return (
        [VALUE_METRICS_OPTIONS_INWARD, AVERAGE_VALUE_METRICS_OPTIONS_INWARD],
        [VALUE_METRICS_OPTIONS_INWARD, AVERAGE_VALUE_METRICS_OPTIONS_INWARD,
         RATIO_METRICS_OPTIONS_INWARD, MARKET_SHARE_METRICS_OPTIONS_INWARD,
         Q_TO_Q_CHANGE_METRICS_OPTIONS_INWARD]
    )

def _process_metrics(options_lists: List[List], selected_metric: Optional[str] = None) -> Dict[str, Dict]:
    """Helper function to process metric options."""
    metrics = {}
    if selected_metric:
        # First try to find the specific metric's option lis
        for options_list in options_lists:
            if any(opt['value'] == selected_metric for opt in options_list):
                metrics.update({opt['value']: opt for opt in options_list})
                return metrics

    # If no specific metric found or none selected, include all options
    for options_list in options_lists:
        metrics.update({opt['value']: opt for opt in options_list})

    return metrics


def get_metric_options(
    primary_y_metric: List[str],
    secondary_y_metric: List[str],
    show_reinsurance_chart: bool,
    premium_loss_selection: List[str]
) -> dict:
    """
    Get metric options based on chart type and selections.

    Args:
        primary_y_metric: List of primary metric selections
        secondary_y_metric: List of secondary metric selections
        show_reinsurance_chart: Boolean indicating if reinsurance chart is shown
        premium_loss_selection: List of selected premium loss types

    Returns:
        Dictionary containing primary and secondary metric options
    """
    try:
        # Get appropriate metric sets
        primary_options, secondary_options = _get_metric_sets(
            show_reinsurance_chart, premium_loss_selection
        )

        # Process primary metrics
        primary_metric = primary_y_metric[0] if primary_y_metric else None
        primary_metrics = _process_metrics(primary_options, primary_metric)

        # Process secondary metrics, excluding primary metrics
        secondary_metric = secondary_y_metric[0] if secondary_y_metric else None
        all_secondary_metrics = _process_metrics(secondary_options, secondary_metric)

        # Remove any metrics that are in primary from secondary
        secondary_metrics = {
            key: value for key, value in all_secondary_metrics.items()
            if key not in primary_metrics
        }

        # Process table metrics
        table_metrics = _process_metrics(
            [VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS, RATIO_METRICS_OPTIONS]
        )

        return {
            'primary_y_metric_options': list(primary_metrics.values()),
            'secondary_y_metric_options': list(secondary_metrics.values())
        }

    except Exception as e:
        logger.error(f"Error getting metric options: {str(e)}")
        return {
            'primary_y_metric_options': [],
            'secondary_y_metric_options': []
        }

def get_column_options(
    x_column_selected: str,
    series_column_selected: str,
    group_column_selected: str,
    show_reinsurance_chart: bool
) -> dict:
    """Get column options based on chart type."""
    try:
        columns = (
            ['year_quarter', 'metric', 'linemain', 'reinsurance_geography',
             'reinsurance_type', 'reinsurance_form']
            if show_reinsurance_chart else
            ['year_quarter', 'metric', 'insurer', 'linemain', 'year', 'quarter']
        )

        return {
            'x_column_options': columns,
            'series_column_options': columns,
            'group_column_options': columns
        }
    except Exception as e:
        logger.error(f"Error getting column options: {str(e)}")
        return {
            'x_column_options': [],
            'series_column_options': [],
            'group_column_options': []
        }

def handle_column_updates(trigger_id: str, x_column: str, series_column: str, group_column: str, selected_linemains: list) -> dict:
    """Handle column updates based on trigger."""
    chart_columns = [x_column, series_column, group_column]
    updates = {}
    logger.info(f"trigger_id handle_column_updates): {trigger_id}")
    if trigger_id == 'compare-insurers-main':
        if 'insurer' not in chart_columns:
            updates['group_column'] = 'insurer'

    elif trigger_id == 'selected-categories-store':
        if len(selected_linemains) > 1 and 'linemain' not in chart_columns:
            logger.info(f"Required columns (len > 1): {required_columns}")
            updates['group_column'] = 'linemain'

    elif trigger_id == 'secondary-y-metric':
        if 'metric' not in chart_columns:
            updates['group_column'] = 'metric'

    return updates

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Optional, Literal, TypedDic
import logging

# Type definitions
ColumnID = Literal['x-column', 'series-column', 'group-column']
ColumnValue = str
Updates = Dict[ColumnID, ColumnValue]

class TemporalColumns(Enum):
    """Enumeration of temporal column values."""
    YEAR = 'year'
    QUARTER = 'quarter'
    YEAR_QUARTER = 'year_quarter'

class RequiredColumns(Enum):
    """Columns that can have multiple values."""
    METRIC = 'metric'
    INSURER = 'insurer'
    LINEMAIN = 'linemain'

@dataclass
class ColumnDefaults:
    """Default values for different column types."""
    X_COLUMN: str = 'default_x'
    SERIES_COLUMN: str = 'default_series'
    GROUP_COLUMN: str = 'default_group'

class ColumnState(TypedDict):
    """Type for tracking column states."""
    x_column: str
    series_column: str
    group_column: str

@dataclass
class MultiSelectCounts:
    """Counts of multiple selections for each column type."""
    metric: in
    insurer: in
    linemain: in

def handle_axis_updates(
    trigger_id: ColumnID,
    x_state: str,
    series_state: str,
    group_state: str,
    x_col: str,
    series_col: str,
    group_col: str,
    main_insurer: List[str],
    compare_insurers: List[str],
    primary_y_metric: List[str],
    secondary_y_metric: List[str],
    selected_linemains: List[str]
) -> Updates:
    """Handle updates to chart axis columns based on user selection and business rules."""

    def get_temporal_pair(col: str) -> Optional[str]:
        """Get the appropriate temporal pair for year/quarter."""
        pairs = {
            TemporalColumns.YEAR.value: TemporalColumns.QUARTER.value,
            TemporalColumns.QUARTER.value: TemporalColumns.YEAR.value
        }
        return pairs.get(col)

    # Initialize updates
    updates: ColumnState = {
        'x_column': x_state,
        'series_column': series_state,
        'group_column': group_state
    }

    logger.info(f"\n{'='*50}\nSTARTING NEW UPDATE\n{'='*50}")
    logger.info(f"Trigger: {trigger_id}")
    logger.info(f"Initial states - X: {x_state}, Series: {series_state}, Group: {group_state}")
    logger.info(f"New values - X: {x_col}, Series: {series_col}, Group: {group_col}")

    # Map trigger values
    trigger_value_map: Dict[ColumnID, str] = {
        'x-column': x_col,
        'series-column': series_col,
        'group-column': group_col
    }

    triggered_value: str = trigger_value_map[trigger_id]
    logger.info(f"\nPHASE 1: HANDLING TRIGGERED VALUE")
    logger.info(f"Triggered value: {triggered_value}")

    # Get multi-selection information
    combined_metrics: List[str] = []
    if primary_y_metric:
        combined_metrics.extend(primary_y_metric)
    if secondary_y_metric:
        combined_metrics.extend(secondary_y_metric)

    all_insurers: List[str] = []
    if main_insurer:
        all_insurers.extend([main_insurer])
    if compare_insurers:
        all_insurers.extend([ins for ins in compare_insurers if isinstance(ins, str)])

    multi_select_counts: MultiSelectCounts = MultiSelectCounts(
        metric=len(combined_metrics),
        insurer=len(all_insurers),
        linemain=len(selected_linemains)
    )

    # Map of column lengths including single-value columns
    current_value_lengths: Dict[str, int] = {
        RequiredColumns.METRIC.value: len(combined_metrics),
        RequiredColumns.INSURER.value: len(all_insurers),
        RequiredColumns.LINEMAIN.value: len(selected_linemains),
        TemporalColumns.YEAR.value: 1,
        TemporalColumns.QUARTER.value: 1,
        TemporalColumns.YEAR_QUARTER.value: 1
    }

    logger.info("\nPHASE 2: MULTI-SELECTION ANALYSIS")
    logger.info(f"Multi-select counts: {multi_select_counts}")
    logger.info(f"Current value lengths: {current_value_lengths}")

    # Get required columns (len >= 1)
    required_columns: Dict[str, int] = {
        col: count for col, count in vars(multi_select_counts).items()
        if count >= 1
    }

    logger.warning(f"Required columns (len > 1): {required_columns}")
    logger.warning(f"triggered_value: {triggered_value}")

    # Set up column updates based on trigger
    if trigger_id == 'x-column':
        updates['x_column'] = triggered_value
        trigger_col: ColumnID = 'x-column'
        remaining_cols: List[ColumnID] = ['series_column', 'group_column']
        remaining_states: Dict[ColumnID, str] = {
            'series_column': updates['series_column'],
            'group_column': updates['group_column']
        }
    elif trigger_id == 'series-column':
        updates['series_column'] = triggered_value
        trigger_col = 'series_column'
        remaining_cols = ['x_column', 'group_column']
        remaining_states = {
            'x_column': updates['x_column'],
            'group_column': updates['group_column']
        }
    else:  # group-column
        updates['group_column'] = triggered_value
        trigger_col = 'group_column'
        remaining_cols = ['x_column', 'series_column']
        remaining_states = {
            'x_column': updates['x_column'],
            'series_column': updates['series_column']
        }

    logger.info(f"trigger_id {trigger_id}")
    logger.info(f"triggered_value {triggered_value}")

    # Handle temporal relationships
    logger.info("\nPHASE 3: TEMPORAL RELATIONSHIP HANDLING")
    if triggered_value == TemporalColumns.YEAR_QUARTER.value:
        logger.info("Year_quarter triggered - excluding year and quarter from remaining options")
        for col in remaining_cols:
            if remaining_states[col] in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value}:
                if col == 'x-column':
                    updates[col] = ColumnDefaults.X_COLUMN
                elif col == 'series-column':
                    updates[col] = ColumnDefaults.SERIES_COLUMN
                else:  # group_column
                    updates[col] = ColumnDefaults.GROUP_COLUMN
                logger.info(f"Removed {remaining_states[col]} from {col}")

    elif triggered_value in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value}:
        logger.info(f"{triggered_value} triggered - attempting to include its pair")
        temporal_pair: Optional[str] = get_temporal_pair(triggered_value)
        pair_placed: bool = False

        # Try to place temporal pair in remaining columns
        for col in remaining_cols:
            if col != 'x_column' and remaining_states[col] not in required_columns:
                if col == 'series_column':
                    updates[col] = temporal_pair
                else:  # group_column
                    updates[col] = temporal_pair
                pair_placed = True
                logger.info(f"Placed {temporal_pair} in {col}")
                break

    # Handle required columns placemen
    if required_columns:
        sorted_required: List[tuple[str, int]] = sorted(
            required_columns.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Filter out triggered value from columns to include
        columns_to_include: List[str] = [
            col for col, _ in sorted_required
            if col != triggered_value
        ]

        current_included: List[str] = [
            col for col in [
                updates['x_column'],
                updates['series_column'],
                updates['group_column']
            ] if col in required_columns
        ]

        logger.warning(f"columns_to_include: {columns_to_include}")
        logger.warning(f"current_included: {current_included}")

        # Find missing required columns
        missing_required: List[str] = [
            col for col in columns_to_include
            if col not in [
                updates['x_column'],
                updates['series_column'],
                updates['group_column']
            ]
        ]

        logger.warning(f"missing_required: {missing_required}")

        if missing_required:
            # Sort remaining columns with x-column las
            remaining_cols_sorted: List[ColumnID] = sorted(
                remaining_cols,
                key=lambda x: 0 if x == 'x-column' else 1
            )

            # Try to place missing required columns
            for required_col in missing_required:
                for col in remaining_cols_sorted:
                    if col != 'x_column':  # Try non-x columns firs






                        current_val = remaining_states[col]

                        logger.warning(f"col in remaining_cols_sorted: {current_val}")
                        logger.warning(f"col in remaining_cols_sorted: {col}")
                        logger.warning(f"col not in trigger cols or current vall not triggered_value: {(col != trigger_col and current_val == triggered_value)}")
                        logger.warning(f"current_val not in required_columns: {current_val not in required_columns}")

                        logger.warning(f"current_val not in year_quarter': {current_val != TemporalColumns.YEAR_QUARTER.value}")
                        logger.warning(f"triggered_value != 'year_quarter' : {triggered_value != TemporalColumns.YEAR_QUARTER.value }")
                        logger.warning(f"current_val not in year', 'quarterr: {current_val not in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value}}")
                        logger.warning(f"triggered_value not in year', 'quarterr: {triggered_value not in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value}}")
                        logger.warning(f"urrent_val != get_temporal_pair(triggered_value : {current_val != get_temporal_pair(triggered_value)}")






                        # Check if column can be replaced
                        if (((col != trigger_col and current_val == triggered_value) or
                             current_val not in required_columns) and
                            current_val != TemporalColumns.YEAR_QUARTER.value and
                            (triggered_value != TemporalColumns.YEAR_QUARTER.value or
                             current_val not in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value}) and
                            (triggered_value not in {TemporalColumns.YEAR.value, TemporalColumns.QUARTER.value} or
                             current_val != get_temporal_pair(triggered_value))):

                            if col == 'series_column':
                                updates['series_column'] = required_col
                            else:  # group_column
                                updates['group_column'] = required_col
                            logger.warning(f"Placed {required_col} in {col}")
                            break
                else:  # Try x_column if still not placed
                    if ('x_column' in remaining_cols and
                        updates['x_column'] not in required_columns and
                        updates['x_column'] != TemporalColumns.YEAR_QUARTER.value):
                        updates['x_column'] = required_col
                        logger.info(f"Placed {required_col} in x_column")

    logger.info("\nFINAL UPDATES:")
    logger.info(f"Final values - X: {updates['x_column']}, Series: {updates['series_column']}, Group: {updates['group_column']}")

    return updates


def handle_premium_loss_updates(premium_loss_selection: list) -> dict:
    """Handle premium loss selection updates."""
    if 'direct' in premium_loss_selection:
        return {

            'primary_y_metric': DEFAULT_PRIMARY_METRICS,
            'secondary_y_metric': DEFAULT_SECONDARY_METRICS
        }

    else:
        return {
            'primary_y_metric': DEFAULT_PRIMARY_METRICS_INWARD,
            'secondary_y_metric': DEFAULT_SECONDARY_METRICS_INWARD
        }


def handle_view_updates(show_reinsurance: bool, show_data_table: bool) -> dict:
    """Handle view type updates."""
    if show_reinsurance:
        return {
            'x_column': DEFAULT_X_COL_REINSURANCE,
            'series_column': DEFAULT_SERIES_COL_REINSURANCE,
            'group_column': DEFAULT_GROUP_COL_REINSURANCE,
            'main_insurer': DEFAULT_INSURER_REINSURANCE,
            'compare_insurers_main': DEFAULT_COMPARE_INSURER_REINSURANCE,
            'primary_y_metric': DEFAULT_PRIMARY_METRICS_REINSURANCE,
            'secondary_y_metric': DEFAULT_SECONDARY_METRICS_REINSURANCE,
            'premium_loss_checklist': DEFAULT_PREMIUM_LOSS_TYPES_REINSURANCE
        }
    elif show_data_table:
        return {
            'x_column': DEFAULT_X_COL_TABLE,
            'series_column': DEFAULT_SERIES_COL_TABLE,
            'group_column': DEFAULT_GROUP_COL_TABLE,
            'main_insurer': DEFAULT_INSURER_TABLE,
            'compare_insurers_main': DEFAULT_COMPARE_INSURER_TABLE,
            'primary_y_metric': DEFAULT_PRIMARY_METRICS_TABLE,
            'secondary_y_metric': DEFAULT_SECONDARY_METRICS_TABLE,
            'premium_loss_checklist': DEFAULT_PREMIUM_LOSS_TYPES_TABLE
        }
    else:
        return {
            'x_column': DEFAULT_X_COL_INSURANCE,
            'series_column': DEFAULT_SERIES_COL_INSURANCE,
            'group_column': DEFAULT_GROUP_COL_INSURANCE,
            'main_insurer': DEFAULT_INSURER,
            'compare_insurers_main': DEFAULT_COMPARE_INSURER,
            'primary_y_metric': DEFAULT_PRIMARY_METRICS,
            'secondary_y_metric': DEFAULT_SECONDARY_METRICS,
            'premium_loss_checklist': DEFAULT_PREMIUM_LOSS_TYPES
        }