from typing import Iterable, List, Dict, Callable, Optional, Tuple, Any, Set, Union, Iterable
from translations import translate


DEFAULT_CHART_TYPE: str = 'bar'
DEFAULT_SECONDARY_CHART_TYPE = 'line'
DEFAULT_MARKET_CHART_TYPE = 'bar'

#'страхование жизни'
DEFAULT_CHECKED_CATEGORIES = ['6']
DEFAULT_INSURER = '1208'

DEFAULT_PRIMARY_METRICS = ['direct_premiums']

DEFAULT_SECONDARY_METRICS = []
DEFAULT_AGGREGATION_TYPE = 'previous_quarter'
DEFAULT_NUMBER_OF_PERIODS = 4
DEFAULT_PREMIUM_LOSS_TYPES = ['direct']
DEFAULT_START_QUARTER = '2018Q1'
DEFAULT_END_QUARTER = '2024Q2'

DEFAULT_X_COL_INSURANCE = 'year_quarter'
DEFAULT_SERIES_COL_INSURANCE = 'metric'
DEFAULT_GROUP_COL_INSURANCE = 'linemain'

INSURANCE_COLUMN_SWITCH = ['year_quarter', 'metric', 'insurer', 'linemain', 'year', 'quarter']
REINSURANCE_COLUMN_SWITCH = ['reinsurance_geography', 'reinsurance_type', 'reinsurance_form', 'year_quarter', 'metric', 'linemain', 'year', 'quarter']



def create_dropdown_options_non_translated(metrics: Union[Dict[str, Dict[str, str]], List[str]]) -> List[Dict[str, Any]]:
    """
    Create dropdown options from a dictionary or list of metrics.

    Args:
        metrics (Union[Dict[str, Dict[str, str]], List[str]]): The metrics to create options from.

    Returns:
        List[Dict[str, Any]]: A list of dropdown options.
    """
    if isinstance(metrics, dict):
        return [{'label': info['label'], 'value': key} for key, info in metrics.items()]
    else:
        return [{'label': metric, 'value': metric} for metric in metrics]




