BUSINESS_TYPE_OPTIONS = [
    {'label': 'Прям.', 'value': 'direct'},
    {'label': 'Входящ.', 'value': 'inward'}
]

METRICS = {
    'direct_premiums': (
        [],  # No dependencies
        lambda d: d.get('direct_premiums', 0),
        'value',
        {'0420162'},
        'Премии по прямому страхованию',
    ),
    'direct_losses': (
        [],
        lambda d: d.get('direct_losses', 0),
        'value',
        {'0420162'},
        'Выплаты по прямому страхованию'
    ),
    'inward_premiums': (
        [],
        lambda d: d.get('inward_premiums', 0),
        'value',
        {'0420162'},
        'Премии по входящему перестрахованию'
    ),
    'inward_losses': (
        [],
        lambda d: d.get('inward_losses', 0),
        'value',
        {'0420162'},
        'Выплаты по входящему перестрахованию'
    ),
    'ceded_premiums': (
        [],
        lambda d: d.get('ceded_premiums', 0),
        'value',
        {'0420158', '0420162'},
        'Исходящее перестрахование - Премии'
    ),
    'ceded_losses': (
        [],
        lambda d: d.get('ceded_losses', 0),
        'value',
        {'0420158', '0420162'},
        'Исходящее перестрахование - Убытки'
    ),
    'new_sums': (
        [],
        lambda d: d.get('new_sums', 0),
        'value',
        {'0420162'},
        'Страховые суммы по заключенным договорам'
    ),
    'sums_end': (
        [],
        lambda d: d.get('sums_end', 0),
        'value',
        {'0420162'},
        'Страховые суммы по действующим договорам'
    ),
    'new_contracts': (
        [],
        lambda d: d.get('new_contracts', 0),
        'quantity',
        {'0420162'},
        'Кол-во заключенных договоров'
    ),
    'contracts_end': (
        [],
        lambda d: d.get('contracts_end', 0),
        'quantity',
        {'0420162'},
        'Кол-во действующих договоров'
    ),
    'premiums_interm': (
        [],
        lambda d: d.get('premiums_interm', 0),
        'value',
        {'0420162'},
        'Премии через посредников'
    ),
    'commissions_interm': (
        [],
        lambda d: d.get('commissions_interm', 0),
        'value',
        {'0420162'},
        'Вознаграждение посредникам'
    ),
    'claims_settled': (
        [],
        lambda d: d.get('claims_settled', 0),
        'quantity',
        {'0420162'},
        'Кол-во урегулированных случаев'
    ),
    'claims_reported': (
        [],
        lambda d: d.get('claims_reported', 0),
        'quantity', 
        {'0420162'},
        'Количество заявленных страховых случаев'
    ),
    'total_premiums': (
        ['direct_premiums', 'inward_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0),
        'value',
        {'0420158'},
        'Премии'
    ),
    'total_losses': (
        ['direct_losses', 'inward_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0),
        'value',
        {'0420158'},
        'Выплаты'
    ),
    # Basic metrics (calculated first)
    'net_balance': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0),
        'value',
        set(),
        'Результат-нетто' 
    ),

    'net_premiums': (
        ['total_premiums', 'ceded_premiums'],
        lambda d: d.get('total_premiums', 0) - d.get('ceded_premiums', 0),
        'value',
        set(),
        'Премии-нетто перестрахования'
    ),

    'net_losses': (
        ['total_losses', 'ceded_losses'],
        lambda d: d.get('total_losses', 0) - d.get('ceded_losses', 0),
        'value',
        set(),
        'Выплаты нетто-перестрахование'
    ),
    'gross_result': (
        ['total_premiums', 'total_losses'],
        lambda d: (d.get('total_premiums', 0)) - 
                 (d.get('total_losses', 0)),
        'value',
        set(),
        'Результат-брутто'
    ),
    'net_result': (
        ['total_premiums', 'total_losses', 
         'ceded_premiums', 'ceded_losses'],
        lambda d: (d.get('total_premiums', 0) - d.get('ceded_premiums', 0)) -
                  (d.get('total_losses', 0) - d.get('ceded_losses', 0)),
        'value',
        set(),
        'Результат-нетто'
    ),
    'average_sum_insured': (
        ['sums_end', 'contracts_end'],
        lambda d: (d.get('sums_end', 0) / 10) / (d.get('contracts_end', 1) * 1000) / 1000,
        'average_value',
        set(),
        'Средняя страховая сумма'
    ),
    'average_new_sum_insured': (
        ['new_sums', 'new_contracts'],
        lambda d: d.get('new_sums', 0) / d.get('new_contracts', 1),
        'average_value',
        set(),
        'Средняя страховая сумма по новым договорам'
    ),
    'average_new_premium': (
        ['direct_premiums', 'new_contracts'],
        lambda d: d.get('direct_premiums', 0) / (d.get('new_contracts', 1) * 1000),
        'average_value',
        set(),
        'Средняя премия по новым договорам'
    ),
    'average_loss': (
        ['direct_losses', 'claims_settled'],
        lambda d: d.get('direct_losses', 0) / (d.get('claims_settled', 1) * 1000),
        'average_value',
        set(),
        'Средняя сумма выплаты'
    ),
    'average_rate': (
        ['new_sums', 'direct_premiums'],
        lambda d: d.get('direct_premiums', 0) / (d.get('new_sums', 1) * 1000),
        'ratio',
        set(),
        'Средняя ставка'
    ),
    'ceded_premiums_ratio': (
        ['ceded_premiums', 'total_premiums'],
        lambda d: d.get('ceded_premiums', 0) / d.get('total_premiums', 1),
        'ratio',
        set(),
        'Доля премий, переданных в перестрахование'
    ),
    'ceded_losses_ratio': (
        ['ceded_losses', 'total_losses'],
        lambda d: d.get('ceded_losses', 0) / d.get('total_losses', 1),
        'ratio',
        set(),
        'Доля выплат, переданных в перестрахование'
    ),
    'ceded_losses_to_ceded_premiums_ratio': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) / d.get('ceded_premiums', 1),
        'ratio',
        set(),
        'Коэффициент выплат по исходящему перестрахованию'
    ),
    'direct_loss_ratio': (
        ['direct_losses', 'direct_premiums'],
        lambda d: d.get('direct_losses', 0) / d.get('direct_premiums', 1),
        'ratio',
        set(),
        'Убыточность по прямым договорам'
    ),
    'inward_loss_ratio': (
        ['inward_losses', 'inward_premiums'],
        lambda d: d.get('inward_losses', 0) / d.get('inward_premiums', 1),
        'ratio',
        set(),
        'Входящее перестрахование - убыточность'
    ),
    'gross_loss_ratio': (
        ['total_losses', 'total_premiums'],
        lambda d: d.get('total_losses', 0) / d.get('total_premiums', 1),
        'ratio',
        set(),
        'Коэффициент убыточности (брутто)'
    ),
    'net_loss_ratio': (
        ['net_losses', 'net_premiums'],
        lambda d: d.get('net_losses', 0) / d.get('net_premiums', 1),
        'ratio',
        set(),
        'Коэффициент убыточности (нетто)'
    ),
    'effect_on_loss_ratio': (
        ['total_losses', 'net_losses', 'total_premiums', 'net_premiums'],
        lambda d: (d.get('total_losses', 0) / d.get('total_premiums', 1)) -
                  (d.get('net_losses', 0) / d.get('net_premiums', 1)),
        'ratio',
        set(),
        'Влияние перестрахования на коэффициент убыточности'
    ),
    'ceded_ratio_diff': (
        ['ceded_losses', 'total_losses', 'ceded_premiums', 'total_premiums'],
        lambda d: (d.get('ceded_losses', 0) / d.get('total_losses', 1)) -
                  (d.get('ceded_premiums', 0) / d.get('total_premiums', 1)),
        'ratio',
        set(),
        'Разница между долями премий и выплат в перестраховании'
    ),
    'premiums_interm_ratio': (
        ['direct_premiums', 'premiums_interm'],
        lambda d: d.get('premiums_interm', 0) / d.get('direct_premiums', 1),
        'ratio',
        set(),
        'Доля премий от посредников'
    ),
    'commissions_rate': (
        ['premiums_interm', 'commissions_interm'],
        lambda d: d.get('commissions_interm', 0) / d.get('premiums_interm', 1),
        'ratio',
        set(),
        'Вознаграждение к премии'
    )
}

