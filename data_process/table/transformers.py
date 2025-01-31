from typing import List, Optional, Dict, Literal
import numpy as np
import pandas as pd
from config.logging_config import get_logger
from data_process.mappings import map_line, map_insurer
from data_process.io import save_df_to_csv

logger = get_logger(__name__)

# Constants
PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'

def format_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Process summary data rows with sorting logic for totals and top-N entries."""
    logger.debug("Processing summary rows")
    if df.empty:
        return df

    # Simplified sort key function
    def get_sort_priority(ins: str) -> tuple:
        ins_lower = ins.lower()
        if ins_lower.startswith('total'): return (2, 0)
        if ins_lower.startswith('top-'):
            try:
                return (1, int(ins.split('-')[1]))
            except (IndexError, ValueError):
                logger.debug(f"Invalid top-N format: {ins}")
                return (1, 0)
        return (0, 0)

    df = df.sort_values(
        by=INSURER_COL, 
        key=lambda x: pd.Series([get_sort_priority(ins) for ins in x])
    )
    
    # Initialize new columns efficiently
    df.insert(0, PLACE_COL, np.nan)
    df[SECTION_HEADER_COL] = False
    
    logger.debug(f"Processed {len(df)} summary rows")
    return df.replace(0, '-').fillna('-')

def get_rank_change(current: int, previous: Optional[int]) -> str:
    """Calculate and format rank change."""
    if previous is None and current is None:
        return f"-"
    if previous is None:
        return str(current)
    diff = previous - current
    if diff == 0:
        return f"{current} (-)"
    return f"{current} ({'+' if diff > 0 else ''}{diff})"

def format_ranking_column(
    df: pd.DataFrame,
    prev_ranks: Optional[Dict] = None,
    current_ranks: Optional[Dict] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Process insurance company rankings and format rank changes."""
    logger.info(f"Formatting ranking column: split_mode={split_mode}, rows={len(df)}")
    
    if df.empty or not current_ranks:
        df.insert(0, PLACE_COL, '')
        return df

    result_df = df.copy()
    result_df.insert(0, PLACE_COL, '')

    def get_rank_info(row):
        if split_mode == 'line':
            insurer = row[INSURER_COL]
            curr = current_ranks.get(insurer)
            prev = prev_ranks.get(insurer) if prev_ranks else None
        else:  # split_mode == 'insurer'
            line, insurer = row[LINE_COL], row[INSURER_COL]
            line_ranks = current_ranks.get(line.lower(), {})
            curr = line_ranks.get(insurer)
            prev = prev_ranks.get(line.lower(), {}).get(insurer) if prev_ranks else None
        
        return get_rank_change(curr, prev) if curr is not None else '-'  # Changed to '-'

    result_df[PLACE_COL] = result_df.apply(get_rank_info, axis=1)
    logger.info(f"Completed ranking column formatting")
    return result_df.replace(['', 0], '-').fillna('-')  # Added '' to replacement