CHART_TYPE_OPTIONS: List[str] = ['line', 'bar', 'area', 'scatter', "smoothed_line", "gradient_mountain"]
REINSURANCE_GRAPH_OPTIONS = ['reinsurance_line', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_form']
REINSURANCE_FORM_DROPDOWN_OPTIONS = ['fac_ob', 'facultative', 'ob_fac', 'obligatory']
REINSURANCE_TYPE_DROPDOWN_OPTIONS = ['non_proportional', 'proportional']
REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS = ['within_russia', 'outside_russia']




DEFAULT_X_COL_REINSURANCE = 'year_quarter'
DEFAULT_SERIES_COL_REINSURANCE = 'metric'
DEFAULT_GROUP_COL_REINSURANCE = 'reinsurance_geography'


def create_dropdown_options(metrics: Union[Dict[str, Dict[str, str]], List[str]]) -> List[Dict[str, Any]]:
    """
    Create dropdown options from a dictionary or list of metrics.

    Args:
        metrics (Union[Dict[str, Dict[str, str]], List[str]]): The metrics to create options from.

    Returns:
        List[Dict[str, Any]]: A list of dropdown options.
    """
    if isinstance(metrics, dict):
        return [{'label': translate(info['label']), 'value': key} for key, info in metrics.items()]
    else:
        return [{'label': translate(metric), 'value': metric} for metric in metrics]

CHART_TYPE_DROPDOWN_OPTIONS = create_dropdown_options(CHART_TYPE_OPTIONS)
REINSURANCE_GRAPH_SWITCH_OPTIONS = create_dropdown_options(REINSURANCE_GRAPH_OPTIONS)
REINSURANCE_FORM_DROPDOWN_OPTIONS = create_dropdown_options(REINSURANCE_FORM_DROPDOWN_OPTIONS)
REINSURANCE_TYPE_DROPDOWN_OPTIONS = create_dropdown_options(REINSURANCE_TYPE_DROPDOWN_OPTIONS)
REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS = create_dropdown_options(REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS)
INSURANCE_COLUMN_SWITCH_OPTIONS = create_dropdown_options_non_translated(INSURANCE_COLUMN_SWITCH)
REINSURANCE_COLUMN_SWITCH_OPTIONS = create_dropdown_options_non_translated(REINSURANCE_COLUMN_SWITCH)






REINSURANCE_FIG_TYPES = ['reinsurance_line', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_form']
INSURANCE_FIG_TYPES = ['market', 'combined', 'period', 'metric']

#DEFAULT_CHECKED_CATEGORIES = ["имущество юр.лиц", "спец. риски", "прочее", "6", "4.1.8", "4.1.1", "3.1", "3.2", "страхование жизни"]


DEFAULT_EXPANDED_CATEGORIES = ["cтрахование нежизни"]
CATEGORIES_TO_EXPAND = {"страхование нежизни", "страхование жизни", "имущество юр.лиц", "ж/д", "море, грузы", "авиа", "спец. риски", "прочее"}

# Define the categories to expand as a list of dictionaries
CATEGORIES_TO_EXPAND_OPTIONS = [
    {"label": "Cтрахование жизни", "value": "страхование жизни"},
    {"label": "НС", "value": "3.1"},
    {"label": "ДМС", "value": "3.2"},

    {"label": "КАСКО", "value": "4.1.1"},
    {"label": "ОСАГО", "value": "6"},
    {"label": "Ж/Д", "value": "ж/д"},
    {"label": "Море, грузы", "value": "море, грузы"},
    {"label": "Авиа", "value": "авиа"},
    {"label": "Фин. риски", "value": "4.4"},
    {"label": "Имущество юр.лиц", "value": "имущество юр.лиц"},
    {"label": "Имущество физ. лиц", "value": "4.1.8"},
    {"label": "Прочее", "value": "прочее"}
]

DEFAULT_COMPARE_INSURER = []
DEFAULT_COMPARE_BENCHMARK =[]



DEFAULT_TABLE_METRIC = 'total_premiums'
DEFAULT_MARKET_CHART_METRIC = ['total_premiums']

DEFAULT_CALCULATED_RATIO_OPTION = []
LINEMAIN_COL = 'linemain'
INSURER_COL = 'insurer'
DATE_COLUMN: str = 'year_quarter'




DEFAULT_VALUE_METRICS = ['ceded_premiums']
DEFAULT_AVERAGE_VALUE_METRICS = []
DEFAULT_RATIO_METRICS = []
DEFAULT_QUANTITY_METRICS = []
DEFAULT_MARKET_SHARE_METRICS = []
DEFAULT_Q_TO_Q_CHANGE_METRICS = []




PERIOD_TYPES: Dict[str, Dict[str, str]] = {
    'previous_quarter': {'label': 'previous_quarter', 'type': 'value'},
    'same_q_last_year': {'label': 'same_q_last_year', 'type': 'value'},
    'same_q_last_year_ytd': {'label': 'same_q_last_year_ytd', 'type': 'value'},
    'same_q_last_year_mat': {'label': 'same_q_last_year_mat', 'type': 'value'},
    'cumulative_sum': {'label': 'cumulative_sum', 'type': 'value'},
    'previous_q_mat': {'label': 'previous_q_mat', 'type': 'value'},
}


# Premium loss options
PREMIUM_LOSS_OPTIONS: Dict[str, Dict[str, str]] = {
    'direct': {'label': 'Direct', 'type': 'value'},
    'inward': {'label': 'Inward', 'type': 'value'}
}




# Metrics
METRICS: Dict[str, Dict[str, str]] = {

    # Value metrics
    'direct_premiums': {'label': 'Direct Premiums', 'type': 'value'},
    'direct_losses': {'label': 'Direct Losses', 'type': 'value'},
    'inward_premiums': {'label': 'Inward Premiums', 'type': 'value'},
    'inward_losses': {'label': 'Inward Losses', 'type': 'value'},

    'total_premiums': {'label': 'Total Premiums', 'type': 'value'},
    'total_losses': {'label': 'Total Losses', 'type': 'value'},
    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},

    'net_premiums': {'label': 'Net Premiums', 'type': 'value'},
    'net_losses': {'label': 'Net Losses', 'type': 'value'},
    'net_balance': {'label': 'Net Balance', 'type': 'value'},
    'gross_result': {'label': 'Gross Result', 'type': 'value'},
    'net_result': {'label': 'Net Result', 'type': 'value'},
    'new_sums': {'label': 'New Sums', 'type': 'value'},
    'sums_end': {'label': 'Sums End', 'type': 'value'},

    #ratio metrics
    'gross_loss_ratio': {'label': 'Gross Loss Ratio', 'type': 'percentage'},
    'net_loss_ratio': {'label': 'Net Loss Ratio', 'type': 'percentage'},
    'effect_on_loss_ratio': {'label': 'Effect on Loss Ratio', 'type': 'percentage'},
    'ceded_premiums_ratio': {'label': 'Ceded Premiums Ratio', 'type': 'percentage'},
    'ceded_losses_ratio': {'label': 'Ceded Losses Ratio', 'type': 'percentage'},
    'ceded_ratio_diff': {'label': 'Ceded Ratio Diff', 'type': 'percentage'},
    'ceded_losses_to_ceded_premiums_ratio': {'label': 'Ceded Losses to Ceded Premiums Ratio', 'type': 'percentage'},

    #'inward_in_market_ceded_premiums': {'label': 'Inward in Market Ceded Premiums', 'type': 'percentage'},
    #'inward_in_market_ceded_losses': {'label': 'Inward in Market Ceded Losses', 'type': 'percentage'},



     #Average value metrics
    'average_sum_insured': {'label': 'Average  Sum Insured', 'type': 'average_value'},
    'average_new_sum_insured': {'label': 'Average New Sum Insured', 'type': 'average_value'},
    'average_loss': {'label': 'Average Loss', 'type': 'average_value'},
    'average_new_premium': {'label': 'Average New Premium', 'type': 'average_value'},


    #Quantity metrics

    'new_contracts': {'label': 'New Contracts', 'type': 'quantity'},
    'contracts_end': {'label': 'Contracts End', 'type': 'quantity'},
    'claims_reported': {'label': 'Claims Reported', 'type': 'quantity'},
    'claims_settled': {'label': 'Claims Settled', 'type': 'quantity'},

    # Market share metrics
    'direct_premiums_market_share': {'label': 'Direct Premiums Market Share', 'type': 'market_share'},
    'direct_losses_market_share': {'label': 'Direct Losses Market Share', 'type': 'market_share'},
    'inward_premiums_market_share': {'label': 'Inward Premiums Market Share', 'type': 'market_share'},
    'inward_losses_market_share': {'label': 'Inward Losses Market Share', 'type': 'market_share'},
    'ceded_premiums_market_share': {'label': 'Ceded Premiums Market Share', 'type': 'market_share'},
    'ceded_losses_market_share': {'label': 'Ceded Losses Market Share', 'type': 'market_share'},
    'total_premiums_market_share': {'label': 'Total Premiums Market Share', 'type': 'market_share'},
    'total_losses_market_share': {'label': 'Total Losses Market Share', 'type': 'market_share'},
    'new_sums_market_share': {'label': 'New Sums Market Share', 'type': 'market_share'},
    'sums_end_market_share': {'label': 'Sums End Market Share', 'type': 'market_share'},
    'new_contracts_market_share': {'label': 'New Contracts Market Share', 'type': 'market_share'},
    'contracts_end_market_share': {'label': 'Contracts End Market Share', 'type': 'market_share'},
    'claims_reported_market_share': {'label': 'Claims Reported Market Share', 'type': 'market_share'},
    'claims_settled_market_share': {'label': 'Claims Settled Market Share', 'type': 'market_share'},

    #q_to_q_change
    'direct_premiums_q_to_q_change': {'label': 'Direct Premiums Growth', 'type': 'q_to_q_change'},
    'direct_losses_q_to_q_change': {'label': 'Direct Losses Growth', 'type': 'q_to_q_change'},
    'inward_premiums_q_to_q_change': {'label': 'Inward Premiums Growth', 'type': 'q_to_q_change'},
    'inward_losses_q_to_q_change': {'label': 'Inward Losses Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_q_to_q_change': {'label': 'Ceded Premiums Growth', 'type': 'q_to_q_change'},
    'ceded_losses_q_to_q_change': {'label': 'Ceded Losses Growth', 'type': 'q_to_q_change'},
    'total_premiums_q_to_q_change': {'label': 'Total Premiums Growth', 'type': 'q_to_q_change'},
    'total_losses_q_to_q_change': {'label': 'Total Losses Growth', 'type': 'q_to_q_change'},

    'net_premiums_q_to_q_change': {'label': 'Net Premiums Growth', 'type': 'q_to_q_change'},
    'net_losses_q_to_q_change': {'label': 'Net Losses Growth', 'type': 'q_to_q_change'},
    'net_balance_q_to_q_change': {'label': 'Net Balance Growth', 'type': 'q_to_q_change'},
    'gross_result_q_to_q_change': {'label': 'Gross Result Growth', 'type': 'q_to_q_change'},
    'net_result_q_to_q_change': {'label': 'Net Result Growth', 'type': 'q_to_q_change'},
    'gross_loss_ratio_q_to_q_change': {'label': 'Gross Loss Ratio Growth', 'type': 'q_to_q_change'},
    'net_loss_ratio_q_to_q_change': {'label': 'Net Loss Ratio Growth', 'type': 'percentage'},
    'effect_on_loss_ratio_q_to_q_change': {'label': 'Effect on Loss Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Premiums Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_losses_ratio_q_to_q_change': {'label': 'Ceded Losses Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_ratio_diff_q_to_q_change': {'label': 'Ceded Ratio Diff Growth', 'type': 'q_to_q_change'},
    'ceded_losses_to_ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Losses to Premiums Ratio Growth', 'type': 'q_to_q_change'},
    'average_sum_insured_q_to_q_change': {'label': 'Average Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_new_sum_insured_q_to_q_change': {'label': 'Average New Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_loss_q_to_q_change': {'label': 'Average Loss Growth', 'type': 'q_to_q_change'},
    'average_new_premium_q_to_q_change': {'label': 'Average Premium Growth', 'type': 'q_to_q_change'},
    'new_sums_q_to_q_change': {'label': 'New Sums Growth', 'type': 'q_to_q_change'},
    'sums_end_q_to_q_change': {'label': 'Sums End Growth', 'type': 'q_to_q_change'},
    'new_contracts_q_to_q_change': {'label': 'New Contracts Growth', 'type': 'q_to_q_change'},
    'contracts_end_q_to_q_change': {'label': 'Contracts End Growth', 'type': 'q_to_q_change'},
    'claims_reported_q_to_q_change': {'label': 'Claims Reported Growth', 'type': 'q_to_q_change'},
    'claims_settled_q_to_q_change': {'label': 'Claims Settled Growth', 'type': 'q_to_q_change'},
    'direct_premiums_market_share_q_to_q_change': {'label': 'Direct Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'direct_losses_market_share_q_to_q_change': {'label': 'Direct Losses Market Share Growth', 'type': 'q_to_q_change'},
    'inward_premiums_market_share_q_to_q_change': {'label': 'Inward Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'inward_losses_market_share_q_to_q_change': {'label': 'Inward Losses Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_market_share_q_to_q_change': {'label': 'Ceded Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_losses_market_share_q_to_q_change': {'label': 'Ceded Losses Market Share Growth', 'type': 'q_to_q_change'},
    'total_premiums_market_share_q_to_q_change': {'label': 'Total Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'total_losses_market_share_q_to_q_change': {'label': 'Total Losses Market Share Growth', 'type': 'q_to_q_change'},
    'new_sums_market_share_q_to_q_change': {'label': 'New Sums Market Share Growth', 'type': 'q_to_q_change'},
    'sums_end_market_share_q_to_q_change': {'label': 'Sums End Market Share Growth', 'type': 'q_to_q_change'},
    'new_contracts_market_share_q_to_q_change': {'label': 'New Contracts Market Share Growth', 'type': 'q_to_q_change'},
    'contracts_end_market_share_q_to_q_change': {'label': 'Contracts End Market Share Growth', 'type': 'q_to_q_change'},
    'claims_reported_market_share_q_to_q_change': {'label': 'Claims Reported Market Share Growth', 'type': 'q_to_q_change'},
    'claims_settled_market_share_q_to_q_change': {'label': 'Claims Settled Market Share Growth', 'type': 'q_to_q_change'},

    #'inward_in_market_ceded_premiums_q_to_q_change': {'label': 'Inward in Market Ceded Premiums Growth', 'type': 'q_to_q_change'},
    #'inward_in_market_ceded_losses_q_to_q_change': {'label': 'Inward in Market Ceded Losses Growth', 'type': 'q_to_q_change'},
}




VALUE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'value'}
AVERAGE_VALUE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'average_value'}
RATIO_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'percentage'}
QUANTITY_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'quantity'}
MARKET_SHARE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'market_share'}
Q_TO_Q_CHANGE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'q_to_q_change'}





MARKET_METRIC_OPTIONS = METRICS


PRIMARY_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'value'}
SECONDARY_METRICS = {k: v for k, v in METRICS.items() if v['type'] in ['percentage', 'ratio']}

LINEMAIN_OPTIONS = {}

from typing import Set, Dict, Lis

INPUT_FILE = '162_net_processed.csv'
OUTPUT_FILE = 'augmented_df.csv'
CACHE_DIR = 'cache_dir'  # Choose an appropriate path or make it configurable

# Column names
year_quarter_col = 'year_quarter'
value_col = 'value'
linemain_col = 'linemain'
insurer_col = 'insurer'
line_type_col = 'line_type'
metric_col = 'metric'
is_line_composition_col = 'is_line_composition'
is_market_share_col = 'is_market_share'
is_q_to_q_growth_col = 'is_q_to_q_growth'
top_n_values = [5, 10, 20, 50]



# Define base metrics present in the DataFrame
base_metrics: Set[str] = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end'
}

