# app_layout.py

import pandas as pd

import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, dash_table
from dash import ctx
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme, Symbol
import dash_bootstrap_components as dbc


import logging
import json

from typing import Iterable, List, Dict, Callable, Optional, Tuple, Any, Se

from functools import lru_cache
from flask_caching import Cache






from translations import (
    LINEMAIN_COL, INSURER_COL, LINEMAIN_OPTIONS,
    DEFAULT_PREMIUM_LOSS_TYPES, DEFAULT_AGGREGATION_TYPE,
    DEFAULT_LINEMAIN, DEFAULT_INSURER, DEFAULT_PRIMARY_METRICS,
    DEFAULT_CHART_TYPE, DEFAULT_SECONDARY_CHART_TYPE, DEFAULT_SECONDARY_METRICS,
    DEFAULT_MARKET_CHART_TYPE, DEFAULT_MARKET_CHART_METRIC,
    DEFAULT_TABLE_METRIC, AGGREGATION_TYPES, AGGREGATION_TYPES_OPTIONS, translate,
    format_metric_name, METRICS, PRIMARY_METRICS, CHART_TYPE_OPTIONS,
    MARKET_METRIC_OPTIONS, CHART_TYPE_DROPDOWN_OPTIONS, MARKET_METRIC_DROPDOWN_OPTIONS,
    PRIMARY_METRICS_OPTIONS, SECONDARY_METRICS_OPTIONS, PREMIUM_LOSS_OPTIONS
)
from styles import (
   get_data_table_styles, COLOR_PALETTE, FONT_STYLES,
)
from data_utils import validate_dataframe, process_dataframe, get_unique_values


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Load the JSON file
with open('./preprocess_map_dict/insurer_map.json') as f:
    insurer_data = json.load(f)

# Create a dictionary mapping insurer values to names
options = [{'label': item['name'], 'value': item['insurer']} for item in insurer_data]

# Load the processed category structure
try:
    with open('hierarchy_leaves_as_keys_labels.json', 'r', encoding='utf-8') as f:
        CATEGORY_STRUCTURE = json.load(f)
except FileNotFoundError:
    logging.error("Error: 'hierarchy_leaves_as_keys_labels.json' file not found.")
    CATEGORY_STRUCTURE = {}  # Provide an empty default structure
except json.JSONDecodeError:
    logging.error("Error: 'hierarchy_leaves_as_keys_labels.json' is not a valid JSON file.")
    CATEGORY_STRUCTURE = {}  # Provide an empty default structure

with open('category_structure_log.json', 'w') as f:
    json.dump(CATEGORY_STRUCTURE, f, indent=2)
logging.info("Category structure written to 'category_structure_log.json'")


#logger.debug(f"CATEGORY_STRUCTURE: {json.dumps(CATEGORY_STRUCTURE, indent=2)}")

# Constants
FULL_WIDTH = 12
HALF_WIDTH = 6
QUARTER_WIDTH = 3

TITLE_STYLE = {
    'fontSize': '24px',
    'fontWeight': 'bold',
    'marginBottom': '20px'
}

SUBTITLE_STYLE = {
    'fontSize': '18px',
    'fontWeight': 'bold',
    'marginBottom': '10px'
}

FILTER_LABEL_STYLE = {
    'fontSize': '16px',
    'fontWeight': 'bold',
    'marginBottom': '5px'
}

OPTION_STYLE = {
    'fontSize': '18px'
}
class SimpleCache:
    def __init__(self):
        self._cache = {}

    def set(self, key, value):
        self._cache[key] = value

    def get(self, key):
        return self._cache.get(key)

cache = SimpleCache()

