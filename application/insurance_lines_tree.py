import functools
import dash_bootstrap_components as dbc
import dash
from dash import dcc, html
from typing import Dict, List, Set, Optional, TypedDict
from config.logging_config import get_logger
from config.default_values import DEFAULT_CHECKED_LINES
from data_process.insurance_line_options import get_insurance_line_options
from data_process.data_utils import load_json
from config.main_config import LINES_162_DICTIONARY

logger = get_logger(__name__)

class InsuranceLineDetails(TypedDict):
    label: str
    children: Optional[List[str]]

DEFAULT_SINGLE_LINE = DEFAULT_CHECKED_LINES[0] if isinstance(DEFAULT_CHECKED_LINES, list) else DEFAULT_CHECKED_LINES

insurance_line_structure = load_json(LINES_162_DICTIONARY)
InsuranceLineStructure = Dict[str, InsuranceLineDetails]

initial_state = list(DEFAULT_CHECKED_LINES)


class TreeItem(html.Div):
    def __init__(
        self,
        code: str,
        label: str,
        level: int,
        is_selected: bool,
        is_expanded: bool,
        has_children: bool,
        has_selected_descendants: bool
    ):
        logger.debug(f"Creating TreeItem: {code}, level: {level}")

        container_children = []

        # Always add either an expand button or a placeholder div
        if has_children:
            expand_button = html.Button(
                "▾" if is_expanded else "▸",
                id={'type': 'category-expand', 'index': code},
                className="expand-button me-2",
                n_clicks=None
            )
            container_children.append(expand_button)
        else:
            # Add placeholder div with same width as expand button
            container_children.append(
                html.Div(className="expand-button-placeholder me-2")
            )

        checkbox_classes = ["insurance-line-checkbox"]
        if has_selected_descendants:
            checkbox_classes.append("parent-of-selected")
        if is_selected:
            checkbox_classes.append("selected")

        label_classes = ["ms-2", "insurance-line-label"]

        checkbox = html.Div([
            dbc.Checkbox(
                id={'type': 'insurance-line-checkbox', 'index': code},
                value=is_selected,
                className=" ".join(checkbox_classes)
            ),
            html.Span(
                label,
                className=" ".join(label_classes)
            )
        ], className="d-flex align-items-center")

        container_children.append(checkbox)

        super().__init__(
            container_children,
            className=f"tree-item level-{level} {'has-selected' if has_selected_descendants else ''}",
            style={'margin-left': f'{level * 20}px'},
            id={'type': 'tree-item', 'index': code}
        )


class InsuranceLinesTree:
    def __init__(
        self,
        insurance_line_structure: InsuranceLineStructure,
        initial_state: Optional[Dict] = None
    ):
        logger.debug("Initializing InsuranceLinesTree")
        self.insurance_line_structure = insurance_line_structure
        self.state = initial_state or []
        self._initialize_cache()

    def _initialize_cache(self) -> None:
        self._descendants_cache = {}
        self._ancestors_cache = {}
        self._children_cache = {}

    @functools.lru_cache(maxsize=128)
    def get_children(self, parent: str) -> List[str]:
        details = self.insurance_line_structure.get(parent, {})
        return details.get('children', []) or []

    def get_descendants(self, category: str) -> Set[str]:
        if category not in self._descendants_cache:
            descendants = set()
            children = self.get_children(category)

            for child in children:
                descendants.add(child)
                descendants.update(self.get_descendants(child))

            self._descendants_cache[category] = descendants
        return self._descendants_cache[category]

    def get_ancestors(self, category: str) -> Set[str]:
        if category not in self._ancestors_cache:
            ancestors = set()
            for code, details in self.insurance_line_structure.items():
                children = details.get('children', [])
                if children and category in children:
                    ancestors.add(code)
                    ancestors.update(self.get_ancestors(code))
            self._ancestors_cache[category] = ancestors
        return self._ancestors_cache[category]

    def handle_parent_child_selections(
        self, selected_lines: List[str], 
        trigger_line: List[str] = None, 
        detailize: bool = False
    ) -> List[str]:
        # logger.error(f"trigger_line {trigger_line}")
        if not detailize:
            new_selected = set(selected_lines)
            for category in trigger_line:
                descendants = self.get_descendants(category)
                logger.debug(f"descendants {descendants}")
                new_selected.difference_update(descendants)
                ancestors = self.get_ancestors(category)
                logger.debug(f"ancestors {ancestors}")
                new_selected.difference_update(ancestors)

        else:
            new_selected = set()
            for category in selected_lines:
                children = self.get_children(category)
                if children:
                    new_selected.update(children)
                else:
                    new_selected.add(category)
        return list(new_selected)

    def create_tree(self, expansion_state: Dict[str, bool], selected: Set[str]) -> html.Div:
        logger.debug("Creating tree")
        logger.debug(f"Expansion state: {expansion_state}")
        logger.debug(f"Selected: {selected}")

        # Get all ancestors of selected items firs
        ancestors_of_selected = set()
        for item in selected:
            ancestors_of_selected.update(self.get_ancestors(item))

        def create_subtree(code: str, level: int = 0) -> Optional[List[html.Div]]:
            if code not in self.insurance_line_structure:
                return None

            details = self.insurance_line_structure[code]
            children = self.get_children(code)

            # Check if this node or any descendants are selected
            descendants = self.get_descendants(code)
            has_selected_descendants = bool(descendants & selected)
            is_ancestor_of_selected = code in ancestors_of_selected

            # Determine expansion state - expand if it's in expansion_state OR if it's an ancestor of selected
            is_expanded = expansion_state.get(code, False) if code in expansion_state else is_ancestor_of_selected

            tree_item = TreeItem(
                code=code,
                label=details['label'],
                level=level,
                is_selected=code in selected,
                is_expanded=is_expanded,
                has_children=bool(children),
                has_selected_descendants=has_selected_descendants or is_ancestor_of_selected
            )

            items = [tree_item]

            # If has children and is expanded, create child items
            if children and is_expanded:
                child_items = []
                for child in children:
                    child_subtree = create_subtree(child, level + 1)
                    if child_subtree:
                        child_items.extend(child_subtree)

                if child_items:
                    collapse = dbc.Collapse(
                        html.Div(child_items, className="tree-children"),
                        id={'type': 'category-collapse', 'index': code},
                        is_open=True  # Always open for ancestors of selected
                    )
                    items.append(collapse)

            return items

        # Get top-level categories
        top_level = [
            code for code in self.insurance_line_structure.keys()
            if not self.get_ancestors(code)
        ]

        all_items = []
        for code in top_level:
            items = create_subtree(code)
            if items:
                all_items.extend(items)

        return html.Div(all_items, className="category-tree")


