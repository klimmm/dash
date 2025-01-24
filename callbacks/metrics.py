FORM_METRICS = {
    '0420158': {'total_premiums', 'total_losses', 'ceded_premiums', 'ceded_losses',
                'net_premiums', 'net_losses'
               },
    '0420162': {'direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses', 
                'ceded_premiums', 'ceded_losses',
                'new_sums', 'sums_end',
                'new_contracts', 'contracts_end',
                'premiums_interm', 'commissions_interm', 
                'claims_settled', 'claims_reported'
               }
}

METRIC_CALCULATIONS = {
    # Basic metrics (calculated first)
    'net_balance': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) - d.get('ceded_premiums', 0)
    ),
    'total_premiums': (
        ['direct_premiums', 'inward_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0)
    ),
    'net_premiums': (
        ['direct_premiums', 'inward_premiums', 'ceded_premiums'],
        lambda d: d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)
    ),
    'total_losses': (
        ['direct_losses', 'inward_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0)
    ),
    'net_losses': (
        ['direct_losses', 'inward_losses', 'ceded_losses'],
        lambda d: d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0)
    ),
    'gross_result': (
        ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses'],
        lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0)) - 
                 (d.get('direct_losses', 0) + d.get('inward_losses', 0))
    ),
    'net_result': (
        ['direct_premiums', 'inward_premiums', 'direct_losses', 'inward_losses', 
         'ceded_premiums', 'ceded_losses'],
        lambda d: (d.get('direct_premiums', 0) + d.get('inward_premiums', 0) - d.get('ceded_premiums', 0)) - 
                 (d.get('direct_losses', 0) + d.get('inward_losses', 0) - d.get('ceded_losses', 0))
    ),
    # Ratio metrics (calculated after basic metrics)
    'average_sum_insured': (
        ['sums_end', 'contracts_end'],
        lambda d: (d.get('sums_end', 0) / 10) / (d.get('contracts_end', 1) * 1000) / 1000
    ),
    'average_new_sum_insured': (
        ['new_sums', 'new_contracts'],
        lambda d: (d.get('new_sums', 0) / 10) / (d.get('new_contracts', 1) * 1000) / 1000
    ),
    'average_new_premium': (
        ['direct_premiums', 'new_contracts'],
        lambda d: d.get('direct_premiums', 0) / (d.get('new_contracts', 1) * 1000)
    ),
    'average_loss': (
        ['direct_losses', 'claims_settled'],
        lambda d: d.get('direct_losses', 0) / (d.get('claims_settled', 1) * 1000)
    ),
    'average_rate': (
        ['new_sums', 'direct_premiums'],
        lambda d: d.get('direct_premiums', 0) / d.get('new_sums', 1)
    ),
    'ceded_premiums_ratio': (
        ['ceded_premiums', 'total_premiums'],
        lambda d: d.get('ceded_premiums', 0) / d.get('total_premiums', 1)
    ),
    'ceded_losses_ratio': (
        ['ceded_losses', 'total_losses'],
        lambda d: d.get('ceded_losses', 0) / d.get('total_losses', 1)
    ),
    'ceded_losses_to_ceded_premiums_ratio': (
        ['ceded_losses', 'ceded_premiums'],
        lambda d: d.get('ceded_losses', 0) / d.get('ceded_premiums', 1)
    ),
    'direct_loss_ratio': (
        ['direct_losses', 'direct_premiums'],
        lambda d: d.get('direct_losses', 0) / d.get('direct_premiums', 1)
    ),
    'inward_loss_ratio': (
        ['inward_losses', 'inward_premiums'],
        lambda d: d.get('inward_losses', 0) / d.get('inward_premiums', 1)
    ),
    'gross_loss_ratio': (
        ['total_losses', 'total_premiums'],
        lambda d: d.get('total_losses', 0) / d.get('total_premiums', 1)
    ),
    'net_loss_ratio': (
        ['net_losses', 'net_premiums'],
        lambda d: d.get('net_losses', 0) / d.get('net_premiums', 1)
    ),
    'effect_on_loss_ratio': (
        ['total_losses', 'net_losses', 'total_premiums', 'net_premiums'],
        lambda d: (d.get('total_losses', 0) / d.get('total_premiums', 1)) -
                 (d.get('net_losses', 0) / d.get('net_premiums', 1))
    ),
    'ceded_ratio_diff': (
        ['ceded_losses', 'total_losses', 'ceded_premiums', 'total_premiums'],
        lambda d: (d.get('ceded_losses', 0) / d.get('total_losses', 1)) -
                 (d.get('ceded_premiums', 0) / d.get('total_premiums', 1))
    ),
    'premiums_interm_ratio': (
        ['direct_premiums', 'premiums_interm'],
        lambda d: d.get('premiums_interm', 0) / d.get('direct_premiums', 1)
    ),
    'commissions_rate': (
        ['premiums_interm', 'commissions_interm'],
        lambda d: d.get('commissions_interm', 0) / d.get('premiums_interm', 1)
    )
}