# Define calculated metrics and their dependencies
calculated_metrics: Dict[str, List[str]] = {
    'net_balance': ['ceded_losses', 'ceded_premiums'],
    'total_premiums': ['direct_premiums', 'inward_premiums'],
    'net_premiums': ['direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'total_losses': ['direct_losses', 'inward_losses'],
    'net_losses': ['direct_losses', 'inward_losses', 'ceded_losses'],
    'gross_result': ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses'],
    'net_result': ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses', 'ceded_premiums', 'ceded_losses']
}

calculated_ratios: Dict[str, List[str]] = {
    'average_sum_insured': ['sums_end', 'contracts_end'],
    'average_new_sum_insured': ['new_sums', 'new_contracts'],
    'average_new_premium': ['direct_premiums', 'new_contracts'],
    'average_loss': ['direct_losses', 'claims_settled'],
    'ceded_premiums_ratio': ['ceded_premiums', 'direct_premiums', 'inward_premiums'],
    'ceded_losses_ratio': ['ceded_losses', 'direct_losses', 'inward_losses'],
    'ceded_losses_to_ceded_premiums_ratio': ['ceded_losses', 'ceded_premiums'],
    'gross_loss_ratio': ['direct_losses', 'inward_losses', 'direct_premiums', 'inward_premiums'],
    'net_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'effect_on_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'ceded_ratio_diff': ['ceded_losses', 'direct_losses', 'inward_losses', 'ceded_premiums', 'direct_premiums', 'inward_premiums']
}



base_metric_options: Set[str] = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end'
}