def print_category_summary(structure, max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        return

    for key, value in structure.items():
        print("  " * current_depth + f"{key}")
        if isinstance(value, dict):
            print_category_summary(value, max_depth, current_depth + 1)

@lru_cache(maxsize=1)
def cached_translate(text: str) -> str:
    """Cache translations to improve performance."""
    return translate(text)

def create_translated_dropdown_options(
    values: Iterable,
    translation_func: Callable = cached_translate
) -> List[Dict[str, str]]:
    """Create consistent dropdown options with translations."""
    return [{'label': translation_func(str(i)), 'value': str(i)} for i in list(values)]

def translate_quarter(quarter: str) -> str:
    """Translate quarter string to Russian format."""
    year, q = quarter.split('Q')
    months = {
        '1': '3 месяца',
        '2': '6 месяцев',
        '3': '9 месяцев',
        '4': '12 месяцев'
    }
    return f"{year} год, {months[q]}"




def create_general_filters(
    df: pd.DataFrame,
    year_quarter_options: List[Dict[str, str]],
    category_structure: Dict[str, Any],
    unique_linemain: Set[str]
) -> dbc.Card:
    """Create the general filters section of the layout."""
    try:
        translated_options = [
            {'label': translate_quarter(option['value']), 'value': option['value']}
            for option in year_quarter_options
        ]

        aggregation_options = [
            {'label': translate('Year-to-Date'), 'value': 'ytd'},
            {'label': translate('Quarterly'), 'value': 'quarterly'},
            {'label': translate('Rolling Sum 4Q'), 'value': 'rolling_sum_4q'},
            {'label': translate('Rolling Year-to-Year'), 'value': 'rolling_year_to_year'},
            {'label': translate('Cumulative Sum'), 'value': 'cumulative_sum'}
        ]

        category_checklist = create_category_checklist(category_structure)

        return dbc.Card([
            dbc.CardBody([
                html.H4(cached_translate("General Filters"), className="card-title mb-3", style=TITLE_STYLE),

                # Hidden start-quarter-dropdown
                html.Div([
                    dcc.Dropdown(
                        id='start-quarter-dropdown',
                        options=translated_options,
                        value=translated_options[0]['value'],
                        clearable=False,
                    ),
                ], style={'display': 'none'}),

                # First row: Year and Quarter selection (end quarter only)
                dbc.Row([
                    dbc.Col([
                        html.Label(
                            cached_translate("Годы, кварталы:"),
                            style=FILTER_LABEL_STYLE
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Dropdown(
                            id='end-quarter-dropdown',
                            options=translated_options,
                            value=translated_options[-1]['value'],
                            clearable=False,
                            style=OPTION_STYLE
                        ),
                    ], width=10),
                ], className="mb-2"),

                # Second row: Insurance Types (Category Checkboxes)
                dbc.Row([
                    dbc.Col([
                        html.Label(
                            cached_translate("Виды страхования:"),
                            style=FILTER_LABEL_STYLE
                        ),
                    ], width=2),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                dbc.Row([
                                    dbc.Col(html.H5("Виды страхования", style=SUBTITLE_STYLE), width="auto"),
                                    dbc.Col(
                                        dbc.Button(
                                            "Раскрыть",
                                            id="toggle-all-categories",
                                            color="primary",
                                            size="sm",
                                            className="float-right"
                                        ),
                                        width="auto"
                                    )
                                ], justify="between", className="g-0")
                            ]),
                            dbc.Collapse(
                                dbc.CardBody(category_checklist),
                                id="category-collapse",
                                is_open=True
                            )
                        ], className="mb-2"),
                    ], width=10),
                ], className="mb-2"),

                # Third row: Direct/Incoming Insurance (premium-loss-checklist)
                dbc.Row([
                    dbc.Col([
                        html.Label(
                            cached_translate("Прямой/входящий:"),
                            style=FILTER_LABEL_STYLE
                        ),
                    ], width=2),
                    dbc.Col([
                        dbc.Checklist(
                            id='premium-loss-checklist',
                            options=PREMIUM_LOSS_OPTIONS,
                            value=DEFAULT_PREMIUM_LOSS_TYPES,
                            inline=True,
                            style=OPTION_STYLE
                        ),
                    ], width=10),
                ], className="mb-2"),

                # Fourth row: Data Type
                dbc.Row([
                    dbc.Col([
                        html.Label(
                            cached_translate("Вид данных:"),
                            style=FILTER_LABEL_STYLE
                        ),
                    ], width=2),
                    dbc.Col([
                        dbc.RadioItems(
                            id='aggregation-type-dropdown',
                            options=aggregation_options,
                            value='ytd',
                            inline=True,
                            style=OPTION_STYLE
                        ),
                    ], width=10),
                ], className="mb-2"),
            ])
        ], className="mb-3")
    except Exception as e:
        logger.error(f"Error in create_general_filters: {str(e)}", exc_info=True)
        return dbc.Card(dbc.CardBody(html.P("Error loading general filters")))

