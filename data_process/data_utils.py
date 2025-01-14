# data_process.data_utils.py

from dash import dcc
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple, Set, Union, Optional
import json
import re
import os
import plotly.graph_objects as go

from config.logging_config import get_logger
from config.main_config import LINES_162_DICTIONARY, INSURERS_DICTIONARY, LINES_158_DICTIONARY


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


def strip_metric_suffixes(metric: str) -> str:
    suffixes_to_remove = [
        '_market_share_q_to_q_change',
        '_q_to_q_change',
        '_market_share'
    ]

    for suffix in suffixes_to_remove:
        if metric.endswith(suffix):
            logger.debug(f"Stripping suffix {suffix} from {metric}")
            return metric[:-len(suffix)]
    return metric


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


def get_top_level_and_children(category_structure):
    # First, identify top-level categories
    top_level = [code for code, category in category_structure.items()
                 if not any(code in cat.get('children', []) for cat in category_structure.values())]

    # Then, get these categories and their direct children
    options = []

    for code, category in category_structure.items():
        if (code in top_level or
            any(code in category_structure[parent].get('children', []) for parent in top_level) or
            any(code in category_structure[child].get('children', [])
                for parent in top_level
                for child in category_structure[parent].get('children', []))):
            options.append({'label': category.get('label', f"Category {code}"), 'value': code})

    return options


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


def get_immediate_children(category):
    return set(category_structure[category].get('children', []))


def handle_parent_child_selections(selected_categories, category_structure, detailize=False):
    logger.info(f"Starting handle_parent_child_selections with selected categories: {selected_categories}")
    logger.info(f"Detailize flag: {detailize}")
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


def get_required_metrics(
    selected_metrics: List[str],
    calculated_metrics: Dict[str, List[str]],
    premium_loss_selection: Optional[List[str]] = None,
    base_metrics: Optional[Set[str]] = None
) -> Set[str]:
    logger.debug("Starting get_required_metrics function")

    def strip_metric_suffixes(metric: str) -> str:
        suffixes_to_remove = [
            '_market_share_q_to_q_change',
            '_q_to_q_change',
            '_market_share'
        ]

        for suffix in suffixes_to_remove:
            if metric.endswith(suffix):
                logger.debug(f"Stripping suffix {suffix} from {metric}")
                return metric[:-len(suffix)]
        return metric

    def update_required_metrics(selected_metrics, calculated_metrics, base_metrics):
        # First, strip suffixes from selected metrics
        cleaned_metrics = [strip_metric_suffixes(metric) for metric in selected_metrics]
        logger.debug(f"Cleaned metrics after stripping suffixes: {cleaned_metrics}")

        required_metrics = set(cleaned_metrics)
        metrics_to_process = list(cleaned_metrics)
        processed_metrics = set()

        while metrics_to_process:
            current_metric = metrics_to_process.pop(0)
            if current_metric in processed_metrics:
                continue

            processed_metrics.add(current_metric)
            logger.debug(f"Processing metric: {current_metric}")

            for calc_metric, base_metrics_for_calc in calculated_metrics.items():
                if calc_metric == current_metric:  # Simplified check
                    logger.debug(f"Found calc_metric: {calc_metric}")
                    new_metrics = set(base_metrics_for_calc) - required_metrics
                    logger.debug(f"new_metrics: {new_metrics}")

                    required_metrics.update(new_metrics)
                    metrics_to_process.extend(new_metrics)

            logger.debug(f"Current required_metrics: {required_metrics}")
            logger.debug(f"Metrics left to process: {metrics_to_process}")

        return required_metrics

    required_metrics = update_required_metrics(selected_metrics, calculated_metrics, base_metrics)

    if premium_loss_selection:
        if 'direct' not in premium_loss_selection:
            required_metrics.difference_update(['direct_premiums', 'direct_losses'])
        if 'inward' not in premium_loss_selection:
            required_metrics.difference_update(['inward_premiums', 'inward_losses'])

    logger.debug(f"List of required metrics: {required_metrics}")
    logger.debug("Finished get_required_metrics function")
    required_metrics = list(required_metrics)
    logger.debug(f"List of required metrics: {required_metrics}")

    return required_metrics


