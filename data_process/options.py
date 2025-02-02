from typing import List, Dict, Tuple
import time

from collections import defaultdict
from functools import wraps, lru_cache
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY
from data_process.io import load_json
from data_process.mappings import map_insurer

logger = get_logger(__name__)

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


@timer
def get_year_quarter_options(df):
    # Get unique and sorted values in one operation
    unique_quarters = pd.Series(df['year_quarter'].unique()).sort_values()

    # Pre-allocate result list
    result_size = len(unique_quarters)
    quarter_options = [None] * result_size

    # Vectorized operations for extracting year and quarter
    years = unique_quarters.dt.year
    quarters = unique_quarters.dt.quarter

    # Build options list
    for i in range(result_size):
        quarter_str = f"{years[i]}Q{quarters[i]}"
        quarter_options[i] = {'label': quarter_str, 'value': quarter_str}

    return quarter_options


@lru_cache(maxsize=1024)
def cached_map_insurer(insurer: str) -> str:
    """Cached version of map_insurer to avoid repeated mappings"""
    return map_insurer(insurer)


@timer
def get_insurers_and_options(
    df: pd.DataFrame,
    all_metrics: List[str],
    lines: List[str]
) -> List[Dict[str, str]]:
    try:
        # Fast array operations for data processing
        data = df[['year_quarter', 'metric', 'insurer', 'linemain', 'value']].values
        year_quarters = data[:, 0]
        metrics = data[:, 1]
        insurers = data[:, 2]
        linemains = data[:, 3]
        values = data[:, 4].astype(np.float64)

        # Process quarters
        latest_quarter = np.max(year_quarters)
        quarter_mask = year_quarters == latest_quarter
        quarter_metrics = np.unique(metrics[quarter_mask])
        metric_to_use = next(m for m in all_metrics if m in quarter_metrics)

        # Create masks
        final_mask = (
            quarter_mask & 
            (metrics == metric_to_use) & 
            np.isin(linemains, lines) & 
            ~np.isin(insurers, ['total', 'top-5', 'top-10', 'top-20'])
        )

        # Filter and aggregate
        filtered_insurers = insurers[final_mask]
        filtered_values = values[final_mask]

        if len(filtered_insurers) == 0:
            return []

        unique_insurers, inverse_indices = np.unique(filtered_insurers, return_inverse=True)
        aggregated = np.zeros(len(unique_insurers))
        np.add.at(aggregated, inverse_indices, filtered_values)

        # Sort insurers
        sort_indices = np.argsort(-aggregated)
        sorted_insurers = unique_insurers[sort_indices]

        # Optimize result creation
        TOP_OPTIONS = ['top-5', 'top-10', 'top-20']

        # Pre-allocate result list
        result_size = len(TOP_OPTIONS) + len(sorted_insurers)
        result = [None] * result_size

        # Fill TOP_OPTIONS first (they don't need mapping)
        for i, option in enumerate(TOP_OPTIONS):
            result[i] = {'label': cached_map_insurer(option), 'value': option}

        # Fill remaining insurers using cached mapping
        for i, insurer in enumerate(sorted_insurers, len(TOP_OPTIONS)):
            result[i] = {'label': cached_map_insurer(insurer), 'value': insurer}

        return result

    except Exception as e:
        logger.error(f"Error generating insurer options: {str(e)}", exc_info=True)
        return []


@timer
def get_rankings(
    df: pd.DataFrame,
    all_metrics: List[str],
    lines: List[str]
) -> Dict[str, Dict[str, Dict[str, int]]]:
    try:
        filtered_df = df[
            df['insurer'].apply(lambda i: i not in {'total', 'top-5', 'top-10', 'top-20'})
        ]

        metric_to_use = next(m for m in all_metrics if m in filtered_df['metric'].unique())
        logger.debug(f"metric to use {metric_to_use}")
        metric_df = filtered_df[filtered_df['metric'] == metric_to_use]

        quarters = sorted(metric_df['year_quarter'].unique())
        if not quarters:
            return {'current_ranks': {}, 'prev_ranks': {}}

        current_quarter = quarters[-1]
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


def get_insurance_line_options(reporting_form, level=1, indent_char="\u2003"):

    category_structure = load_json(LINES_162_DICTIONARY) if reporting_form == '0420162' else load_json(LINES_158_DICTIONARY)

    def clean_label(label):
        """Remove 'Добровольное' from the label and handle extra spaces"""
        return ' '.join(label.replace('Добровольное', '').split())

    def traverse_categories(code, current_level=0, max_level=None):
        # Check if category exists in structure
        if code not in category_structure:
            return []

        if max_level is not None and current_level > max_level:
            return []

        result = []
        # Add current category
        label = category_structure[code].get('label', f"Category {code}")
        cleaned_label = clean_label(label)
        indentation = indent_char * current_level
        result.append({
            'label': f"{indentation}{cleaned_label}",
            'value': code
        })

        # Add children if within max_level
        if max_level is None or current_level < max_level:
            # Safely get children, defaulting to empty list if none exist
            children = category_structure[code].get('children', [])
            for child in children:
                if child in category_structure:
                    result.extend(traverse_categories(child, current_level + 1, max_level))

        return result

    root = "все линии"
    if root not in category_structure:
        return []

    # Start with root category and traverse
    return traverse_categories(root, 0, level)