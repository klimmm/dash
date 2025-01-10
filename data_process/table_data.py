# data_process.table_data.py
import pandas as pd
import numpy as np
from dash import dash_table
from typing import List, Tuple, Optional, Dict, OrderedDict
from application.components.dash_table import generate_dash_table_config
from data_process.data_utils import map_line
from constants.translations import translate
from config.logging_config import get_logger

logger = get_logger(__name__)


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

    logger.debug(f"Updating data table. table_selected_metric: {table_selected_metric}")

    table_data = table_data_pivot(df, table_selected_metric, prev_ranks)

    table_config = generate_dash_table_config(
        df=table_data,
        period_type=period_type,
        toggle_selected_market_share=toggle_selected_market_share,
        toggle_selected_qtoq=toggle_selected_qtoq
    )

    data_table = dash_table.DataTable(**table_config)

    mapped_lines = map_line(selected_linemains)

    lines_str = ', '.join(mapped_lines) if isinstance(mapped_lines, list) else mapped_lines
    table_title = f"Топ-{number_of_insurers} страховщиков"
    table_subtitle = f"{translate(table_selected_metric[0])}: {lines_str}"

    return data_table, table_title, table_subtitle


def table_data_pivot(
    df: pd.DataFrame,
    table_selected_metric: List[str], 
    prev_ranks: Optional[Dict[str, int]] = None
) -> pd.DataFrame:

    logger.debug("Starting table data pivot")

    try:
        # 1. Prepare metrics and initial filtering
        def _prepare_metrics(base_metrics: List[str]) -> List[str]:
            """Generate complete list of metrics including derived ones."""
            derived_suffixes = ['q_to_q_change', 'market_share', 'market_share_q_to_q_change']
            return (base_metrics +
                    [f"{m}_{suffix}" for m in base_metrics for suffix in derived_suffixes])

        metrics_to_keep = _prepare_metrics(table_selected_metric)
        logger.debug(f"metrics_to_keep : {metrics_to_keep}")
        filtered_df = df[df['metric'].isin(metrics_to_keep)].copy()

        # 2. Format time periods and extract metric components
        def _format_time_periods(df: pd.DataFrame) -> pd.DataFrame:
            """Convert year_quarter to standard YYYYQX format."""
            df['year_quarter'] = pd.to_datetime(df['year_quarter']).dt.to_period('Q').astype(str)
            return df

        def _extract_metric_components(df: pd.DataFrame, base_metrics: List[str]) -> pd.DataFrame:
            """Split metrics into base metric and attribute components."""
            def extract_metric_attribute(metric, base_metrics):
                # Sort base_metrics by length, longest first
                sorted_bases = sorted(base_metrics, key=len, reverse=True)
                for base in sorted_bases:
                    if metric.startswith(base):
                        suffix = metric[len(base):].lstrip('_')
                        return base, suffix or ''
                return metric, ''

            df[['base_metric', 'attribute']] = df.apply(
                lambda row: pd.Series(extract_metric_attribute(row['metric'], base_metrics)),
                axis=1
            )
            return df

        processed_df = _format_time_periods(filtered_df)
        processed_df = _extract_metric_components(processed_df, table_selected_metric)
        logger.debug(f"metrics uniqye processed_df after _extract_metric_components: {processed_df['metric'].unique() }")

        # 3. Create and format pivot table
        def _create_pivot_columns(df: pd.DataFrame) -> pd.DataFrame:
            """Create unified column names for pivot operation."""
            df['column_name'] = df.apply(
                lambda row: f"{row['base_metric']}_{row['year_quarter']}"
                           f"{'_' + row['attribute'] if row['attribute'] else ''}",
                axis=1
            )
            return df

        def _pivot_data(df: pd.DataFrame) -> pd.DataFrame:
            """Create pivot table with insurers as index."""
            return df.pivot_table(
                index='insurer',
                columns='column_name',
                values='value',
                aggfunc='first'
            ).reset_index()

        processed_df = _create_pivot_columns(processed_df)
        logger.debug(f"processed_df first row:\n{processed_df.head(1).to_string()}")
        logger.debug(f"metrics uniqye processed_df: {processed_df['column_name'].unique() }")
        pivot_df = _pivot_data(processed_df)
        logger.debug(f"pivot_df: {pivot_df.head() }")
        logger.debug(f"pivot_df first row:\n{pivot_df.head(1).to_string()}")

        # 4. Organize columns and handle missing values
        def _organize_columns(df: pd.DataFrame, base_metrics: List[str],
                             time_periods: List[str]) -> pd.DataFrame:
            """Organize columns in desired order and format."""
            attributes = ['', 'q_to_q_change', 'market_share', 'market_share_q_to_q_change']
            desired_columns = ['insurer'] + [
                f"{metric}_{year}{'_' + attr if attr else ''}"
                for metric in base_metrics
                for attr in attributes
                for year in sorted(time_periods, reverse=True)
            ]
            # Remove duplicates while preserving order
            desired_columns = list(OrderedDict.fromkeys(desired_columns))

            # Add missing columns and reorder
            for col in desired_columns:
                if col not in df.columns:
                    df[col] = pd.NA
            return df[desired_columns]

        organized_df = _organize_columns(
            pivot_df,
            table_selected_metric,
            processed_df['year_quarter'].unique()
        )

        logger.debug(f"organized_df first row:\n{organized_df.head(1).to_string()}")

        # 5. Clean and sort the final table
        def _clean_and_sort_table(df: pd.DataFrame) -> pd.DataFrame:
            # Remove empty columns except insurer
            value_cols = df.columns[df.columns != 'insurer']
            mask = ~((df[value_cols] == 0) | df[value_cols].isna()).all()
            keep_cols = ['insurer'] + list(value_cols[mask])
            df = df[keep_cols]

            # Separate regular and summary rows
            summary_mask = df['insurer'].str.lower().str.startswith(('top', 'total'))
            main_df = df[~summary_mask].copy()
            summary_df = df[summary_mask].copy()

            # Sort by first metric column
            sort_col = value_cols[0]
            main_df[sort_col] = pd.to_numeric(main_df[sort_col], errors='coerce')
            main_df = main_df.sort_values(by=sort_col, ascending=False)

            # Add numbering with previous rank
            main_df.insert(0, 'N', range(1, len(main_df) + 1))
            if prev_ranks:
                main_df['N'] = main_df.apply(
                    lambda row: f"{int(row['N'])} ({prev_ranks.get(row['insurer'], 'n/a')})"
                    if row['insurer'] in prev_ranks else str(int(row['N'])),
                    axis=1
                )
            else:
                main_df['N'] = main_df['N'].astype(str)

            # Combine and finalize
            summary_df.insert(0, 'N', np.nan)
            final_df = pd.concat([main_df, summary_df], ignore_index=True)

            return final_df.fillna('n/a')

        final_df = _clean_and_sort_table(organized_df)
        logger.debug(f"final_df first row:\n{final_df.head(1).to_string()}")

        logger.debug(f"Completed table pivot. Output shape: {final_df.shape}")
        return final_df

    except Exception as e:
        logger.error(f"Error in table_data_pivot: {e}", exc_info=True)
        raise

    final_df = _clean_and_sort_table(organized_df)

    return final_df