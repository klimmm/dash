import pandas as pd
import numpy as np
from dash import dash_table
from dash.dash_table.Format import Format, Scheme, Group
from typing import Any, List, Tuple, Optional, Dict
from data_process.data_utils import map_line, map_insurer, save_df_to_csv
from constants.translations import translate
from config.logging_config import get_logger
from constants.filter_options import METRICS
from data_process.table_styles import generate_table_config

logger = get_logger(__name__)

# Core constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
SECTION_HEADER_COL = 'is_section_header'
METRIC_SUFFIXES = ['q_to_q_change', 'market_share', 'market_share_q_to_q_change']

def get_data_table(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    selected_linemains: List[str],
    period_type: str,
    number_of_insurers: int,
    toggle_selected_market_share: Optional[List[str]],
    toggle_selected_qtoq: Optional[List[str]],
    prev_ranks: Optional[Dict[str, int]] = None
) -> Tuple[dash_table.DataTable, str, str]:
    """
    Generate table configuration with styles and formatting.
    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    save_df_to_csv(df, "df_before_pivot.csv")
    table_data = table_data_pivot(df, table_selected_metric, prev_ranks)
    save_df_to_csv(table_data, "df_after_pivot.csv")

    table_config = generate_dash_table_config(
        df=table_data,
        table_selected_metric=table_selected_metric,
        period_type=period_type,
        toggle_selected_market_share=toggle_selected_market_share,
        toggle_selected_qtoq=toggle_selected_qtoq
    )

    mapped_lines = map_line(selected_linemains)
    lines_str = ', '.join(mapped_lines) if isinstance(mapped_lines, list) else mapped_lines

    return (
        dash_table.DataTable(**table_config),
        f"Топ-{number_of_insurers} страховщиков",
        f"{translate(table_selected_metric[0])}: {lines_str}"
    )

def format_rank_change(current_rank: int, previous_rank: Optional[int]) -> str:
    """Format rank with change indicator."""
    if previous_rank is None:
        return str(current_rank)

    rank_change = previous_rank - current_rank
    change_str = (
        f"+{rank_change}" if rank_change > 0 else
        f"{rank_change}" if rank_change < 0 else
        "-"
    )
    return f"{current_rank} ({change_str})"

def process_main_data(df: pd.DataFrame, prev_ranks: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    """Process main data rows with rankings."""
    if df.empty:
        return df

    sort_col = [col for col in df.columns if col != INSURER_COL][0]
    df = df.sort_values(by=sort_col, ascending=False)

    df.insert(0, PLACE_COL, range(1, len(df) + 1))
    if prev_ranks:
        df[PLACE_COL] = df.apply(
            lambda row: format_rank_change(int(row[PLACE_COL]), prev_ranks.get(row[INSURER_COL])),
            axis=1
        )
    else:
        df[PLACE_COL] = df[PLACE_COL].astype(str)

    df[SECTION_HEADER_COL] = False
    return df.replace(0, '-').fillna('-')

def process_summary_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process summary data rows."""
    if df.empty:
        return df

    df = df.sort_values(
        by=INSURER_COL,
        key=lambda x: pd.Series([
            (2 if ins.lower().startswith('total') else
             1 if ins.lower().startswith('top-') else 0,
             int(ins.split('-')[1]) if ins.lower().startswith('top-') else 0)
            for ins in x
        ])
    )

    df.insert(0, PLACE_COL, np.nan)
    df[SECTION_HEADER_COL] = False
    return df.replace(0, '-').fillna('-')

def table_data_pivot(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None
) -> pd.DataFrame:
    """Process and pivot table data with rankings and metrics."""
    try:
        metrics_to_keep = table_selected_metric + [
            f"{m}_{suffix}" for m in table_selected_metric 
            for suffix in METRIC_SUFFIXES
        ]

        df = df[df['metric'].isin(metrics_to_keep)].copy()
        unique_lines = sorted(df['linemain'].unique())
        multiple_lines = len(unique_lines) > 1

        dfs = []
        for line in unique_lines:
            if multiple_lines:
                dfs.extend([
                    pd.DataFrame([{PLACE_COL: '', INSURER_COL: '', SECTION_HEADER_COL: False}]),
                    pd.DataFrame([{PLACE_COL: '', INSURER_COL: map_line(line), SECTION_HEADER_COL: True}])
                ])

            line_df = df[df['linemain'] == line]
            pivot_df = create_pivot_table(line_df, table_selected_metric)
            summary_mask = pivot_df[INSURER_COL].str.lower().str.contains('^top|^total')
            main_data = process_main_data(
                pivot_df[~summary_mask], 
                prev_ranks.get(line) if prev_ranks else None
            )
            summary_data = process_summary_data(pivot_df[summary_mask])

            dfs.append(pd.concat([main_data, summary_data], ignore_index=True))

        return pd.concat(dfs, ignore_index=True)

    except Exception as e:
        logger.error(f"Error in table_data_pivot: {e}", exc_info=True)
        raise

