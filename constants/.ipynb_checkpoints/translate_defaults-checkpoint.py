

DEFAULT_AGGREGATION_TYPE = 'previous_q_mat'
DEFAULT_Q_VALUE = 4
DEFAULT_BUTTON_INDEX = 1
DEFAULT_START_QUARTER = '2022Q1'
DEFAULT_END_QUARTER = '2024Q2'
DEFAULT_NUMBER_OF_PERIODS = 10
DEFAULT_PERIOD_TYPE = {'main': 'qoq', 'sub': '1h'}

DEFAULT_CHECKED_CATEGORIES = ['осаго']
DEFAULT_INSURER = 'total'


DEFAULT_COMPARE_INSURER = []
DEFAULT_PRIMARY_METRICS = ['direct_premiums', 'direct_losses']
DEFAULT_SECONDARY_METRICS = []

#DEFAULT_COMPARE_INSURER = ['top-5-benchmark', 'others']

#DEFAULT_SECONDARY_METRICS = ['average_new_sum_insured_q_to_q_change', 'direct_premiums_market_share_q_to_q_change']

DEFAULT_PREMIUM_LOSS_TYPES = ['direct']
DEFAULT_TABLE_METRIC = ['direct_premiums']
DEFAULT_ADDITIONAL_TABLE_METRIC = []
#DEFAULT_AGGREGATION_TYPE = 'same_q_last_year_mat'







'''DEFAULT_NUMBER_OF_PERIODS = 6
DEFAULT_PERIOD_TYPE = {'main': 'mat', 'sub': 'q'}
DEFAULT_PRIMARY_METRICS = ['ceded_losses_to_ceded_premiums_ratio']'''


DEFAULT_X_COL_INSURANCE = 'year_quarter'
DEFAULT_SERIES_COL_INSURANCE = 'metric'
DEFAULT_GROUP_COL_INSURANCE = 'linemain'


DEFAULT_SERIES_GROUP = False
DEFAULT_SERIES_STACK = False
DEFAULT_GROUPS_STACK = False

DEFAULT_CHART_TYPE = 'bar'
DEFAULT_SECONDARY_CHART_TYPE = 'line'


#'страхование жизни'


#DEFAULT_COMPARE_BENCHMARK =['others']
DEFAULT_COMPARE_BENCHMARK =[]

DEFAULT_INSURER_REINSURANCE = 'total'
DEFAULT_COMPARE_INSURER_REINSURANCE = []
DEFAULT_PRIMARY_METRICS_REINSURANCE = ['ceded_premiums']
DEFAULT_SECONDARY_METRICS_REINSURANCE = []
DEFAULT_X_COL_REINSURANCE = 'year_quarter'
DEFAULT_SERIES_COL_REINSURANCE = 'linemain'
DEFAULT_GROUP_COL_REINSURANCE = 'metric'
DEFAULT_PREMIUM_LOSS_TYPES_REINSURANCE = ['direct', 'inward']



DEFAULT_INSURER_TABLE = 'total'
DEFAULT_COMPARE_INSURER_TABLE = []
DEFAULT_PRIMARY_METRICS_TABLE = ['direct_premiums']
DEFAULT_SECONDARY_METRICS_TABLE = []
DEFAULT_X_COL_TABLE = 'year_quarter'
DEFAULT_SERIES_COL_TABLE = 'metric'
DEFAULT_GROUP_COL_TABLE = 'insurer'
DEFAULT_PREMIUM_LOSS_TYPES_TABLE = ['direct', 'inward']



DEFAULT_PRIMARY_METRICS_INWARD = ['inward_premiums', 'inward_losses']
DEFAULT_SECONDARY_METRICS_INWARD = []

#DEFAULT_CHECKED_CATEGORIES = ["имущество юр.лиц", "спец. риски", "прочее", "6", "4.1.8", "4.1.1", "3.1", "3.2", "страхование жизни"]


DEFAULT_EXPANDED_CATEGORIES = ["cтрахование нежизни"]
CATEGORIES_TO_EXPAND = {"страхование нежизни", "страхование жизни", "имущество юр.лиц", "ж/д", "море, грузы", "авиа", "спец. риски", "прочее"}




from typing import Iterable, List, Dict, Callable, Optional, Tuple, Any, Set, Union, Iterable
from constants.translations import translate