calculated_ratio_options: Set[str] = {
    'average_sum_insured',
    'average_new_sum_insured',
    'average_new_premium',
    'average_loss',
    'ceded_premiums_ratio',
    'ceded_losses_ratio',
    'ceded_losses_to_ceded_premiums_ratio',
    'gross_loss_ratio',
    'net_loss_ratio',
    'effect_on_loss_ratio',
    'ceded_ratio_diff'
}

calculated_averages_options: Set[str] = {
    'average_sum_insured',
    'average_new_sum_insured',
    'average_new_premium',
    'average_loss'
}








def create_dropdown_options(metrics: Union[Dict[str, Dict[str, str]], List[str]]) -> List[Dict[str, Any]]:
    """
    Create dropdown options from a dictionary or list of metrics.

    Args:
        metrics (Union[Dict[str, Dict[str, str]], List[str]]): The metrics to create options from.

    Returns:
        List[Dict[str, Any]]: A list of dropdown options.
    """
    if isinstance(metrics, dict):
        return [{'label': translate(info['label']), 'value': key} for key, info in metrics.items()]
    else:
        return [{'label': translate(metric), 'value': metric} for metric in metrics]





#CATEGORIES_TO_EXPAND_OPTIONS_FILTER = create_dropdown_options(CATEGORIES_TO_EXPAND_OPTIONS)