def create_app_layout(
    df: pd.DataFrame,
    year_quarter_options: List[Dict[str, str]],
    translate: callable,
    market_metric_dropdown_options: List[Dict[str, str]],
    default_table_metric: str
) -> html.Div:
    """Create the main application layout."""
    try:
        validate_dataframe(df)
        processed_df = process_dataframe(df)

        unique_linemain = set(df[LINEMAIN_COL].unique())

        layout = dbc.Container([
            dcc.Store(id='category-expand-states', data={}),
            dcc.Store(id='all-expanded', data=False),
            dcc.Store(id='selected-linemain-store'),
            dcc.Store(id='actual-aggregation-type'),
            dbc.NavbarSimple(
                brand=cached_translate("Insurance Data Dashboard"),
                brand_href="#",
                color="primary",
                dark=True,
                className="mb-4"
            ),
            create_general_filters(processed_df, year_quarter_options, CATEGORY_STRUCTURE, unique_linemain),
            html.Div(id="selected-categories-output", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Tabs([
                        create_combined_metrics_tab(processed_df),
                        create_market_overview_tab(),
                        create_data_table_tab(
                            translate,
                            market_metric_dropdown_options,
                            default_table_metric
                        ),
                    ])
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Collapse(
                        dbc.Card(
                            dbc.CardBody([
                                html.H4(cached_translate("Debug Logs")),
                                html.Pre(
                                    id='debug-output',
                                    style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-all'}
                                )
                            ])
                        ),
                        id="debug-collapse",
                        is_open=False,
                    ),
                    dbc.Button(
                        cached_translate("Toggle Debug Logs"),
                        id="debug-toggle",
                        className="mt-3",
                        color="secondary"
                    )
                ], width=12)
            ], className="mt-4")
        ], fluid=True)

        return layou
    except Exception as e:
        logging.error(f"Error in create_app_layout: {str(e)}", exc_info=True)
        return html.Div([
            html.H1("Error"),
            html.P(f"An error occurred while creating the layout: {str(e)}")
        ])



# Load the processed category structure
try:
    with open('hierarchy_leaves_as_keys_labels.json', 'r', encoding='utf-8') as f:
        CATEGORY_STRUCTURE = json.load(f)
except FileNotFoundError:
    logging.error("Error: 'hierarchy_leaves_as_keys_labels.json' file not found.")
    CATEGORY_STRUCTURE = {}  # Provide an empty default structure
except json.JSONDecodeError:
    logging.error("Error: 'hierarchy_leaves_as_keys_labels.json' is not a valid JSON file.")
    CATEGORY_STRUCTURE = {}  # Provide an empty default structure



def create_checklist_item(code: str, label: str, has_children: bool, level: int) -> Dict[str, Any]:
    """Create a single checklist item."""
    return {
        'type': 'checklist-item',
        'code': code,
        'label': label,
        'has_children': has_children,
        'level': level
    }

def create_category_checklist(category_structure):

    top_level_categories = [code for code in category_structure.keys() if '.' not in code]

    top_level_categories = [
    code for code in category_structure.keys()
    if not any(code in item.get('children', []) for item in category_structure.values())
    ]

    checklist = [create_checklist_component({
        'code': code,
        'label': category_structure[code]['label'],
        'has_children': bool(category_structure[code].get('children')),
        'level': 0
    }) for code in top_level_categories]

    return html.Div([
        html.Div(id="selected-categories-header", className="mb-2"),
        html.Div(checklist, id="category-checklist", className="category-checklist")
    ])



def create_checklist_component(item: Dict[str, Any]) -> html.Div:
    children = [
        dbc.Checkbox(
            id={'type': 'category-checkbox', 'index': item['code']},
            label=f"{item['code']}. {item['label']}",
            value=False
        ),
        html.Button(
            "▼",
            id={'type': 'category-collapse-button', 'index': item['code']},
            style={
                'marginLeft': '5px',
                'border': 'none',
                'background': 'none',
                'visibility': 'visible' if item['has_children'] else 'hidden',
            }
        ),
        dbc.Collapse(
            id={'type': 'category-collapse', 'index': item['code']},
            is_open=False,
            children=[html.Div(id={'type': 'category-placeholder', 'index': item['code']})]
        )
    ]

    return html.Div(children, style={'marginLeft': f'{20 * item["level"]}px'})
















