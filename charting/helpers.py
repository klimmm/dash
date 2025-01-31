import pandas as pd
from typing import List
from config.logging_config import get_logger

logger = get_logger(__name__)


def sort_dataframe(
    df: pd.DataFrame,
    x_column: str,
    series_column: str,
    group_column: str,
    main_insurer: List[str] = None,
    compare_insurers: List[str] = None,
    primary_y_metrics: List[str] = None,
    secondary_y_metrics: List[str] = None
) -> pd.DataFrame:
    # Return early if DataFrame is empty
    if df.empty:
        return df
    df = df.copy()
    logger.debug(f"df head before sorting {df.head()}")
    logger.debug(f"group_column {group_column}")
    logger.debug(f"series_column {series_column}")

    # Handle insurer ordering
    if group_column == 'insurer' or series_column == 'insurer':
        logger.debug(f"main_insurer {main_insurer}")
        logger.debug(f"compare_insurers {compare_insurers}")
        insurer_col = 'insurer'
        if insurer_col in df.columns and (main_insurer or compare_insurers):
            # Create ordered categories: main insurers -> compare insurers -> others
            all_insurers = [*(main_insurer or []), *(compare_insurers or [])]
            other_insurers = sorted(set(df[insurer_col]) - set(all_insurers))
            ordered_insurers = [*(main_insurer or []), *(compare_insurers or []), *other_insurers]
            logger.debug(f"ordered_insurers {ordered_insurers}")

            # Create categorical with explicit ordering
            df[insurer_col] = pd.Categorical(
                df[insurer_col],
                categories=ordered_insurers,
                ordered=True
            )

            # Add an order column for insurers
            df['insurer_order'] = df[insurer_col].cat.codes
            logger.debug(f"insurer categories: {df[insurer_col].cat.categories}")
            logger.debug(f"insurer codes: {df[['insurer', 'insurer_order']].head()}")

    # Handle metric ordering
    if group_column == 'metric' or series_column == 'metric':
        logger.debug(f"primary_y_metrics {primary_y_metrics}")
        logger.debug(f"secondary_y_metrics {secondary_y_metrics}")
        metric_col = 'metric'
        if metric_col in df.columns and (primary_y_metrics or secondary_y_metrics):
            # Create ordered categories: primary metrics -> secondary metrics -> others
            all_metrics = [*(primary_y_metrics or []), *(secondary_y_metrics or [])]
            other_metrics = sorted(set(df[metric_col]) - set(all_metrics))
            ordered_metrics = [*(primary_y_metrics or []), *(secondary_y_metrics or []), *other_metrics]
            logger.debug(f"ordered_metrics {ordered_metrics}")

            # Create categorical with explicit ordering
            df[metric_col] = pd.Categorical(
                df[metric_col],
                categories=ordered_metrics,
                ordered=True
            )

            # Add an order column for metrics
            df['metric_order'] = df[metric_col].cat.codes
            logger.debug(f"metric categories: {df[metric_col].cat.categories}")
            logger.debug(f"metric codes: {df[['metric', 'metric_order']].head()}")

    # Build sort columns list
    sort_cols = []
    ascending = []

    # Handle time-based columns first
    if 'year_quarter' in df.columns:
        sort_cols.append('year_quarter')
        ascending.append(True)
    else:
        if 'year' in df.columns:
            sort_cols.append('year')
            ascending.append(True)
        if 'quarter' in df.columns:
            sort_cols.append('quarter')
            ascending.append(True)

    # Add ordering columns for categorical variables
    if 'insurer_order' in df.columns:
        sort_cols.append('insurer_order')
        ascending.append(True)
    if 'metric_order' in df.columns:
        sort_cols.append('metric_order')
        ascending.append(True)

    # Add value column if present
    if 'value' in df.columns:
        sort_cols.append('value')
        ascending.append(False)

    logger.debug(f"sort_cols: {sort_cols}")
    logger.debug(f"ascending: {ascending}")

    # Return unsorted DataFrame if no sort columns
    if not sort_cols:
        return df

    # Sort the DataFrame
    df = df.sort_values(by=sort_cols, ascending=ascending)
    logger.debug(f"df head after sorting {df.head()}")

    # Drop the temporary ordering columns
    if 'insurer_order' in df.columns:
        df = df.drop('insurer_order', axis=1)
    if 'metric_order' in df.columns:
        df = df.drop('metric_order', axis=1)

    return df