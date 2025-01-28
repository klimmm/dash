import pandas as pd
from typing import List, Dict
from config.logging_config import get_logger
from data_process.data_utils import map_insurer, save_df_to_csv

logger = get_logger(__name__)


def get_insurer_options(
    df: pd.DataFrame,
    all_metrics: List[str],
    lines: List[str]
) -> Dict[str, List[str]]:
    """
    Generate insurer options and rankings.

    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    logger.info("Starting insurer options and rankings generation")

    try:
        filtered_df = df[
            df['insurer'].apply(lambda i: i not in {'total', 'top-5', 'top-10', 'top-20'})
        ]

        # Find first available metric
        try:
            metric_to_use = next(m for m in all_metrics if m in filtered_df['metric'].unique())
            logger.info(f"Selected metric: {metric_to_use}")
        except StopIteration:
            logger.error("No valid metrics found in data")
            raise ValueError("No valid metrics available")

        # Get metric-filtered data
        metric_df = filtered_df[filtered_df['metric'] == metric_to_use]
        quarters = sorted(metric_df['year_quarter'].unique())

        if not quarters:
            logger.warning("No quarters found in data")
            return {
                'top5': [], 'top10': [], 'top20': [], 'insurer_options': [],
                'current_ranks': {}, 'prev_ranks': {}
            }

        # Get latest quarter data for first line
        latest_quarter = quarters[-1]
        latest_data = metric_df[
            (metric_df['linemain'] == lines[0]) & 
            (metric_df['year_quarter'] == latest_quarter)
        ].sort_values('value', ascending=False)

        logger.debug(f"Processing data for quarter {latest_quarter}")

        # Get sorted insurers from filtered data
        all_insurers = latest_data['insurer'].unique().tolist()

        # Generate rankings for current and previous quarters
        current_quarter = latest_quarter
        prev_quarter = quarters[-2] if len(quarters) > 1 else None

        rankings = {'current_ranks': {}, 'prev_ranks': {}}

        # Process rankings for both quarters
        for period, target_quarter in [
            ('current_ranks', current_quarter),
            ('prev_ranks', prev_quarter)
        ]:
            if target_quarter:
                logger.info(f"Generating {period} for quarter {target_quarter}")
                quarter_df = metric_df[metric_df['year_quarter'] == target_quarter]

                for line_id in metric_df['linemain'].unique():
                    line_df = quarter_df[quarter_df['linemain'] == line_id]

                    if not line_df.empty:
                        logger.debug(f"Processing {period} for line_id: {line_id}")
                        save_df_to_csv(line_df, f"{line_id}_{target_quarter}_line_df.csv")

                        rankings[period][line_id] = dict(
                            zip(
                                line_df.sort_values('value', ascending=False)['insurer'].astype(str),
                                range(1, len(line_df) + 1)
                            )
                        )
                        logger.debug(f"Generated {len(rankings[period][line_id])} rankings for line_id {line_id}")

        # Create options with mapped labels
        insurer_options = [
            {'label': map_insurer(i), 'value': i} 
            for i in ['top-5', 'top-10', 'top-20'] + all_insurers
        ]

        logger.info(f"Generated options for {len(all_insurers)} insurers")

        return {
            'top5': all_insurers[:5],
            'top10': all_insurers[:10],
            'top20': all_insurers[:20],
            'insurer_options': insurer_options,
            'current_ranks': rankings['current_ranks'],
            'prev_ranks': rankings['prev_ranks']
        }

    except Exception as e:
        logger.error(f"Error generating insurer options: {str(e)}", exc_info=True)
        return {
            'top5': [],
            'top10': [],
            'top20': [],
            'insurer_options': [],
            'current_ranks': {},
            'prev_ranks': {}
        }