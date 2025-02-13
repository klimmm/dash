from typing import Any, cast, Dict, List, Optional, Set, TypedDict

import pandas as pd
from dash.dash_table.Format import Format, Scheme, Group  # type: ignore

from app.table.style import get_table_styles_config
from config.logging import get_logger, timer
from constants.translations import translate
from core.insurers.mapper import map_insurer
from core.lines.mapper import map_line
from core.metrics.definitions import METRICS, MetricTuple
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

logger = get_logger(__name__)


class UnitsConfig(TypedDict):
    value: str
    average_value: str
    quantity: str
    ratio: str
    default: str


class FormatsConfig(TypedDict):
    ytd: Dict[str, str]
    units: UnitsConfig
    percentage_indicators: Set[str]


FORMATS: FormatsConfig = {
    'ytd': {'1': '3М', '2': '6М', '3': '9М', '4': '12М'},
    'units': {
        'value': 'млрд. руб.',
        'average_value': 'тыс. руб.',
        'quantity': 'тыс. шт.',
        'ratio': '%',
        'default': 'млрд руб.'
    },
    'percentage_indicators': {'market_share', 'change', 'ratio', 'rate'}
}


def get_base_unit(metric: str) -> str:
    """Returns base unit for metric."""
    metric_info: Optional[MetricTuple] = METRICS.get(metric)
    if metric_info is None:
        return cast(str, FORMATS['units']['default'])

    metric_type: str = metric_info[2]
    units_dict = cast(UnitsConfig, FORMATS['units'])
    result = units_dict.get(metric_type, units_dict['default'])
    return cast(str, result)


def process_market_share(df: pd.DataFrame) -> pd.DataFrame:
    """Process market share columns."""
    for col in df.filter(like='market_share_change').columns:
        logger.debug(f"col {col}")
        df[col] = df[col].map(lambda v: '-' if v in (0, '-') else v * 100)
    return df


def format_period(qtr: str, ptype: str = '', comp: bool = False) -> str:
    """Format period string."""
    if not qtr or len(qtr) != 6:
        return qtr
    try:
        yr, q = qtr[2:4], qtr[5]
        if ptype == 'ytd':
            return yr if comp else f"{FORMATS['ytd'].get(q, q)} {yr}"
        return yr if comp and ptype in ['yoy_y', 'yoy_q'] else \
            f"{q}кв." if comp else f"{q} кв. {yr}"
    except Exception as e:
        logger.error(f"Period format error: {e}")
        return qtr


def get_comparison_quarter(curr_qtr: str, cols: List[str]) -> Optional[str]:
    """Get comparison quarter."""
    if not curr_qtr or len(curr_qtr) < 6:
        return None
    try:
        yr, q = curr_qtr[:4], curr_qtr[5]
        candidates = [
            f"{int(yr)-1}Q{q}",
            f"{yr}Q{str(int(q)-1)}" if q != '1' else f"{int(yr)-1}Q4"
        ]
        base_cols = [c for c in cols if '_change' not in c]
        return next((cand for cand in candidates
                    if any(cand in col for col in base_cols)), None)
    except Exception as e:
        logger.error(f"Comparison quarter error: {e}")
        return None


def get_column_format(col: str) -> Format:
    """Get column format configuration."""
    is_mkt_share = 'market_share_change' in col
    is_pct = any(ind in col for ind in FORMATS['percentage_indicators'])
    return Format(
        precision=2 if (is_pct or is_mkt_share) else 3,
        scheme=Scheme.fixed if (
            not is_pct or is_mkt_share) else Scheme.percentage,
        group=Group.yes,
        groups=3,
        group_delimiter=',',
        sign='+' if 'change' in col else ''
    )

from typing import Dict, Any

METRICS_UNITS = {
    'value': 'млрд. руб.',
    'average_value': 'тыс. руб.',
    'quantity': 'тыс. шт.',
    'ratio': '%',
    'default': 'млрд руб.'
}