def setup_callbacks(app: dash.Dash) -> None:


    @app.callback(
        [Output('category-expand-states', 'data'),
         Output('all-expanded', 'data'),
         Output({'type': 'category-collapse', 'index': ALL}, 'is_open'),
         Output({'type': 'category-collapse-button', 'index': ALL}, 'children'),
         Output('toggle-all-categories', 'children'),
         Output('selected-linemain-store', 'data'),
         Output({'type': 'category-checkbox', 'index': ALL}, 'disabled'),
         Output({'type': 'category-checkbox', 'index': ALL}, 'value'),
         Output('selected-categories-header', 'children')],
        [Input('toggle-all-categories', 'n_clicks'),
         Input({'type': 'category-collapse-button', 'index': ALL}, 'n_clicks'),
         Input({'type': 'category-checkbox', 'index': ALL}, 'value')],
        [State('category-expand-states', 'data'),
         State('all-expanded', 'data'),
         State({'type': 'category-collapse', 'index': ALL}, 'id'),
         State({'type': 'category-checkbox', 'index': ALL}, 'id')]
        )
    def update_category_state(toggle_all_clicks, individual_clicks, checkbox_values,
                              current_states, all_expanded, collapse_ids, checkbox_ids):
        logger.debug(f"Current states: {current_states}")
        logger.debug(f"Collapse IDs: {collapse_ids}")

        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        new_states = current_states.copy() if current_states is not None else {}

        if triggered_id == 'toggle-all-categories':
            new_all_expanded = not all_expanded
            new_states = {collapse['index']: new_all_expanded for collapse in collapse_ids}
        elif 'category-collapse-button' in triggered_id:
            for i, clicks in enumerate(individual_clicks):
                if clicks is not None:
                    category_index = collapse_ids[i]['index']
                    new_states[category_index] = not new_states.get(category_index, False)

        logger.debug(f"New states: {new_states}")

        collapse_values = [new_states.get(collapse['index'], False) for collapse in collapse_ids]
        logger.debug(f"Collapse values: {collapse_values}")

        new_button_texts = ["▲" if new_states.get(collapse['index'], False) else "▼" for collapse in collapse_ids]
        new_all_expanded = all(new_states.values())
        toggle_all_text = "Collapse All" if new_all_expanded else "Expand All"

        # Handle checkbox state
        selected_items = [id_dict['index'] for value, id_dict in zip(checkbox_values, checkbox_ids) if value]

        if not selected_items:
            selected_items = ['4']  # Default selection

        disabled_states = []
        checked_states = []
        for id_dict in checkbox_ids:
            code = id_dict['index']
            is_checked = code in selected_items
            is_disabled = any(code.startswith(selected) and code != selected for selected in selected_items)
            disabled_states.append(is_disabled)
            checked_states.append(is_checked)

        if not selected_items:
            header_text = "No categories selected"
        elif len(selected_items) <= 3:
            header_text = "Selected: " + ", ".join(selected_items)
        else:
            header_text = f"{len(selected_items)} categories selected"

        logger.debug(f"Returning: {len(collapse_values)} collapse values, {len(new_button_texts)} button texts, {len(disabled_states)} disabled states, {len(checked_states)} checked states")

        # Verify that all lists have the same length
        if not (len(collapse_values) == len(new_button_texts) == len(disabled_states) == len(checked_states)):
            logger.warning(f"Mismatch in returned list lengths: collapse_values={len(collapse_values)}, new_button_texts={len(new_button_texts)}, disabled_states={len(disabled_states)}, checked_states={len(checked_states)}")

        return (new_states, new_all_expanded, collapse_values, new_button_texts,
                toggle_all_text, selected_items, disabled_states, checked_states, header_text)

    @app.callback(
        Output({'type': 'category-placeholder', 'index': MATCH}, 'children'),
        Input('category-expand-states', 'data'),
        State({'type': 'category-placeholder', 'index': MATCH}, 'id')
    )
    def load_subcategory(expand_states, placeholder_id):
        logger.debug(f"load_subcategory called for {placeholder_id}")
        logger.debug(f"Expand states: {expand_states}")
        try:
            current_index = placeholder_id['index']

            if not expand_states.get(current_index, False):
                logger.debug(f"Category {current_index} is collapsed, returning empty list")
                return []  # Return empty if category is collapsed

            subcategory_structure = CATEGORY_STRUCTURE.get(current_index, {})
            logger.debug(f"Subcategory structure for {current_index}: {subcategory_structure}")

            if not subcategory_structure.get('children'):
                logger.debug(f"No children for category {current_index}")
                return []

            children = subcategory_structure.get('children', [])
            logger.debug(f"Children of category {current_index}: {children}")

            subcategory_components = []
            for child in children:
                child_data = CATEGORY_STRUCTURE.get(child, {})
                item = create_checklist_item(child, child_data.get('label', ''), bool(child_data.get('children')), 1)
                subcategory_components.append(create_checklist_component(item))

            logger.debug(f"Created {len(subcategory_components)} subcategory components")

            return subcategory_components

        except Exception as e:
            logger.error(f"Error in load_subcategory: {str(e)}", exc_info=True)
            return html.Div(f"Error loading subcategory: {str(e)}")


    @app.callback(
        Output('actual-aggregation-type', 'data'),
        [Input('end-quarter-dropdown', 'value'),
         Input('aggregation-type-dropdown', 'value')]
    )
    def update_aggregation_type(end_quarter, aggregation_type):
        # Implement the logic for updating the actual aggregation type based on the dropdown values
        # Return the updated aggregation type
        return aggregation_type















