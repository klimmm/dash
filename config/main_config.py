# config.py
import dash_bootstrap_components as dbc
from typing import Dict, List, Any

# Application configuration
APP_TITLE: str = "Insurance Data Dashboard"
DEBUG_MODE: bool = True
PORT: int = 8051
#dev_tools_hot_reload
HOT_RELOAD: bool = True

DATA_FILE_REINSURANCE: str = './data_files/reinsurance_market.csv'
DATA_FILE_158: str = './data_files/3rd_158_net.csv'
DATA_FILE_162: str = './data_files/3rd_162_net.csv'

INSURERS_DICTIONARY: str = './domain/insurers/definitions/insurer_map.json'
LINES_162_DICTIONARY: str = './domain/lines/definitions/insurance_lines_162_rev.json'
LINES_158_DICTIONARY: str = './domain/lines/definitions/insurance_lines_158_rev.json'

# Dash configuration to prevent reloads
# Dash configuration
DASH_CONFIG = {
    'debug': DEBUG_MODE,
    'dev_tools_hot_reload': False,
    'jupyter_mode': 'tab',
    'port': PORT
}