LINEMAIN_OPTIONS = create_dropdown_options(LINEMAIN_OPTIONS)
PREMIUM_LOSS_OPTIONS = create_dropdown_options(PREMIUM_LOSS_OPTIONS)
MARKET_METRIC_DROPDOWN_OPTIONS = create_dropdown_options(MARKET_METRIC_OPTIONS)
PERIOD_TYPES_OPTIONS = create_dropdown_options(PERIOD_TYPES)
PRIMARY_METRICS_OPTIONS = create_dropdown_options(PRIMARY_METRICS)
SECONDARY_METRICS_OPTIONS = create_dropdown_options(SECONDARY_METRICS)
METRICS_OPTIONS = create_dropdown_options(METRICS)
CALCULATED_RATIO_OPTIONS = create_dropdown_options(calculated_ratio_options)


VALUE_METRICS_OPTIONS = create_dropdown_options(VALUE_METRICS)
AVERAGE_VALUE_METRICS_OPTIONS = create_dropdown_options(AVERAGE_VALUE_METRICS)
RATIO_METRICS_OPTIONS = create_dropdown_options(RATIO_METRICS)
QUANTITY_METRICS_OPTIONS = create_dropdown_options(QUANTITY_METRICS)
MARKET_SHARE_METRICS_OPTIONS = create_dropdown_options(MARKET_SHARE_METRICS)
Q_TO_Q_CHANGE_METRICS_OPTIONS = create_dropdown_options(Q_TO_Q_CHANGE_METRICS)

