import functools
import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, List, Set, Optional, TypedDict
from config.logging_config import get_logger
from config.default_values import DEFAULT_CHECKED_LINES
from data_process.io import load_json
from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY

logger = get_logger(__name__)

DEFAULT_SINGLE_LINE = DEFAULT_CHECKED_LINES[0] if isinstance(DEFAULT_CHECKED_LINES, list) else DEFAULT_CHECKED_LINES
initial_state = list(DEFAULT_CHECKED_LINES)
insurance_line_structure_162 = load_json(LINES_162_DICTIONARY)
insurance_line_structure_158 = load_json(LINES_158_DICTIONARY)


class InsuranceLineDetails(TypedDict):
    label: str
    children: Optional[List[str]]


InsuranceLineStructure = Dict[str, InsuranceLineDetails]


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
            style={'marginLeft': f'{level * 20}px'},
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
            if not detailize:
                new_selected = selected_lines.copy()  # Create a copy of the list
                for category in trigger_line:
                    descendants = self.get_descendants(category)
                    logger.debug(f"descendants {descendants}")
                    # Remove descendants using list comprehension
                    new_selected = [line for line in new_selected if line not in descendants]
                    
                    ancestors = self.get_ancestors(category)
                    logger.debug(f"ancestors {ancestors}")
                    # Remove ancestors using list comprehension
                    new_selected = [line for line in new_selected if line not in ancestors]
            else:
                new_selected = []
                for category in selected_lines:
                    children = self.get_children(category)
                    logger.debug(f"children {children}")
                    if children:
                        # Extend list with children while avoiding duplicates
                        for child in children:
                            if child not in new_selected:
                                new_selected.append(child)
                    else:
                        # Add category if not already in list
                        if category not in new_selected:
                            new_selected.append(category)

            logger.debug(f"new_selected {new_selected}")
            return new_selected

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
            logger.debug(f"Label: {details['label']} for code: {code}")

            logger.debug(f"Creating TreeItem with props - code: {code}, label: {details['label']}, "
             f"level: {level}, is_selected: {code in selected}, is_expanded: {is_expanded}, "
             f"has_children: {bool(children)}, has_selected_descendants: {has_selected_descendants}")
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
                          style={"display": "none"}, color="info", className="ms-1"),
            ])
        ],
        className="mb-3"
    )


lines_tree_162 = InsuranceLinesTree(insurance_line_structure_162, initial_state)
lines_tree_158 = InsuranceLinesTree(insurance_line_structure_158, initial_state)