METRICS_DIRECT: Dict[str, Dict[str, str]] = {

    # Value metrics
    'direct_premiums': {'label': 'Direct Premiums', 'type': 'value'},
    'direct_losses': {'label': 'Direct Losses', 'type': 'value'},
    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},

    'new_contracts': {'label': 'New Contracts', 'type': 'quantity'},
    'new_sums': {'label': 'New Sums', 'type': 'value'},
    'average_new_sum_insured': {'label': 'Average New Sum Insured', 'type': 'average_value'},
    'average_new_premium': {'label': 'Average New Premium', 'type': 'average_value'},
    'claims_settled': {'label': 'Claims Settled', 'type': 'quantity'},
    'average_loss': {'label': 'Average Loss', 'type': 'average_value'},

    #'net_balance': {'label': 'Net Balance', 'type': 'value'},
    #'gross_result': {'label': 'Gross Result', 'type': 'value'},
    #'net_result': {'label': 'Net Result', 'type': 'value'},
    'sums_end': {'label': 'Sums End', 'type': 'value'},

    #ratio metrics
    #'net_loss_ratio': {'label': 'Net Loss Ratio', 'type': 'percentage'},

    #'gross_loss_ratio': {'label': 'Gross Loss Ratio', 'type': 'percentage'},
    #'effect_on_loss_ratio': {'label': 'Effect on Loss Ratio', 'type': 'percentage'},
    'ceded_premiums_ratio': {'label': 'Ceded Premiums Ratio', 'type': 'percentage'},
    'ceded_losses_ratio': {'label': 'Ceded Losses Ratio', 'type': 'percentage'},
    #'ceded_ratio_diff': {'label': 'Ceded Ratio Diff', 'type': 'percentage'},
    'ceded_losses_to_ceded_premiums_ratio': {'label': 'Ceded Losses to Ceded Premiums Ratio', 'type': 'percentage'},


    'premiums_interm_total': {'label': 'premiums_interm_total', 'type': 'value'},
    'commissions_electronic': {'label': 'commissions_electronic', 'type': 'value'},

    'commissions_nonelec': {'label': 'commissions_nonelec', 'type': 'value'},
    'premiums_interm_electronic': {'label': 'premiums_interm_electronic', 'type': 'value'},

    'premiums_interm_nonelec': {'label': 'premiums_interm_nonelec', 'type': 'value'},
    'commissions_total': {'label': 'commissions_total', 'type': 'value'},

     #Average value metrics
    'average_sum_insured': {'label': 'Average  Sum Insured', 'type': 'average_value'},

    #Quantity metrics
    'contracts_end': {'label': 'Contracts End', 'type': 'quantity'},
    'claims_reported': {'label': 'Claims Reported', 'type': 'quantity'},

    # Market share metrics
    'direct_premiums_market_share': {'label': 'Direct Premiums Market Share', 'type': 'market_share'},
    'direct_losses_market_share': {'label': 'Direct Losses Market Share', 'type': 'market_share'},
    'ceded_premiums_market_share': {'label': 'Ceded Premiums Market Share', 'type': 'market_share'},
    'ceded_losses_market_share': {'label': 'Ceded Losses Market Share', 'type': 'market_share'},
    #'new_sums_market_share': {'label': 'New Sums Market Share', 'type': 'market_share'},
    #'sums_end_market_share': {'label': 'Sums End Market Share', 'type': 'market_share'},
    #'new_contracts_market_share': {'label': 'New Contracts Market Share', 'type': 'market_share'},
    #'contracts_end_market_share': {'label': 'Contracts End Market Share', 'type': 'market_share'},
    #'claims_reported_market_share': {'label': 'Claims Reported Market Share', 'type': 'market_share'},
    #'claims_settled_market_share': {'label': 'Claims Settled Market Share', 'type': 'market_share'},

    #q_to_q_change
    'direct_premiums_q_to_q_change': {'label': 'Direct Premiums Growth', 'type': 'q_to_q_change'},
    'direct_losses_q_to_q_change': {'label': 'Direct Losses Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_q_to_q_change': {'label': 'Ceded Premiums Growth', 'type': 'q_to_q_change'},
    'ceded_losses_q_to_q_change': {'label': 'Ceded Losses Growth', 'type': 'q_to_q_change'},

    #'net_premiums_q_to_q_change': {'label': 'Net Premiums Growth', 'type': 'q_to_q_change'},
    #'net_losses_q_to_q_change': {'label': 'Net Losses Growth', 'type': 'q_to_q_change'},
    #'net_balance_q_to_q_change': {'label': 'Net Balance Growth', 'type': 'q_to_q_change'},
    #'gross_result_q_to_q_change': {'label': 'Gross Result Growth', 'type': 'q_to_q_change'},
    #'net_result_q_to_q_change': {'label': 'Net Result Growth', 'type': 'q_to_q_change'},
    #'gross_loss_ratio_q_to_q_change': {'label': 'Gross Loss Ratio Growth', 'type': 'q_to_q_change'},
    'net_loss_ratio_q_to_q_change': {'label': 'Net Loss Ratio Growth', 'type': 'percentage'},
    #'effect_on_loss_ratio_q_to_q_change': {'label': 'Effect on Loss Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Premiums Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_losses_ratio_q_to_q_change': {'label': 'Ceded Losses Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_ratio_diff_q_to_q_change': {'label': 'Ceded Ratio Diff Growth', 'type': 'q_to_q_change'},
    'ceded_losses_to_ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Losses to Premiums Ratio Growth', 'type': 'q_to_q_change'},
    #'average_sum_insured_q_to_q_change': {'label': 'Average Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_new_sum_insured_q_to_q_change': {'label': 'Average New Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_loss_q_to_q_change': {'label': 'Average Loss Growth', 'type': 'q_to_q_change'},
    'average_new_premium_q_to_q_change': {'label': 'Average Premium Growth', 'type': 'q_to_q_change'},
    #'new_sums_q_to_q_change': {'label': 'New Sums Growth', 'type': 'q_to_q_change'},
    #'sums_end_q_to_q_change': {'label': 'Sums End Growth', 'type': 'q_to_q_change'},
    #'new_contracts_q_to_q_change': {'label': 'New Contracts Growth', 'type': 'q_to_q_change'},
    #'contracts_end_q_to_q_change': {'label': 'Contracts End Growth', 'type': 'q_to_q_change'},
    #'claims_reported_q_to_q_change': {'label': 'Claims Reported Growth', 'type': 'q_to_q_change'},
    #'claims_settled_q_to_q_change': {'label': 'Claims Settled Growth', 'type': 'q_to_q_change'},
    'direct_premiums_market_share_q_to_q_change': {'label': 'Direct Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'direct_losses_market_share_q_to_q_change': {'label': 'Direct Losses Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_market_share_q_to_q_change': {'label': 'Ceded Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_losses_market_share_q_to_q_change': {'label': 'Ceded Losses Market Share Growth', 'type': 'q_to_q_change'},
    #'new_sums_market_share_q_to_q_change': {'label': 'New Sums Market Share Growth', 'type': 'q_to_q_change'},
    #'sums_end_market_share_q_to_q_change': {'label': 'Sums End Market Share Growth', 'type': 'q_to_q_change'},
    #'new_contracts_market_share_q_to_q_change': {'label': 'New Contracts Market Share Growth', 'type': 'q_to_q_change'},
    #'contracts_end_market_share_q_to_q_change': {'label': 'Contracts End Market Share Growth', 'type': 'q_to_q_change'},
    #'claims_reported_market_share_q_to_q_change': {'label': 'Claims Reported Market Share Growth', 'type': 'q_to_q_change'},
    #'claims_settled_market_share_q_to_q_change': {'label': 'Claims Settled Market Share Growth', 'type': 'q_to_q_change'},
}