def create_combined_metrics_tab(df: pd.DataFrame) -> dbc.Tab:
    """Create the combined metrics tab."""
    try:
        return dbc.Tab([
            dbc.Card([
                dbc.CardBody([
                    # First row: Insurer selection
                    dbc.Row([
                        dbc.Col([
                            html.Label(
                                cached_translate("Select Insurer:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(
                                id='insurer-radio',
                                options=options,
                                value=DEFAULT_INSURER,
                                clearable=False,
                                style=OPTION_STYLE
                            ),
                        ], width=10),
                    ], className="mb-2"),

                    # Second row: Benchmark and Competitor
                    dbc.Row([
                        dbc.Col([
                            html.Label(
                                cached_translate("Сравнить:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=2),
                        dbc.Col([
                            html.Label(
                                cached_translate("Peer"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=1),
                        dbc.Col([
                            dcc.Dropdown(
                                id='compare-to-dropdown',
                                options=[],  # Initialize with empty options
                                multi=True,
                                style=OPTION_STYLE
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Label(
                                cached_translate("Бенчмарк"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=1),
                        dbc.Col([
                            dbc.Checklist(
                                id='compare-to-benchmark',
                                options=[],  # Initialize with empty options
                                value=[],
                                inline=True,
                                style=OPTION_STYLE
                            ),
                        ], width=4),

                    ], className="mb-2"),

                    # Third row: Primary Metrics and Chart Type
                    dbc.Row([
                        dbc.Col([
                            html.Label(
                                cached_translate("Select Primary Metrics:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(
                                id='primary-metric-dropdown',
                                options=PRIMARY_METRICS_OPTIONS,
                                value=DEFAULT_PRIMARY_METRICS,
                                multi=True,
                                style=OPTION_STYLE
                            ),
                        ], width=5),
                        dbc.Col([
                            html.Label(
                                cached_translate("Select Primary Chart Type:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=1),
                        dbc.Col([
                            dcc.Dropdown(
                                id='combined-chart-type',
                                options=CHART_TYPE_DROPDOWN_OPTIONS,
                                value=DEFAULT_CHART_TYPE,
                                clearable=False,
                                style=OPTION_STYLE
                            ),
                        ], width=4),
                    ], className="mb-2"),

                    # Fourth row: Secondary Metrics and Chart Type
                    dbc.Row([
                        dbc.Col([
                            html.Label(
                                cached_translate("Select Secondary Metrics:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=2),
                        dbc.Col([
                            dcc.Dropdown(
                                id='secondary-metric-dropdown',
                                options=SECONDARY_METRICS_OPTIONS,
                                value=DEFAULT_SECONDARY_METRICS,
                                multi=True,
                                style=OPTION_STYLE
                            ),
                        ], width=5),
                        dbc.Col([
                            html.Label(
                                cached_translate("Select Secondary Chart Type:"),
                                style=FILTER_LABEL_STYLE
                            ),
                        ], width=1),
                        dbc.Col([
                            dcc.Dropdown(
                                id='combined-secondary-chart-type',
                                options=CHART_TYPE_DROPDOWN_OPTIONS,
                                value=DEFAULT_SECONDARY_CHART_TYPE,
                                clearable=False,
                                style=OPTION_STYLE
                            ),
                        ], width=4),
                    ], className="mb-2"),
                ])
            ], className="mb-3"),
            dcc.Graph(id='combined-graph', style={'height': '60vh'})
        ], label=cached_translate("Combined Metrics"))
    except Exception as e:
        logger.error(f"Error in create_combined_metrics_tab: {str(e)}", exc_info=True)
        return dbc.Tab(dbc.Card(dbc.CardBody(html.P("Error loading combined metrics tab"))))

def create_market_overview_tab() -> dbc.Tab:
    """Create the market overview tab."""
    try:
        return dbc.Tab([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Label(
                                        cached_translate("Select Chart Type:"),
                                        style=FILTER_LABEL_STYLE
                                    ),
                                    dcc.Dropdown(
                                        id='market-chart-type',
                                        options=CHART_TYPE_DROPDOWN_OPTIONS,
                                        value=DEFAULT_MARKET_CHART_TYPE,
                                        clearable=False,
                                        style=OPTION_STYLE
                                    ),
                                ])
                            ], className="h-100")
                        ], width=HALF_WIDTH),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Label(
                                        cached_translate("Select Metric:"),
                                        style=FILTER_LABEL_STYLE
                                    ),
                                    dcc.Dropdown(
                                        id='market-chart-metric',
                                        options=MARKET_METRIC_DROPDOWN_OPTIONS,
                                        value=DEFAULT_MARKET_CHART_METRIC,
                                        clearable=False,
                                        style=OPTION_STYLE
                                    ),
                                ])
                            ], className="h-100")
                        ], width=HALF_WIDTH),
                    ], className="g-2"),
                ])
            ], className="mb-3"),
            dcc.Graph(id='market-graph', style={'height': '60vh'})
        ], label=cached_translate("Market Overview"))
    except Exception as e:
        logger.error(f"Error in create_market_overview_tab: {str(e)}", exc_info=True)
        return dbc.Tab(dbc.Card(dbc.CardBody(html.P("Error loading market overview tab"))))

def create_data_table_tab(
    translate: Callable,
    market_metric_dropdown_options: List[Dict[str, str]],
    default_table_metric: str
) -> dbc.Tab:
    """Create the data table tab."""
    return dbc.Tab([
        dbc.Card([
            dbc.CardBody([
                html.H4(
                    cached_translate("Топ-10"),
                    className="card-title",
                    style={'fontSize': '1.5rem', 'color': 'black'}
                ),
                html.Div([
                    html.H5(
                        id='table-title-row1',
                        className="mb-0 font-weight-bold",
                        style={'fontSize': '1.25rem', 'color': 'black'}
                    ),
                    html.H5(
                        id='table-title-row2',
                        className="mt-0 text-muted",
                        style={'fontSize': '1.25rem'}
                    ),
                ], id='table-title-container', className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Label(
                                    cached_translate("Select Metric:"),
                                    style=FILTER_LABEL_STYLE
                                ),
                                dcc.Dropdown(
                                    id='table-metric-dropdown',
                                    options=market_metric_dropdown_options,
                                    value=default_table_metric,
                                    clearable=False,
                                    style=OPTION_STYLE
                                )
                            ])
                        ], className="h-100")
                    ], width=12),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Label(
                                    cached_translate("Show Market Share:"),
                                    style=FILTER_LABEL_STYLE
                                ),
                                dbc.RadioItems(
                                    id='show-market-share',
                                    options=[
                                        {'label': cached_translate('Yes'), 'value': 'yes'},
                                        {'label': cached_translate('No'), 'value': 'no'}
                                    ],
                                    value='yes',
                                    inline=True,
                                    inputStyle={"marginRight": "5px"},
                                    labelStyle={"marginRight": "15px"}
                                )
                            ])
                        ], className="h-100")
                    ], width=12)
                ], className="g-2 mb-3"),
                dcc.Loading(
                    id="loading-table",
                    type="default",
                    children=[html.Div(id='data-table', style={'height': '50vh', 'overflow': 'auto'})]
                ),
                html.Div(id='processing-error', className="text-danger mt-3")
            ])
        ])
    ], label=cached_translate("Data Table"))




    # Add more callbacks as needed for other components
# Add custom CSS styles
def get_custom_css() -> str:
    return '''
    <style>
        /* Reduce form group margins */
        .form-group {
            margin-bottom: 0.5rem;
        }
        /* Reduce Dropdown height */
        .Select-control {
            height: 30px;
        }
        .Select-placeholder, .Select-input, .Select-value {
            line-height: 30px !important;
        }
        /* Reduce checklist margins */
        .form-check {
            margin-bottom: 0.25rem;
        }
        /* Add margins between cards */
        .card {
            margin-bottom: 1rem;
        }
        /* Style category accordion */
        .accordion-button {
            padding: 0.5rem 1rem;
        }
        .accordion-body {
            padding: 0.5rem;
        }
        .category-checklist .form-check {
            margin-bottom: 0.25rem;
        }
        /* ... other styles ... */
        #combined-graph, #market-graph {
            height: 70vh !important;
        }
        /* ... other styles ... */
        .custom-tabs .nav-item {
            width: 33.33%;
        }
        .custom-tabs .nav-link {
            text-align: center;
        }
    </style>
    '''
