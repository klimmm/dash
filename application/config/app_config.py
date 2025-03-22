import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Optional

class AppConfig:
    """Configuration class for Insurance Data Dashboard application."""

    # Application configuration
    APP_TITLE = "Insurance Data Dashboard"
    DEBUG_MODE = True
    PORT = 8051

    # Data file paths
    DATA_FILE_REINSURANCE = './infrastructure/data/raw/reinsurance_market.csv'
    DATA_FILE_158 = './infrastructure/data/raw/3rd_158_net.csv'
    DATA_FILE_162 = './infrastructure/data/etl/form162/processing/intermediate_data/3rd_162_net.csv'

    # Dictionary file paths
    INSURERS_DICTIONARY = './infrastructure/data/json/insurers.json'
    CONVERTED_INSURERS_DICTIONARY = './infrastructure/data/json/converted_insurers.json'
    LINES_162_DICTIONARY = './infrastructure/data/json/hierarchy/insurance_lines_162_rev.json'
    LINES_158_DICTIONARY = './infrastructure/data/json/hierarchy/insurance_lines_158_rev.json'
    METRICS_162_DICTIONARY = './infrastructure/mapping/metrics_tree_162.json'
    METRICS_158_DICTIONARY = './infrastructure/mapping/metrics_tree_158.json'
    OUTPUT_CSV_DIR = './infrastructure/data/processed'
    LOG_FILE = 'app.log'
    LOG_PATH = './logs'  # Path('logs')
    # Dash configuration
    DASH_CONFIG = {
        'debug': DEBUG_MODE,
        'dev_tools_hot_reload': False,
        'jupyter_mode': 'tab',
        'port': PORT
    }
    DEFAULT_STORAGE_TYPE = 'memory'