def process_inputs(
    primary_y_metric,
    secondary_y_metric,
    main_insurer,
    compare_insurers,
    x_column, series_column, group_column
):
    def ensure_list(value):
        if value is None:
            return []
        return [value] if isinstance(value, str) else list(value) if value else []
    primary_y_metric = ensure_list(primary_y_metric)
    secondary_y_metric = ensure_list(secondary_y_metric)

    chart_selected_metric = [m for m in (primary_y_metric + secondary_y_metric) if m]
    table_selected_metric = ensure_list(primary_y_metric)
    main_insurer = ensure_list(main_insurer)
    compare_insurers = ensure_list(compare_insurers)
    selected_insurers = ensure_list(main_insurer) + ensure_list(compare_insurers)
    chart_columns=[x_column, series_column, group_column]

    return primary_y_metric, secondary_y_metric, chart_selected_metric, table_selected_metric, main_insurer, compare_insurers, selected_insurers, chart_columns


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


def print_dataframe_info(df: pd.DataFrame, stage: str = ""):
    logger.debug(f"DataFrame Info - {stage}")
    logger.debug("Column Names:")
    for col in df.columns:
        logger.debug(f"- {col}")
    logger.debug("=" * 50)

    logger.debug("Data Types:")
    logger.debug(df.dtypes)
    logger.debug("=" * 50)

    for col in df.columns:
        unique_values = df[col].unique()
        logger.debug(f"{col}: {len(unique_values)} unique values")
        logger.debug(f"  Values: {unique_values}")
    logger.debug("=" * 50)


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


def load_and_preprocess_data(file_path):

    logger.debug(f"Starting to load and preprocess data from {file_path}")

    dtype_dict = {
    'datatypec': 'object',
    'linemain': 'object',
    'insurer': 'object',
    'value': 'float64'
    }

    try:
        df = pd.read_csv(file_path, dtype=dtype_dict, parse_dates=['year_quarter'])
        print(f"Data loaded: {len(df)} rows x {len(df.columns)} columns")

        # Add prints before each preprocessing step
        df['metric'] = df['metric'].fillna(0)

        df = df.sort_values('year_quarter', ascending=True)

        return df

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise


insurer_data = load_json(INSURERS_DICTIONARY)
default_insurer_options = [{'label': item['short_name'], 'value': item['reg_number']} for item in insurer_data]
default_insurer_options.append({'label': 'Всего по рынку', 'value': 'total'})
default_insurer_options.append({'label': 'Остальные', 'value': 'others'})
insurer_name_map = {item['reg_number']: item['short_name'] for item in insurer_data}
default_benchmark_options = [{'label': 'Остальные', 'value': 'others'}, {'label': 'Топ-5', 'value': 'top-5'}]


