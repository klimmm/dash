
from checklistutils import category_structure, DEFAULT_CHECKED_CATEGORIES


from typing import Dict, List, Set, Optional, Any, TypedDic
import dash
from dash import dcc, html, Input, Output, State, ALL, MATCH, ClientsideFunction
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import logging
import json
from dataclasses import dataclass, asdic
import re


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Type definitions
class CategoryDetails(TypedDict):
    label: str
    children: Optional[List[str]]

CategoryStructure = Dict[str, CategoryDetails]

@dataclass
class CategoryState:
    """Centralized state management for category selection"""
    selected: Set[str]
    expanded: Set[str]

    @classmethod
    def from_store(cls, data: Dict) -> 'CategoryState':
        return cls(
            selected=set(data.get('selected', [])),
            expanded=set(data.get('expanded', []))
        )

    def to_store(self) -> Dict:
        return {
            'selected': list(self.selected),
            'expanded': list(self.expanded)
        }

class CategoryChecklist:
    def __init__(
        self,
        category_structure: CategoryStructure,
        initial_state: Optional[CategoryState] = None
    ):
        self.category_structure = category_structure
        self.state = initial_state or CategoryState(set(), set())

    def get_children(self, parent: str) -> List[str]:
        """Safely get children of a category"""
        details = self.category_structure.get(parent, {})
        children = details.get('children')
        return children if children else []

    def get_all_descendants(self, category: str) -> Set[str]:
        """Get all descendant categories recursively"""
        descendants = set()
        children = self.get_children(category)

        for child in children:
            descendants.add(child)
            descendants.update(self.get_all_descendants(child))

        return descendants

    def get_ancestors(self, category: str) -> Set[str]:
        """Get all ancestor categories for a given category"""
        ancestors = set()
        for code, details in self.category_structure.items():
            children = details.get('children', [])
            if children and category in children:
                ancestors.add(code)
                ancestors.update(self.get_ancestors(code))
        return ancestors

    def handle_parent_child_selections(self, selected_categories: List[str], detailize: bool = False) -> List[str]:
        """Handle parent-child selections according to original logic"""
        if not detailize:
            # Remove all descendants if their ancestor is selected
            new_selected = set(selected_categories)
            for category in selected_categories:
                if category in self.category_structure:
                    descendants = self.get_all_descendants(category)
                    removed_descendants = new_selected.intersection(descendants)
                    new_selected.difference_update(removed_descendants)
                    if removed_descendants:
                        logging.debug(f"Removed descendants of {category}: {removed_descendants}")
        else:
            # Add children for categories that have them, or keep the category if it's a leaf
            new_selected = set()
            for category in selected_categories:
                children = self.get_children(category)
                if children:
                    new_selected.update(children)
                    logging.debug(f"Detailized {category}. Added children: {children}")
                else:
                    new_selected.add(category)
                    logging.debug(f"Category {category} has no children, keeping it as is")

        return list(new_selected)

    def create_checklist(self) -> html.Div:
        """Create tree-structured checklist"""
        def create_tree_item(code: str, level: int = 0) -> Optional[html.Div]:
            if code not in self.category_structure:
                return None

            details = self.category_structure[code]
            children = self.get_children(code)

            # Create checkbox with proper styling
            checkbox_container = html.Div([
                dbc.Checkbox(
                    id={'type': 'category-checkbox', 'code': code},
                    value=code in self.state.selected,
                    className="category-checkbox"
                ),
                html.Span(
                    details['label'],
                    className="ms-2 category-label"
                )
            ], className="d-flex align-items-center")

            container_children = [checkbox_container]

            if children:
                is_expanded = code in self.state.expanded
                expand_button = html.Button(
                    "▼" if is_expanded else "▶",
                    id={'type': 'category-expand', 'code': code},
                    className="expand-button me-2"
                )
                container_children.insert(0, expand_button)

                child_components = []
                for child in children:
                    child_component = create_tree_item(child, level + 1)
                    if child_component:
                        child_components.append(child_component)

                if child_components:
                    collapse = dbc.Collapse(
                        html.Div(
                            child_components,
                            className="tree-children"
                        ),
                        id={'type': 'category-collapse', 'code': code},
                        is_open=is_expanded
                    )
                    container_children.append(collapse)

            return html.Div(
                container_children,
                className=f"tree-item level-{level}",
                style={'margin-left': f'{level * 20}px'}
            )

        # Get top-level categories
        all_children = set()
        for details in self.category_structure.values():
            children = details.get('children')
            if children:
                all_children.update(children)

        top_level = [
            code for code in self.category_structure.keys()
            if code not in all_children
        ]

        # Create tree structure
        tree_items = [
            create_tree_item(code)
            for code in top_level
            if create_tree_item(code) is not None
        ]

        return html.Div(
            tree_items,
            className="category-tree",
            id="category-tree-container"
        )

