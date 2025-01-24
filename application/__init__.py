# application.__init__
import dash
import dash_bootstrap_components as dbc
import logging
import os
import pandas as pd
import time
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate
from functools import lru_cache
from typing import Dict, Any, List
from application.app_layout import create_app_layout
from application.create_component import FilterComponents
from application.components.insurance_lines_tree import insurance_lines_tree, InsuranceLinesTree
from callbacks.app_layout_callbacks import (
    setup_debug_callbacks,
    setup_resize_observer_callback,
    setup_sidebar_callbacks
)
from callbacks.buttons_callbacks import setup_buttons_callbacks
from callbacks.get_available_metrics import get_metric_options, get_premium_loss_state
from callbacks.filter_update_callbacks import setup_filter_update_callbacks
from callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from callbacks.ui_callbacks import setup_ui_callbacks
from config.default_values import (
    DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_REPORTING_FORM,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_PRIMARY_METRICS,
    DEFAULT_PERIOD_TYPE, DEFAULT_NUMBER_OF_PERIODS
)
from config.logging_config import (
    memory_monitor, setup_logging,
    get_logger, track_callback,
    track_callback_end
)
from config.main_config import (
    APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158,
    DATA_FILE_REINSURANCE,
    LINES_162_DICTIONARY, INSURERS_DICTIONARY, LINES_158_DICTIONARY,
    DASH_CONFIG,
)
from constants.translations import translate, translate_quarter
from constants.filter_options import (
    BASE_METRICS, CALCULATED_METRICS, CALCULATED_RATIOS,
    PREMIUM_LOSS_OPTIONS,
    METRICS_OPTIONS,
    METRICS,
    VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS,
    RATIO_METRICS_OPTIONS
)
from data_process.calculate_metrics import (
    get_required_metrics, calculate_metrics
)
from data_process.data_utils import (
    save_df_to_csv,
    load_json, map_line, map_insurer,
    category_structure_162, category_structure_158, get_categories_by_level

)
from data_process.process_filters import (
    filter_by_date_range_and_period_type, process_insurers_data,
    add_market_share_rows, add_growth_rows
)
from data_process.table_data import get_data_table