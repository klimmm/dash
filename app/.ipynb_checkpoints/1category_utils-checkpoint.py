import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json
from logging_config import get_logger
from .data_utils import category_structure
from .filter_options import CATEGORIES_TO_EXPAND, DEFAULT_CHECKED_CATEGORIES, CATEGORIES_TO_EXPAND_OPTIONS

logger = get_logger(__name__)


class CategoryChecklist:
    def __init__(self, category_structure, DEFAULT_CHECKED_CATEGORIES, DEFAULT_EXPANDED_CATEGORIES):
        self.category_structure = category_structure
        self.DEFAULT_CHECKED_CATEGORIES = DEFAULT_CHECKED_CATEGORIES
        self.DEFAULT_EXPANDED_CATEGORIES = DEFAULT_EXPANDED_CATEGORIES

    def create_checklist(self):
        logger.info("Starting to create checklist")
        components = self._create_category_components(list(self.category_structure.keys()), level=0)
        return html.Div([
            # Removed duplicate 'selected-categories-header' to fix DuplicateIdError
            html.Div(components, id="category-checklist", className="category-checklist")
        ])

    def _create_category_components(self, category_codes, level):
        components = []
        for code in category_codes:
            if level == 0 and any(code in cat.get('children', []) for cat in self.category_structure.values()):
                continue  # Skip non-top-level categories when at level 0
            category = self.category_structure[code]
            component = self._create_category_component(code, category, level)
            components.append(component)
        return components

    def _create_category_component(self, code, category, level):
        has_children = bool(category.get('children'))
        is_open = level > 0

        component = []

        checkbox_and_button = [
            dbc.Checkbox(
                id={'type': 'category-checkbox', 'category_code': code},
                label=f"{category['label']}",
                value=code in self.DEFAULT_CHECKED_CATEGORIES  # Set default value based on self.DEFAULT_CHECKED_CATEGORIES
            )
        ]

        if has_children:
            checkbox_and_button.append(
                html.Button(
                     "▼" if is_open else "▶",  # Change button text based on expanded state
                    id={'type': 'category-collapse-button', 'category_code': code},
                    style={
                        'marginLeft': '5px',
                        'border': 'none',
                        'background': 'none',
                        'padding': '0',
                        'cursor': 'pointer',
                    }
                )
            )

        component.append(
            html.Div(
                checkbox_and_button,
                style={
                    'display': 'flex',
                    'alignItems': 'center',
                }
            )
        )

        if has_children:
            children_components = self._create_category_components(category.get('children', []), level+1)
            component.append(
                dbc.Collapse(
                    id={'type': 'category-collapse', 'category_code': code},
                    is_open = code in self.DEFAULT_EXPANDED_CATEGORIES,
                    children=children_components
                )
            )

        return html.Div(component, style={'marginLeft': f'{20 * level}px'})


def setup_callbacks(app: dash.Dash) -> None:
    # Callback for expanding/collapsing individual categories remains unchanged
    @app.callback(
        Output({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
        Output({'type': 'category-collapse-button', 'category_code': MATCH}, 'children'),
        Input({'type': 'category-collapse-button', 'category_code': MATCH}, 'n_clicks'),
        State({'type': 'category-collapse', 'category_code': MATCH}, 'is_open'),
        prevent_initial_call=True
    )
    def toggle_collapse(n_clicks, is_open):
        if n_clicks:
            new_is_open = not is_open
            new_button_text = "▼" if new_is_open else "▶"
            return new_is_open, new_button_tex
        return is_open, "▼" if is_open else "▶"

    # Callback for the toggle-all button to show/hide the entire menu
    @app.callback(
        Output("category-collapse", "is_open"),
        Output("toggle-all-categories", "children"),
        Input("toggle-all-categories", "n_clicks"),
        State("category-collapse", "is_open"),
        prevent_initial_call=False
    )
    def toggle_category_menu(n_clicks, current_is_open):
        logger.info(f"toggle_category_menu called with n_clicks: {n_clicks}")

        if n_clicks is None:
            # Initial state: collapsed
            return False, "Показать все линии"

        # Toggle visibility
        new_is_open = not current_is_open
        new_button_text = "Показать все" if not new_is_open else "Виды страхования"
        return new_is_open, new_button_tex

    # Callback for toggling the additional categories filter
    @app.callback(
        Output("additional-categories-collapse", "is_open"),
        Input("toggle-additional-categories", "n_clicks"),
        State("additional-categories-collapse", "is_open"),
        prevent_initial_call=True
    )
    def toggle_additional_categories(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    # Callback to update selected-linemain-store
    @app.callback(
        Output('selected-linemain-store', 'data'),
        Input({'type': 'category-checkbox', 'category_code': ALL}, 'value'),
        State({'type': 'category-checkbox', 'category_code': ALL}, 'id'),
        Input('categories-to-expand-filter', 'value'),
    )
    def update_selected_linemain(category_values, category_ids, expand_categories):
        """
        Update the selected categories based on category checklist and categories to expand.
        """
        logger.info(f"Function called with category_values: {category_values}, category_ids: {category_ids}, expand_categories: {expand_categories}")

        # Extract selected categories from category checklis
        selected_categories = [id['category_code'] for value, id in zip(category_values, category_ids) if value]
        logger.info(f"Initially selected categories: {selected_categories}")


        return list(selected_categories)












__all__ = ['CategoryChecklist', 'category_structure', 'setup_callbacks']