def create_checklist_app(
    category_structure: CategoryStructure,
    default_categories: Optional[List[str]] = None
) -> dash.Dash:
    """Create the Dash application with checklist functionality"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )

    # Initialize state
    initial_state = CategoryState(
        selected=set(default_categories or []),
        expanded=set()
    )

    # Create checklist instance
    checklist = CategoryChecklist(category_structure, initial_state)

    # Create dropdown options
    dropdown_options = [
        {'label': details['label'], 'value': code}
        for code, details in category_structure.items()
    ]

    # Define app layout with styles in className and style props
    app.layout = dbc.Container([
        html.Div([
            # State stores
            dcc.Store(
                id='category-state',
                data=initial_state.to_store()
            ),

            # UI Components
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='category-dropdown',
                        options=dropdown_options,
                        value=list(initial_state.selected),
                        multi=True,
                        placeholder="Select categories...",
                        className="mb-3"
                    )
                ])
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Drill down",
                        id="detailize-button",
                        color="secondary",
                        className="me-2 mb-3"
                    ),
                    dbc.Button(
                        "Expand All",
                        id="expand-all-button",
                        color="secondary",
                        className="mb-3"
                    ),
                ])
            ]),

            dbc.Row([
                dbc.Col([
                    html.Div(
                        checklist.create_checklist(),
                        id="checklist-container",
                        style={
                            'padding': '1rem'
                        }
                    )
                ])
            ])
        ])
    ], fluid=True)

    # Create assets folder and add CSS file
    import os
    assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)

    css_path = os.path.join(assets_path, 'styles.css')
    with open(css_path, 'w') as f:
        f.write('''
.category-tree {
    padding: 1rem;
}
.tree-item {
    margin: 0.5rem 0;
}
.tree-children {
    margin-left: 2rem;
    border-left: 1px solid #dee2e6;
    padding-left: 1rem;
}
.expand-button {
    background: none;
    border: none;
    padding: 0 0.5rem;
    cursor: pointer;
}
.category-label {
    user-select: none;
}
.level-0 {
    font-weight: bold;
}
''')

    register_callbacks(app, checklist)

    return app



def register_callbacks(app: dash.Dash, checklist: CategoryChecklist) -> None:
    """Register all callbacks for the application"""

    @app.callback(
        [
            Output('category-state', 'data'),
            Output('category-dropdown', 'value'),
            Output({'type': 'category-checkbox', 'code': ALL}, 'value')
        ],
        [
            Input({'type': 'category-checkbox', 'code': ALL}, 'value'),
            Input('category-dropdown', 'value'),
            Input('detailize-button', 'n_clicks')
        ],
        [
            State({'type': 'category-checkbox', 'code': ALL}, 'id'),
            State('category-state', 'data')
        ],
        prevent_initial_call=True
    )
    def update_category_state(
        checkbox_values: List[bool],
        dropdown_value: List[str],
        detailize_clicks: int,
        checkbox_ids: List[Dict],
        current_state: Dic
    ) -> tuple:
        """Update category state based on user interactions"""
        ctx = dash.callback_contex
        if not ctx.triggered:
            raise PreventUpdate

        state = CategoryState.from_store(current_state)
        trigger = ctx.triggered[0]['prop_id']

        try:
            if 'category-dropdown' in trigger:
                selected = dropdown_value or []
            elif 'category-checkbox' in trigger:
                selected = [
                    id_dict['code']
                    for value, id_dict in zip(checkbox_values, checkbox_ids)
                    if value
                ]
            else:
                selected = list(state.selected)

            # Apply parent-child selection logic
            detailize = 'detailize-button' in trigger
            final_selected = checklist.handle_parent_child_selections(selected, detailize)

            # Update state
            state.selected = set(final_selected)

            # Create checkbox values array
            checkbox_values = [
                code in final_selected
                for id_dict in checkbox_ids
                for code in [id_dict['code']]
            ]

            return state.to_store(), final_selected, checkbox_values

        except Exception as e:
            logging.exception("Error updating category state")
            raise PreventUpdate

    @app.callback(
        [
            Output({'type': 'category-collapse', 'code': MATCH}, 'is_open'),
            Output({'type': 'category-expand', 'code': MATCH}, 'children')
        ],
        Input({'type': 'category-expand', 'code': MATCH}, 'n_clicks'),
        State({'type': 'category-collapse', 'code': MATCH}, 'is_open'),
        prevent_initial_call=True
    )
    def toggle_category(n_clicks: int, is_open: bool) -> tuple:
        """Toggle category expansion state"""
        if not n_clicks:
            raise PreventUpdate

        new_is_open = not is_open
        return new_is_open, "▼" if new_is_open else "▶"

    @app.callback(
        Output('checklist-container', 'children'),
        [Input('expand-all-button', 'n_clicks')],
        [State('category-state', 'data')],
        prevent_initial_call=True
    )
    def rebuild_checklist(n_clicks, state_data):
        """Only rebuild checklist when explicitly requested"""
        if not n_clicks:
            raise PreventUpdate

        state = CategoryState.from_store(state_data)
        checklist.state = state
        return checklist.create_checklist()

# Modify the CategoryChecklist.create_checklist method to preserve expansion state

# Test the implementation
if __name__ == '__main__':
    # Sample category structure

    # Create and run app
    app = create_checklist_app(
        category_structure=category_structure,
        default_categories=DEFAULT_CHECKED_CATEGORIES
    )
    app.run_server(debug=True)