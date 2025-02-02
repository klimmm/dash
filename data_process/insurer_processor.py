import json
import re
import time
from functools import wraps, lru_cache
from typing import List, Dict, Set

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.default_values import DEFAULT_INSURER
from config.main_config import INSURERS_DICTIONARY

logger = get_logger(__name__)

class InsurerDataProcessor:
    # Class-level attributes
    DEFAULT_INSURER = DEFAULT_INSURER
    insurers_dictionary_path = INSURERS_DICTIONARY

    def __init__(self, df: pd.DataFrame = None):
        """
        Optionally initialize with a DataFrame if methods require it.
        For methods like map_insurer that do not require a DataFrame,
        you can call them directly as static methods.
        """
        self.df = df

    @staticmethod
    def timer(func):
        """A simple timer decorator to log execution time."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(f"{func.__name__} took {(end - start) * 1000:.2f}ms to execute")
            return result
        return wrapper

    @staticmethod
    def map_insurer(insurer_code: str) -> str:
        """
        Map an insurer code to its human-readable name using a JSON dictionary.
        Uses the dictionary defined by the class attribute `insurers_dictionary_path`.
        Also handles special cases like 'top-X' and 'top-X-benchmark'.
        """
        with open(InsurerDataProcessor.insurers_dictionary_path, 'r', encoding='utf-8') as f:
            insurer_mapping = {item['reg_number']: item['short_name'] for item in json.load(f)}

        insurer_mapping['total'] = 'Весь рынок'
        insurer_mapping['others'] = 'Остальные'

        # Regular expressions to match special patterns
        top_pattern = re.compile(r'^top-(\d+)$')
        benchmark_pattern = re.compile(r'^top-(\d+)-benchmark$')

        top_match = top_pattern.match(insurer_code)
        if top_match:
            n = top_match.group(1)
            return f'Топ {n}'

        benchmark_match = benchmark_pattern.match(insurer_code)
        if benchmark_match:
            n = benchmark_match.group(1)
            return f'Топ {n} Бенчмарк'

        return insurer_mapping.get(insurer_code, insurer_code)

    @staticmethod
    @lru_cache(maxsize=1024)
    def cached_map_insurer(insurer: str) -> str:
        """Cached version of map_insurer to avoid repeated file I/O."""
        return InsurerDataProcessor.map_insurer(insurer)

    @timer
    def get_insurer_options(self, all_metrics: List[str], lines: List[str]) -> List[Dict[str, str]]:
        """
        Returns a list of dictionaries with 'label' and 'value' keys for insurer options.
        This method requires that the instance was initialized with a DataFrame.
        """
        try:
            data = self.df[['year_quarter', 'metric', 'insurer', 'linemain', 'value']].values
            year_quarters = data[:, 0]
            metrics = data[:, 1]
            insurers = data[:, 2]
            linemains = data[:, 3]
            values = data[:, 4].astype(np.float64)

            latest_quarter = np.max(year_quarters)
            quarter_mask = year_quarters == latest_quarter
            quarter_metrics = np.unique(metrics[quarter_mask])
            metric_to_use = next(m for m in all_metrics if m in quarter_metrics)

            final_mask = (
                quarter_mask &
                (metrics == metric_to_use) &
                np.isin(linemains, lines) &
                ~np.isin(insurers, ['total', 'top-5', 'top-10', 'top-20'])
            )
            filtered_insurers = insurers[final_mask]
            filtered_values = values[final_mask]

            if len(filtered_insurers) == 0:
                return []

            unique_insurers, inverse_indices = np.unique(filtered_insurers, return_inverse=True)
            aggregated = np.zeros(len(unique_insurers))
            np.add.at(aggregated, inverse_indices, filtered_values)
            sort_indices = np.argsort(-aggregated)
            sorted_insurers = unique_insurers[sort_indices]

            TOP_OPTIONS = ['top-5', 'top-10', 'top-20']
            result_size = len(TOP_OPTIONS) + len(sorted_insurers)
            result = [None] * result_size

            # Fill in the TOP_OPTIONS first
            for i, option in enumerate(TOP_OPTIONS):
                result[i] = {'label': self.cached_map_insurer(option), 'value': option}
            # Fill in the remaining insurers
            for i, insurer in enumerate(sorted_insurers, len(TOP_OPTIONS)):
                result[i] = {'label': self.cached_map_insurer(insurer), 'value': insurer}

            return result

        except Exception as e:
            logger.error(f"Error generating insurer options: {str(e)}", exc_info=True)
            return []

    @timer
    def get_consistently_top_insurers(self, all_metrics: List[str], lines: List[str]) -> Dict[str, Set[str]]:
        """
        Returns a dictionary mapping 'top_5', 'top_10', and 'top_20' to sets of insurers
        that are consistently top performers for each given line.
        """
        try:
            logger.debug("Calculating consistently top insurers.")
            data = self.df[['year_quarter', 'metric', 'insurer', 'linemain', 'value']].values
            year_quarters, metrics, insurers, linemains, values = data.T
            values = values.astype(np.float64)

            latest_quarter = np.max(year_quarters)
            unique_metrics = np.unique(metrics)
            metric_to_use = next(m for m in all_metrics if m in unique_metrics)

            quarter_mask = year_quarters == latest_quarter
            metric_mask = metrics == metric_to_use
            exclude_mask = np.isin(insurers, ['total', 'top-5', 'top-10', 'top-20'])
            base_mask = quarter_mask & metric_mask & ~exclude_mask

            top_insurers_by_line = {line: {'top_5': set(), 'top_10': set(), 'top_20': set()} for line in lines}

            for line in lines:
                line_mask = base_mask & (linemains == line)
                line_insurers = insurers[line_mask]
                line_values = values[line_mask]
                if len(line_insurers) > 0:
                    sort_indices = np.argsort(-line_values)
                    sorted_insurers = line_insurers[sort_indices]
                    top_insurers_by_line[line]['top_5'] = set(sorted_insurers[:5])
                    top_insurers_by_line[line]['top_10'] = set(sorted_insurers[:10])
                    top_insurers_by_line[line]['top_20'] = set(sorted_insurers[:20])

            consistent_top_performers = {
                ranking: set.intersection(*(
                    top_insurers_by_line[line][ranking]
                    for line in lines
                    if top_insurers_by_line[line][ranking]
                )) if all(top_insurers_by_line[line][ranking] for line in lines) else set()
                for ranking in ['top_5', 'top_10', 'top_20']
            }
            logger.debug("Successfully calculated top insurers.")
            return consistent_top_performers

        except Exception as e:
            logger.error(f"Error finding consistently top insurers: {str(e)}", exc_info=True)
            return {'top_5': set(), 'top_10': set(), 'top_20': set()}

    @timer
    def get_rankings(self, all_metrics: List[str], lines: List[str]) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Returns ranking dictionaries for the current and previous quarters.
        The returned structure is:
            {
              'current_ranks': { line: { insurer: rank, ... } },
              'prev_ranks': { line: { insurer: rank, ... } }
            }
        """
        try:
            filtered_df = self.df[self.df['insurer'].apply(
                lambda i: i not in {'total', 'top-5', 'top-10', 'top-20'}
            )]

            metric_to_use = next(m for m in all_metrics if m in filtered_df['metric'].unique())
            logger.debug(f"metric to use {metric_to_use}")
            metric_df = filtered_df[filtered_df['metric'] == metric_to_use]

            quarters = sorted(metric_df['year_quarter'].unique())
            if not quarters:
                return {'current_ranks': {}, 'prev_ranks': {}}

            current_quarter = quarters[-1]
            prev_quarter = quarters[-2] if len(quarters) > 1 else None

            rankings = {'current_ranks': {}, 'prev_ranks': {}}

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
                            rankings[period][line_id] = dict(
                                zip(
                                    line_df.sort_values('value', ascending=False)['insurer'].astype(str),
                                    range(1, len(line_df) + 1)
                                )
                            )
            return rankings

        except Exception as e:
            logger.error(f"Error generating rankings: {str(e)}", exc_info=True)
            return {'current_ranks': {}, 'prev_ranks': {}}

    @timer
    def filter_by_insurer(
        self,
        selected_metrics: List[str],
        selected_insurers: List[str] = None,
        top_n_list: List[int] = [5, 10, 20],
        split_mode: str = 'line'
    ) -> pd.DataFrame:
        """Optimized version of filter_by_insurer"""
        try:
            # Early validation
            if self.df.empty or len(self.df['insurer'].unique()) <= 1:
                return pd.DataFrame()
    
            # Cache frequently accessed data
            df = self.df
            excluded_insurers = ['top-5', 'top-10', 'top-20', 'total']
            latest_quarter = df['year_quarter'].max()
            unique_metrics = df['metric'].unique()
            ranking_metric = next((m for m in selected_metrics if m in unique_metrics), unique_metrics[0])
            
            # Pre-filter the latest data once
            latest_mask = (
                (df['year_quarter'] == latest_quarter) & 
                (~df['insurer'].isin(excluded_insurers)) & 
                (df['metric'] == ranking_metric)
            )
            latest_df = df[latest_mask]
            
            # Handle top-N filtering
            number_of_insurers = next(
                (n for n in [5, 10, 20] if f'top-{n}' in (selected_insurers or [])),
                0
            )
            
            specific_insurers = [
                ins for ins in (selected_insurers or [])
                if not ins.startswith('top-') and ins not in excluded_insurers
            ]
    
            # Optimize split_mode handling
            if split_mode == 'insurer':
                if number_of_insurers:
                    total_values = (
                        latest_df.groupby('insurer')['value']
                        .sum()
                        .nlargest(number_of_insurers)
                        .index
                    )
                    filtered_insurers = list(set(total_values) | set(specific_insurers))
                else:
                    filtered_insurers = specific_insurers
    
                if filtered_insurers:
                    mask = df['insurer'].isin(filtered_insurers + excluded_insurers)
                    df = df[mask]
            else:  # line mode
                line_ids = df['linemain'].unique()
                if number_of_insurers:
                    # Compute top insurers per line in one pass
                    top_insurers_by_line = {
                        line: set(latest_df[latest_df['linemain'] == line]
                            .nlargest(number_of_insurers, 'value')['insurer'])
                        for line in line_ids
                    }
                else:
                    top_insurers_by_line = {line: set() for line in line_ids}
    
                # Create a combined mask for all lines
                final_mask = pd.Series(False, index=df.index)
                for line_id in line_ids:
                    line_insurers = top_insurers_by_line[line_id] | set(specific_insurers)
                    if line_insurers:
                        line_mask = (
                            (df['linemain'] == line_id) & 
                            (df['insurer'].isin(list(line_insurers) + excluded_insurers))
                        )
                        final_mask = final_mask | line_mask
                
                if not final_mask.empty:
                    df = df[final_mask]
    
            # Handle top_n_list filtering
            if 999 not in top_n_list:
                df = df[df['insurer'] != 'total']
                
            numbers_to_filter = [n for n in [5, 10, 20] if n not in top_n_list]
            if numbers_to_filter:
                pattern = '|'.join(f'top-{n}' for n in numbers_to_filter)
                df = df[~df['insurer'].str.match(pattern)]
    
            # Create categories for sorting
            latest_data = (
                latest_df.groupby('insurer')['value']
                .sum()
                .sort_values(ascending=False)
            )
            full_insurer_categories = latest_data.index.tolist() + excluded_insurers
            
            ordered_metrics = [m for m in selected_metrics if m in unique_metrics]
            remaining_metrics = [m for m in unique_metrics if m not in selected_metrics]
            full_metric_categories = ordered_metrics + remaining_metrics
    
            # Apply categories and sort
            df['insurer'] = pd.Categorical(df['insurer'], categories=full_insurer_categories, ordered=True)
            df['metric'] = pd.Categorical(df['metric'], categories=full_metric_categories, ordered=True)
            df = df.sort_values(['metric', 'insurer'])
    
            # Convert back to strings explicitly before returning
            df['insurer'] = df['insurer'].astype(str)
            df['metric'] = df['metric'].astype(str)
            
            return df
    
        except Exception as e:
            logger.error(f"Error filtering by insurer: {str(e)}", exc_info=True)
            return pd.DataFrame()