METRICS_INWARD: Dict[str, Dict[str, str]] = {

    # Value metrics
    'inward_premiums': {'label': 'Inward Premiums', 'type': 'value'},
    'inward_losses': {'label': 'Inward Losses', 'type': 'value'},

    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},

    'net_premiums': {'label': 'Net Premiums', 'type': 'value'},
    'net_losses': {'label': 'Net Losses', 'type': 'value'},
    #'net_balance': {'label': 'Net Balance', 'type': 'value'},
    #'gross_result': {'label': 'Gross Result', 'type': 'value'},
    #'net_result': {'label': 'Net Result', 'type': 'value'},

    #ratio metrics
    #'gross_loss_ratio': {'label': 'Gross Loss Ratio', 'type': 'percentage'},
    'net_loss_ratio': {'label': 'Net Loss Ratio', 'type': 'percentage'},
    #'effect_on_loss_ratio': {'label': 'Effect on Loss Ratio', 'type': 'percentage'},
    'ceded_premiums_ratio': {'label': 'Ceded Premiums Ratio', 'type': 'percentage'},
    'ceded_losses_ratio': {'label': 'Ceded Losses Ratio', 'type': 'percentage'},
    #'ceded_ratio_diff': {'label': 'Ceded Ratio Diff', 'type': 'percentage'},
    'ceded_losses_to_ceded_premiums_ratio': {'label': 'Ceded Losses to Ceded Premiums Ratio', 'type': 'percentage'},

    #'inward_in_market_ceded_premiums': {'label': 'Inward in Market Ceded Premiums', 'type': 'percentage'},
    #'inward_in_market_ceded_losses': {'label': 'Inward in Market Ceded Losses', 'type': 'percentage'},

    # Market share metrics
    'inward_premiums_market_share': {'label': 'Inward Premiums Market Share', 'type': 'market_share'},
    'inward_losses_market_share': {'label': 'Inward Losses Market Share', 'type': 'market_share'},
    'ceded_premiums_market_share': {'label': 'Ceded Premiums Market Share', 'type': 'market_share'},
    'ceded_losses_market_share': {'label': 'Ceded Losses Market Share', 'type': 'market_share'},

    #q_to_q_change
    'inward_premiums_q_to_q_change': {'label': 'Inward Premiums Growth', 'type': 'q_to_q_change'},
    'inward_losses_q_to_q_change': {'label': 'Inward Losses Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_q_to_q_change': {'label': 'Ceded Premiums Growth', 'type': 'q_to_q_change'},
    'ceded_losses_q_to_q_change': {'label': 'Ceded Losses Growth', 'type': 'q_to_q_change'},

    #'net_premiums_q_to_q_change': {'label': 'Net Premiums Growth', 'type': 'q_to_q_change'},
    #'net_losses_q_to_q_change': {'label': 'Net Losses Growth', 'type': 'q_to_q_change'},
    #'net_balance_q_to_q_change': {'label': 'Net Balance Growth', 'type': 'q_to_q_change'},
    #'gross_result_q_to_q_change': {'label': 'Gross Result Growth', 'type': 'q_to_q_change'},
    #'net_result_q_to_q_change': {'label': 'Net Result Growth', 'type': 'q_to_q_change'},
    #'gross_loss_ratio_q_to_q_change': {'label': 'Gross Loss Ratio Growth', 'type': 'q_to_q_change'},
    'net_loss_ratio_q_to_q_change': {'label': 'Net Loss Ratio Growth', 'type': 'percentage'},
    #'effect_on_loss_ratio_q_to_q_change': {'label': 'Effect on Loss Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Premiums Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_losses_ratio_q_to_q_change': {'label': 'Ceded Losses Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_ratio_diff_q_to_q_change': {'label': 'Ceded Ratio Diff Growth', 'type': 'q_to_q_change'},
    'ceded_losses_to_ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Losses to Premiums Ratio Growth', 'type': 'q_to_q_change'},

    'inward_premiums_market_share_q_to_q_change': {'label': 'Inward Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'inward_losses_market_share_q_to_q_change': {'label': 'Inward Losses Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_market_share_q_to_q_change': {'label': 'Ceded Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_losses_market_share_q_to_q_change': {'label': 'Ceded Losses Market Share Growth', 'type': 'q_to_q_change'},


    #'inward_in_market_ceded_premiums_q_to_q_change': {'label': 'Inward in Market Ceded Premiums Growth', 'type': 'q_to_q_change'},
    #'inward_in_market_ceded_losses_q_to_q_change': {'label': 'Inward in Market Ceded Losses Growth', 'type': 'q_to_q_change'},
}


VALUE_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'value'}
AVERAGE_VALUE_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'average_value'}
RATIO_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'percentage'}
QUANTITY_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'quantity'}
MARKET_SHARE_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'market_share'}
Q_TO_Q_CHANGE_METRICS_INWARD = {k: v for k, v in METRICS_INWARD.items() if v['type'] == 'q_to_q_change'}


VALUE_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'value'}
AVERAGE_VALUE_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'average_value'}
RATIO_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'percentage'}
QUANTITY_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'quantity'}
MARKET_SHARE_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'market_share'}
Q_TO_Q_CHANGE_METRICS_DIRECT = {k: v for k, v in METRICS_DIRECT.items() if v['type'] == 'q_to_q_change'}




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


VALUE_METRICS_OPTIONS_DIRECT = create_dropdown_options(VALUE_METRICS_DIRECT)
AVERAGE_VALUE_METRICS_OPTIONS_DIRECT = create_dropdown_options(AVERAGE_VALUE_METRICS_DIRECT)
RATIO_METRICS_OPTIONS_DIRECT = create_dropdown_options(RATIO_METRICS_DIRECT)
QUANTITY_METRICS_OPTIONS_DIRECT = create_dropdown_options(QUANTITY_METRICS_DIRECT)
MARKET_SHARE_METRICS_OPTIONS_DIRECT = create_dropdown_options(MARKET_SHARE_METRICS_DIRECT)
Q_TO_Q_CHANGE_METRICS_OPTIONS_DIRECT = create_dropdown_options(Q_TO_Q_CHANGE_METRICS_DIRECT)


VALUE_METRICS_OPTIONS_INWARD = create_dropdown_options(VALUE_METRICS_INWARD)
AVERAGE_VALUE_METRICS_OPTIONS_INWARD = create_dropdown_options(AVERAGE_VALUE_METRICS_INWARD)
RATIO_METRICS_OPTIONS_INWARD = create_dropdown_options(RATIO_METRICS_INWARD)
QUANTITY_METRICS_OPTIONS_INWARD = create_dropdown_options(QUANTITY_METRICS_INWARD)
MARKET_SHARE_METRICS_OPTIONS_INWARD = create_dropdown_options(MARKET_SHARE_METRICS_INWARD)
Q_TO_Q_CHANGE_METRICS_OPTIONS_INWARD = create_dropdown_options(Q_TO_Q_CHANGE_METRICS_INWARD)







from typing import Iterable, List, Dict, Callable, Optional, Tuple, Any, Set, Union, Iterable
from constants.translations import translate

LINE_158 = {
    '1n': {'label': "ДМС"},
    '2n': {'label': "НС"},
    '3n': {'label': "ОСАГО"},
    '4n': {'label': "Зеленая карта"},
    '5n': {'label': "ОСГОПП"},
    '6n': {'label': "ОСАГО"},
    '7n': {'label': "Автокаско"},
    '8n': {'label': "Авиа, море, грузы"},
    '9n': {'label': "С/х с господдержкой"},
    '10n': {'label': "Имущество"},
    '11n': {'label': "ОСОПО"},
    '12n': {'label': "отв. застройщика"},
    '13n': {'label': "отв. тур"},
    '14n': {'label': "проч. отв."},
    '15n': {'label': "фин. и предпр. риски"},
    '16n': {'label': "взр"},
    '17n': {'label': "Непропорция"},
    '18n': {'label': "накопительное страхование жизни"},
    '19n': {'label': "инвестиционное страхование жизни"},
    '20n': {'label': "пенсионное страхование"},
    '21n': {'label': "прочее страхование жизни"}
}

