import pandas as pd
import numpy as np
from dash import dash_table
from dash.dash_table.Format import Format, Scheme, Group
from typing import Any, List, Tuple, Optional, Dict, OrderedDict
from data_process.data_utils import map_line, map_insurer, save_df_to_csv
from constants.translations import translate
from config.logging_config import get_logger
from constants.filter_options import METRICS
from data_process.table_styles import generate_table_config
logger = get_logger(__name__)

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
IDENTIFIER_COLS = {PLACE_COL, INSURER_COL}

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
    """Generate a formatted data table with rankings and metrics."""
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

    logger.debug(f"prev_ranks {prev_ranks}")
    data_table = dash_table.DataTable(**table_config)
    
    mapped_lines = map_line(selected_linemains)
    lines_str = ', '.join(mapped_lines) if isinstance(mapped_lines, list) else mapped_lines
    
    return (
        data_table,
        f"Топ-{number_of_insurers} страховщиков",
        f"{translate(table_selected_metric[0])}: {lines_str}"
    )

def table_data_pivot(
    df: pd.DataFrame,
    table_selected_metric: List[str], 
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None  # Changed type hint
) -> pd.DataFrame:
    """Process and pivot table data with rankings and metrics."""
    logger.debug("Starting table data pivot")
    
    try:
        unique_lines = df['linemain'].unique()
        multiple_lines = len(unique_lines) > 1
    
        # Generate metrics to keep
        metric_suffixes = ['q_to_q_change', 'market_share', 'market_share_q_to_q_change']
        metrics_to_keep = (
            table_selected_metric +
            [f"{m}_{suffix}" for m in table_selected_metric for suffix in metric_suffixes]
        )
        
        # Initial data processing
        processed_df = df[df['metric'].isin(metrics_to_keep)].copy()
        processed_df['year_quarter'] = pd.to_datetime(processed_df['year_quarter']).dt.to_period('Q').astype(str)
        
        final_dfs = []
        
        for line in sorted(unique_lines):
            # Add section header row for the line
            if multiple_lines:
                separator_row = pd.DataFrame([{
                    'N': '',
                    'insurer': '',
                    'is_section_header': False
                }])
                final_dfs.append(separator_row)
                
                header_row = pd.DataFrame([{
                    'N': '',
                    'insurer': map_line(line),  # Using map_line to translate the line name
                    'is_section_header': True  # Adding a marker for styling
                }])
                final_dfs.append(header_row)
            
            line_df = processed_df[processed_df['linemain'] == line].copy()
            
            # Extract metric components
            def split_metric(metric: str) -> Tuple[str, str]:
                base = next((m for m in sorted(table_selected_metric, key=len, reverse=True) 
                            if metric.startswith(m)), metric)
                return base, metric[len(base):].lstrip('_') if metric.startswith(base) else ''
            
            line_df[['base_metric', 'attribute']] = pd.DataFrame(
                line_df['metric'].apply(split_metric).tolist(),
                index=line_df.index
            )
            
            # Create unified column names and pivot
            line_df['column_name'] = (
                line_df['base_metric'] + '_' + 
                line_df['year_quarter'] + 
                line_df['attribute'].apply(lambda x: f'_{x}' if x else '')
            )
            
            pivot_df = line_df.pivot_table(
                index='insurer',
                columns='column_name',
                values='value',
                aggfunc='first'
            ).reset_index()
            
            # Organize columns
            time_periods = sorted(line_df['year_quarter'].unique(), reverse=True)
            attributes = ['', 'q_to_q_change', 'market_share', 'market_share_q_to_q_change']
            desired_columns = ['insurer'] + [
                f"{metric}_{year}{'_' + attr if attr else ''}"
                for metric in table_selected_metric
                for attr in attributes
                for year in time_periods
            ]
            desired_columns = list(OrderedDict.fromkeys(desired_columns))
            
            # Add missing columns
            for col in desired_columns:
                if col not in pivot_df.columns:
                    pivot_df[col] = pd.NA
            
            pivot_df = pivot_df[desired_columns]
            
            # Clean and sort the line data
            value_cols = [col for col in pivot_df.columns if col != 'insurer']
            mask = ~((pivot_df[value_cols] == 0) | pivot_df[value_cols].isna()).all()
            final_cols = ['insurer'] + [col for col, keep in zip(value_cols, mask) if keep]
            
            line_df = pivot_df[final_cols].copy()
            
            # Split and process regular and summary rows
            summary_mask = line_df['insurer'].str.lower().str.startswith(('top', 'total'))
            main_df = line_df[~summary_mask].copy()
            summary_df = line_df[summary_mask].copy()
            
            # Sort main data
            sort_col = value_cols[0]
            main_df[sort_col] = pd.to_numeric(main_df[sort_col], errors='coerce')
            main_df = main_df.sort_values(by=sort_col, ascending=False)
            
            # Add rankings with change indicators
            main_df.insert(0, 'N', range(1, len(main_df) + 1))
            if prev_ranks and line in prev_ranks:  # Check if we have ranks for this line
                main_df['N'] = main_df.apply(
                    lambda row: format_rank_change(
                        current_rank=int(row['N']),
                        previous_rank=prev_ranks[line].get(row['insurer'])  # Get rank for specific line
                    ),
                    axis=1
                )
            else:
                main_df['N'] = main_df['N'].astype(str)
            
            # Process summary rows
            summary_df = sort_summary_rows(summary_df)
            summary_df.insert(0, 'N', np.nan)
            
            # Add is_section_header column
            main_df['is_section_header'] = False
            summary_df['is_section_header'] = False
            summary_df = summary_df.replace(0, '-').fillna('-')
            main_df = main_df.replace(0, '-').fillna('-')
            
            # Combine main and summary for this line
            line_final_df = pd.concat([main_df, summary_df], ignore_index=True)

            final_dfs.append(line_final_df)
        
        # Combine all lines
        final_df = pd.concat(final_dfs, ignore_index=True)
        
        return final_df
        
    except Exception as e:
        logger.error(f"Error in table_data_pivot: {e}", exc_info=True)
        raise
        