def create_pivot_table(df: pd.DataFrame, selected_metrics: List[str]) -> pd.DataFrame:
    """Create pivot table from raw data."""
    df = df.copy()
    df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)

    # Get base metric from metric column
    def get_base_metric(x):
        for m in sorted(selected_metrics, key=len, reverse=True):
            if str(x).startswith(str(m)):
                return m
        return x

    df['base_metric'] = df['metric'].apply(get_base_metric)
    df['attribute'] = df.apply(
        lambda row: str(row['metric']).replace(str(row['base_metric']), '').lstrip('_'),
        axis=1
    )

    # Create column names in specific order
    time_periods = sorted(df['year_quarter'].unique(), reverse=True)
    attributes = ['', 'q_to_q_change', 'market_share', 'market_share_q_to_q_change']
    desired_columns = ['insurer'] + [
        f"{metric}_{year}{'_' + attr if attr else ''}"
        for metric in selected_metrics
        for attr in attributes
        for year in time_periods
    ]

    df['column_name'] = df.apply(
        lambda row: f"{row['base_metric']}_{row['year_quarter']}" + 
                   (f"_{row['attribute']}" if row['attribute'] else ''),
        axis=1
    )

    # Create pivot table
    pivot_df = df.pivot_table(
        index=INSURER_COL,
        columns='column_name',
        values='value',
        aggfunc='first'
    ).reset_index()

    # Add missing columns and remove empty ones
    for col in desired_columns:
        if col not in pivot_df.columns:
            pivot_df[col] = pd.NA

    value_cols = [col for col in desired_columns if col != INSURER_COL]
    mask = ~((pivot_df[value_cols] == 0) | pivot_df[value_cols].isna()).all()
    return pivot_df[[INSURER_COL] + [col for col, keep in zip(value_cols, mask) if keep]]

def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """Format quarter string into readable period format."""
    if not quarter_str or len(quarter_str) != 6:
        return quarter_str

    year_short = quarter_str[2:4]
    quarter = quarter_str[5]

    if period_type == 'ytd':
        if comparison:
            return year_short
        return {
            '1': f'3 мес. {year_short}',
            '2': f'1 пол. {year_short}',
            '3': f'9 мес. {year_short}',
            '4': f'12 мес. {year_short}'
        }[quarter]

    return (year_short if comparison and period_type in ['yoy_y', 'yoy_q'] 
            else f'{quarter}кв.' if comparison 
            else f'{quarter} кв. {year_short}')

def get_comparison_quarter(current_quarter: str, columns: List[str]) -> Optional[str]:
    """Get the comparison quarter for a given quarter."""
    if not current_quarter:
        return None

    year, q_num = current_quarter[:4], current_quarter[5]
    year_ago = f"{int(year)-1}Q{q_num}"
    prev_q = f"{year}Q{int(q_num)-1}" if q_num != '1' else f"{int(year)-1}Q4"

    base_columns = [c for c in columns if '_q_to_q_change' not in c]
    for candidate in [year_ago, prev_q]:
        if any(candidate in c for c in base_columns):
            return candidate
    return None

def get_column_format(col_name: str) -> Format:
    """Get format configuration for a column."""
    is_market_share_qtoq = 'market_share_q_to_q_change' in col_name
    is_percentage = any(x in col_name for x in ['market_share', 'q_to_q_change', 'ratio', 'rate'])

    return Format(
        precision=2 if is_percentage or is_market_share_qtoq else 3,
        scheme=Scheme.fixed if is_market_share_qtoq else 
               Scheme.percentage if is_percentage else Scheme.fixed,
        group=Group.yes,
        groups=3,
        group_delimiter=',',
        sign='+' if 'q_to_q_change' in col_name else ''
    )

def generate_dash_table_config(
    df: pd.DataFrame,
    table_selected_metric: List[str],
    period_type: str,
    toggle_selected_market_share: Optional[List[str]] = None,
    toggle_selected_qtoq: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate complete table configuration."""
    df_modified = df.copy()

    # Process market share changes
    market_share_cols = [c for c in df_modified.columns if 'market_share_q_to_q_change' in c]
    for col in market_share_cols:
        df_modified[col] = df_modified[col].apply(
            lambda x: '-' if x in (0, '-') else x * 100
        )

    # Generate column configurations
    columns = []
    for col in df.columns:
        if col == SECTION_HEADER_COL:
            continue

        if col in {PLACE_COL, INSURER_COL}:
            columns.append({
                "id": col,
                "name": [translate(col)] * 3
            })
            continue

        metric = next((m for m in sorted(METRICS, key=len, reverse=True) 
                      if col.startswith(m)), '')
        quarter = col[len(metric)+1:].split('_')[0] if metric else ''

        is_qtoq = 'q_to_q_change' in col
        is_market_share = 'market_share' in col

        if is_qtoq:
            comparison = get_comparison_quarter(quarter, df.columns)
            header = (f"{format_period(quarter, period_type, True)} vs "
                     f"{format_period(comparison, period_type, True)}"
                     if comparison else format_period(quarter, period_type))
            base = 'Δ(п.п.)' if is_market_share else '%Δ'
        else:
            header = format_period(quarter, period_type)
            base = translate('market_share') if is_market_share else 'млрд руб.'

        columns.append({
            "id": col,
            "name": [translate(metric), base, header],
            "type": "numeric",
            "format": get_column_format(col)
        })

    # Generate final config
    table_config = generate_table_config(
        df=df,
        columns=columns,
        show_market_share="show" in (toggle_selected_market_share or []),
        show_qtoq="show" in (toggle_selected_qtoq or [])
    )

    table_config['data'] = df_modified.assign(
        insurer=lambda x: x['insurer'].map(map_insurer)
    ).to_dict('records')

    return table_config