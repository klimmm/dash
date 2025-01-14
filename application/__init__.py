# application.__init__

from config.default_values import (
    DEFAULT_PREMIUM_LOSS_TYPES,
    DEFAULT_SECONDARY_METRICS,
    DEFAULT_CHECKED_LINES,
    DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_PRIMARY_METRICS,
    DEFAULT_PERIOD_TYPE, DEFAULT_NUMBER_OF_PERIODS
)

from config.main_config import (
    APP_TITLE, DEBUG_MODE, PORT, DATA_FILE_162, DATA_FILE_158,
    DATA_FILE_REINSURANCE,
    LINES_162_DICTIONARY, INSURERS_DICTIONARY, LINES_158_DICTIONARY,
    DASH_CONFIG,
    DATA_FILE_158
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

from application.app_layout import create_app_layout
from application.components.insurance_lines_tree import InsuranceLinesTree
from application.components.dash_table import generate_dash_table_config
from application.callbacks.period_filter import setup_period_type_callbacks
from application.callbacks.insurance_lines_callbacks import setup_insurance_lines_callbacks
from application.callbacks.filter_update_callbacks import setup_filter_update_callbacks

from data_process.data_utils import (
    create_year_quarter_options, load_and_preprocess_data,
    save_df_to_csv, log_dataframe_info, print_dataframe_info,
    load_json, log_chart_structure, process_inputs, map_line, map_insurer
)
from data_process.process_filters import MetricsProcessor
from data_process.table_data import get_data_table