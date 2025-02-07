from typing import Dict, List, Set, Optional

from dash import html
import dash_bootstrap_components as dbc

from application.style.style_constants import StyleConstants
from config.default_values import DEFAULT_CHECKED_LINES, DEFAULT_REPORTING_FORM
from config.logging_config import get_logger
from domain.lines.tree import Tree, lines_tree_162, lines_tree_158

logger = get_logger(__name__)


class TreeRenderer:
    """Handles rendering of tree structure into UI components."""

    @staticmethod
    def create_tree_item(code: str, label: str, level: int, is_selected: bool,
                         is_expanded: bool, has_children: bool,
                         has_selected_descendants: bool) -> html.Div:
        """Create a single tree item component."""
        container_children = [
            # Use a constant for the expand button class.
            html.Button(
                "−" if is_expanded else "+",
                id={'type': 'node-expand', 'index': code},
                className=StyleConstants.TREE["EXPAND_BUTTON"],
                n_clicks=None
            ) if has_children else html.Div(className=StyleConstants.TREE["EXPAND_BUTTON_PLACEHOLDER"])
        ]

        # Build checkbox class names based on state.
        checkbox_classes = [StyleConstants.TREE["NODE_CHECKBOX"]]
        if has_selected_descendants:
            checkbox_classes.append(StyleConstants.TREE["PARENT_OF_SELECTED"])
        if is_selected:
            checkbox_classes.append(StyleConstants.TREE["SELECTED"])

        container_children.append(html.Div([
            dbc.Checkbox(
                id={'type': 'node-checkbox', 'index': code},
                value=is_selected,
                className=" ".join(checkbox_classes)
            ),
            html.Span(label, className=StyleConstants.TREE["INSURANCE_LINE_LABEL"])
        ], className=StyleConstants.TREE["D_FLEX_ALIGN_ITEMS_CENTER"]))

        # Build the complete class string for the tree item.
        classes = [
            StyleConstants.TREE["TREE_ITEM"],
            f"{StyleConstants.TREE['LEVEL_PREFIX']}{level}"
        ]
        if has_selected_descendants:
            classes.append(StyleConstants.TREE["HAS_SELECTED"])

        return html.Div(
            container_children,
            className=" ".join(classes),
            style={'marginLeft': f'{level * 10.4}px'},
            id={'type': 'tree-item', 'index': code}
        )

    @classmethod
    def create_tree(cls, tree: Tree, expansion_state: Dict[str, bool],
                    selected: Set[str]) -> html.Div:
        """Create the complete tree UI structure."""
        def create_subtree(code: str, level: int = 0) -> Optional[List[html.Div]]:
            if not tree.node_exists(code):
                return None

            children = tree.get_children(code)
            is_expanded = expansion_state.get('states', {}).get(code, False)

            tree_item = cls.create_tree_item(
                code=code,
                label=tree.get_node_label(code),
                level=level,
                is_selected=code in selected,
                is_expanded=is_expanded,
                has_children=bool(children),
                has_selected_descendants=bool(tree.get_descendants(code) & selected)
            )

            items = [tree_item]
            if children and is_expanded:
                child_items = []
                for child in children:
                    if subtree := create_subtree(child, level + 1):
                        child_items.extend(subtree)
                if child_items:
                    items.append(
                        dbc.Collapse(
                            html.Div(child_items, className=StyleConstants.TREE["TREE_CHILDREN"]),
                            id={'type': 'insurance-line-collapse', 'index': code},
                            is_open=True
                        )
                    )
            return items

        top_level = tree.get_top_level_nodes()
        return html.Div([item for code in top_level
                         if (items := create_subtree(code)) for item in items])


class DropdownTree(html.Div):
    """Dropdown component that displays a tree structure."""

    def __init__(self, tree: Tree, expansion_state: Dict[str, bool],
                 selected: List[str],
                 placeholder: str = "Выберите вид страхования",
                 is_open: bool = False):
        selected_tags = []
        if selected:
            for code in selected:
                if tree.node_exists(code):
                    # Here you might perform additional text cleanup if needed.
                    label = tree.get_node_label(code).replace('Добровольное', 'Добровольное').strip()
                    selected_tags.append(
                        html.Div([
                            html.Span(label, className=StyleConstants.TREE["SELECTED_TAG_LABEL"]),
                            html.Span(
                                "✕",
                                className=StyleConstants.TREE["SELECTED_TAG_REMOVE"],
                                id={'type': 'tree-dropdown-remove-tag', 'index': code}
                            )
                        ], className=StyleConstants.TREE["SELECTED_TAG"])
                    )

        header_content = [
            html.Div(
                selected_tags or [html.Div(placeholder, className=StyleConstants.TREE["DROPDOWN_PLACEHOLDER"])],
                className=StyleConstants.TREE["DROPDOWN_TAGS_CONTAINER"]
            ),
            html.Div("▲" if is_open else "▼", className=StyleConstants.TREE["DROPDOWN_ARROW"])
        ]

        super().__init__([
            html.Div(
                header_content,
                id={'type': 'tree-dropdown-header', 'index': 'header'},
                className=StyleConstants.TREE["TREE_DROPDOWN_HEADER"],
                n_clicks=0
            ),
            dbc.Collapse(
                html.Div(
                    html.Div(
                        TreeRenderer.create_tree(tree, expansion_state, set(selected)),
                        id='tree-container'
                    ),
                    className=StyleConstants.TREE["TREE_DROPDOWN_CONTENT"]
                ),
                id={'type': 'tree-dropdown-collapse', 'index': 'main'},
                is_open=is_open
            )
        ],
            className=StyleConstants.TREE["TREE_DROPDOWN_CONTAINER"],
            id="tree-dropdown"
        )

def create_dropdown_tree():
    return DropdownTree(
        tree=(lines_tree_162 if DEFAULT_REPORTING_FORM == '0420162' else lines_tree_158),
        expansion_state={'states': {}},
        selected=DEFAULT_CHECKED_LINES,
        placeholder="Выберите вид страхования",
        is_open=False
    )
