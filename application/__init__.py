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
from application.insurance_lines_tree import insurance_lines_tree_162, insurance_lines_tree_158
from callbacks.app_layout_callbacks import (
    setup_debug_callbacks,
    setup_resize_observer_callback,
    setup_sidebar_callbacks
)
from callbacks.buttons_callbacks import setup_buttons_callbacks_multichoice, setup_buttons_callbacks_singlechoice
from callbacks.update_insurer_callbacks import setup_insurers_callbacks
from callbacks.insurance_lines_selection_callbacks import setup_insurance_lines_callbacks
from callbacks.insurance_lines_tree_callbacks import setup_insurance_lines_tree_callbacks

from callbacks.ui_callbacks import setup_ui_callbacks
from callbacks.process_data_callback import setup_process_data_callback
from callbacks.update_metric_callbacks import setup_metric_callbacks
from callbacks.get_metrics import get_metric_options
from config.default_values import (
    DEFAULT_REPORTING_FORM,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_BUSINESS_TYPE, 
    DEFAULT_PRIMARY_METRICS,
    DEFAULT_PERIOD_TYPE, 
    DEFAULT_NUMBER_OF_PERIODS,
    DEFAULT_END_QUARTER,
    TOP_N_LIST
)
from config.logging_config import (
    memory_monitor, setup_logging,
    get_logger, track_callback,
    track_callback_end, monitor_memory,
    log_callback
)
from config.main_config import (
    APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158,
    DATA_FILE_REINSURANCE,
    LINES_162_DICTIONARY, INSURERS_DICTIONARY, LINES_158_DICTIONARY,
    DASH_CONFIG,
)
from constants.translations import translate, translate_quarter
from constants.filter_options import (
    BASE_METRICS, 
    CALCULATED_METRICS,
    CALCULATED_RATIOS,
    BUSINESS_TYPE_OPTIONS,
    METRICS_OPTIONS,
    METRICS,
    VALUE_METRICS_OPTIONS, 
    AVERAGE_VALUE_METRICS_OPTIONS,
    RATIO_METRICS_OPTIONS
)
from constants.style_config import StyleConstants
from data_process.data_utils import save_df_to_csv, load_json, map_line, map_insurer, get_year_quarter_options
from data_process.business_type_checklist_config import get_checklist_config
from data_process.insurer_options import get_insurer_options
from data_process.add_top_n_rows import add_top_n_rows
from data_process.calculate_growth import add_growth_rows
from data_process.calculate_market_share import add_market_share_rows
from data_process.calculate_metrics import get_required_metrics, calculate_metrics
from data_process.filter_date_range import filter_year_quarter
from data_process.filter_insurers import process_insurers_data
from data_process.insurance_line_options import get_insurance_line_options
from data_process.filter_period_type import filter_by_period_type
from data_process.load_insurance_dataframes import load_insurance_dataframes
from data_process.table_data import get_data_table