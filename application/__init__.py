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
from memory_profiler import profile
from typing import Dict, Any, List
from application.checklist_components import ChecklistComponent
from application.app_layout import create_app_layout
from application.insurance_lines_tree import insurance_lines_tree, InsuranceLinesTree
from callbacks.app_layout_callbacks import (
    setup_debug_callbacks,
    setup_resize_observer_callback,
    setup_sidebar_callbacks
)
from callbacks.buttons_callbacks import setup_buttons_callbacks
from callbacks.get_available_metrics import get_checklist_config
from callbacks.update_insurer_callbacks import setup_insurers_callbacks, setup_sync_insurers_callback
from callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from callbacks.ui_callbacks import setup_ui_callbacks
from callbacks.process_data_callback import setup_process_data_callback
from callbacks.update_metric_callbacks import setup_sync_metrics_callback, setup_metric_callbacks, get_metric_options

from config.default_values import (
    DEFAULT_REPORTING_FORM,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_BUSINESS_TYPE, DEFAULT_PRIMARY_METRICS,
    DEFAULT_PERIOD_TYPE, DEFAULT_NUMBER_OF_PERIODS,
    DEFAULT_END_QUARTER
)
from config.logging_config import (
    memory_monitor, setup_logging,
    get_logger, track_callback,
    track_callback_end, monitor_memory,
    callback_error_handler
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
    BUSINESS_TYPE_OPTIONS,
    METRICS_OPTIONS,
    METRICS,
    VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS,
    RATIO_METRICS_OPTIONS
)
from data_process.data_utils import (
    save_df_to_csv,
    load_json,
    map_line,
    map_insurer,
    category_structure_162,
    category_structure_158,
    get_categories_by_level
)
from application.style_config import StyleConstants

from data_process.calculate_growth import add_growth_rows
from data_process.calculate_market_share import add_market_share_rows
from data_process.calculate_metrics import get_required_metrics, calculate_metrics
from data_process.filter_date_range import filter_year_quarter
from data_process.filter_insurers import process_insurers_data
from data_process.filter_period_type import filter_by_period_type
from data_process.table_data import get_data_table