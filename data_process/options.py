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