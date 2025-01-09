import pandas as pd
from typing import Optional, List, Any, Se
import logging
import json
from constants.mapping import map_insurer
from data_process.data_utils import default_insurer_options
from logging_config import setup_logging, set_debug_level, DebugLevels, get_logger, debug_log, intensive_debug_log, custom_profile

logger = get_logger(__name__)


def get_insurer_options(df: pd.DataFrame, main_insurer: List[str], top_n_list: List[int], selected_metrics: List[str], base_metrics: Set[str]):

    #logger.debug(f"Input DataFrame shape: {df.shape}")
    #main_insurer = [item for sublist in main_insurer for item in (sublist if isinstance(sublist, list) else [sublist])]
    logger.debug(f"get_insurer_options len of insurer unique: {len(df['insurer'].unique().tolist())}")


    if len(df['insurer'].unique().tolist()) <= 1:
        insurers_options = compare_options = default_insurer_options
        logger.debug(f"insurer_options: {insurers_options}")

    else:

        if selected_metrics:
            ranking_metric = selected_metrics[0] if selected_metrics[0] in df['metric'].unique().tolist() else df['metric'].unique()[0]
        elif len(df['metric'].unique()) > 0:
            ranking_metric = df['metric'].unique()[0]
        else:
            ranking_metric = 'direct_premiums'  # or handle this case as appropriate for your application

        logger.debug(f"ranking_metric: {ranking_metric}")
        logger.debug(f"unique_metric: {df['metric'].unique().tolist()}")

        benchmark_insurers = [f"top-{n}-benchmark" for n in top_n_list]
        top_n_rows = [f"top-{n}" for n in top_n_list]
        total_rows = ['total']
        others_rows = ['others']

        #logger.debug(f"df unique linemain: {df['linemain'].unique()}")

        insurers_to_exclude = benchmark_insurers + top_n_rows + total_rows + others_rows

        group_columns = [col for col in df.columns if col not in ['linemain', 'value']]
        df = df.groupby(group_columns)['value'].sum().reset_index()
        df['linemain'] = 'all_lines'

        filtered_df = df[
            (~df['insurer'].isin(insurers_to_exclude)) &
            (df['metric'] == ranking_metric) &
            (df['linemain'] == 'all_lines')
        ]
        filtered_df = filtered_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)
        all_insurers_original = list(dict.fromkeys(filtered_df['insurer']))  # Preserve order and remove duplicates

        end_quarter_dt = df['year_quarter'].max()
        end_quarter_df = filtered_df[filtered_df['year_quarter'] == end_quarter_dt]

        #logger.debug(f"df unique insurers: {end_quarter_df['insurer'].unique()}")

        #end_quarter_df = end_quarter_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)
        insurers_end_quarter = list(dict.fromkeys(end_quarter_df['insurer']))  # Preserve order and remove duplicates
        insurers_not_in_end_quarter = [insurer for insurer in all_insurers_original if insurer not in insurers_end_quarter]

        top5_insurers_options = end_quarter_df.groupby('insurer')['value'].sum().nlargest(5).index.tolist()
        insurers_not_in_top5 = [insurer for insurer in insurers_end_quarter if insurer not in top5_insurers_options]

        insurers_options = [{'label': map_insurer(insurer), 'value': insurer}
                             for insurer in (top5_insurers_options + total_rows + top_n_rows + insurers_not_in_top5 + insurers_not_in_end_quarter)]


        compare_options = [{'label': map_insurer(insurer), 'value': insurer}
                                for insurer in (top5_insurers_options + total_rows + others_rows + benchmark_insurers + top_n_rows + insurers_not_in_top5 + insurers_not_in_end_quarter)
                                if not main_insurer or insurer not in main_insurer
        ]


    #logger.debug(f"end_quarter: {end_quarter}")
    logger.debug(f"df unique insurers: {df['insurer'].unique()}")


    return insurers_options, compare_options



def get_insurers_for_ranking(df: pd.DataFrame, number_of_insurers: int, top_n_list: List[int], selected_metrics: List[str], base_metrics: Set[str]):

    logger.debug(f"number of insurers {number_of_insurers}")

    if len(df['insurer'].unique().tolist()) <= 1:
        top_n_insurers = []
    else:

        benchmark_insurers = [f"top-{n}-benchmark" for n in top_n_list]
        top_n_rows = [f"top-{n}" for n in top_n_list]
        total_rows = ['total']
        others_rows = ['others']

        #logger.debug(f"df unique linemain: {df['linemain'].unique()}")

        insurers_to_exclude = benchmark_insurers + top_n_rows + total_rows + others_rows

        if selected_metrics:
            ranking_metric = selected_metrics[0]
        elif len(df['metric'].unique()) > 0:
            ranking_metric = df['metric'].unique()[0]
        else:
            ranking_metric = 'direct_premiums'  # or handle this case as appropriate for your application

        logger.debug(f"selected_metrics of insurers {selected_metrics}")
        logger.debug(f"metric unique{df['metric'].unique()}")
        logger.debug(f"ranking_metric {ranking_metric}")
        logger.debug(f"insurers of unique {df['insurer'].unique()}")
        logger.debug(f"linem of unique {df['linemain'].unique()}")
        logger.debug(f"year_quarter of unique {df['year_quarter'].unique()}")


        end_quarter_dt = df['year_quarter'].max()
        end_quarter_df = df[
            (~df['insurer'].isin(insurers_to_exclude)) &
            (df['year_quarter'] == end_quarter_dt) &
            (df['metric'] == ranking_metric) &
            (df['linemain'] == 'all_lines')
        ]
        end_quarter_df = end_quarter_df.sort_values(['value'], ascending=[False]).reset_index(drop=True)
        logger.debug(f"insurers of unique after {end_quarter_df['insurer'].unique()}")

        top_n_insurers = end_quarter_df['insurer'].head(number_of_insurers).tolist()

    logger.debug(f"top_n_insurersget_insurers_for_ranking {top_n_insurers}")

    return top_n_insurers