insurance_lines_tree = InsuranceLinesTree(insurance_line_structure, initial_state)


def get_insurance_lines_tree_components(container_class=None, label_class=None, button_class=None, dropdown_col_class=None, dropdown_class=None):
    reporting_form = '0420162'
    """Create insurance lines tree components"""
    dropdown = html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Линия:", className=label_class),
            ], width=3, className=dropdown_col_class),
            dbc.Col([
                dcc.Dropdown(
                    id='insurance-line-dropdown',
                    options=get_insurance_line_options(reporting_form, level=2),
                    value=DEFAULT_SINGLE_LINE,
                    multi=False,
                    clearable=False
                ),
            ], width=9),            
        ], className="mb-0 g-0")
    ])

    toggle_button = dbc.Row([
        dbc.Col(
            dbc.Button(
                "Показать все",
                id='expand-all-button',
                size="sm",
                className=button_class,
                style={"display": "none"}
            ),
            className="pe-1"
        ),
    ], className="g-0")

    components = [
        toggle_button,
        dcc.Store(id='insurance-lines-state', data=initial_state),
        dcc.Store(id='expansion-state', data={'states': {}, 'all_expanded': False}),
        dcc.Store(id='tree-state', data={'states': {}, 'all_expanded': False}),
        html.Div([
            dropdown,
            html.Div(id="tree-container")
        ], className=container_class)
    ]

    return components


def create_tree_control_buttons():
    return html.Div([
        dbc.Row([
            dbc.ButtonGroup([
                dbc.Button(
                    "Показать иерархию",
                    id="collapse-button",
                    size="sm",
                    className="py-0 btn-secondary-custom",
                    style={"height": "26px"},
                    n_clicks=0
                ),
                dbc.Button(
                    "Drill down",
                    id="detailize-button",
                    size="sm",
                    className="py-0 ms-1 btn-secondary-custom",
                    style={"height": "26px"},

                )
            ])
        ], className="mb-2")
    ])


def create_insurance_lines_tree_app(
    insurance_line_structure: InsuranceLineStructure,
    default_categories: Optional[List[str]] = None
) -> dash.Dash:

    app = dash.Dash(
        __name__,  # Corrected from **name** to __name__
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )

    app.layout = dbc.Container([
        *get_insurance_lines_tree_components(insurance_line_structure, initial_state),
    ], fluid=True)

    setup_insurance_lines_callbacks(app)
    return app

def create_lines_checklist_buttons() -> dbc.Row:
    """Create hierarchy control buttons."""
    return dbc.Row(
        [
            dbc.Col([
                dbc.Button("Показать все", id="expand-all-button",
                          style={"display": "none"}, color="secondary"),
                dbc.Button("Показать иерархию", id="collapse-button",
                          style={"display": "none"}, color="info", className="ms-1"),
                dbc.Button("Drill down", id="detailize-button",
                          style={"display": "none"}, color="success", className="ms-1")
            ])
        ],
        className="mb-3"
    )


def create_debug_footer() -> html.Div:
    """Create debug footer component."""
    return html.Div(
        id="debug-footer",
        className="debug-footer",
        children=[
            dbc.Button(
                "Toggle Debug Logs",
                id="debug-toggle",
                color="secondary",
                className="btn-custom btn-debug-toggle"
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Debug Logs", className="debug-title"),
                        html.Pre(id="debug-output", className="debug-output")
                    ]),
                    className="debug-card"
                ),
                id="debug-collapse",
                is_open=False
            )
        ], style={"display": "none"},
    )

if __name__ == '__main__':
    # Configure logging at the start of the application
    logger.basicConfig(
        level=logger.debug,  # Use INFO for important events, can change to DEBUG for more detail
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Example category structure and default categories remain the same
    '''insurance_line_structure = {
        'A': {'label': 'Category A', 'children': ['A1', 'A2']},
        'A1': {'label': 'Subcategory A1', 'children': None},
        'A2': {'label': 'Subcategory A2', 'children': None},
        'B': {'label': 'Category B', 'children': ['B1', 'B2']},
        'B1': {'label': 'Subcategory B1', 'children': None},
        'B2': {'label': 'Subcategory B2', 'children': None},
    }

    DEFAULT_CHECKED_LINES = ['A1', 'B1']'''

    logger.debug("Starting application...")
    app = create_insurance_lines_tree_app(
        insurance_line_structure=insurance_line_structure,
        default_categories=DEFAULT_CHECKED_LINES
    )

    logger.debug("Running server...")
    app.run_server(debug=True)