def process_group_data(
    df: pd.DataFrame,
    group_col: str,
    item_col: str,
    item_mapper: callable,
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Process group data with enhanced metric ordering and pivot operations."""
    logger.info(f"Processing group data: split_mode={split_mode}, rows={len(df)}")
    
    if df.empty:
        return pd.DataFrame()
    try:
        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
        logger.debug(f"Unique quarters found: {df['year_quarter'].unique()}")

        logger.debug("Creating column names")
        df['column_name'] = df['metric'] + '_' + df['year_quarter']
        
        # Get and organize metrics - only use metrics that exist in the data
        logger.debug("Organizing metrics and their roots")
        metrics = sorted(df['metric'].unique())
        logger.debug(f"Found unique metrics: {metrics}")

        # Find root metrics with logging - only for existing metrics
        root_metrics = {}
        for m in metrics:
            possible_roots = [r for r in metrics if m.startswith(r)]
            if not possible_roots:
                logger.debug(f"No root found for metric: {m}")
                continue
            root = min(possible_roots, key=len)
            root_metrics[m] = root
            logger.debug(f"Metric '{m}' assigned to root '{root}'")

        # Create metric groups DataFrame - only for existing combinations
        logger.debug("Creating metric groups DataFrame")
        try:
            metric_groups = pd.DataFrame({
                'metric': metrics,
                'root': [root_metrics[m] for m in metrics]
            })
            metric_groups = metric_groups.sort_values(['root', 'metric'])
            logger.debug(f"Metric groups structure:\n{metric_groups}")
        except Exception as e:
            logger.error(f"Error creating metric groups DataFrame: {e}")
            raise

        # Create ordered columns - only for existing combinations
        logger.debug("Creating ordered column list")
        quarters = sorted(df['year_quarter'].unique(), reverse=True)
        logger.debug(f"Processing quarters in order: {quarters}")

        # Get actual data combinations before any transformations
        actual_combinations = df.groupby(['metric', 'year_quarter']).size()
        logger.debug("Raw metric-quarter combinations in data:")
        logger.debug(actual_combinations)
        
        # Create explicit set of existing combinations
        existing_combinations = set()
        for (metric, quarter) in actual_combinations.index:
            combo = f"{metric}_{quarter}"
            existing_combinations.add(combo)
            logger.debug(f"Found existing combination: {combo}")
        
        logger.debug(f"All existing combinations: {sorted(existing_combinations)}")
        
        ordered_cols = []
        for _, group in metric_groups.groupby('root'):
            root_name = group['root'].iloc[0]
            logger.debug(f"Processing metric group for root: {root_name}")
            for metric in group['metric']:
                for quarter in quarters:
                    col_name = f"{metric}_{quarter}"
                    # Strict check - must exist in original data
                    if col_name in existing_combinations:
                        ordered_cols.append(col_name)
                        logger.debug(f"✓ Adding column: {col_name}")
                    else:
                        logger.debug(f"✗ Skipping non-existent column: {col_name}")
        
        logger.debug("Final ordered columns:")
        for col in ordered_cols:
            logger.debug(f"- {col}")

        logger.info(f"debug {len(ordered_cols)} ordered columns")
        logger.debug(f"First few ordered columns: {ordered_cols[:5]}")

        # Update column_name categoricals - only for existing combinations
        logger.debug("Setting up column ordering")
        try:
            df['column_name'] = pd.Categorical(
                df['column_name'],
                categories=ordered_cols,
                ordered=True
            )
            logger.debug("Successfully set column ordering")
        except Exception as e:
            logger.error(f"Error setting column categories: {e}")
            logger.debug(f"Current column_name values: {df['column_name'].unique()}")
            logger.debug(f"Ordered columns: {ordered_cols[:10]}...")
            raise
        
        # Pivot and process data - use observed=True to only create columns that exist
        pivot_df = df.pivot_table(
            index=[INSURER_COL, LINE_COL],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True,  # Changed to True to only include existing combinations
            dropna=False  
        ).reset_index()

        # Split and process summary/regular rows
        is_summary = pivot_df[INSURER_COL].str.lower().str.contains('^top|^total')
        result_df = pd.concat([
            format_ranking_column(pivot_df[~is_summary], prev_ranks, current_ranks, split_mode),
            format_summary_rows(pivot_df[is_summary])
        ], ignore_index=True) if is_summary.any() else format_ranking_column(
            pivot_df, prev_ranks, current_ranks, split_mode
        )

        # Apply mappings and formatting
        result_df[INSURER_COL] = result_df[INSURER_COL].apply(map_insurer)
        result_df[LINE_COL] = result_df[LINE_COL].apply(map_line)
        result_df[SECTION_HEADER_COL] = False
        
        # Organize final columns - only include columns that exist
        base_cols = {INSURER_COL, LINE_COL}
        metric_cols = [col for col in pivot_df.columns if col not in base_cols]
        final_cols = ([PLACE_COL] if PLACE_COL in result_df.columns else []) + \
                    [INSURER_COL, LINE_COL] + metric_cols + [SECTION_HEADER_COL]
        
        logger.info(f"Successfully processed group data: output_rows={len(result_df)}")
        return result_df[final_cols].replace(0, '-').fillna('-')

    except Exception as e:
        logger.error(f"Error processing group data: {str(e)}", exc_info=True)
        return pd.DataFrame()

def transform_table_data(
    df: pd.DataFrame,
    selected_metrics: List[str],
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    current_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    split_mode: Literal['line', 'insurer'] = 'line'
) -> pd.DataFrame:
    """Transform and format table data with enhanced error handling and logging."""
    logger.info(f"Starting table transformation: split_mode={split_mode}, rows={len(df)}")
    
    try:
        # Configure grouping
        group_configs = {
            'line': (LINE_COL, INSURER_COL, map_line, map_insurer),
            'insurer': (INSURER_COL, LINE_COL, map_insurer, map_line)
        }
        group_col, item_col, group_mapper, item_mapper = group_configs[split_mode]
        
        transformed_dfs = []
        for group in df[group_col].unique():
            logger.debug(f"Processing group: {group}")
            
            # Get group-specific ranks
            group_prev_ranks = prev_ranks.get(group.lower(), {}) if split_mode == 'line' and prev_ranks else prev_ranks
            group_current_ranks = current_ranks.get(group.lower(), {}) if split_mode == 'line' and current_ranks else current_ranks

            group_df = process_group_data(
                df[df[group_col] == group].copy(),
                group_col,
                item_col,
                item_mapper,
                group_prev_ranks,
                group_current_ranks,
                split_mode
            )

            metric_cols = [col for col in group_df.columns 
                         if col not in [PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL]]
            
            # Sort non-summary rows by first metric
            is_summary = group_df[INSURER_COL].str.lower().str.contains(
                '^топ|^total|весь рынок', 
                na=False
            )
            regular_rows = group_df[~is_summary].copy()
            if not regular_rows.empty:
                regular_rows['_sort_value'] = pd.to_numeric(
                    regular_rows[metric_cols[0]].replace('-', float('-inf')), 
                    errors='coerce'
                )
                regular_rows = regular_rows.sort_values(
                    '_sort_value', 
                    ascending=False
                ).drop(columns=['_sort_value'])
            
            transformed_dfs.append(pd.concat([regular_rows, group_df[is_summary]]))

        if not transformed_dfs:
            logger.debug("No data to transform")
            return pd.DataFrame()

        # Combine and format final output
        result_df = pd.concat(transformed_dfs, ignore_index=True)
        drop_col = LINE_COL if split_mode == 'line' else INSURER_COL
        result_df = result_df.drop(columns=[drop_col])
        
        # Reorder columns
        base_cols = ['N', 'insurer'] if split_mode == 'line' else ['linemain', 'N']
        other_cols = [col for col in result_df.columns if col not in base_cols]
        
        logger.info("Table transformation completed successfully")
        return result_df[base_cols + other_cols]

    except Exception as e:
        logger.error(f"Error in table transformation: {str(e)}", exc_info=True)
        raise