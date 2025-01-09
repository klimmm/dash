import json
import os
import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import logging
from memory_profiler import profile

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the category structure
def load_json(file_path):
    logger.info(f"Attempting to load JSON from {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded JSON data")
        return data
    except FileNotFoundError:
        logger.error(f"JSON file not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {str(e)}")
        return {}

# Path to your JSON file
JSON_FILE_PATH = '/users/klim/Desktop/dash_inusrance_app/modified_insurance.json'

# Load the JSON structure
category_structure = load_json(JSON_FILE_PATH)
logger.info(f"Loaded category structure with {len(category_structure)} top-level categories")

# Default checked categories
DEFAULT_CHECKED_CATEGORIES = ['6']  # Ensure these match the 'code' values in your JSON
logger.info(f"Default checked categories: {DEFAULT_CHECKED_CATEGORIES}")

class CategoryChecklist:
    def __init__(self, category_structure, selected_categories=None, expanded_categories=None, default_categories=None):
        self.category_structure = category_structure
        logger.debug(f"selected_categories '{selected_categories}'")
        logger.debug(f"default_categories '{default_categories}'")
        self.expanded_categories = set(expanded_categories or [])

        if selected_categories:
            self.checked_categories = set(selected_categories)
        elif default_categories:
            self.checked_categories = set(default_categories)
        else:
            self.checked_categories = set(DEFAULT_CHECKED_CATEGORIES)

        logger.debug(f"Using categories: {self.checked_categories}")
        self.parent_categories = self.find_ancestors_for_multiple(self.checked_categories)

        logger.info(f"Initialized CategoryChecklist with {len(self.checked_categories)} selected categories: {self.checked_categories}")
        logger.info(f"Expanded categories: {len(self.parent_categories)}: {self.parent_categories}")

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
                        current = category
                        path.append(current)
                        found = True
                        break
                if not found:
                    current = None
            logger.debug(f"Ancestor path for {target}: {' -> '.join(reversed(path))}")
            return ancestors

        all_ancestors = set()
        for category in checked_categories:
            category_ancestors = find_ancestors(category)
            logger.debug(f"Ancestors for category {category}: {category_ancestors}")
            all_ancestors.update(category_ancestors)

        logger.debug(f"All ancestors for checked categories {checked_categories}: {all_ancestors}")
        return all_ancestors
    def create_checklist(self):
        logger.info("Creating category checklist")
        logger.debug(f"Checked categories: {self.checked_categories}")
        logger.debug(f"Expanded categories: {self.parent_categories}")

        components = self._create_category_components(list(self.category_structure.keys()), level=0)

        logger.debug(f"Created {len(components)} top-level components")
        return html.Div(components, id="category-checklist", className="category-checklist")


    def _create_category_components(self, category_codes, level):
        components = []
        children_of_parent = [child for code in self.parent_categories for child in self.category_structure.get(code, {}).get('children', [])]
        grandchildren_of_parent = [child for code in children_of_parent  for child in self.category_structure.get(code, {}).get('children', [])]
        children_of_expanded = [child for code in self.expanded_categories for child in self.category_structure.get(code, {}).get('children', [])]

        for code in category_codes:

            category = self.category_structure.get(code, {})

            #condition1 = level == 0 and (code in self.checked_categories or code in self.expanded_categories)
            #condition2 = level != 0 and code in self.checked_categories
            #condition3 = code in self.expanded_categories and any(child in self.checked_categories for child in category.get('children', []))

            #logger.debug(f"Category: {code}, Level: {level}")
            #logger.debug(f"Condition 1 (top-level and checked/expanded): {condition1}")
            #logger.debug(f"Condition 2 (non-top-level and checked): {condition2}")
            #logger.debug(f"Condition 3 (expanded with checked children): {condition3}")

            if level == 0 and any(code in cat.get('children', []) for cat in self.category_structure.values()):
                continue  # Skip non-top-level categories when at level 0

            #if level == 0 or code in self.expanded_categories or code in children_of_expanded or code in grandchildren_of_expanded:

            if level <= 1 or code in self.parent_categories or code in self.expanded_categories or code in children_of_expanded or code in children_of_parent or code in grandchildren_of_parent:

                logger.debug(f"Creating component for category: {code} at level {level}")
                component = self._create_category_component(code, category, level)
                components.append(component)
            else:
                pass #logger.debug(f"Skipping component creation for category: {code} at level {level}")

        logger.debug(f"Created {len(components)} components at level {level}")
        return components

    def _create_category_component(self, code, category, level):
        logger.debug(f"Creating component for category: {code} at level {level}")
        has_children = bool(category.get('children'))
        checkbox = dbc.Checkbox(
            id={'type': 'category-checkbox', 'category_code': code},
            label=f"{category.get('label', 'No Label')}",
            value=code in self.checked_categories
        )

        if has_children:
            button = html.Button(
                "▼" if code in self.expanded_categories else "▶",
                id={'type': 'category-collapse-button', 'category_code': code},
                style={
                    'marginLeft': '5px',
                    'border': 'none',
                    'background': 'none',
                    'padding': '0',
                    'cursor': 'pointer',
                    'fontSize': '1rem',
                }
            )
            checkbox_and_button = html.Div([checkbox, button], style={'display': 'flex', 'alignItems': 'center'})
        else:
            checkbox_and_button = checkbox

        component = [checkbox_and_button]
        logger.debug(f"Base component created for category: {code}")
        children_of_expanded = [child for code in self.parent_categories for child in self.category_structure.get(code, {}).get('children', [])]

        if has_children:
            if code in self.category_structure:
                logger.debug(f"Category {code} is checked, processing all children")
                children_components = self._create_category_components(category['children'], level + 1)

                logger.debug(f"Category {code} has children")
            if code in self.checked_categories:
                logger.debug(f"Category {code} is checked, processing all children")
                children_components = self._create_category_components(category['children'], level + 1)
            elif code in self.parent_categories:
                logger.debug(f"Category {code} is expanded but not checked, processing only checked children")
                children_to_process = [child for child in category['children']]
                logger.debug(f"Children to process for {code}: {children_to_process}")
                children_components = self._create_category_components(category['children'], level + 1)
            elif code in children_of_expanded:
                logger.debug(f"Category {code} is expanded but not checked, processing only checked children")
                children_to_process = [child for child in category['children']]
                logger.debug(f"Children to process for {code}: {children_to_process}")
                children_components = self._create_category_components(category['children'], level + 1)




            else:
                logger.debug(f"Category {code} is neither checked nor expanded, no children processed")
                children_components = []

            if children_components:
                logger.debug(f"Creating collapse for category {code} with {len(children_components)} children")
                collapse = dbc.Collapse(
                    id={'type': 'category-collapse', 'category_code': code},
                    is_open=code in self.parent_categories or code in self.checked_categories,
                    children=children_components
                )
                component.append(collapse)
            else:
                logger.debug(f"No children components created for category {code}")

        logger.debug(f"Finished creating component for category: {code} at level {level}")
        return html.Div(component, style={'marginLeft': f'{20 * level}px', 'marginTop': '5px'})