def create_year_quarter_options(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Create year-quarter options efficiently."""
    # Extract unique periods once
    unique_periods = pd.PeriodIndex(df['year_quarter'].dt.to_period('Q')).unique()

    # Create options in a single list comprehension
    options = [
        {
            'label': period.strftime('%YQ%q'),
            'value': period.strftime('%YQ%q')
        }
        for period in unique_periods
    ]

    return options


category_structure_162 = load_json(LINES_162_DICTIONARY)

category_structure_158 = load_json(LINES_158_DICTIONARY)


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

def parse_title_text(title_text: str) -> Tuple[str, List[str]]:
    """
    Parse title text to separate main title and subtitles.

    Args:
        title_text: Original title text with HTML spans

    Returns:
        Tuple of (main_title, list_of_subtitles)
    """
    if not title_text:
        return "", []

    # Split by <br> or <br/> tags
    parts = re.split(r'<br\s*/?>', title_text)

    # First part is the main title
    main_title = parts[0] if parts else ""

    # Extract subtitles from spans
    subtitles = []
    span_pattern = re.compile(r"<span[^>]*>(.*?)</span>")

    for part in parts[1:]:
        match = span_pattern.search(part)
        if match:
            subtitle = match.group(1)
            subtitles.append(subtitle)

    return main_title, subtitles


def extract_chart_structure(figure: Union[dict, go.Figure]) -> Dict[str, Any]:
    """
    Extract and analyze the hierarchical structure of the chart.
    """
    # Convert figure to dict if it's a Figure objec
    fig_dict = figure if isinstance(figure, dict) else figure.to_dict()

    # Initialize structure containers
    groups_structure = defaultdict(lambda: defaultdict(list))

    if 'data' in fig_dict:
        for trace in fig_dict['data']:
            name = trace.get('name', '')
            group = trace.get('legendgroup')

            if group:
                groups_structure[group]['traces'].append(name)
            else:
                groups_structure['ungrouped']['traces'].append(name)

    # Extract and parse title
    title = ""
    subtitles = []
    if 'layout' in fig_dict and 'title' in fig_dict['layout']:
        title_data = fig_dict['layout']['title']
        if isinstance(title_data, dict):
            title_text = title_data.get('text', '')
            title, subtitles = parse_title_text(title_text)
        else:
            title = str(title_data)

    # Analyze structure
    structure_analysis = {
        'groups': {},
        'total_traces': 0,
        'title': title,
        'subtitles': subtitles
    }

    for group, data in groups_structure.items():
        traces = data['traces']
        unique_traces = sorted(set(traces))

        structure_analysis['groups'][group] = {
            'traces': traces,
            'unique_traces': unique_traces,
            'trace_count': len(traces),
            'unique_count': len(unique_traces),
            'instances_per_trace': {
                trace: traces.count(trace)
                for trace in unique_traces
            }
        }
        structure_analysis['total_traces'] += len(traces)

    return structure_analysis


def format_log_message(
    structure: Dict[str, Any],
    config: Dict[str, str]
) -> str:
    """Format the log message to show the hierarchical structure"""
    lines = [
        "Chart Generation Structure:",
        f"  Series Column: {config.get('series_column', 'N/A')}",
        f"  Group Column: {config.get('group_column', 'N/A')}",
        f"  X Column: {config.get('x_column', 'N/A')}",
        "",
        "Trace Structure:"
    ]

    for group, data in structure['groups'].items():
        if group != 'ungrouped':
            lines.extend([
                f"  Legend Group: {group}",
                "    Traces:"
            ])
        else:
            lines.extend([
                "  Ungrouped Traces:"
            ])

        for trace in data['unique_traces']:
            instances = data['instances_per_trace'][trace]
            lines.append(f"    - {trace} (× {instances} instances)")

        lines.append("")

    lines.extend([
        f"Total Traces: {structure['total_traces']}",
        "",
        "Title:",
        f"  {structure['title']}"
    ])

    if structure['subtitles']:
        lines.extend([
            "",
            "Subtitles:"
        ])
        for subtitle in structure['subtitles']:
            lines.append(f"  {subtitle}")

    return "\n".join(lines)

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

def log_chart_structure(
    figure: Union[dict, go.Figure, dcc.Graph],
    logger: logging.Logger,
    series_column: str = None,
    group_column: str = None,
    x_column: str = None
) -> None:
    """
    Log the hierarchical structure of the chart.
    """
    if isinstance(figure, dcc.Graph):
        figure = figure.figure

    config = {
        'series_column': series_column,
        'group_column': group_column,
        'x_column': x_column
    }

    structure = extract_chart_structure(figure)
    formatted_message = format_log_message(structure, config)
    logger.warning("\n" + formatted_message)


__all__ = ['load_csv', 'print_dataframe_info', 'create_insurer_options', 'create_additional_table_metrics', 'create_year_quarter_options', 'load_and_preprocess_data', 'load_json', 'map_insurer', 'map_line', 'map_insurer_code_to_name', 'map_line_code_to_name', 'map_metric_code_to_name', 'category_structure', 'default_insurer_options']
