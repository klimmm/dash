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
    def __init__(self, category_structure, selected_categories=None, default_categories=None):
        self.category_structure = category_structure
        logger.debug(f"selected_categories '{selected_categories}'")
        logger.debug(f"default_categories '{default_categories}'")

        if selected_categories:
            self.checked_categories = set(selected_categories)
        elif default_categories:
            self.checked_categories = set(default_categories)
        else:
            self.checked_categories = set(DEFAULT_CHECKED_CATEGORIES)

        logger.debug(f"Using categories: {self.checked_categories}")

        self.expanded_categories = self.find_ancestors_for_multiple(self.checked_categories)
        # Note: We no longer add checked_categories to expanded_categories here

        logger.info(f"Initialized CategoryChecklist with {len(self.checked_categories)} selected categories: {self.checked_categories}")
        logger.info(f"Expanded categories: {len(self.expanded_categories)}: {self.expanded_categories}")

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
        logger.debug(f"Expanded categories: {self.expanded_categories}")

        components = self._create_category_components(list(self.category_structure.keys()), level=0)

        logger.debug(f"Created {len(components)} top-level components")
        return html.Div(components, id="category-checklist", className="category-checklist")

    def _create_category_components(self, category_codes, level):
        components = []
        for code in category_codes:
            if code not in self.category_structure:
                logger.warning(f"Category code '{code}' not found in structure")
                continue

            category = self.category_structure.get(code, {})

            # Create component if it's a top-level category, in expanded categories, or checked
            if (level == 0 and (code in self.checked_categories or code in self.expanded_categories)) or
               code in self.checked_categories or
               (code in self.expanded_categories and any(child in self.checked_categories for child in category.get('children', []))):

                component = self._create_category_component(code, category, level)
                components.append(component)

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
                "▼" if code in self.expanded_categories or code in self.checked_categories else "▶",
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

        if has_children:
            if code in self.checked_categories:
                # For checked categories, process all children
                children_components = self._create_category_components(category['children'], level + 1)
            elif code in self.expanded_categories:
                # For expanded (but not checked) categories, only process checked children
                children_to_process = [child for child in category['children'] if child in self.checked_categories]
                children_components = self._create_category_components(children_to_process, level + 1)
            else:
                children_components = []

            if children_components:
                collapse = dbc.Collapse(
                    id={'type': 'category-collapse', 'category_code': code},
                    is_open=code in self.expanded_categories or code in self.checked_categories,
                    children=children_components
                )
                component.append(collapse)

        return html.Div(component, style={'marginLeft': f'{20 * level}px', 'marginTop': '5px'})category_codes:
            if code not in self.category_structure:
                logger.warning(f"Category code '{code}' not found in structure")
                continue

            category = self.category_structure.get(code, {})

            condition1 = level == 0 and (code in self.checked_categories or code in self.expanded_categories)
            condition2 = code in self.checked_categories
            condition3 = code in self.expanded_categories and any(child in self.checked_categories for child in category.get('children', []))


                component = self._create_category_component(code, category, level)
                components.append(component)
            else:


        logger.debug(f"Created {len(components)} components at level {level}")
        return components or code in self.checked_categories else "▶",
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
            checkbox_and_button = checkboxin self.checked_categories]
 or code in self.checked_categories



def create_checklist_layout() ->  dbc.Card:
    logger.warning(f"DEFAULT_CHECKED_CATEGORIES in create_checklist_layout: {DEFAULT_CHECKED_CATEGORIES}")
    checklist = CategoryChecklist(category_structure, selected_categories=DEFAULT_CHECKED_CATEGORIES)
    return dbc.Container([
        dcc.Store(id='selected-categories-store', data=DEFAULT_CHECKED_CATEGORIES),
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
        State("category-collapse", "is_open"),
    )
    def update_category_checklist(n_clicks, selected_categories, is_open):
        ctx = dash.callback_contex
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        logger.debug(f"selected_categories in update_category_checklist: {selected_categories}")

        # Ensure that at least the default categories are always selected and remove duplicates
        if not selected_categories:
            selected_categories = DEFAULT_CHECKED_CATEGORIES
        else:
            selected_categories = list(dict.fromkeys(selected_categories))

        if trigger_id == "toggle-all-categories":
            logger.info(f"toggle_category_menu triggered. n_clicks: {n_clicks}, current_is_open: {is_open}")
            new_is_open = not is_open
            new_button_text = "Показать все" if not new_is_open else "Виды страхования"
            logger.info(f"Toggling category menu. New state: {new_is_open}, New text: {new_button_text}")
        else:
            new_is_open = is_open
            new_button_text = "Показать все" if not is_open else "Виды страхования"

        logger.info(f"Updating category checklist. is_open: {new_is_open}")
        checklist = CategoryChecklist(category_structure, selected_categories=selected_categories)
        return checklist.create_checklist(), new_is_open, new_button_tex

    @app.callback(
        Output({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
        Output({'type': 'category-collapse-button', 'category_code': MATCH}, 'children'),
        Input({'type': 'category-collapse-button', 'category_code': MATCH}, 'n_clicks'),
        State({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
    )
    def toggle_category_collapse(n_clicks, is_open):
        if n_clicks:
            return not is_open, "▼" if not is_open else "▶"
        return is_open, "▼" if is_open else "▶"

    logger.info("Dash app created with all callbacks")

def create_dash_app():
    logger.info("Creating Dash app")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

    app.layout = create_checklist_layout()
    setup_checklist_callbacks(app)  # Set up callbacks from app_layou

    return app


if __name__ == '__main__':
    logger.info("Starting the Dash app")
    app = create_dash_app()
    app.run_server(debug=True)
    logger.info("Dash app server started")



