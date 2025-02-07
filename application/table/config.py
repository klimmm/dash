from typing import Optional, Dict, Any, List

import pandas as pd
from dash.dash_table.Format import Format, Scheme, Group

from config.logging_config import get_logger, timer
from constants.translations import translate
from application.table.style import get_table_styles_config
from domain.insurers.mapper import map_insurer
from domain.lines.mapper import map_line
from domain.metrics.definitions import METRICS


logger = get_logger(__name__)

FORMATS = {
    'ytd': {'1': '3 мес.', '2': '1 пол.', '3': '9 мес.', '4': '12 мес.'},
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
    return FORMATS['units'].get(
        METRICS.get(metric, [None, None, None])[2],
        FORMATS['units']['default']
    )


def process_market_share(df: pd.DataFrame) -> pd.DataFrame:
    """Process market share columns."""
    for col in df.filter(like='market_share_change').columns:
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


def get_column_config(col: str, split_mode: str,
                      metric: str, qtr: str,
                      period_type: str, all_cols: List[str],
                      line: Optional[str] = None,
                      insurer: Optional[str] = None) -> Dict[str, Any]:
    """Generate column configuration."""
    # Handle identifier columns
    if col in ['N', 'insurer', 'linemain']:
        name = ([map_line(line[0]), translate(col), translate(col)]
                if col in ['N', 'insurer'] and split_mode == 'line' and line
                else [map_insurer(insurer[0]), translate(col), translate(col)]
                if col in ['N', 'linemain'] and split_mode == 'insurer' and insurer
                else [translate(col)] * 3)
        return {"id": col, "name": name}

    # Handle metric columns
    is_change = 'change' in col
    is_mkt_share = 'market_share' in col

    if is_change:
        comp = get_comparison_quarter(qtr, all_cols)
        header = (f"{format_period(qtr, period_type, True)} vs "
                  f"{format_period(comp, period_type, True)}"
                  if comp else format_period(qtr, period_type))
        base = 'Δ(п.п.)' if is_mkt_share else '%Δ'
    else:
        header = format_period(qtr, period_type)
        base = translate(
            'market_share') if is_mkt_share else get_base_unit(metric)

    return {
        "id": col,
        "name": [translate(metric), base, header],
        "type": "numeric",
        "format": get_column_format(col)
    }


@timer
def create_datatable(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    period_type: str,
    toggle_show_market_share: Optional[List[str]] = None,
    toggle_show_change: Optional[List[str]] = None,
    split_mode: str = None,
    line: str = None,
    insurer: str = None
) -> Dict[str, Any]:
    """Create complete datatable configuration."""
    try:
        # Process data and generate configs
        df_mod = process_market_share(df)
        sorted_metrics = sorted(METRICS, key=len, reverse=True)
        curr_metric = next((m for m in sorted_metrics
                           if any(col.startswith(m) for col in df.columns)), '')

        # Generate column configurations
        columns = []
        id_cols = ['N', 'insurer', 'linemain']
        col_order = (['N', 'insurer', 'linemain'] if split_mode == 'line'
                     else ['linemain', 'N', 'insurer'])

        # Add identifier columns
        for col in [c for c in col_order if c in df.columns]:
            columns.append(get_column_config(
                col, split_mode, curr_metric, '',
                period_type, list(df.columns), line, insurer
            ))

        # Add metric columns
        for col in df.columns:
            if col not in id_cols:
                metric = next((m for m in sorted_metrics
                              if col.startswith(m)), '')
                qtr = (col[len(metric)+1:].split('_')[-1]
                       if metric else '')
                columns.append(get_column_config(
                    col, split_mode, metric, qtr,
                    period_type, list(df.columns), line, insurer
                ))

        # Handle hidden columns
        hidden_cols = [
            col for col in df.columns
            if (col not in set(id_cols) and
                (('market_share' in col and not toggle_show_market_share) or
                ('_change' in col and not toggle_show_change)))
        ]

        # Generate table configuration
        base_config = get_table_styles_config(df)
        table_id = {
            'type': 'dynamic-table',
            'index': f"{split_mode}-{str(line).replace(' ', '')}-{str(insurer).replace(' ', '')}"
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
            'data': df_mod.assign(
                insurer=lambda x: x['insurer'].fillna('').map(map_insurer)
                if 'insurer' in x.columns else '',
                linemain=lambda x: x['linemain'].fillna('').map(map_line)
                if 'linemain' in x.columns else ''
            ).to_dict('records')
        }
    except Exception as e:
        logger.error(f"Datatable creation error: {e}")
        raise


__all__ = ['create_datatable']