def create_checklist_layout() ->  dbc.Card:
    logger.warning(f"DEFAULT_CHECKED_CATEGORIES in create_checklist_layout: {DEFAULT_CHECKED_CATEGORIES}")
    checklist = CategoryChecklist(category_structure, selected_categories=DEFAULT_CHECKED_CATEGORIES)
    return dbc.Container([
        dcc.Store(id='selected-categories-store', data=DEFAULT_CHECKED_CATEGORIES),
        dcc.Store(id='expanded-categories-store', data=[]),  # Add this line
        html.Div(id="dummy-output"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dcc.Dropdown(
                        id='category-filter-dropdown',
                        options=[{'label': category.get('label', f"Category {code}"), 'value': code}
                                 for code, category in category_structure.items()],
                        value=DEFAULT_CHECKED_CATEGORIES,
                        multi=True,
                        placeholder="Select categories..."
                    )
                ], className="mb-2"),
                dbc.Row([
                    dbc.Button(
                        "Виды страхования",
                        id="toggle-all-categories",
                        color="secondary",
                        size="sm",
                        className="me-2 simple-button"
                    ),
                ], className="mb-2"),
                dbc.Collapse(
                    checklist.create_checklist(),
                    id="category-collapse",
                    is_open=True
                ),
            ], className="mb-3")
        ])
    ])
import re
import json
import as
def create_app_layout():
    logger.info("Creating app layout")
    layout = create_checklist_layout()
    logger.info("App layout created")
    return layou