# Example usage:
# This will create a list of dictionaries in the format:
# [
#     {'label': 'добровольное медицинское страхование', 'value': '1'},
#     {'label': 'страхование от несчастных случаев и болезней', 'value': '2'},
#     ...
# ]






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



INSURANCE_COLUMN_SWITCH = ['year_quarter', 'metric', 'insurer', 'linemain', 'year', 'quarter']
REINSURANCE_COLUMN_SWITCH = ['reinsurance_geography', 'reinsurance_type', 'reinsurance_form', 'year_quarter', 'metric', 'linemain', 'year', 'quarter', 'insurer']


CHART_TYPE_OPTIONS: List[str] = ['line', 'bar', 'area', 'scatter']
REINSURANCE_GRAPH_OPTIONS = ['reinsurance_line', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_form']
REINSURANCE_FORM_DROPDOWN_OPTIONS = ['fac_ob', 'facultative', 'ob_fac', 'obligatory']
REINSURANCE_TYPE_DROPDOWN_OPTIONS = ['non_proportional', 'proportional']
REINSURANCE_GEOGRAPHY_DROPDOWN_OPTIONS = ['within_russia', 'outside_russia']


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





LINEMAIN_COL = 'linemain'
INSURER_COL = 'insurer'
DATE_COLUMN: str = 'year_quarter'






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

    'new_contracts': {'label': 'New Contracts', 'type': 'quantity'},
    'new_sums': {'label': 'New Sums', 'type': 'value'},
    'average_new_sum_insured': {'label': 'Average New Sum Insured', 'type': 'average_value'},
    'average_new_premium': {'label': 'Average New Premium', 'type': 'average_value'},
    'claims_settled': {'label': 'Claims Settled', 'type': 'quantity'},
    'average_loss': {'label': 'Average Loss', 'type': 'average_value'},





    'net_premiums': {'label': 'Net Premiums', 'type': 'value'},
    'net_losses': {'label': 'Net Losses', 'type': 'value'},
    #'net_balance': {'label': 'Net Balance', 'type': 'value'},
    #'gross_result': {'label': 'Gross Result', 'type': 'value'},
    #'net_result': {'label': 'Net Result', 'type': 'value'},
    'sums_end': {'label': 'Sums End', 'type': 'value'},

    #ratio metrics
    #'gross_loss_ratio': {'label': 'Gross Loss Ratio', 'type': 'percentage'},
    'net_loss_ratio': {'label': 'Net Loss Ratio', 'type': 'percentage'},
    #'effect_on_loss_ratio': {'label': 'Effect on Loss Ratio', 'type': 'percentage'},
    'ceded_premiums_ratio': {'label': 'Ceded Premiums Ratio', 'type': 'percentage'},
    'ceded_losses_ratio': {'label': 'Ceded Losses Ratio', 'type': 'percentage'},
    #'ceded_ratio_diff': {'label': 'Ceded Ratio Diff', 'type': 'percentage'},
    'ceded_losses_to_ceded_premiums_ratio': {'label': 'Ceded Losses to Ceded Premiums Ratio', 'type': 'percentage'},

    #'inward_in_market_ceded_premiums': {'label': 'Inward in Market Ceded Premiums', 'type': 'percentage'},
    #'inward_in_market_ceded_losses': {'label': 'Inward in Market Ceded Losses', 'type': 'percentage'},

    'premiums_interm_total': {'label': 'premiums_interm_total', 'type': 'value'},
    'commissions_electronic': {'label': 'commissions_electronic', 'type': 'value'},

    'commissions_nonelec': {'label': 'commissions_nonelec', 'type': 'value'},
    'premiums_interm_electronic': {'label': 'premiums_interm_electronic', 'type': 'value'},

    'premiums_interm_nonelec': {'label': 'premiums_interm_nonelec', 'type': 'value'},
    'commissions_total': {'label': 'commissions_total', 'type': 'value'},

     #Average value metrics
    'average_sum_insured': {'label': 'Average  Sum Insured', 'type': 'average_value'},

    #Quantity metrics
    'contracts_end': {'label': 'Contracts End', 'type': 'quantity'},
    'claims_reported': {'label': 'Claims Reported', 'type': 'quantity'},

    # Market share metrics
    'direct_premiums_market_share': {'label': 'Direct Premiums Market Share', 'type': 'market_share'},
    'direct_losses_market_share': {'label': 'Direct Losses Market Share', 'type': 'market_share'},
    'inward_premiums_market_share': {'label': 'Inward Premiums Market Share', 'type': 'market_share'},
    'inward_losses_market_share': {'label': 'Inward Losses Market Share', 'type': 'market_share'},
    'ceded_premiums_market_share': {'label': 'Ceded Premiums Market Share', 'type': 'market_share'},
    'ceded_losses_market_share': {'label': 'Ceded Losses Market Share', 'type': 'market_share'},
    'total_premiums_market_share': {'label': 'Total Premiums Market Share', 'type': 'market_share'},
    'total_losses_market_share': {'label': 'Total Losses Market Share', 'type': 'market_share'},
    #'new_sums_market_share': {'label': 'New Sums Market Share', 'type': 'market_share'},
    #'sums_end_market_share': {'label': 'Sums End Market Share', 'type': 'market_share'},
    #'new_contracts_market_share': {'label': 'New Contracts Market Share', 'type': 'market_share'},
    #'contracts_end_market_share': {'label': 'Contracts End Market Share', 'type': 'market_share'},
    #'claims_reported_market_share': {'label': 'Claims Reported Market Share', 'type': 'market_share'},
    #'claims_settled_market_share': {'label': 'Claims Settled Market Share', 'type': 'market_share'},

    #q_to_q_change
    'direct_premiums_q_to_q_change': {'label': 'Direct Premiums Growth', 'type': 'q_to_q_change'},
    'direct_losses_q_to_q_change': {'label': 'Direct Losses Growth', 'type': 'q_to_q_change'},
    'inward_premiums_q_to_q_change': {'label': 'Inward Premiums Growth', 'type': 'q_to_q_change'},
    'inward_losses_q_to_q_change': {'label': 'Inward Losses Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_q_to_q_change': {'label': 'Ceded Premiums Growth', 'type': 'q_to_q_change'},
    'ceded_losses_q_to_q_change': {'label': 'Ceded Losses Growth', 'type': 'q_to_q_change'},
    'total_premiums_q_to_q_change': {'label': 'Total Premiums Growth', 'type': 'q_to_q_change'},
    'total_losses_q_to_q_change': {'label': 'Total Losses Growth', 'type': 'q_to_q_change'},

    #'net_premiums_q_to_q_change': {'label': 'Net Premiums Growth', 'type': 'q_to_q_change'},
    #'net_losses_q_to_q_change': {'label': 'Net Losses Growth', 'type': 'q_to_q_change'},
    #'net_balance_q_to_q_change': {'label': 'Net Balance Growth', 'type': 'q_to_q_change'},
    #'gross_result_q_to_q_change': {'label': 'Gross Result Growth', 'type': 'q_to_q_change'},
    #'net_result_q_to_q_change': {'label': 'Net Result Growth', 'type': 'q_to_q_change'},
    #'gross_loss_ratio_q_to_q_change': {'label': 'Gross Loss Ratio Growth', 'type': 'q_to_q_change'},
    'net_loss_ratio_q_to_q_change': {'label': 'Net Loss Ratio Growth', 'type': 'percentage'},
    #'effect_on_loss_ratio_q_to_q_change': {'label': 'Effect on Loss Ratio Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Premiums Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_losses_ratio_q_to_q_change': {'label': 'Ceded Losses Ratio Growth', 'type': 'q_to_q_change'},
    #'ceded_ratio_diff_q_to_q_change': {'label': 'Ceded Ratio Diff Growth', 'type': 'q_to_q_change'},
    'ceded_losses_to_ceded_premiums_ratio_q_to_q_change': {'label': 'Ceded Losses to Premiums Ratio Growth', 'type': 'q_to_q_change'},
    #'average_sum_insured_q_to_q_change': {'label': 'Average Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_new_sum_insured_q_to_q_change': {'label': 'Average New Sum Insured Growth', 'type': 'q_to_q_change'},
    'average_loss_q_to_q_change': {'label': 'Average Loss Growth', 'type': 'q_to_q_change'},
    'average_new_premium_q_to_q_change': {'label': 'Average Premium Growth', 'type': 'q_to_q_change'},
    #'new_sums_q_to_q_change': {'label': 'New Sums Growth', 'type': 'q_to_q_change'},
    #'sums_end_q_to_q_change': {'label': 'Sums End Growth', 'type': 'q_to_q_change'},
    #'new_contracts_q_to_q_change': {'label': 'New Contracts Growth', 'type': 'q_to_q_change'},
    #'contracts_end_q_to_q_change': {'label': 'Contracts End Growth', 'type': 'q_to_q_change'},
    #'claims_reported_q_to_q_change': {'label': 'Claims Reported Growth', 'type': 'q_to_q_change'},
    #'claims_settled_q_to_q_change': {'label': 'Claims Settled Growth', 'type': 'q_to_q_change'},
    'direct_premiums_market_share_q_to_q_change': {'label': 'Direct Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'direct_losses_market_share_q_to_q_change': {'label': 'Direct Losses Market Share Growth', 'type': 'q_to_q_change'},
    'inward_premiums_market_share_q_to_q_change': {'label': 'Inward Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'inward_losses_market_share_q_to_q_change': {'label': 'Inward Losses Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_market_share_q_to_q_change': {'label': 'Ceded Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'ceded_losses_market_share_q_to_q_change': {'label': 'Ceded Losses Market Share Growth', 'type': 'q_to_q_change'},
    'total_premiums_market_share_q_to_q_change': {'label': 'Total Premiums Market Share Growth', 'type': 'q_to_q_change'},
    'total_losses_market_share_q_to_q_change': {'label': 'Total Losses Market Share Growth', 'type': 'q_to_q_change'},
    #'new_sums_market_share_q_to_q_change': {'label': 'New Sums Market Share Growth', 'type': 'q_to_q_change'},
    #'sums_end_market_share_q_to_q_change': {'label': 'Sums End Market Share Growth', 'type': 'q_to_q_change'},
    #'new_contracts_market_share_q_to_q_change': {'label': 'New Contracts Market Share Growth', 'type': 'q_to_q_change'},
    #'contracts_end_market_share_q_to_q_change': {'label': 'Contracts End Market Share Growth', 'type': 'q_to_q_change'},
    #'claims_reported_market_share_q_to_q_change': {'label': 'Claims Reported Market Share Growth', 'type': 'q_to_q_change'},
    #'claims_settled_market_share_q_to_q_change': {'label': 'Claims Settled Market Share Growth', 'type': 'q_to_q_change'},

    #'inward_in_market_ceded_premiums_q_to_q_change': {'label': 'Inward in Market Ceded Premiums Growth', 'type': 'q_to_q_change'},
    #'inward_in_market_ceded_losses_q_to_q_change': {'label': 'Inward in Market Ceded Losses Growth', 'type': 'q_to_q_change'},
}


# Metrics
REINSURANCE_METRICS: Dict[str, Dict[str, str]] = {

    # Value metrics
    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},
    'inward_premiums': {'label': 'Inward Premiums', 'type': 'value'},
    'inward_losses': {'label': 'Inward Losses', 'type': 'value'},



    #q_to_q_change

    'inward_premiums_q_to_q_change': {'label': 'Inward Premiums Growth', 'type': 'q_to_q_change'},
    'inward_losses_q_to_q_change': {'label': 'Inward Losses Growth', 'type': 'q_to_q_change'},
    'ceded_premiums_q_to_q_change': {'label': 'Ceded Premiums Growth', 'type': 'q_to_q_change'},
    'ceded_losses_q_to_q_change': {'label': 'Ceded Losses Growth', 'type': 'q_to_q_change'},

    #'inward_in_market_ceded_premiums_q_to_q_change': {'label': 'Inward in Market Ceded Premiums Growth', 'type': 'q_to_q_change'},
    #'inward_in_market_ceded_losses_q_to_q_change': {'label': 'Inward in Market Ceded Losses Growth', 'type': 'q_to_q_change'},
}

VALUE_METRICS_REINSURANCE = {k: v for k, v in REINSURANCE_METRICS.items() if v['type'] == 'value'}
Q_TO_Q_CHANGE_METRICS_REINSURANCE = {k: v for k, v in REINSURANCE_METRICS.items() if v['type'] == 'q_to_q_change'}


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
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end', 'premiums_interm_total', 'commissions_electronic', 'commissions_nonelec', 'premiums_interm_electronic', 'premiums_interm_nonelec', 'commissions_total', 'net_balance', 'total_premiums', 'net_premiums', 'total_losses', 'net_losses', 'gross_result', 'net_result'
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
    'ceded_premiums_ratio': ['ceded_premiums', 'total_premiums'],
    'ceded_losses_ratio': ['ceded_losses', 'total_losses'],
    'ceded_losses_to_ceded_premiums_ratio': ['ceded_losses', 'ceded_premiums'],
    'gross_loss_ratio': ['direct_losses', 'inward_losses', 'direct_premiums', 'inward_premiums'],
    'net_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'effect_on_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'ceded_ratio_diff': ['ceded_losses', 'direct_losses', 'inward_losses', 'ceded_premiums', 'direct_premiums', 'inward_premiums', 'total_losses', 'total_premiums', 'ceded_losses_ratio', 'ceded_premiums_ratio']
}



base_metric_options: Set[str] = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end'
}

