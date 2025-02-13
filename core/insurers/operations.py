from typing import List, Optional
import pandas as pd
from config.logging import timer, get_logger
logger = get_logger(__name__)

@timer
def get_ordered_insurers(df: pd.DataFrame, top_n: int = 0) -> List[str]:
    """
    Maintain consistent ordering of insurers based on value sums.
    """
    logger.info(f"Starting get_ordered_insurers with top_n={top_n}")
    
    value_sums = df.groupby('insurer')['value'].sum()
    logger.debug(f"Value sums calculated:\n{value_sums}")
    
    EXCLUDED_INSURERS = frozenset(['top-5', 'top-10', 'top-20', 'total'])
    logger.debug(f"Excluded insurers: {EXCLUDED_INSURERS}")
    
    if top_n > 0:
        ordered = value_sums.nlargest(top_n).index.tolist()
        logger.debug(f"Top {top_n} insurers before filtering: {ordered}")
    else:
        ordered = value_sums.sort_values(ascending=False).index.tolist()
        logger.debug(f"All insurers before filtering: {ordered}")
    
    # Filter and append special categories
    ordered = [ins for ins in ordered if ins not in EXCLUDED_INSURERS]
    logger.debug(f"Insurers after filtering excluded: {ordered}")
    
    if top_n > 0 and f'top-{top_n}' in EXCLUDED_INSURERS:
        ordered.append(f'top-{top_n}')
        logger.debug(f"Added top-{top_n} category: {ordered}")
    elif top_n == 0:
        ordered.extend(x for x in EXCLUDED_INSURERS if x != 'total')
        logger.debug(f"Added all special categories except total: {ordered}")
    
    ordered.append('total')
    logger.info(f"Final ordered insurers: {ordered}")
    
    return ordered

@timer
@timer
def filter_and_sort_by_insurer(
    df: pd.DataFrame,
    latest_df: pd.DataFrame,
    top_insurers: int,
    selected_insurers: List[str],
    split_mode: str,
    pivot_column: str
) -> pd.DataFrame:
    """
    Filter and sort insurers while maintaining line-specific ordering.
    When pivot_column is 'line' and split_mode is 'insurer' or 'metric_base',
    identifies top insurers across all lines before filtering.
    """
    logger.info(f"Starting filter_and_sort_by_insurer with top_insurers={top_insurers}, "
                f"split_mode={split_mode}, pivot_column={pivot_column}")
    
    if top_insurers == 0:
        ordered_insurers = [ins for ins in selected_insurers + ['total'] if pd.notna(ins)]
        filtered_df = df[df['insurer'].isin(ordered_insurers)].copy()
        filtered_df['insurer'] = pd.Categorical(
            filtered_df['insurer'],
            categories=ordered_insurers,
            ordered=True
        )
        return filtered_df
    
    if (split_mode in ('insurer', 'metric_base') and pivot_column == 'line'):
        # Identify top insurers across all lines - get_ordered_insurers already includes special categories
        logger.info("Identifying top insurers across all lines")
        filtered_insurers = get_ordered_insurers(latest_df, top_insurers)
        logger.debug(f"Insurers after get_ordered_insurers: {filtered_insurers}")
        
        # Filter the DataFrame to include insurers (including special categories)
        filtered_df = df[df['insurer'].isin(filtered_insurers)].copy()
        
        # Set categorical order based on the order from get_ordered_insurers
        filtered_df['insurer'] = pd.Categorical(
            filtered_df['insurer'],
            categories=filtered_insurers,
            ordered=True
        )
        
        logger.debug(f"Final insurers after cross-line filtering: {filtered_insurers}")
        return filtered_df
    
    if split_mode in ('insurer', 'metric_base'):
        filtered_insurers = get_ordered_insurers(latest_df, top_insurers)
        filtered_df = df[df['insurer'].isin(filtered_insurers)].copy()
        filtered_df['insurer'] = pd.Categorical(
            filtered_df['insurer'],
            categories=filtered_insurers,
            ordered=True
        )
        return filtered_df
    
    # Line mode processing with line-specific ordering
    logger.info("Processing in line mode with line-specific ordering")
    
    result_parts = []
    for line in df['line'].unique():
        logger.debug(f"Processing line: {line}")
        
        # Get line-specific data
        line_data = latest_df[latest_df['line'] == line]
        current_line_data = df[df['line'] == line]
        
        # Get line-specific order with its own top-X insurers
        line_insurers = get_ordered_insurers(line_data, top_insurers)
        line_insurers = [ins for ins in line_insurers if pd.notna(ins)]
        logger.debug(f"Line {line} insurers (no nulls): {line_insurers}")
        
        # Filter current data for this line using its specific insurers
        line_df = current_line_data[
            current_line_data['insurer'].isin(line_insurers)
        ].copy()
        
        if not line_df.empty:
            # Use line-specific categorical order
            line_df['insurer'] = pd.Categorical(
                line_df['insurer'],
                categories=line_insurers,
                ordered=True
            )
            logger.debug(f"Final categorical order for line {line}: {line_df['insurer'].cat.categories.tolist()}")
            result_parts.append(line_df)
    
    if result_parts:
        # Concatenate while preserving line-specific categories
        result = pd.concat(result_parts, ignore_index=True)
        logger.info(f"Final insurers after line mode processing: {result['insurer'].unique().tolist()}")
        return result
    else:
        logger.debug("No valid data after processing, returning empty DataFrame")
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df['insurer'] = pd.Categorical([], ordered=True)
        return empty_df


