# constants/filter_options.py

from typing import Dict, Any, Union, Callable, List
from constants.translations import translate

BASE_OPTIONS = {
    'REPORTING_FORM': {
        '0420162': {'label': '0420162', 'type': 'value'}, # 0420162 «Сведения о деятельности страховщика»
        '0420158': {'label': '0420158', 'type': 'value'} # 0420158 «Отчет о структуре финансового результата по учетным группам»'
    },
    'PREMIUM_LOSS': {
        'direct': {'label': 'Direct', 'type': 'value'},
        'inward': {'label': 'Inward', 'type': 'value'}
    }
}


# Metrics Configuration
BASE_METRICS = {
    'ceded_losses', 'ceded_premiums', 'claims_reported', 'claims_settled',
    'contracts_end', 'direct_losses', 'direct_premiums', 'inward_losses',
    'inward_premiums', 'new_contracts', 'new_sums', 'sums_end',
    'premiums_interm', 'commissions_interm',
    'net_balance', 'total_premiums', 'net_premiums', 'total_losses',
    'net_losses', 'gross_result', 'net_result'
}

# Keeping original CALCULATED_METRICS and CALCULATED_RATIOS for backwards compatibility
CALCULATED_METRICS = {
    'net_balance': ['ceded_losses', 'ceded_premiums'],
    'total_premiums': ['direct_premiums', 'inward_premiums'],
    'net_premiums': ['direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'total_losses': ['direct_losses', 'inward_losses'],
    'net_losses': ['direct_losses', 'inward_losses', 'ceded_losses'],
    'gross_result': ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses'],
    'net_result': ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses', 'ceded_premiums', 'ceded_losses']
}

CALCULATED_RATIOS = {
    'average_sum_insured': ['sums_end', 'contracts_end'],
    'average_new_sum_insured': ['new_sums', 'new_contracts'],
    'average_new_premium': ['direct_premiums', 'new_contracts'],
    'average_loss': ['direct_losses', 'claims_settled'],
    'average_rate': ['new_sums', 'direct_premiums'],
    'commissions_rate': ['premiums_interm', 'commissions_interm'],
    'ceded_premiums_ratio': ['ceded_premiums', 'total_premiums'],
    'ceded_losses_ratio': ['ceded_losses', 'total_losses'],
    'ceded_losses_to_ceded_premiums_ratio': ['ceded_losses', 'ceded_premiums'],
    'direct_loss_ratio': ['direct_losses', 'direct_premiums'],
    'inward_loss_ratio': ['inward_losses', 'inward_premiums'],
    'gross_loss_ratio': ['direct_losses', 'inward_losses', 'direct_premiums', 'inward_premiums'],
    'net_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'effect_on_loss_ratio': ['direct_losses', 'inward_losses', 'ceded_losses', 'direct_premiums', 'inward_premiums', 'ceded_premiums'],
    'ceded_ratio_diff': ['ceded_losses', 'direct_losses', 'inward_losses', 'ceded_premiums', 'direct_premiums', 'inward_premiums', 'total_losses', 'total_premiums', 'ceded_losses_ratio', 'ceded_premiums_ratio'],
    'premiums_interm_ratio': ['direct_premiums', 'premiums_interm']
}

def create_metric_definition(label: str, metric_type: str) -> Dict[str, str]:
    """Create a standardized metric definition dictionary."""
    return {'label': label, 'type': metric_type}

# Define base metrics with their types
METRICS = {
    # Value metrics
    **{metric: create_metric_definition(f"{metric.replace('_', ' ').title()}", 'value')
       for metric in ['direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses',
                     'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
                     'net_premiums', 'net_losses', 'premiums_interm',
                     'commissions_interm', 'new_sums', 'sums_end']},

    # Quantity metrics
    **{metric: create_metric_definition(f"{metric.replace('_', ' ').title()}", 'quantity')
       for metric in ['new_contracts', 'contracts_end', 'claims_reported', 'claims_settled']},

    # Average metrics
    **{metric: create_metric_definition(f"{metric.replace('_', ' ').title()}", 'average_value')
       for metric in ['average_sum_insured', 'average_new_sum_insured', 'average_new_premium', 
                     'average_loss', 'average_rate']},

    # Percentage metrics
    **{metric: create_metric_definition(f"{metric.replace('_', ' ').title()}", 'percentage')
       for metric in ['net_loss_ratio', 'ceded_premiums_ratio', 'ceded_losses_ratio',
                     'ceded_losses_to_ceded_premiums_ratio', 'direct_loss_ratio',
                     'inward_loss_ratio', 'gross_loss_ratio', 'premiums_interm_ratio',
                     'commissions_rate']},  # Added the missing ratio metrics

    # Market share metrics
    **{f"{base}_market_share": create_metric_definition(f"{base.replace('_', ' ').title()} Market Share", 'market_share')
       for base in ['direct_premiums', 'direct_losses', 'inward_premiums',
                   'inward_losses', 'ceded_premiums', 'ceded_losses']},

    # Quarter-to-quarter change metrics
    **{f"{base}_q_to_q_change": create_metric_definition(f"{base.replace('_', ' ').title()} Growth", 'q_to_q_change')
       for base in ['direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses',
                   'ceded_premiums', 'ceded_losses', 'total_premiums', 'total_losses',
                   'net_loss_ratio', 'ceded_premiums_ratio', 'ceded_losses_to_ceded_premiums_ratio',
                   'average_new_sum_insured', 'average_loss', 'average_new_premium',
                   'direct_premiums_market_share', 'direct_losses_market_share',
                   'ceded_premiums_market_share', 'ceded_losses_market_share']}
}

# Specific metrics for form 158
METRICS_158 = {k: v for k, v in METRICS.items() if k in {
    'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
    'net_premiums', 'net_losses', 'ceded_premiums_ratio',
    'ceded_losses_to_ceded_premiums_ratio'
}}

def create_dropdown_options(
    items: Union[Dict[str, Dict[str, str]], List[str]],
    translation_func: Callable = translate
) -> List[Dict[str, Any]]:
    """Create dropdown options with optional translation."""
    if isinstance(items, dict):
        return [{'label': translation_func(info['label']), 'value': key} 
                for key, info in items.items()]
    return [{'label': translation_func(item), 'value': item} for item in items]

# Generate dropdown options
LINEMAIN_OPTIONS = create_dropdown_options({})  # Empty dict as per original
REPORTING_FORM_OPTIONS = create_dropdown_options(BASE_OPTIONS['REPORTING_FORM'])
PREMIUM_LOSS_OPTIONS = create_dropdown_options(BASE_OPTIONS['PREMIUM_LOSS'])

# Filtered metric options
VALUE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'value'}
AVERAGE_VALUE_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'average_value'}
RATIO_METRICS = {k: v for k, v in METRICS.items() if v['type'] == 'percentage'}

# Generate metric dropdown options
VALUE_METRICS_OPTIONS = create_dropdown_options(VALUE_METRICS)
AVERAGE_VALUE_METRICS_OPTIONS = create_dropdown_options(AVERAGE_VALUE_METRICS)
RATIO_METRICS_OPTIONS = create_dropdown_options(RATIO_METRICS)
VALUE_METRICS_OPTIONS_158 = create_dropdown_options(METRICS_158)
METRICS_OPTIONS = create_dropdown_options(METRICS)