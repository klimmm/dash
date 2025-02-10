from typing import Any, Callable, Dict, List, Set, Tuple, TypeVar

MetricTuple = Tuple[
    List[str],
    Callable[[Dict[str, Any]], float],      # Second element: lambda function
    str,                                    # Third element: metric type string
    Set[str],                               # Fourth element: set of form codes
    str                                     # Fifth element: description
]

K = TypeVar('K')  # For dictionary key type
N = TypeVar('N', int, float)  # For numeric types


def calc_ratio(num: K, den: K, d: Dict[K, N], default: N = 1) -> float:
    """Calculate ratio with default value handling

    Args:
        num: Key to look up numerator value in dictionary
        den: Key to look up denominator value in dictionary 
        d: Dictionary containing values for calculation
        default: Default value if denominator key not found, defaults to 1

    Returns:
        float: Ratio of num/den values from dictionary
    """
    return d.get(num, 0) / d.get(den, default)


# Define METRICS type
METRICS: Dict[str, MetricTuple] = {
    # Basic metrics
    'direct_premiums': (
        [], lambda d: d.get('direct_premiums', 0),
        'value', {'0420162'}, 'Премии по прямому страхованию'),

    'direct_losses': (
        [], lambda d: d.get('direct_losses', 0),
        'value', {'0420162'}, 'Выплаты по прямому страхованию'),

    'inward_premiums': (
        [], lambda d: d.get('inward_premiums', 0),
        'value', {'0420162'}, 'Премии по входящему перестрахованию'),

    'inward_losses': (
        [], lambda d: d.get('inward_losses', 0),
        'value', {'0420162'}, 'Выплаты по входящему перестрахованию'),

    'ceded_premiums': (
        [], lambda d: d.get('ceded_premiums', 0),
        'value', {'0420158', '0420162'}, 'Исходящее перестрахование - Премии'),

    'ceded_losses': (
        [], lambda d: d.get('ceded_losses', 0),
        'value', {'0420158', '0420162'}, 'Исходящее перестрахование - Убытки'),

    'new_contracts': (
        [], lambda d: d.get('new_contracts', 0),
        'quantity', {'0420162'}, 'Кол-во заключенных договоров'),

    'contracts_end': (
        [], lambda d: d.get('contracts_end', 0),
        'quantity', {'0420162'}, 'Кол-во действующих договоров'),

    'premiums_interm': (
        [], lambda d: d.get('premiums_interm', 0),
        'value', {'0420162'}, 'Премии через посредников'),

    'commissions_interm': (
        [], lambda d: d.get('commissions_interm', 0),
        'value', {'0420162'}, 'Вознаграждение посредникам'),

    'new_sums': (
        [], lambda d: d.get('new_sums', 0),
        'value', {'0420162'}, 'Страховая сумма по новым договорам'),

    'sums_end': (
        [], lambda d: d.get('sums_end', 0),
        'value', {'0420162'}, 'Страховая сумма по действующим договорам'),

    'claims_reported': (
        [], lambda d: d.get('claims_reported', 0),
        'quantity', {'0420162'}, 'Заявленные убытки'),

    'claims_settled': (
        [], lambda d: d.get('claims_settled', 0),
        'quantity', {'0420162'}, 'Урегулированные убытки'),

    # Calculated metrics
    'total_premiums': (
        ['direct_premiums', 'inward_premiums'], lambda d:
        sum(d.get(x, 0) for x in ['direct_premiums', 'inward_premiums']),
        'value', {'0420158', '0420162'}, 'Премии'),

    'total_losses': (
        ['direct_losses', 'inward_losses'], lambda d:
        sum(d.get(x, 0) for x in ['direct_losses', 'inward_losses']),
        'value', {'0420158', '0420162'}, 'Выплаты'),

    'net_premiums': (
        ['total_premiums', 'ceded_premiums'], lambda d:
        d.get('total_premiums', 0) - d.get('ceded_premiums', 0),
        'value', {'0420158', '0420162'}, 'Премии-нетто перестрахование'),

    'net_losses': (
        ['total_losses', 'ceded_losses'], lambda d:
        d.get('total_losses', 0) - d.get('ceded_losses', 0),
        'value', {'0420158', '0420162'}, 'Выплаты нетто-перестрахование'),

    'net_result': (
        ['net_premiums', 'net_losses'], lambda d:
        d.get('net_premiums', 0) - d.get('net_losses', 0),
        'value', {'0420158', '0420162'}, 'Результат нетто'),

    'gross_result': (
        ['total_premiums', 'total_losses'], lambda d:
        d.get('total_premiums', 0) - d.get('total_losses', 0),
        'value', {'0420158', '0420162'}, 'Результат брутто'),

    # Ratios and averages
    'average_new_premium': (
        ['direct_premiums', 'new_contracts'], lambda d: 
        d.get('direct_premiums', 0) / (d.get('new_contracts', 1) * 1000),
        'average_value', {'0420162'}, 'Средняя премия по новым договорам'),

    'average_loss': (
        ['direct_losses', 'claims_settled'], lambda 
        d: d.get('direct_losses', 0) / (d.get('claims_settled', 1) * 1000),
        'average_value', {'0420162'}, 'Средняя сумма выплаты'),

    'average_rate': (
        ['new_sums', 'direct_premiums'], lambda d: 
        d.get('direct_premiums', 0) / (d.get('new_sums', 1) * 1000),
        'ratio', {'0420162'}, 'Средняя ставка'),

    'average_sum_insured': (
        ['sums_end', 'contracts_end'], lambda d: 
        d.get('sums_end', 0) / (d.get('contracts_end', 1) * 1000),
        'average_value', {'0420162'}, 'Средняя страховая сумма'),

    'average_new_sum_insured': (
        ['new_sums', 'new_contracts'], lambda d:
        d.get('new_sums', 0) / (d.get('new_contracts', 1) * 1000),
        'average_value',
        {'0420162'}, 'Средняя страховая сумма по новым договорам'),

    'ceded_premiums_ratio': (
        ['ceded_premiums', 'total_premiums'], lambda d:
        calc_ratio('ceded_premiums', 'total_premiums', d),
        'ratio',
        {'0420158', '0420162'}, 'Доля премий, переданных в перестрахование'),

    'ceded_losses_ratio': (
        ['ceded_losses', 'total_losses'], lambda d:
        calc_ratio('ceded_losses', 'total_losses', d),
        'ratio',
        {'0420158', '0420162'}, 'Доля выплат, переданных в перестрахование'),

    'premiums_interm_ratio': (
        ['direct_premiums', 'premiums_interm'], lambda d:
        calc_ratio('premiums_interm', 'direct_premiums', d),
        'ratio', {'0420162'}, 'Доля премий от посредников'),

    'commissions_rate': (
        ['premiums_interm', 'commissions_interm'], lambda d:
        calc_ratio('commissions_interm', 'premiums_interm', d),
        'ratio', {'0420162'}, 'Вознаграждение к премии'),

    'net_loss_ratio': (
        ['net_losses', 'net_premiums'], lambda d:
        calc_ratio('net_losses', 'net_premiums', d),
        'ratio', {'0420158', '0420162'}, 'Убыточность нетто'),

    'gross_loss_ratio': (
        ['total_losses', 'total_premiums'], lambda d:
        calc_ratio('total_losses', 'total_premiums', d),
        'ratio', {'0420158', '0420162'}, 'Убыточность брутто'),

    'direct_loss_ratio': (
        ['direct_losses', 'direct_premiums'], lambda d:
        calc_ratio('direct_losses', 'direct_premiums', d),
        'ratio', {'0420162'}, 'Убыточность прямого страхования'),

    'inward_loss_ratio': (
        ['inward_losses', 'inward_premiums'], lambda d:
        calc_ratio('inward_losses', 'inward_premiums', d),
        'ratio', {'0420162'}, 'Убыточность входящего перестрахования'),

    'ceded_losses_to_ceded_premiums_ratio': (
        ['ceded_losses', 'ceded_premiums'], lambda d:
        calc_ratio('ceded_losses', 'ceded_premiums', d), 
        'ratio',
        {'0420158', '0420162'}, 'Убыточность исходящего перестрахования'),

    'ceded_ratio_diff': (
        ['ceded_losses_ratio', 'ceded_premiums_ratio'], lambda d:
        d.get('ceded_losses_ratio', 0) - d.get('ceded_premiums_ratio', 0),
        'ratio', {'0420158', '0420162'}, 'Разница долей перестрахования'),

    'effect_on_loss_ratio': (
        ['gross_loss_ratio', 'net_loss_ratio'], lambda d:
        d.get('gross_loss_ratio', 0) - d.get('net_loss_ratio', 0),
        'ratio', {'0420158', '0420162'}, 'Влияние на убыточность')
}

VALID_METRICS = [
    'direct_premiums',
    'direct_losses',
    'inward_premiums',
    'inward_losses',
    'ceded_premiums',
    'ceded_losses',
    # 'new_sums',
    # 'sums_end',
    'new_contracts',
    'contracts_end',
    'premiums_interm',
    'commissions_interm',
    # 'claims_settled',
    # 'claims_reported',
    'total_premiums',
    'total_losses',
    # 'net_balance',
    'net_premiums',
    'net_losses',
    # 'gross_result',
    # 'net_result',
    # 'average_sum_insured',
    # 'average_new_sum_insured',
    'average_new_premium',
    'average_loss',
    'average_rate',
    'ceded_premiums_ratio',
    'ceded_losses_ratio',
    'ceded_losses_to_ceded_premiums_ratio',
    # 'direct_loss_ratio',
    # 'inward_loss_ratio',
    # 'gross_loss_ratio',
    # 'net_loss_ratio',
    # 'effect_on_loss_ratio',
    # 'ceded_ratio_diff',
    'premiums_interm_ratio',
    'commissions_rate'
]