calculated_metrics_options: Set[str] = {
    'net_balance',
    'total_premiums',
    'net_premiums',
    'total_losses',
    'net_losses',
    'gross_result',
    'net_result'
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


base_metrics_list = [{'label': translate(metric), 'value': metric} for metric in base_metrics]


#CATEGORIES_TO_EXPAND_OPTIONS_FILTER = create_dropdown_options(CATEGORIES_TO_EXPAND_OPTIONS)

LINEMAIN_OPTIONS = create_dropdown_options(LINEMAIN_OPTIONS)
PREMIUM_LOSS_OPTIONS = create_dropdown_options(PREMIUM_LOSS_OPTIONS)
MARKET_METRIC_DROPDOWN_OPTIONS = create_dropdown_options(MARKET_METRIC_OPTIONS)
PERIOD_TYPES_OPTIONS = create_dropdown_options(PERIOD_TYPES)
PRIMARY_METRICS_OPTIONS = create_dropdown_options(PRIMARY_METRICS)
SECONDARY_METRICS_OPTIONS = create_dropdown_options(SECONDARY_METRICS)
METRICS_OPTIONS = create_dropdown_options(METRICS)
CALCULATED_RATIO_OPTIONS = create_dropdown_options(calculated_ratio_options)
REINSURANCE_METRIC_OPTIONS = create_dropdown_options(REINSURANCE_METRICS)

VALUE_METRICS_OPTIONS = create_dropdown_options(VALUE_METRICS)
AVERAGE_VALUE_METRICS_OPTIONS = create_dropdown_options(AVERAGE_VALUE_METRICS)
RATIO_METRICS_OPTIONS = create_dropdown_options(RATIO_METRICS)
QUANTITY_METRICS_OPTIONS = create_dropdown_options(QUANTITY_METRICS)
MARKET_SHARE_METRICS_OPTIONS = create_dropdown_options(MARKET_SHARE_METRICS)
Q_TO_Q_CHANGE_METRICS_OPTIONS = create_dropdown_options(Q_TO_Q_CHANGE_METRICS)
VALUE_METRICS_OPTIONS_REINSURANCE = create_dropdown_options(VALUE_METRICS_REINSURANCE)
Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE = create_dropdown_options(Q_TO_Q_CHANGE_METRICS_REINSURANCE)


ALL_METRICS_OPTIONS = (VALUE_METRICS_OPTIONS +
    AVERAGE_VALUE_METRICS_OPTIONS +
    RATIO_METRICS_OPTIONS +
    MARKET_SHARE_METRICS_OPTIONS +
    Q_TO_Q_CHANGE_METRICS_OPTIONS )

MAIN_METRICS_OPTIONS_TABLE = (VALUE_METRICS_OPTIONS + QUANTITY_METRICS_OPTIONS)
ADDITIONAL_METRICS_OPTIONS_TABLE = (AVERAGE_VALUE_METRICS_OPTIONS + RATIO_METRICS_OPTIONS)

LINE_158_OPTIONS = create_dropdown_options_non_translated(LINE_158)


ALL_METRICS_OPTIONS_Y = PRIMARY_METRICS_OPTIONS

ALL_METRICS_OPTIONS_Y2 = (SECONDARY_METRICS_OPTIONS + AVERAGE_VALUE_METRICS_OPTIONS)

'''(
    VALUE_METRICS_OPTIONS +
     +
    MARKET_SHARE_METRICS_OPTIONS +
     +
    AVERAGE_VALUE_METRICS_OPTIONS +
    Q_TO_Q_CHANGE_METRICS_OPTIONS +
     +
    SECONDARY_METRICS_OPTIONS
)'''







# translations.py

from typing import Iterable, List, Dict, Callable, Optional, Tuple, Any, Set, Union, Iterable
import json
import dash_bootstrap_components as dbc


# Translations dictionary
# Translations dictionary
TRANSLATIONS: Dict[str, str] = {

    # Dashboard
    "Insurance Data Dashboard": "Insturance dashboard",
    "Line": "Line",
    "Insurer": "Insurer",
    "Data Table": "Ranking",
    "Metrics Overview": "Metrics Overview",

    # General Filters
    "General Filters": "Общие фильтры",
    "Select Line Type:": "Включить вид страхования (жизнь/не-жизнь):",
    "Include Premiums/Losses:": "Включить данные по:",
    "Select Aggregation Type:": "Период анализа:",
    "Select Main Line(s):": "Вид(ы) страхования:",
    "Select Insurer:": "Страховщик:",
    "Select Primary Metrics:": "Показатель:",
    "Select Primary Chart Type:": "График:",
    "Select Secondary Chart Type:": "График:",
    "Select Secondary Metrics:": "Дополнительные показатели:",
    "Select Chart Type:": "Тип графика:",
    "Select Metric:": "Показатель:",

    # Chart Types
    "line": "Линейная",
    "bar": "Столбчатая",
    "area": "С областями",
    "scatter": "Точечная",
    "Line": "line",
    "Bar": "bar",
    "Area": "area",
    "Scatter": "scatter",

    # Period Types
    "same_q_last_year_ytd": "Нарастающим итогом с начала года (YTD)",
    "same_q_last_year": "Аналогичный квартал прошлого года",
    "same_q_last_year_mat": "Cкользящий годовой итог (Y-to-Y)",
    "previous_q_mat": "Скользящая годовая сумма (Q-to-Q)",
    "cumulative_sum": "Накопительный итог за все время",
    "previous_quarter": "Чистые квартальные данные",
    "same_q_last_year_ytd": "Нарастающим итогом с начала года (YTD)",
    "same_q_last_year": "Аналогичный квартал прошлого года",
    "same_q_last_year_mat": "Скользящая годовая сумм (Y-to-Y)",
    "previous_q_mat": "Скользящая годовая сумм (Q-to-Q)",
    "cumulative_sum": "Накопительный итог за все время",
    "previous_quarter": "Чистые квартальные данные",

    # Line Types
    "Direct": "Прямое",
    "Inward": "Входящее",
    "премии": "direct_premiums",
    "выплаты": "direct_losses",

    "входящее перестрахование премии": "inward_premiums",
    "входящее перестрахование выплаты": "inward_losses",
    "исходящее перестрахование премии": "ceded_premiums",
    "исходящее перестрахование выплаты": "ceded_losses",

    "direct_premiums": "премии",
    "direct_losses": "выплаты",
    "inward_premiums": "входящее перестрахование премии",
    "inward_losses": "входящее перестрахование выплаты",
    "ceded_premiums": "исходящее перестрахование премии",
    "ceded_losses": "исходящее перестрахование выплаты",
    "new_contracts": "новые договоры количество",
    "new_sums": "новые договоры суммы",
    "contracts_end": "действующие договоры количество",
    "sums_end": "действующие договоры суммы",
    "claims_reported": "заявленные случаи",
    "claims_settled": "урегулированные случаи",
    "premiums_interm_nonelec": "премии через посредников не электронно",
    "premiums_interm_electronic": "премии через посредников электронно",
    "premiums_interm_total": "премии через посредников всего",
    "commissions_nonelec": "комиссии посредникам не электронно",
    "commissions_electronic": "комиссии посредникам электронно",
    "commissions_total": "комиссии посредникам всего",
    "premiums_comm_interm": "премии и комиссии посредникам",
    # Market Metrics
    "Total Premiums": "Премии",
    "Total Losses": "Выплаты",
    "Ceded Premiums": "Премии по исходящему перестрахованию",
    "Ceded Losses": "Убытки по исходящему перестрахованию",
    "New Contracts": "Количество заключенных договоров страхования",
    "New Sums": "Страховые суммы по заключенным договорам страхования",
    "Claims Settled": "Количество урегулированных страховых случаев",
    "Average New Sum Insured": "Средняя страховая сумма по заключенным договорам",
    "Average New Premium": "Средняя премия по заключенным договорам",
    "average_loss": "Средний убыток",
    "Direct Premiums": "Премии по прямым договорам",
    "Direct Losses": "Убытки по прямым договорам",


    "direct_premiums": "Премии по прямым договорам",
    "direct_losses": "Убытки по прямым договорам",
    "ceded_premiums": "Премии по исходящему перестрахованию",
    "ceded_losses": "Убытки по исходящему перестрахованию",
    "new_contracts": "Количество заключенных договоров страхования",

    "new_sums": "Страховые суммы по заключенным договорам страхования",
    "contracts_end": "Количество действующих договоров",
    "sums_end": "Страховые суммы по действующим договорам",
    "claims_reported": "Количество заявленных страховых случаев",
    "claims_settled": "Количество урегулированных страховых случаев",
    "total_premiums": "Совокупный объем премий",
    "total_losses": "Совокупный объем выплат",
    "inward_premiums": "Премии по входящему перестрахованию",
    "inward_losses": "Убытки по договорам входящего перестрахования",
    "net_losses": "Убытки за вычетом перестрахования",
    "net_premiums": "Премии за вычетом исходящего перестрахования",
    "net_balance": "Доля пере в убытках за минусом премии в пере",

    # Metrics Labels
    "ceded_premiums_market_share": "Доля рынка по переданным премиям",
    "ceded_losses_market_share": "Доля рынка по переданным убыткам",
    "total_losses_market_share": "Доля рынка по убыткам",
    "total_premiums_market_share": "Доля рынка по премии",
    "ceded_premiums_ratio": "Премии в перестрахование / прямые премии",
    "ceded_losses_ratio": "Убытки в перестрахование / прямые убытки",
    "ceded_ratio_diff": "разница в коэффициентах премий и убытков",
    "ceded_losses_to_ceded_premiums_ratio": "Убытки / премии по исходящему перестрахованию",
    "gross_loss_ratio": "К/У до перестрахования",
    "net_loss_ratio": "К/У с учетом перестрахования",
    "effect_on_loss_ratio": "Влияние на коэффициент убыточности",
    "average_sum_insured": "Средняя страховая сумма по действующим договорам",
    "average_new_premium": "Средняя премия по заключенным договорам",
    "New Contracts": "Количество заключенных договоров страхования, тыс. ед.",
    "average_new_sum_insured": "Средняя страховая сумма по заключенным договорам",
    "average_loss": "Средний убыток",
    "inward_in_market_ceded_premiums": "Доля входящей премии от всех исходящих на рынке",
    "inward_in_market_ceded_losses": "Доля входящих убытков от всех исходящих на рынке",
    "gross_result": "gross_result",

    "net_result": "net_result",




    # Column Headers
    "N": "№",
    "insurer": "Страховщик",
    "q_to_q_change_premiums": "Прирост, %",
    "market_share_q_to_q_change": "Дельта, %",
    "q_to_q_change": "Прирост, %",
    "market_share": "Доля рынка, %",
    "market_share_change": "Дельта, %",
    "q_to_q_change_losses": "Прирост, %",
    "loss_ratio": "КУ, %",
    "q_to_q_change_loss_ratio": "Дельта, %",

    # Concentration
    "Top 5 Concentration": "Топ-5",
    "Top 10 Concentration": "Топ-10",
    "Top 20 Concentration": "Топ-20",
    "Top 50 Concentration": "Топ-50",
    "Top 100 Concentration": "Топ-100",
    "Total Market": "Весь рынок",

    # Quarters
    "Q1": "3M",
    "Q2": "1H",
    "Q3": "9M",
    "Q4": "FY",

    # Miscellaneous
    "Quarter": "Квартал",
    "Value": "Значение",
    "Percentage / Ratio": "Процент / Коэффициент",
    "Market Share by Line of Business": "Доля рынка по видам страхования",
    "Market Share": "Доля рынка",
    "Line of Business": "Вид страхования",

    # Debug Logs
    "Debug Logs": "Debug Logs",
    "Toggle Debug Logs": "Toggle Debug Logs",
    "Select Additional Metrics": "",
    "Number of Insurers": "",
    "Number of Periods": "",
    "Show Market Share Columns": "",
    "Show Q-to-Q Change Columns": "",

    "within_russia": "на территории Российской Федерации",
    "outside_russia": "из-за пределов территории Российской Федерации",
    "outside_russia": "за пределы территории Российской Федерации",
    "facultative": "факультативное",
    "obligatory": "облигаторное",
    "ob_fac": "облигаторно-факультативное",
    "fac_ob": "факультативно-облигаторное",
    "proportional": "пропорция",
    "non_proportional": "непропорция",
    "reinsurance_geography": "По географии перестрахования",
    "reinsurance_form": "По форме перестрахования",
    "reinsurance_type": "По виду перестрахования",
    "reinsurance_line": "-",

    "reinsurance_line": "Reinsurance Line",
    "reinsurance_geography": "Reinsurance Geography",
    "reinsurance_type": "Reinsurance Type",
    "reinsurance_form": "Reinsurance Form",
    "Select Graph Type": "",
    "Reinsurance Geography": "По географии перестрахования",
    "Reinsurance Type": "По виду перестрахования",
    "Reinsurance Form": "По форме перестрахования",
    "Select Form": "Select Form",
    "Select Type": "Select Type",
    "Select Geography": "Select Geography",
    "combined": "Insurer",
    "market": "Line",
    "Number of Periods": "N",

    "Hide": "Скрыть все категории",

    "net_premiums": "Премии-нетто",
    "net_losses": "Выплаты-нетто",
    "net_balance": "Результат страховых операций",


    "total_premiums": "Совокупные страховые премии",
    "total_losses": "Совокупные страховые выплаты",
    "ceded_premiums": "Премии, переданные в перестрахование",
    "ceded_losses": "Выплаты по договорам перестрахования",
    "new_contracts": "Количество новых договоров, шт.",
    "new_sums": "Страховые суммы по новым договорам",
    "average_new_sum_insured": "Средняя страховая сумма по новым договорам, млн руб.",
    "average_new_premium": "Средняя премия по новым договорам, тыс. руб.",
    "claims_settled": "Количество урегулированных страховых случаев, шт.",
    "average_loss": "Средняя сумма страховой выплаты, тыс. руб.",
    "direct_premiums": "Премии по прямому страхованию",
    "direct_losses": "Выплаты по прямому страхованию",
    "inward_premiums": "Премии по входящему перестрахованию",
    "inward_losses": "Выплаты по входящему перестрахованию",
    "net_premiums": "Премии-нетто",
    "net_losses": "Выплаты-нетто",
    "net_balance": "Результат страховых операций",
    "gross_result": "Валовой результат страховых операций",
    "net_result": "Финансовый результат страховых операций",
    "sums_end": "Страховые суммы на конец отчетного периода",
    "gross_loss_ratio": "Коэффициент убыточности (брутто), %",
    "net_loss_ratio": "Коэффициент убыточности (нетто), %",
    "effect_on_loss_ratio": "Влияние перестрахования на убыточность, п.п.",
    "ceded_premiums_ratio": "Доля премий, переданных в перестрахование, %",
    "ceded_losses_ratio": "Доля выплат, возмещенных по перестрахованию, %",
    "ceded_ratio_diff": "Разница между долями переданных премий и возмещенных выплат, п.п.",
    "ceded_losses_to_ceded_premiums_ratio": "Убыточность операций перестрахования, %",
    "premiums_interm_total": "Общая сумма премий, собранных через посредников",
    "commissions_electronic": "Комиссионные по электронным договорам",
    "commissions_nonelec": "Комиссионные по неэлектронным договорам",
    "premiums_interm_electronic": "Премии по электронным договорам через посредников",
    "premiums_interm_nonelec": "Премии по неэлектронным договорам через посредников",
    "commissions_total": "Общая сумма комиссионных вознаграждений",
    "average_sum_insured": "Средняя страховая сумма, млн руб.",
    "contracts_end": "Количество действующих договоров на конец периода, шт.",
    "claims_reported": "Количество заявленных страховых случаев, шт.",

    'Total Premiums': 'Совокупные страховые премии',
    'Total Losses': 'Совокупные страховые выплаты',
    'Ceded Premiums': 'Премии, переданные в перестрахование',
    'Ceded Losses': 'Выплаты, полученные от перестраховщиков',
    'New Contracts': 'Новые договоры, шт.',
    'New Sums': 'Страховые суммы по новым договорам',
    'Average New Sum Insured': 'Средняя страховая сумма по новым договорам, млн руб.',
    'Average New Premium': 'Средняя премия по новым договорам, тыс. руб.',
    'Claims Settled': 'Урегулированные страховые случаи, шт.',
    'Average Loss': 'Средняя сумма страховой выплаты, тыс. руб.',
    'Direct Premiums': 'Премии по прямому страхованию',
    'Direct Losses': 'Выплаты по прямому страхованию',
    'Inward Premiums': 'Премии по входящему перестрахованию',
    'Inward Losses': 'Выплаты по входящему перестрахованию',
    'Net Premiums': 'Чистые премии',
    'Net Losses': 'Чистые выплаты',
    'Net Balance': 'Чистый баланс',
    'Gross Result': 'Валовой результат',
    'Net Result': 'Чистый результат',
    'Sums End': 'Страховые суммы на конец периода',
    'Gross Loss Ratio': 'Коэффициент убыточности (брутто), %',
    'Net Loss Ratio': 'Коэффициент убыточности (нетто), %',
    'Effect on Loss Ratio': 'Влияние на коэффициент убыточности, п.п.',
    'Ceded Premiums Ratio': 'Доля премий, переданных в перестрахование, %',
    'Ceded Losses Ratio': 'Доля выплат, полученных от перестраховщиков, %',
    'Ceded Ratio Diff': 'Разница долей переданных премий и полученных выплат, п.п.',
    'Ceded Losses to Ceded Premiums Ratio': 'Убыточность операций перестрахования, %',
    'premiums_interm_total': 'Общая сумма премий через посредников',
    'commissions_electronic': 'Комиссии по электронным договорам',
    'commissions_nonelec': 'Комиссии по неэлектронным договорам',
    'premiums_interm_electronic': 'Премии по электронным договорам через посредников',
    'premiums_interm_nonelec': 'Премии по неэлектронным договорам через посредников',
    'commissions_total': 'Общая сумма комиссионных вознаграждений',
    'Average Sum Insured': 'Средняя страховая сумма, млн руб.',
    'Contracts End': 'Действующие договоры на конец периода, шт.',
    'Claims Reported': 'Заявленные страховые случаи, шт.'
    }





def translate(text: str) -> str:
    """
    Translate the given text using the TRANSLATIONS dictionary.

    Args:
        text (str): The text to translate.

    Returns:
        str: The translated text, or the original text if no translation is found.
    """
    return TRANSLATIONS.get(text, text)




















#'Прочее имущество юр. лиц'
# Default values





def translate_quarter_column(column_name: str, quarter: str) -> str:
    """
    Translate a quarter-specific column name.

    Args:
        column_name (str): The base column name to translate.
        quarter (str): The quarter identifier (e.g., "2023Q1").

    Returns:
        str: The translated column name with the quarter.
    """
    base_translation = translate(column_name.split('_')[0])
    return f"{base_translation} ({quarter})"



#@lru_cache(maxsize=1)
def cached_translate(text: str) -> str:
    """Cache translations to improve performance."""
    return translate(text)

def create_translated_dropdown_options(
    values: Iterable,
    translation_func: Callable = cached_translate
) -> List[Dict[str, str]]:
    """Create consistent dropdown options with translations."""
    return [{'label': translation_func(str(i)), 'value': str(i)} for i in list(values)]

def translate_quarter(quarter: str) -> str:
    """Translate quarter string to Russian format."""
    year, q = quarter.split('Q')
    months = {
        '1': '3 месяца',
        '2': '6 месяцев',
        '3': '9 месяцев',
        '4': '12 месяцев'
    }
    return f"{year} год, {months[q]}"

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

# Pre-create the options