def get_column_config(
    col: str,
    period_type: str,
    split_mode_value: str,
    pivot_column: str = 'metric_base',
    split_mode: str = 'line'
) -> Dict[str, Any]:
    """Generate column configuration with multi-level headers."""
    
    # Extract quarter from column name
    qtr = next((part for part in col.split('_') 
                if part.startswith('20') and 'Q' in part), '')
    
    # Initialize levels
    first_level = ""
    second_level = ""
    third_level = ""
    
    # Determine if we're dealing with special columns
    is_initial_cols = col in ['line', 'insurer', 'metric_base']
    
    # Handle list-type split_mode_value
    value = split_mode_value[0] if isinstance(split_mode_value, list) else split_mode_value
    
    # For special columns (metric_base, insurer, line)
    if is_initial_cols:
        # For the first two columns, always use the mapped split_mode_value
        if split_mode == 'line':
            first_level = map_line(value)
        elif split_mode == 'insurer':
            first_level = map_insurer(value)
        else:
            first_level = translate(value)
            
        # Set second and third levels for initial columns
        second_level = translate(col)
        third_level = translate(col)
    
    # For data columns
    else:
        # Extract base metric name (everything before _base, _rank, or _market)
        base_parts = []
        for part in col.split('_'):
            if part in ['base', 'rank', 'market_share', 'market']:
                break
            base_parts.append(part)
        base_metric = '_'.join(base_parts)
        
        # Determine column type flags
        is_change = 'change' in col
        is_mkt_share = 'market_share' in col
        is_rank = 'rank' in col
        is_default = 'base' in col
        is_metric = base_metric if base_metric else None

        # Set first level for data columns
        # If base_metric is a 4-digit code or special value (top-20, total), treat it as an insurer
        if base_metric.isdigit() and len(base_metric) == 4 or base_metric in ['top-20', 'total']:
            first_level = map_insurer(base_metric)
        else:
            first_level = translate(base_metric)

        # Set second level
        if is_change:
            second_level = 'Δ(п.п.)' if is_mkt_share else '%Δ'
        elif is_mkt_share:
            second_level = translate('market_share')
        elif is_rank:
            second_level = translate('rank')
        elif is_default and is_metric:
            # Default to 'default' unit if metric not found
            second_level = METRICS_UNITS['default']
            # Try to find metric in METRICS if it exists
            try:
                if isinstance(METRICS, dict) and is_metric in METRICS:
                    metric_type = METRICS[is_metric].get('value', 'default')
                    second_level = METRICS_UNITS.get(metric_type, METRICS_UNITS['default'])
            except (AttributeError, KeyError):
                pass
        else:
            second_level = format_period(qtr, period_type)

        # Set third level
        if is_change:
            third_level = (f"{format_period(qtr, period_type, True)} vs "
                         f"{format_period(qtr, period_type, True)}"
                         if qtr else '')
        elif is_rank:
            third_level = f"{format_period(qtr, period_type)}."

        else:
            third_level = format_period(qtr, period_type) if qtr else ''

    '''print(f"split_mode: {split_mode}")
    print(f"split_mode_value: {split_mode_value}")
    print(f"Column: {col}")
    print(f"First level: {first_level}")
    print(f"Second level: {second_level}")
    print(f"Third level: {third_level}")'''

    return {
        "id": col,
        "name": [
            first_level,
            second_level,
            third_level
        ],
        "type": "numeric" if '_20' in col else "text",
        "format": get_column_format(col)
    }

def create_datatable(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    period_type: str,
    show_market_share: Optional[List[str]] = None,
    show_change: Optional[List[str]] = None,
    show_rank: Optional[List[str]] = None,
    split_mode: Optional[str] = None,
    line: Optional[List[str]] = None,
    insurer: Optional[List[str]] = None,
    metric: Optional[List[str]] = None,
    pivot_column: str = 'metric_base'

) -> Dict[str, Any]:
    """Create complete datatable configuration."""
    try:
        logger.debug(f"df col {df.columns}")

        for col in df.columns:
            logger.debug(f"df col {col}")
        # Generate column configurations
        columns = [
            get_column_config(
                col=col,
                period_type=period_type,
                split_mode_value=line if split_mode == 'line' else insurer if split_mode == 'insurer' else metric,
                pivot_column=pivot_column,
                split_mode=split_mode
            )
            for col in df.columns
        ]
        
        # Handle hidden columns
        hidden_cols = [
            col for col in df.columns
            if (('market_share' in col and not show_market_share) or
                ('_change' in col and not show_change) or
                ('_rank' in col and not show_rank))
        ]
        
        # Generate table configuration
        base_config = get_table_styles_config(df)
        table_id = {
            'type': 'dynamic-table',
            'index': (
                f"{split_mode}-"
                f"{str(line).replace(' ', '')}-"
                f"{str(insurer).replace(' ', '')}"
            )
        }

        return {
            **base_config,
            'id': table_id,
            'columns': [{**col, 'hideable': False, 'selectable': False,
                        'deletable': False, 'renamable': False}
                       for col in columns],
            'hidden_columns': hidden_cols,
            'sort_action': 'none',
            'filter_action': 'none',
            'merge_duplicate_headers': True,
            'sort_as_null': ['', 'No answer', 'No Answer', 'N/A', 'NA'],
            'column_selectable': False,
            'row_selectable': False,
            'cell_selectable': True,
            'page_action': 'none',
            'editable': False,
            'style_data': {**base_config.get('style_data', {}),
                          'cursor': 'pointer'},
            'style_data_conditional': [
                *base_config.get('style_data_conditional', []),
                {'if': {'state': 'active'},
                 'backgroundColor': 'rgba(0, 116, 217, 0.1)'}
            ],
            'data': df.assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer)
                if 'insurer' in x.columns else '',
                line=lambda x: x['line'].fillna('').map(map_line)
                if 'line' in x.columns else '',
                metric_base=lambda x: x['metric_base'].fillna('').map(translate)
                if 'metric_base' in x.columns else ''

            ).to_dict('records')
        }
    except Exception as e:
        logger.error(f"Datatable creation error: {e}")
        raise 