def format_rank_change(current_rank: int, previous_rank: Optional[int]) -> str:
    """Format rank with change indicator."""
    if previous_rank is None:
        return str(current_rank)
        
    rank_change = previous_rank - current_rank
    change_str = (
        f"+{rank_change}" if rank_change > 0 else
        f"-{abs(rank_change)}" if rank_change < 0 else
        "-"
    )
    return f"{current_rank} ({change_str})"

def sort_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Sort summary rows based on their prefix and number."""
    def get_sort_key(insurer: str) -> Tuple[int, int]:
        insurer = insurer.lower()
        if insurer.startswith('total'):
            return (2, 0)
        if insurer.startswith('top-'):
            try:
                return (1, int(insurer.split('-')[1]))
            except (IndexError, ValueError):
                return (1, float('inf'))
        return (0, 0)
    
    return df.sort_values(
        by='insurer',
        key=lambda x: pd.Series([get_sort_key(ins) for ins in x]),
        ascending=True
    )

def get_column_format(col_name: str) -> Format:
    """Get format configuration for a column."""
    is_market_share_qtoq = 'market_share_q_to_q_change' in col_name
    is_percentage = any(x in col_name for x in ['market_share', 'q_to_q_change', 'ratio', 'rate'])
    
    return Format(
        precision=2 if is_percentage or is_market_share_qtoq else 3,
        scheme=Scheme.fixed if is_market_share_qtoq else (
            Scheme.percentage if is_percentage else Scheme.fixed
        ),
        group=Group.yes,
        groups=3,
        group_delimiter=',',
        sign='+' if 'q_to_q_change' in col_name else ''
    )

def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """Format quarter string into readable period format."""
    if not quarter_str or len(quarter_str) != 6:
        raise ValueError("Quarter string must be in format 'YYYYQ1', e.g. '2024Q1'")
    
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
    
    if comparison:
        return year_short if period_type in ['yoy_y', 'yoy_q'] else f'{quarter}кв.'
    return f'{quarter} кв. {year_short}'

def get_comparison_quarters(columns: List[str]) -> Dict[str, str]:
    """Get mapping of quarters to their comparison quarters."""
    quarter_pairs = {}
    for col in columns:
        if 'q_to_q_change' not in col:
            continue
            
        current_quarter = next((part for part in col.split('_') 
                              if 'Q' in part and len(part) >= 5), None)
        if not current_quarter:
            continue
            
        year, q_num = current_quarter[:4], current_quarter[5]
        year_ago = f"{int(year)-1}Q{q_num}"
        prev_q = f"{year}Q{int(q_num)-1}" if q_num != '1' else f"{int(year)-1}Q4"
        
        comparison = (
            year_ago if any(year_ago in c for c in columns if '_q_to_q_change' not in c) else
            prev_q if any(prev_q in c for c in columns if '_q_to_q_change' not in c) else
            None
        )
        
        if comparison:
            quarter_pairs[current_quarter] = comparison
            
    return quarter_pairs

def generate_dash_table_config(
    df: pd.DataFrame,
    table_selected_metric,
    period_type: str,
    columns_config: Optional[Dict[str, str]] = None,
    toggle_selected_market_share: Optional[List[str]] = None,
    toggle_selected_qtoq: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate complete table configuration with styling and formatting."""
    show_market_share = toggle_selected_market_share and "show" in toggle_selected_market_share
    show_qtoq = toggle_selected_qtoq and "show" in toggle_selected_qtoq

    # Handle market share q-to-q change columns
    df_modified = df.copy()
    market_share_qtoq_cols = [col for col in df_modified.columns 
                             if 'market_share_q_to_q_change' in col]
    for col in market_share_qtoq_cols:
        df_modified[col] = df_modified[col].apply(
            lambda x: '-' if x == 0 or x == '-' else x * 100
        )

    # Generate column configurations
    columns = []
    comparison_quarters = get_comparison_quarters(df.columns)

    identifier_cols = set(IDENTIFIER_COLS)
    for col in df.columns:
        # Skip is_section_header column
        if col == 'is_section_header':
            continue
            
        logger.warning("Processing column: %s", col)
        logger.warning("Available METRICS keys: %s", sorted(METRICS.keys()))
        
        all_matches = [m for m in sorted(METRICS.keys(), key=len, reverse=True) 
                      if col.startswith(m)]
        
        metric = next((m for m in sorted(METRICS.keys(), key=len, reverse=True) 
                      if col.startswith(m)), '')
                      
        logger.debug("Selected metric for column %s: %s", col, metric)

        if col in identifier_cols:
            if metric:
                logger.warning("Found metric %s for identifier column %s", metric, col)
            else:
                logger.warning("No metric found for identifier column %s", col)
            columns.append({
                "id": col,
                "name": [translate(col), translate(col), translate(col)]
            })
            continue

        quarter = col[len(metric)+1:].split('_')[0] if metric else col.split('_')[0]
        
        is_qtoq = 'q_to_q_change' in col
        is_market_share = 'market_share' in col
        
        if is_qtoq:
            comparison = comparison_quarters.get(quarter, '')
            header = (
                f"{format_period(quarter, period_type, True)} vs "
                f"{format_period(comparison, period_type, True)}"
            ) if comparison else format_period(quarter, period_type)
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

    # Get complete table configuration from styling module
    table_config = generate_table_config(
        df=df,
        columns=columns,
        show_market_share=show_market_share,
        show_qtoq=show_qtoq
    )
    
    # Add data to the configuration
    table_config['data'] = df_modified.assign(
        insurer=lambda x: x['insurer'].map(map_insurer)
    ).to_dict('records')
    
    return table_config