def get_metrics_options(form_ids=None, metric_types=None, valid_metrics=None, metrics_dict=METRICS):
    """
    Generate dropdown options from METRIC_CALCULATIONS with optional filtering by forms, types and metric names
    Args:
        form_ids (list, optional): List of form IDs to filter by (e.g., ['0420162', '0420158'])
        metric_types (list, optional): List of metric types to filter by (e.g., ['value', 'ratio'])
        valid_metrics (list, optional): List of specific metric names in desired order
        metrics_dict (dict): Dictionary with metrics definitions
    Returns:
        list: List of dictionaries with 'label' and 'value' pairs
    """
    if valid_metrics is None:
        return [
            {'label': metric_info[4], 'value': metric_name}
            for metric_name, metric_info in metrics_dict.items()
            if (form_ids is None or any(form_id in metric_info[3] for form_id in form_ids))
            and (metric_types is None or metric_info[2] in metric_types)
        ]
    
    return [
        {'label': metrics_dict[metric][4], 'value': metric}
        for metric in valid_metrics
        if metric in metrics_dict
        and (form_ids is None or any(form_id in metrics_dict[metric][3] for form_id in form_ids))
        and (metric_types is None or metrics_dict[metric][2] in metric_types)
    ]

# Example usage:
valid_metrics = [
    'direct_premiums',
    'direct_losses',
    'inward_premiums',
    'inward_losses',
    'ceded_premiums',
    'ceded_losses',
    #'new_sums',
    #'sums_end',
    'new_contracts',
    'contracts_end',
    'premiums_interm',
    'commissions_interm',
    #'claims_settled',
    #'claims_reported',
    'total_premiums',
    'total_losses',
    #'net_balance',
    'net_premiums',
    'net_losses',
    #'gross_result',
    #'net_result',
    #'average_sum_insured',
    #'average_new_sum_insured',
    'average_new_premium',
    'average_loss',
    'average_rate',
    'ceded_premiums_ratio',
    'ceded_losses_ratio',
    #'ceded_losses_to_ceded_premiums_ratio',
    #'direct_loss_ratio',
    #'inward_loss_ratio',
    #'gross_loss_ratio',
    #'net_loss_ratio',
    #'effect_on_loss_ratio',
    #'ceded_ratio_diff',
    'premiums_interm_ratio',
    'commissions_rate'
]

METRICS_OPTIONS = get_metrics_options(valid_metrics=valid_metrics)
VALUE_METRICS_OPTIONS = get_metrics_options(metric_types=['value'], valid_metrics=valid_metrics)