# config.py

# Application configuration
APP_TITLE: str = "Insurance Data Dashboard"
DEBUG_MODE: bool = True
PORT: int = 8051
#dev_tools_hot_reload
HOT_RELOAD: bool = True

DATA_FILE_REINSURANCE: str = './data/raw/reinsurance_market.csv'
DATA_FILE_158: str = './data/raw/3rd_158_net.csv'
DATA_FILE_162: str = './data/raw/3rd_162_net.csv'

INSURERS_DICTIONARY: str = './core/insurers/definitions/insurer_map.json'
LINES_162_DICTIONARY: str = './core/lines/definitions/insurance_lines_162_rev.json'
LINES_158_DICTIONARY: str = './core/lines/definitions/insurance_lines_158_rev.json'

# Dash configuration to prevent reloads
# Dash configuration
DASH_CONFIG = {
    'debug': DEBUG_MODE,
    'dev_tools_hot_reload': False,
    'jupyter_mode': 'tab',
    'port': PORT
}