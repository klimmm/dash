import logging
from typing import Dict, Any, List, Union
import plotly.graph_objects as go
from dash import dcc
from collections import defaultdic

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import plotly.graph_objects as go
from dash import dcc
from collections import defaultdic
import re
from logging_config import get_logger
logger = logging.getLogger(__name__)

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