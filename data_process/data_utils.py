# data_process.data_utils.py

import pandas as pd
import json
import re
import os
from typing import List, Dict
from config.main_config import LINES_162_DICTIONARY, INSURERS_DICTIONARY, LINES_158_DICTIONARY
from config.logging_config import get_logger
logger = get_logger(__name__)

def load_json(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        raise

category_structure_162 = load_json(LINES_162_DICTIONARY)
category_structure_158 = load_json(LINES_158_DICTIONARY)


def get_categories_by_level(category_structure, level=1, indent_char="  "):
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
            # Only traverse existing children
            for child in children:
                if child in category_structure:  # Extra safety check
                    result.extend(traverse_categories(child, current_level + 1, max_level))

        return result

    # Verify root category exists
    root = "все линии"
    if root not in category_structure:
        return []  # Return empty list if root category doesn't exist

    # Start with root category and traverse
    return traverse_categories(root, 0, level)


def handle_parent_child_selections(selected_categories, category_structure, detailize=False):
    logger.info(f"Starting handle_parent_child_selections with selected categories: {selected_categories}")
    logger.info(f"Detailize flag: {detailize}")

    def get_immediate_children(category):
        return set(category_structure[category].get('children', []))

    def get_all_descendants(category):
        descendants = set()
        to_process = get_immediate_children(category)

        while to_process:
            current = to_process.pop()
            descendants.add(current)
            # Add children of current category to processing queue
            if current in category_structure:
                to_process.update(get_immediate_children(current))

        return descendants

    if not detailize:
        new_selected = set(selected_categories)
        # Remove all descendants if their ancestor is selected
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                descendants = get_all_descendants(category)
                removed_descendants = new_selected.intersection(descendants)
                new_selected.difference_update(removed_descendants)
                if removed_descendants:
                    logger.debug(f"Removed descendants of {category}: {removed_descendants}")
    else:
        new_selected = set()
        # Add children for categories that have them, or keep the category if it's a leaf
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                children = get_immediate_children(category)
                new_selected.update(children)
                logger.info(f"Detailized {category}. Added children: {children}")
            else:
                new_selected.add(category)
                logger.info(f"Category {category} has no children, keeping it as is")

    final_selected = list(new_selected)
    logger.info(f"Final selected categories: {final_selected}")
    return final_selected


def save_df_to_csv(df, filename, max_rows=500):
    """
    Save a DataFrame to two CSV files - one with random rows and one with the first N rows.

    Args:
        df (pd.DataFrame): The DataFrame to save
        filename (str): The base name of the file to save to
        max_rows (int): The maximum number of rows to save (default: 1000)
    """
    output_dir = './outputs/intermediate'
    os.makedirs(output_dir, exist_ok=True)

    n_rows = min(max_rows, len(df))

    # Create both samples
    df_to_save = df.sample(n=n_rows)
    df_to_save_ordered = df.head(n=n_rows)

    # Generate filenames
    base_name = os.path.splitext(filename)[0]  # Remove extension if presen
    full_path_sample = os.path.join(output_dir, f"{base_name}_random.csv")
    full_path_ordered = os.path.join(output_dir, f"{base_name}_first.csv")

    # Save both files
    df_to_save.to_csv(full_path_sample, index=False)
    df_to_save_ordered.to_csv(full_path_ordered, index=False)

    logger.debug(f"Saved {n_rows} random rows to {full_path_sample}")
    logger.debug(f"Saved {n_rows} ordered rows to {full_path_ordered}")


def log_dataframe_info(df: pd.DataFrame, step_name: str):
    logger.debug(f"--- {step_name} ---")
    logger.debug(f"DataFrame shape: {df.shape}")
    logger.debug(f"Columns: {df.columns.tolist()}")
    for column in df.columns:
        unique_values = df[column].nunique()
        logger.debug(f"Unique values in '{column}': {unique_values}")
        if unique_values < 10:
            logger.debug(f"Unique values: {df[column].unique().tolist()}")
    logger.debug(f"First 5 rows:\n{df.head().to_string()}")
    logger.debug("-------------------")


def map_insurer(insurer_code: str) -> str:
    # Load the insurer mapping from the JSON file
    with open(INSURERS_DICTIONARY, 'r', encoding='utf-8') as f:
        INSURER_MAPPING = {item['reg_number']: item['short_name'] for item in json.load(f)}

    INSURER_MAPPING['total'] = 'Весь рынок'
    INSURER_MAPPING['others'] = 'Остальные'

    # Regular expressions to match 'top-X' and 'top-Y-benchmark' patterns
    top_pattern = re.compile(r'^top-(\d+)$')
    benchmark_pattern = re.compile(r'^top-(\d+)-benchmark$')

    # Check for 'top-X' pattern
    top_match = top_pattern.match(insurer_code)
    if top_match:
        n = top_match.group(1)
        return f'Топ {n}'

    # Check for 'top-Y-benchmark' pattern
    benchmark_match = benchmark_pattern.match(insurer_code)
    if benchmark_match:
        n = benchmark_match.group(1)
        return f'Топ {n} Бенчмарк'

    # Fallback to the existing mapping or return the original insurer_code
    return INSURER_MAPPING.get(insurer_code, insurer_code)


def map_line(line_code):
    # Load first JSON file
    with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data1 = json.load(f)

    # Load second JSON file
    with open(LINES_158_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data2 = json.load(f)

    # Combine the two dictionaries
    # If there are duplicate keys, the second file will override the firs
    combined_data = {**insurance_data1, **insurance_data2}

    # Create the mapping dictionary
    LINE_MAPPING = {category: data['label'] for category, data in combined_data.items()}

    # Handle both list and single inputs
    if isinstance(line_code, list):
        return [LINE_MAPPING.get(code, code) for code in line_code]

    return LINE_MAPPING.get(line_code, line_code)


def format_period(quarter_str: str, period_type: str = '', comparison: bool = False) -> str:
    """Format quarter string into readable period format"""
    if not quarter_str or len(quarter_str) != 6:
        raise ValueError("Quarter string must be in format 'YYYYQ1', e.g. '2024Q1'")

    year_short = quarter_str[2:4]
    quarter = quarter_str[5]

    period_formats = {
        'ytd': {
            True: lambda q, y: f'{y}',
            False: lambda q, y: {
                '1': f'3 мес. {y}',
                '2': f'1 пол. {y}',
                '3': f'9 мес. {y}',
                '4': f'12 мес. {y}'
            }[q]
        },
        '': {
            True: lambda q, y: f'{y}' if period_type in ['yoy_y', 'yoy_q'] else f'{q}кв.',
            False: lambda q, y: f'{q} кв. {y}'
        }
    }

    format_func = period_formats.get(period_type, period_formats[''])[comparison]
    return format_func(quarter, year_short)


def get_comparison_quarters(columns: List[str]) -> Dict[str, str]:

    """Get mapping of quarters to their comparison quarters"""
    quarter_pairs = {}
    for col in columns:
        if 'q_to_q_change' not in col:
            continue

        current_quarter = next((part for part in col.split('_') if 'Q' in part and len(part) >= 5), None)
        if not current_quarter:
            continue

        year = current_quarter[:4]
        q_num = current_quarter[5]

        year_ago = f"{int(year)-1}Q{q_num}"
        prev_q = f"{year}Q{int(q_num)-1}" if q_num != '1' else f"{int(year)-1}Q4"

        quarter_pairs[current_quarter] = (
            year_ago if any(year_ago in c for c in columns if '_q_to_q_change' not in c)
            else prev_q if any(prev_q in c for c in columns if '_q_to_q_change' not in c)
            else None
        )

    return {k: v for k, v in quarter_pairs.items() if v}