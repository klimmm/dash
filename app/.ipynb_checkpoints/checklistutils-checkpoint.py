# data_utils.py

import dash

import pandas as pd
from typing import List, Dict, Any, Tuple, Se
import json
import re
import os
from functools import lru_cache
import logging

def load_json(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.debug(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {file_path}")
        raise

from typing import Union, List, Optional, Any



def get_immediate_children(category):
    return set(category_structure[category].get('children', []))

def handle_parent_child_selections(selected_categories, category_structure, detailize=False):
    logging.info(f"Starting handle_parent_child_selections with selected categories: {selected_categories}")
    logging.info(f"Detailize flag: {detailize}")
    if not detailize:
        new_selected = set(selected_categories)
        # Remove all descendants if their ancestor is selected
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                descendants = get_all_descendants(category)
                removed_descendants = new_selected.intersection(descendants)
                new_selected.difference_update(removed_descendants)
                if removed_descendants:
                    logging.debug(f"Removed descendants of {category}: {removed_descendants}")
    else:
        new_selected = set()
        # Add children for categories that have them, or keep the category if it's a leaf
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                children = get_immediate_children(category)
                new_selected.update(children)
                logging.info(f"Detailized {category}. Added children: {children}")
            else:
                new_selected.add(category)
                logging.info(f"Category {category} has no children, keeping it as is")

    final_selected = list(new_selected)
    logging.info(f"Final selected categories: {final_selected}")
    return final_selected


DEFAULT_CHECKED_CATEGORIES = ['осаго']


category_structure = load_json('/users/klim/Desktop/dash_inusrance_app/dash-last/constants/modified_insurance_life_comb.json')


import dash_bootstrap_components as dbc
from dash import dcc
from dash import html



#        'options': get_top_level_and_children(category_structure),



# Use the function to get the options
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

def get_categories_by_level(category_structure, level=1):
    """
    Get categories up to specified level of depth, ordered by hierarchy,
    excluding the word 'Добровольное' from labels.

    Args:
        category_structure (dict): Dictionary of categories with their metadata and children
        level (int): Depth level to traverse (0 for top level only, 1 for top + children, etc.)

    Returns:
        list: List of dictionaries containing category labels and values, ordered by hierarchy level
    """
    def find_top_level():
        return [code for code, category in category_structure.items()
                if not any(code in cat.get('children', [])
                          for cat in category_structure.values())]

    def get_level_categories(parent_codes, current_level=0, max_level=1):
        if current_level > max_level:
            return []

        # Get direct children of current level
        current_level_categories = []
        for parent in parent_codes:
            children = category_structure[parent].get('children', [])
            current_level_categories.extend(children)

        # If we've reached desired level or there are no more children, return
        if current_level == max_level or not current_level_categories:
            return [current_level_categories]

        # Recursively get next levels
        next_levels = get_level_categories(
            current_level_categories,
            current_level + 1,
            max_level
        )

        return [current_level_categories] + next_levels

    def clean_label(label):
        """Remove 'Добровольное' from the label and handle extra spaces"""
        return ' '.join(label.replace('Добровольное', '').split())

    # Get top-level categories
    top_level = find_top_level()

    # Initialize result with top level
    all_categories_by_level = [top_level]

    # If level > 0, get additional levels
    if level > 0:
        additional_levels = get_level_categories(top_level, 0, level - 1)
        all_categories_by_level.extend(additional_levels)

    # Convert to list of dictionaries, maintaining order and cleaning labels
    result = []
    for level_categories in all_categories_by_level:
        for code in level_categories:
            original_label = category_structure[code].get('label', f"Category {code}")
            cleaned_label = clean_label(original_label)
            result.append({
                'label': cleaned_label,
                'value': code
            })

    return resul
# Dictionary mapping dropdown IDs to their configurations
DROPDOWN_CONFIG = {
    'category-dropdown': {
        'label': False,
        'options': get_categories_by_level(category_structure, level=3),
        'value': DEFAULT_CHECKED_CATEGORIES,
        'multi': True,
        'placeholder': "Select categories..."

    }
}


def create_dropdown_component(id, options=None, xs=12, sm=8, md=6):
    if id not in DROPDOWN_CONFIG:
        raise ValueError(f"No configuration found for dropdown id: {id}")

    config = DROPDOWN_CONFIG[id]
    return dbc.Col([
        html.Label(config.get('label', ''), className="filter-label"),

        dcc.Dropdown(
            id=id,
            options=config['options'],
            value=config['value'],
            multi=config.get('multi', False),
            placeholder=config.get('placeholder', ''),
            clearable=config.get('clearable', True),
            className="filter-dropdown"
        )
    ], xs=xs, sm=sm, md=md, className="p-0")




