import json
import os
import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import logging
from memory_profiler import profile
import re
import json
import as
# Set up logging

#from constants.filter_options import DEFAULT_CHECKED_CATEGORIES
DEFAULT_CHECKED_CATEGORIES = ['спец. риски']
#from logging_config import get_logging
#logging = get_logging(__name__)




def create_checklist_layout():
    logging.debug("Creating app layout")

    layout = dbc.Container([
        create_combined_category_dropdown_button_row(),
        create_stores_row(),
        create_checklist_row(),

    ], fluid=True)

    logging.debug("App layout created")
    return layou



# Load the category structure
def load_json(file_path):
    logging.debug(f"Attempting to load JSON from {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.debug(f"Successfully loaded JSON data")
        return data
    except FileNotFoundError:
        logging.error(f"JSON file not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {str(e)}")
        return {}

# Path to your JSON file
JSON_FILE_PATH = '/Users/klim/Desktop/dash_inusrance_app/dash/constants/modified_insurance.json'

# Load the JSON structure
category_structure = load_json(JSON_FILE_PATH)
logging.debug(f"Loaded category structure with {len(category_structure)} top-level categories")

# Default checked categories
logging.debug(f"Default checked categories: {DEFAULT_CHECKED_CATEGORIES}")

class CategoryChecklist:
    def __init__(self, category_structure, selected_categories=None, expanded_categories=None, default_categories=None):
        self.category_structure = category_structure
        logging.debug(f"selected_categories '{selected_categories}'")
        logging.debug(f"default_categories '{default_categories}'")
        logging.debug(f"expanded_categories_received by categorychecklist '{default_categories}'")

        self.expanded_categories = set(expanded_categories or [])
        logging.warning(f"self.expanded_categories: {self.expanded_categories}")

        self.checked_categories = set(selected_categories)


        self.parent_categories = self.find_ancestors_for_multiple(self.checked_categories)

        logging.debug(f"Using categories: {self.checked_categories}")


        logging.debug(f"Initialized CategoryChecklist with {len(self.checked_categories)} selected categories: {self.checked_categories}, {len(self.expanded_categories)} expanded categories: {self.expanded_categories}")


    def find_ancestors_for_multiple(self, checked_categories):
        def find_ancestors(target):
            ancestors = set()
            current = targe
            path = [current]
            while current:
                found = False
                for category, details in self.category_structure.items():
                    if current in details.get('children', []):
                        ancestors.add(category)
                        #logging.debug(f"Found ancestor: {category} for {current}")
                        current = category
                        path.append(current)
                        found = True
                        break
                if not found:
                    #logging.debug(f"No more ancestors found for {current}")
                    current = None
            #logging.debug(f"Ancestor path for {target}: {' -> '.join(reversed(path))}")
            return ancestors

        all_ancestors = set()
        for category in checked_categories:
            category_ancestors = find_ancestors(category)
            #logging.debug(f"Ancestors for category {category}: {category_ancestors}")
            all_ancestors.update(category_ancestors)

        #logging.debug(f"All ancestors for checked categories {checked_categories}: {all_ancestors}")
        return all_ancestors

    def create_checklist(self):
        logging.debug("Starting to create checklist")
        components = self._create_category_components(tuple(list(self.category_structure.keys())), 0)
        logging.debug(f"Created {len(components)} top-level components")
        return html.Div(components, id="category-checklist", className="category-checklist")

    def _create_category_components(self, category_codes, level):
        components = []
        for code in category_codes:
            if level == 0 and any(code in cat.get('children', []) for cat in self.category_structure.values()):
                continue
            if level > 3:
                continue
            category = self.category_structure.get(code)
            if not category:
                continue
            component = self._create_category_component(code, category, level)
            components.append(component)
        return components

    def _create_category_component(self, code, category, level):
        is_expanded = code in self.expanded_categories
        #logging.warning(f"self.expanded_categories: {self.expanded_categories}")
        is_checked = code in self.checked_categories

        checkbox = dbc.Checkbox(
            id={'type': 'category-checkbox', 'category_code': code},
            label=category['label'],
            value=is_checked,
            className="category-checkbox"
        )

        if category.get('children'):

            expand_button = html.Button(
                "▼" if is_expanded else "▶",
                id={'type': 'category-collapse-button', 'category_code': code},
                className="category-expand-button",
                style={
                    'marginLeft': '5px',
                    'border': 'none',
                    'background': 'none',
                    'padding': '0',
                    'cursor': 'pointer',
                }
            )

            component = html.Div([
                checkbox,
                expand_button
            ], className="category-component d-flex align-items-center")
        else:
            component = checkbox

        if category.get('children'):
            children_components = self._create_category_components(tuple(category['children']), level+1)
            component = html.Div([
                component,
                dbc.Collapse(
                    children_components,
                    id={'type': 'category-collapse', 'category_code': code},
                    is_open=is_expanded
                )
            ])

        return html.Div(
            component,
            className=f"category-level-{level}",
            style={'marginLeft': f'{20 * level}px', 'marginTop': '5px'}
        )



def create_combined_category_dropdown_button_row():
    return dbc.Row([
         html.Label("Вид страхования", className="filter-dropdown"),

        dbc.Col([
            dcc.Dropdown(

                id='category-filter-dropdown',
                options=[{'label': category.get('label', f"Category {code}"), 'value': code}
                         for code, category in category_structure.items()],
                value=DEFAULT_CHECKED_CATEGORIES,
                multi=True,
                placeholder="Select categories...",
                className="filter-dropdown"
            )
        ], xs=12, sm=8, md=8, className="p-0"),
        dbc.Col([
            html.Label("", className="filter-label"),
            dbc.Button(
                "Раскрыть все",
                id="toggle-all-categories",
                color="primary",
                n_clicks=0,
                #size="sm",
                className="simple-button me-1 p-1 d-inline-block"
            )
        ], xs=12, sm=4, md=2, className="p-0")

        dbc.Col([
            html.Label("", className="filter-label"),
            dbc.Button(
                "Drill down",
                id="detailize-button",
                color="primary",
                #size="sm",
                className="simple-button me-1 p-1 d-inline-block"
            )
        ], xs=12, sm=4, md=2, className="p-0"),


    ], className="p-0")  # Remove gutters from the row


def create_stores_row():
    return dbc.Row([
        dcc.Store(id='selected-categories-store', data=DEFAULT_CHECKED_CATEGORIES),
        dcc.Store(id='expanded-categories-store', data=[]),
        dcc.Store(id='all-categories-expanded', data=False),

        html.Div(id="dummy-output"),
    ], className="p-0")


def create_checklist_row():
    checklist = CategoryChecklist(category_structure, selected_categories=DEFAULT_CHECKED_CATEGORIES)

    return dbc.Row([
        dbc.Collapse(
            checklist.create_checklist(),
            id="category-collapse",
            is_open=True
        )
    ], className="p-0")

import logging

import logging

def handle_parent_child_selections(selected_categories, category_structure, detailize=False):
    logging.debug(f"Starting handle_parent_child_selections with selected categories: {selected_categories}")
    logging.debug(f"Detailize flag: {detailize}")

    def get_immediate_children(category):
        return set(category_structure[category].get('children', []))


    if not detailize:
        new_selected = set(selected_categories)

        # Remove children if their parent is selected
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                children = get_immediate_children(category)
                removed_children = new_selected.intersection(children)
                new_selected.difference_update(removed_children)
                if removed_children:
                    logging.debug(f"Removed children of {category}: {removed_children}")
    else:
        new_selected = set()
        # Add children for categories that have them
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                children = get_immediate_children(category)
                new_selected.update(children)
                logging.debug(f"Detailized {category}. Added children: {children}")

    final_selected = list(new_selected)
    logging.debug(f"Final selected categories: {final_selected}")
    return final_selected

# Modify the update_store_and_sync_dropdown callback

# Update your callback to use this function


def setup_checklist_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output('selected-categories-store', 'data'),
        Output('category-filter-dropdown', 'value'),
        Input({'type': 'category-checkbox', 'category_code': ALL}, 'value'),
        Input('category-filter-dropdown', 'value'),
        Input('detailize-button', 'n_clicks'),
        State({'type': 'category-checkbox', 'category_code': ALL}, 'id'),
        State('selected-categories-store', 'data'),
        prevent_initial_call=True
    )
    def update_store_and_sync_dropdown(checkbox_values, dropdown_value, detailize_clicks, checkbox_ids, current_selected):
        ctx = dash.callback_contex
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]

        logging.debug(f"update_store_and_sync_dropdown triggered by: {trigger}")

        if trigger == 'category-filter-dropdown':
            new_selected = dropdown_value or []
            detailize = False
        elif trigger == 'detailize-button':
            new_selected = current_selected
            detailize = True
        else:  # checkbox trigger
            new_selected = [
                id_dict['category_code'] for value, id_dict in zip(checkbox_values, checkbox_ids)
                if value and id_dict['category_code'] in category_structure
            ]
            detailize = False

        new_selected = handle_parent_child_selections(new_selected, category_structure, detailize)

        logging.debug(f"Final new selected categories: {new_selected}")
        return new_selected, new_selected


    @app.callback(
        Output('expanded-categories-store', 'data'),
        Input({'type': 'category-collapse-button', 'category_code': ALL}, 'n_clicks'),
        State({'type': 'category-collapse-button', 'category_code': ALL}, 'id'),
        State('expanded-categories-store', 'data'),
        prevent_initial_call=True
    )
    def update_expanded_categories(n_clicks_list, button_ids, expanded_categories):
        ctx = dash.callback_contex
        if not ctx.triggered or not any(n_clicks_list):
            raise PreventUpdate
        logging.warning(f"Updated expanded categories ctx : {ctx}")

        triggered_id = ctx.triggered[0]['prop_id']
        match = re.search(r'"category_code":"([^"]*)"', triggered_id)
        if match:
            category_code = match.group(1)
            logging.warning(f"expanded triggered category_code: {category_code}")
        else:
            logging.error(f"Failed to extract category_code from: {triggered_id}")
            return expanded_categories  # Return unchanged if extraction fails

        logging.warning(f"expanded triggered triggered_id: {triggered_id}")
        logging.warning(f"expanded triggered category_code: {category_code}")

        if expanded_categories is None:
            expanded_categories = []
        logging.warning(f"expanded categories: {expanded_categories}")

        if category_code in expanded_categories:
            expanded_categories.remove(category_code)
        else:
            expanded_categories.append(category_code)

        logging.warning(f"Updated expanded categories: {expanded_categories}")
        return expanded_categories

    @app.callback(
        Output({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
        Output({'type': 'category-collapse-button', 'category_code': MATCH}, 'children'),
        Input({'type': 'category-collapse-button', 'category_code': MATCH}, 'n_clicks'),
        State({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
    )

    def toggle_category_collapse(n_clicks, is_open):
        if not n_clicks:
            raise PreventUpdate

        ctx = dash.callback_contex
        logging.warning(f"toggle_category_collapse ctx: {ctx}")

        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]['prop_id']
        logging.warning(f"Full triggered_id: {triggered_id}")

        # Use regex to extract the entire category_code, including any dots
        match = re.search(r'"category_code":"([^"]*)"', triggered_id)
        if match:
            category_code = match.group(1)
            logging.warning(f"Extracted category_code: {category_code}")
        else:
            logging.error(f"Failed to extract category_code from: {triggered_id}")
            category_code = "Unknown"

        new_is_open = not is_open
        new_button_text = "▼" if new_is_open else "▶"

        logging.warning(f"Category: {category_code}")
        logging.warning(f"new_is_open: {new_is_open}")
        logging.warning(f"new_button_text: {new_button_text}")

        return new_is_open, new_button_tex


    @app.callback(
        Output("category-collapse", "children"),
        Output("category-collapse", "is_open"),
        Output("toggle-all-categories", "children"),
        Input("toggle-all-categories", "n_clicks"),
        Input('selected-categories-store', 'data'),
        Input('expanded-categories-store', 'data'),
        State("category-collapse", "is_open"),
    )
    def update_category_checklist(n_clicks, selected_categories, expanded_categories, is_open):
        ctx = dash.callback_contex
        if not ctx.triggered:
            # Initial load
            return None, False, "Раскрыть все"

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        logging.debug(f"update_category_checklist triggered by: {trigger_id}")

        if trigger_id == "toggle-all-categories":
            new_is_open = not is_open
            new_button_text = "Скрыть" if new_is_open else "Раскрыть все"
        else:
            new_is_open = is_open
            new_button_text = "Скрыть" if is_open else "Раскрыть все"

        checklist = CategoryChecklist(category_structure, selected_categories=selected_categories, expanded_categories=expanded_categories)
        return checklist.create_checklist(), new_is_open, new_button_tex






def create_dash_app():
    logging.debug("Creating Dash app")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    app.layout = create_checklist_layout()
    setup_checklist_callbacks(app)
    return app

if __name__ == '__main__':
    logging.debug("Starting the Dash app")
    app = create_dash_app()
    app.run_server(debug=True)
    logging.debug("Dash app server started")