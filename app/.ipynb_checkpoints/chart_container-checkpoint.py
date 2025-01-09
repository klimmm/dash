import dash_bootstrap_components as dbc
import logging
from dash import Dash, html, dcc, clientside_callback, Input, Outpu
import dash_bootstrap_components as dbc
import json
logger = logging.getLogger(__name__)


import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, dash_table, html, clientside_callback
import pandas as pd
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme, Symbol
import dash_bootstrap_components as dbc
import logging
from typing import List, Dic
from functools import lru_cache
from flask_caching import Cache
from functools import lru_cache
import logging



def log_component_structure(component, depth=0):
    indent = "  " * depth
    if component is None:
        logger.info(f"{indent}None")
    elif isinstance(component, dict):
        component_type = component.get('type', 'Unknown')
        component_namespace = component.get('namespace', 'Unknown')
        logger.info(f"{indent}{component_type} ({component_namespace})")

        if 'props' in component:
            props = component['props']
            if 'children' in props:
                children = props['children']
                if isinstance(children, list):
                    for child in children:
                        log_component_structure(child, depth + 1)
                elif isinstance(children, dict):
                    log_component_structure(children, depth + 1)

            for key in ['className', 'width']:
                if key in props:
                    logger.info(f"{indent}  {key}: {props[key]}")
    elif isinstance(component, (str, int, float)):
        logger.info(f"{indent}{type(component).__name__}: {component}")
    else:
        logger.info(f"{indent}{type(component).__name__}")

def count_charts(component):
    if isinstance(component, dict):
        if component.get('type') == 'Graph' and component.get('namespace') == 'dash_core_components':
            return 1
        elif 'props' in component and 'children' in component['props']:
            children = component['props']['children']
            if isinstance(children, list):
                return sum(count_charts(child) for child in children)
            else:
                return count_charts(children)
    elif isinstance(component, list):
        return sum(count_charts(child) for child in component)
    return 0




def update_charts_container(existing_charts, dynamic_graph, chart_count):

    dynamic_graph['props']['width'] = 6

    log_component_structure(dynamic_graph)


    # Update charts lis
    if existing_charts is not None and isinstance(existing_charts, dict) and existing_charts['type'] == 'Div':
        row = existing_charts['props']['children'][0]
        row['props']['children'].append(dynamic_graph)
        updated_charts = existing_charts

    else:
        logger.error(f"Unexpected structure for existing_charts: {type(existing_charts)}")
        updated_charts = {
            'type': 'Div',
            'namespace': 'dash_html_components',
            'props': {
                'children': [
                    {
                        'type': 'Row',
                        'namespace': 'dash_bootstrap_components',
                        'props': {
                            'children': [dynamic_graph]
                        }
                    }
                ]
            }
        }

    chart_count += 1
    total_charts = count_charts(updated_charts)


    logger.debug(f"Added dynamic graph, index: {chart_count}")

    total_charts = count_charts(updated_charts)
    logger.info(f"Total charts after update: {total_charts}")

    logger.debug("Updated charts structure:")
    log_component_structure(updated_charts)

    # The layout is now the updated_charts itself
    charts_layout = updated_charts

    logger.debug("Final layout structure:")
    log_component_structure(charts_layout)

    return charts_layout, chart_coun
