from typing import Dict, List, Set


METRICS_FOR_MARKET_SHARE = [
    'direct_premiums', 'direct_losses', 'inward_premiums', 'inward_losses',
    'ceded_premiums', 'ceded_losses', 'new_contracts', 'contracts_end',
    'premiums_interm', 'commissions_interm', 'new_sums',  'sums_end',
    'claims_reported', 'claims_settled', 'total_losses', 'total_premiums',
    'net_losses', 'net_premiums']

class Columns:
    INSURER = 'insurer'
    LINE = 'line'
    METRIC = 'metric'
    VALUE = 'value'
    VALUE_TYPE = 'value_type'
    YEAR_QUARTER = 'year_quarter'
    RANK = 'rank'
    RANK_CHANGE = 'rank_change'

    # Aliases dictionary for backward compatibility during migration
    DICT: Dict[str, str] = {
        'insurer': INSURER,
        'line': LINE,
        'metric': METRIC
    }

    # Collection of columns for operations
    ALL_EXCEPT_VALUE: List[str] = [LINE, INSURER, METRIC, YEAR_QUARTER, VALUE_TYPE]
    VALID_PIVOT: Set[str] = {LINE, INSURER, METRIC, YEAR_QUARTER, VALUE_TYPE}


class ValueTypes:
    BASE = 'base'
    BASE_CHANGE = 'base_change'
    MARKET_SHARE = 'market_share'
    MARKET_SHARE_CHANGE = 'market_share_change'
    RANK = 'rank'
    RANK_CHANGE = 'rank_change'

    # Suffixes for derived types
    CHANGE_SUFFIX = '_change'
    RANK_SUFFIX = '_rank'


class SpecialValues:
    INFINITY_SIGN = '∞'
    TOP_ROW_PREFIX = 'top-'
    ALL_LINES = 'все линии'
    TOTAL_LINES = 'lin_total'

    # Collections
    TOP_N_OPTIONS = [5, 10, 20]
    NON_INSURERS = {'top-5', 'top-10', 'top-20', 'total'}
    TOTAL_INSURER = 'total'
    ALL_INSURERS = 'all_insurers'
    # Thresholds
    BASE_INFINITY_THRESHOLD = 10
    MARKET_SHARE_INFINITY_THRESHOLD = 100
    MAX_REGULAR_CHANGE = 100.0  # 10000%
    MAX_MARKET_SHARE_CHANGE = 100.0  # 100 percentage points


class PeriodTypes:
    QOQ = 'qoq'
    YTD = 'ytd'
    YOYY = 'yoy-y'
    YOYQ = 'yoy-q'


class ViewModes:
    MARKET_SHARE = 'market-share'
    CHANGE = 'change'
    RANK = 'rank'


class FormatConfig:
    """Configuration for the LabelMapper class."""
    # Default translations
    TRANSLATIONS = {
        "0420162": "Отчетность по форме 0420162 Сведения о деятельности страховщика",
        "0420158": "Отчетность по форме 0420158 Отчет о структуре финансового результата по видам страхования",
        "metric": "Показатель",
        "rank": "Ранк",
        "year_quarter": "Период",
        "insurer": "Страховщик",
        "line": "Вид страхования"
    }

    # Value type displays using ValueTypes directly
    VALUE_TYPE_DISPLAYS = {
        ValueTypes.MARKET_SHARE_CHANGE: 'Δ(п.п.)',
        ValueTypes.BASE_CHANGE: '%Δ',
        ValueTypes.MARKET_SHARE: 'Доля рынка, %',
        ValueTypes.RANK: 'Ранк'
    }
