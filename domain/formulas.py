from typing import List, Dict, Callable, Tuple

# Type definitions
MetricName = str
MetricComputation = Callable[[Dict[str, float]], float]
MetricDependencies = List[str]
MetricFormula = Tuple[MetricDependencies, MetricComputation]


class MetricsFormulas:
    """Domain knowledge about insurance metric relationships."""

    @staticmethod
    def raw(base_metric: MetricName, multiplier: float = 1) -> MetricFormula:
        """Create a formula that directly uses a base metric with optional multiplier."""
        return ([], lambda d: d.get(base_metric, 0) * multiplier)

    @staticmethod
    def add(addends: MetricDependencies) -> MetricFormula:
        """Create a formula that adds multiple metrics."""
        return (addends, lambda d: sum(d.get(x, 0) for x in addends))

    @staticmethod
    def subtract(minuend: str, subtrahend: str) -> MetricFormula:
        """Create a formula that subtracts one metric from another."""
        return ([minuend, subtrahend],
                lambda d: d.get(minuend, 0) - d.get(subtrahend, 0))

    @staticmethod
    def divide(numerator: str, denominator: str,
               multiplier: float = 1) -> MetricFormula:
        """Create a formula that divides one metric by another with optional multiplier."""
        return ([numerator, denominator],
                lambda d: d.get(numerator, 0) / d.get(denominator, 1) * multiplier)

    @classmethod
    def get_default_formulas(cls) -> Dict[str, MetricFormula]:
        """Define standard insurance metric formulas."""
        return {
            # Base metrics
            'direct_premiums': cls.raw('direct_premiums'),
            'direct_losses': cls.raw('direct_losses'),
            'inward_premiums': cls.raw('inward_premiums'),
            'inward_losses': cls.raw('inward_losses'),
            'ceded_premiums': cls.raw('ceded_premiums'),
            'ceded_losses': cls.raw('ceded_losses'),
            'new_contracts': cls.raw('new_contracts'),
            'contracts_end': cls.raw('contracts_end'),
            'premiums_interm': cls.raw('premiums_interm'),
            'commissions_interm': cls.raw('commissions_interm'),
            'new_sums': cls.raw('new_sums'),
            'sums_end': cls.raw('sums_end'),
            'claims_reported': cls.raw('claims_reported'),
            'claims_settled': cls.raw('claims_settled'),

            # Derived metrics
            'total_premiums': cls.add(['direct_premiums', 'inward_premiums']),
            'total_losses': cls.add(['direct_losses', 'inward_losses']),
            'net_premiums': cls.subtract('total_premiums', 'ceded_premiums'),
            'net_losses': cls.subtract('total_losses', 'ceded_losses'),
            'net_result': cls.subtract('net_premiums', 'net_losses'),
            'gross_result': cls.subtract('total_premiums', 'total_losses'),
            'average_premium': cls.divide('direct_premiums', 'new_contracts', 1),
            'average_claim': cls.divide('direct_losses', 'claims_settled', 1),
            'premium_rate': cls.divide('direct_premiums', 'new_sums', 100),
            'average_sum_insured': cls.divide('sums_end', 'contracts_end', 1),
            'average_new_sum_insured': cls.divide('new_sums', 'new_contracts', 1),
            'ceded_premiums_ratio': cls.divide('ceded_premiums', 'total_premiums'),
            'ceded_losses_ratio': cls.divide('ceded_losses', 'total_losses'),
            'premiums_interm_ratio': cls.divide('premiums_interm', 'direct_premiums'),
            'commission_rate': cls.divide('commissions_interm', 'premiums_interm'),
            'net_loss_ratio': cls.divide('net_losses', 'net_premiums'),
            'gross_loss_ratio': cls.divide('total_losses', 'total_premiums'),
            'direct_loss_ratio': cls.divide('direct_losses', 'direct_premiums'),
            'inward_loss_ratio': cls.divide('inward_losses', 'inward_premiums'),
            'ceded_loss_ratio': cls.divide('ceded_losses', 'ceded_premiums'),
            'reinsurance_impact': cls.subtract('ceded_losses_ratio', 'ceded_premiums_ratio'),
            'reinsurance_effect': cls.subtract('gross_loss_ratio', 'net_loss_ratio')
        }