@timer
def reindex_and_sort(
    data: pd.DataFrame,
    metrics: List[str] = None,
    use_all: bool = False,
    valid_combinations: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Reindex DataFrame with all valid combinations of dimensions while preserving insurer order.
    """
    logger.info("Starting reindex_and_sort")
    logger.debug(f"Input metrics: {metrics}")
    logger.debug(f"Use all: {use_all}")
    
    # Preserve original insurer order
    insurer_order = None
    if 'insurer' in data.columns and isinstance(data['insurer'].dtype, pd.CategoricalDtype):
        insurer_order = data['insurer'].cat.categories.tolist()
        logger.debug(f"Preserving insurer order: {insurer_order}")
    
    # Get unique metric-quarter combinations
    metric_quarters = data[['metric', 'metric_base', 'value_type', 'year_quarter']].drop_duplicates()
    
    if valid_combinations is None:
        if use_all:
            logger.debug("Creating full cartesian product of insurers and lines")
            insurers = data['insurer'].unique()
            lines = data['line'].unique()
            combinations = pd.DataFrame([
                {'insurer': ins, 'line': line}
                for ins in insurers
                for line in lines
            ])
        else:
            logger.debug("Using existing insurer-line combinations")
            combinations = data[['insurer', 'line']].drop_duplicates()
    else:
        logger.debug("Using provided valid combinations")
        combinations = valid_combinations.copy()
    
    logger.debug(f"Number of combinations: {len(combinations)}")
    
    # Create cross product with metrics and quarters
    full_data = []
    for _, combo in combinations.iterrows():
        for _, mq in metric_quarters.iterrows():
            full_data.append({
                'insurer': combo['insurer'],
                'line': combo['line'],
                'metric': mq['metric'],
                'metric_base': mq['metric_base'],
                'value_type': mq['value_type'],
                'year_quarter': mq['year_quarter']
            })
    
    full_df = pd.DataFrame(full_data)
    
    # Merge with original data
    merged_df = pd.merge(
        full_df,
        data,
        how='left',
        on=['insurer', 'line', 'metric', 'metric_base', 'value_type', 'year_quarter']
    )
    
    # Set up metric ordering
    metrics_order = []
    if metrics:
        metrics_order.extend([m for m in metrics if m in merged_df['metric'].unique()])
    metrics_order.extend([m for m in merged_df['metric'].unique() if m not in metrics_order])
    logger.debug(f"Final metrics order: {metrics_order}")
    
    merged_df['metric'] = pd.Categorical(
        merged_df['metric'],
        categories=metrics_order,
        ordered=True
    )
    
    # Restore insurer order if it was preserved
    if insurer_order is not None:
        merged_df['insurer'] = pd.Categorical(
            merged_df['insurer'],
            categories=insurer_order,
            ordered=True
        )
        logger.debug(f"Restored insurer order: {merged_df['insurer'].cat.categories.tolist()}")
    
    # Sort by metric first, then by the categorical insurer order
    sorted_df = merged_df.sort_values(['metric', 'insurer'])
    logger.info(f"Final shape after reindexing and sorting: {sorted_df.shape}")
    
    return sorted_df