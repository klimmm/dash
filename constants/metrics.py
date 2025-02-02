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