def setup_checklist_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output('selected-categories-store', 'data'),
        Output('category-filter-dropdown', 'value'),
        Input({'type': 'category-checkbox', 'category_code': ALL}, 'value'),
        Input('category-filter-dropdown', 'value'),
        State({'type': 'category-checkbox', 'category_code': ALL}, 'id'),
    )
    def update_store_and_sync_dropdown(checkbox_values, dropdown_value, checkbox_ids):
        logger.info("update_store_and_sync_dropdown callback triggered")
        ctx = dash.callback_contex

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"Trigger ID: {trigger_id}")

        if trigger_id == 'category-filter-dropdown':
            logger.info(f"Updating store from dropdown. New value: {dropdown_value}")
            new_selected = dropdown_value or DEFAULT_CHECKED_CATEGORIES
        else:
            logger.info("Updating store from checkboxes")
            new_selected = [
                id_dict['category_code'] for value, id_dict in zip(checkbox_values, checkbox_ids)
                if value and id_dict['category_code'] in category_structure
            ]

        # Ensure that at least the default categories are always selected
        if not new_selected:
            new_selected = DEFAULT_CHECKED_CATEGORIES

        # Remove duplicates while preserving order
        new_selected = list(dict.fromkeys(new_selected))

        logger.info(f"New selected categories: {new_selected}")
        return new_selected, new_selected

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
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        logger.debug(f"selected_categories in update_category_checklist: {selected_categories}")
        logger.debug(f"expanded_categories in update_category_checklist: {expanded_categories}")

        if not selected_categories:
            selected_categories = DEFAULT_CHECKED_CATEGORIES

        if trigger_id == "toggle-all-categories":
            new_is_open = not is_open
            new_button_text = "Показать все" if not new_is_open else "Виды страхования"
        else:
            new_is_open = is_open
            new_button_text = "Показать все" if not is_open else "Виды страхования"

        checklist = CategoryChecklist(category_structure, selected_categories=selected_categories, expanded_categories=expanded_categories)
        return checklist.create_checklist(), new_is_open, new_button_tex

    @app.callback(
        Output({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
        Output({'type': 'category-collapse-button', 'category_code': MATCH}, 'children'),
        Input({'type': 'category-collapse-button', 'category_code': MATCH}, 'n_clicks'),
        State({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
    )
    def toggle_category_collapse(n_clicks, is_open):
        if not n_clicks:
            raise PreventUpdate

        new_is_open = not is_open
        new_button_text = "▼" if new_is_open else "▶"

        return new_is_open, new_button_tex






    @app.callback(
        Output('expanded-categories-store', 'data'),
        Input({'type': 'category-collapse-button', 'category_code': ALL}, 'n_clicks'),
        State({'type': 'category-collapse', 'category_code': ALL}, 'is_open'),
        State({'type': 'category-collapse-button', 'category_code': ALL}, 'id'),
        State('expanded-categories-store', 'data')
    )
    def update_expanded_categories(n_clicks_list, is_open_list, button_ids, expanded_categories):
        ctx = dash.callback_contex
        logger.debug("update_expanded_categories callback triggered")
        logger.debug(f"Initial expanded_categories: {expanded_categories}")

        if not ctx.triggered:
            logger.debug("No trigger, preventing update")
            raise PreventUpdate

        if expanded_categories is None:
            expanded_categories = []

        triggered_id = ctx.triggered[0]['prop_id']
        logger.debug(f"Triggered prop_id: {triggered_id}")

        match = re.search(r'"category_code":"([^"]*)"', triggered_id)
        if match:
            category_code = match.group(1)
            logger.debug(f"Triggered category_code: {category_code}")
        else:
            logger.error(f"Failed to extract category_code from triggered_id: {triggered_id}")
            raise PreventUpdate

        # Find the index of the triggered button
        triggered_index = next((i for i, bid in enumerate(button_ids) if bid['category_code'] == category_code), None)
        logger.error(f"Ftriggered_index: {triggered_index}")

        if triggered_index is not None:
            is_open = not is_open_list[triggered_index]  # Toggle the state
            logger.debug(f"Toggling category {category_code} to {'open' if is_open else 'closed'}")

            if is_open and category_code not in expanded_categories:
                expanded_categories.append(category_code)
                logger.debug(f"Added {category_code} to expanded_categories")
            elif not is_open and category_code in expanded_categories:
                expanded_categories.remove(category_code)
                logger.debug(f"Removed {category_code} from expanded_categories")
        else:
            logger.warning(f"Could not find triggered category {category_code} in button_ids")

        logger.debug(f"Final expanded_categories: {expanded_categories}")
        return expanded_categories

    logger.info("Dash app created with all callbacks")

def create_dash_app():
    logger.info("Creating Dash app")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    app.layout = create_checklist_layout()
    setup_checklist_callbacks(app)
    return app

if __name__ == '__main__':
    logger.info("Starting the Dash app")
    app = create_dash_app()
    app.run_server(debug=True)
    logger.info("Dash app server started")