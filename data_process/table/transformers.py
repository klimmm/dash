from typing import List, Optional, Dict, Literal

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from data_process.mappings import map_line, map_insurer
from data_process.io import save_df_to_csv

logger = get_logger(__name__)

PLACE_COL = 'N'
INSURER_COL = 'insurer'
LINE_COL = 'linemain'
SECTION_HEADER_COL = 'is_section_header'


def format_summary_rows(df: pd.DataFrame) -> pd.DataFrame:
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


def format_ranking_column(
    df: pd.DataFrame,
    prev_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    current_ranks: Optional[Dict[str, Dict[str, int]]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    """Process insurance company rankings and format rank changes."""
    if df.empty:
        return df

    result_df = df.copy()

    if not current_ranks:
        result_df.insert(0, PLACE_COL, '')
        return result_df

    def get_current_rank(row):
        if split_mode == 'line':
            return current_ranks.get(row['insurer'], -1)
        return current_ranks.get(row['linemain'], {}).get(row['insurer'], -1)

    def format_rank_change(row, current_rank):
        if current_rank == -1:
            return ''

        if split_mode == 'line':
            previous = prev_ranks.get(row['insurer']) if prev_ranks else None
        else:
            line_prev_ranks = prev_ranks.get(row['linemain'], {}) if prev_ranks else {}
            previous = line_prev_ranks.get(row['insurer'])

        if previous is None:
            return str(current_rank)

        diff = previous - current_rank
        change = '-' if diff == 0 else f"+{diff}" if diff > 0 else str(diff)
        return f"{current_rank} ({change})"

    current_ranks_list = result_df.apply(get_current_rank, axis=1)
    result_df.insert(0, PLACE_COL, current_ranks_list)

    if prev_ranks:
        result_df[PLACE_COL] = result_df.apply(
            lambda row: format_rank_change(row, int(row[PLACE_COL])), 
            axis=1
        )
    else:
        result_df[PLACE_COL] = result_df[PLACE_COL].apply(
            lambda x: str(x) if x != -1 else ''
        )

    return result_df


def process_group_data(
    df: pd.DataFrame,
    group_col: str,
    item_col: str,
    item_mapper: callable,
    prev_ranks: Optional[Dict[str, int]] = None,
    current_ranks: Optional[Dict[str, int]] = None,
    split_mode: str = 'line'
) -> pd.DataFrame:
    try:
        logger.info(f"Processing group data with type: {split_mode}")
        unique_metrics = df['metric'].unique()
        logger.debug(f"Unique metrics in order before pivot: {unique_metrics}")

        df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
        df['column_name'] = df['metric'] + '_' + df['year_quarter']
        all_quarters = sorted(df['year_quarter'].unique(), reverse=True)

        # Group metrics by their root metric while preserving original order
        metric_groups = {}
        root_metrics_order = []  # To preserve order of root metrics

        for metric in unique_metrics:
            # Find the shortest metric that is a prefix of this metric
            root_metric = min(
                (m for m in unique_metrics if metric.startswith(m)),
                key=len
            )
            if root_metric not in metric_groups:
                root_metrics_order.append(root_metric)
            metric_groups.setdefault(root_metric, []).append(metric)

        # Sort metrics within each group by length (shorter names come first)
        for root_metric in metric_groups:
            metric_groups[root_metric] = sorted(metric_groups[root_metric], key=len)

        # Create ordered column names using original root metrics order
        ordered_column_names = []
        for root_metric in root_metrics_order:  # Use preserved order instead of sorting
            for metric in metric_groups[root_metric]:
                for quarter in all_quarters:
                    ordered_column_names.append(f"{metric}_{quarter}")

        logger.debug(f"ordered_column_names : {ordered_column_names}")

        df['column_name'] = pd.Categorical(
            df['column_name'],
            categories=ordered_column_names,
            ordered=True
        )

        # Rest of your existing code...
        save_df_to_csv(df, "transform_before_pivot_df.csv")
        # Create a copy of the DataFrame first to avoid the SettingWithCopyWarning
        #df_copy = df.copy()

        pivot_df = df.pivot_table(
            index=['insurer', 'linemain'],
            columns='column_name',
            values='value',
            aggfunc='first',
            observed=True  # Add this parameter
        ).reset_index()
        save_df_to_csv(pivot_df, "transform_pivot_df.csv")

        # Process rankings and summary rows
        is_summary = pivot_df['insurer'].str.lower().str.contains('^top|^total')
        if is_summary.any():
            regular_data = format_ranking_column(
                pivot_df[~is_summary],
                prev_ranks,
                current_ranks,
                split_mode
            )
            summary_data = format_summary_rows(pivot_df[is_summary])
            result_df = pd.concat([regular_data, summary_data], ignore_index=True)
        else:
            result_df = format_ranking_column(
                pivot_df,
                prev_ranks,
                current_ranks,
                split_mode
            )

        # Create final structure using ordered metric columns
        columns = pivot_df.columns.tolist()
        base_cols = {INSURER_COL, LINE_COL}
        final_cols = ([PLACE_COL] if PLACE_COL in result_df.columns else []) + \
                    [INSURER_COL, LINE_COL] + \
                    [col for col in columns if col not in base_cols] + \
                    [SECTION_HEADER_COL]

        # Map values
        result_df[INSURER_COL] = result_df[INSURER_COL].apply(map_insurer)
        result_df[LINE_COL] = result_df[LINE_COL].apply(map_line)
        result_df[SECTION_HEADER_COL] = False

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
    """Transform and format table data based on specified grouping type."""
    try:
        logger.info(f"Starting table transformation with split_mode: {split_mode}")

        # Define grouping configuration
        if split_mode == 'line':
            group_col = LINE_COL
            item_col = INSURER_COL
            group_mapper = map_line
            item_mapper = map_insurer
        else:  # split_mode == 'insurer'
            group_col = INSURER_COL
            item_col = LINE_COL
            group_mapper = map_insurer
            item_mapper = map_line

        transformed_dfs = []

        for group in df[group_col].unique():
            logger.debug(f"Processing group: {group}")

            # Get group-specific ranks
            if split_mode == 'line':
                group_prev_ranks = prev_ranks.get(group.lower()) if prev_ranks else None
                group_current_ranks = current_ranks.get(group.lower()) if current_ranks else None
            else:
                group_prev_ranks = prev_ranks
                group_current_ranks = current_ranks

            save_df_to_csv(df[df[group_col] == group], "transform_before_group.csv")
            # Process group data
            group_df = process_group_data(
                df[df[group_col] == group].copy(),
                group_col,
                item_col,
                item_mapper,
                group_prev_ranks,
                group_current_ranks,
                split_mode
            )

            save_df_to_csv(group_df, "group_df_transform_before_concat.csv")
            if not group_df.empty:
                # Sort within group by first metric
                metric_cols = [col for col in group_df.columns 
                             if col not in [PLACE_COL, INSURER_COL, LINE_COL, SECTION_HEADER_COL]]

                if metric_cols:
                    sort_metric = metric_cols[0]
                    logger.debug(f"Sorting group {group} by metric: {sort_metric}")

                    # Separate summary and regular rows within group
                    is_summary = group_df[INSURER_COL].str.lower().str.contains(
                        '^топ|^total|весь рынок', 
                        na=False
                    )
                    regular_rows = group_df[~is_summary].copy()
                    summary_rows = group_df[is_summary]

                    # Sort regular rows within group
                    if not regular_rows.empty:
                        regular_rows['_sort_value'] = pd.to_numeric(
                            regular_rows[sort_metric].replace('-', float('-inf')), 
                            errors='coerce'
                        ).fillna(float('-inf'))

                        regular_rows = regular_rows.sort_values(
                            '_sort_value', 
                            ascending=False
                        ).drop(columns=['_sort_value'])

                    # Combine sorted regular rows with summary rows for this group
                    group_df = pd.concat([regular_rows, summary_rows])
                    logger.warning(f"Sorting group {group_df}")

                transformed_dfs.append(group_df)

        # Combine results
        result_df = pd.concat(transformed_dfs, ignore_index=True) if transformed_dfs else pd.DataFrame()
        logger.warning(f"result_df {result_df}")
        save_df_to_csv(result_df, "df_transform_after_concat.csv")
        # Drop appropriate column based on grouping type
        if not result_df.empty:
            drop_col = LINE_COL if split_mode == 'line' else INSURER_COL
            result_df = result_df.drop(columns=[drop_col])

            # Reorder columns for line grouping
            if split_mode == 'line':
                cols = result_df.columns.tolist()
                desired_order = ['N', 'insurer'] + [col for col in cols if col not in ['N', 'insurer']]
                result_df = result_df[desired_order]
            else:  # split_mode == 'insurer'
                cols = result_df.columns.tolist()
                desired_order = ['linemain', 'N'] + [col for col in cols if col not in ['linemain', 'N']]
                result_df = result_df[desired_order]

        logger.info("Table transformation completed successfully")
        return result_df

    except Exception as e:
        logger.error(f"Error in table transformation: {e}", exc_info=True)
        raise