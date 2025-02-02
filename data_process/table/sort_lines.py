import json
from typing import Dict
import pandas as pd


def build_label_to_key_map(data: Dict) -> Dict[str, str]:
    """Create mapping from labels to keys"""
    label_map = {}
    for key, value in data.items():
        if isinstance(value, dict) and 'label' in value:
            label_map[value['label']] = key
    return label_map


def get_path_depth(data: Dict, key: str) -> int:
    """Get depth of a key in hierarchy"""
    depth = 0
    current = key
    while True:
        parent = None
        for potential_parent, node_data in data.items():
            if 'children' in node_data and current in node_data['children']:
                parent = potential_parent
                depth += 1
                break
        if not parent:
            break
        current = parent
    return depth


def sort_and_indent_df(df: pd.DataFrame, json_str: str) -> pd.DataFrame:
    """
    Sort DataFrame rows according to insurance hierarchy and add indentation
    Args:
        df: DataFrame with 'linemain' column containing insurance labels
        json_str: JSON string containing insurance hierarchy data
    Returns:
        DataFrame: Sorted DataFrame with indented labels
    """
    data = json.loads(json_str)
    label_to_key = build_label_to_key_map(data)

    # Create a mapping of labels to their order and depth
    label_order = {}
    order_idx = 0

    def process_node(key, depth=0):
        nonlocal order_idx
        if key in data:
            label = data[key]['label']
            label_order[label] = (order_idx, depth)
            order_idx += 1
            if 'children' in data[key]:
                for child in data[key]['children']:
                    process_node(child, depth + 1)

    # Start processing from root
    process_node('все линии')

    # Create sorting key function
    def get_sort_key(label):
        return label_order.get(label, (float('inf'), 0))

    # Sort DataFrame and get depths
    df = df.copy()
    df['sort_key'] = df['linemain'].apply(lambda x: get_sort_key(x))
    df = df.sort_values(by='sort_key')

    # Get the minimum depth present in the actual data
    min_depth = min(row['sort_key'][1] for _, row in df.iterrows() if row['sort_key'][1] != float('inf'))

    # Add indentation based on relative depth from minimum present
    df['linemain'] = df.apply(
        lambda row: "---" * (row['sort_key'][1] - min_depth if row['sort_key'][1] != float('inf') else 0) + row['linemain'], 
        axis=1
    )

    # Clean up
    df = df.drop(columns=['sort_key'])
    return df