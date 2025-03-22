from typing import List, Optional
from dash import html
import dash_bootstrap_components as dbc
from presentation.style_constants import StyleConstants


class TreeComponent:
    """Handles rendering of tree structures into UI components."""

    @staticmethod
    def _create_expand_button(code: str, is_expanded: bool, 
                              component_id: str, custom: bool = False) -> html.Button:
        """Create an expansion button for tree nodes."""
        if custom:
            icon = html.I(className=f"{StyleConstants.TREE['EXPAND_ICON_PREFIX']} "
                          f"{'fa-chevron-down' if is_expanded else 'fa-chevron-right'}")
            btn_class = f"{StyleConstants.TREE['EXPAND_BUTTON']} "\
                        f"{StyleConstants.TREE.get('TOP_LEVEL_EXPAND_BUTTON', '')}"
        else:
            icon = "−" if is_expanded else "+"
            btn_class = StyleConstants.TREE["EXPAND_BUTTON"]

        return html.Button(
            icon,
            id={'type': f'{component_id}-node-expand', 'index': code},
            className=btn_class,
            n_clicks=None
        )

    @staticmethod
    def create_tree_item(
        code: str,
        label: str,
        level: int,
        is_selected: bool,
        is_expanded: bool,
        has_children: bool,
        has_selected_descendants: bool,
        component_id: str = "tree",
        custom_top_level: bool = False
    ) -> html.Div:
        """Create a single tree item component."""
        container_children = []
        label_components = []

        if custom_top_level:
            label_components.append(
                html.Span(
                    label,
                    className=f"{StyleConstants.TREE['TREE_ITEM_LABEL']} "
                            f"{StyleConstants.TREE.get('TOP_LEVEL_LABEL', '')}"
                )
            )
            if has_children:
                label_components.append(
                    TreeComponent._create_expand_button(
                        code, is_expanded, component_id, True
                    )
                )
        else:
            if has_children:
                container_children.append(
                    TreeComponent._create_expand_button(
                        code, is_expanded, component_id
                    )
                )
            else:
                container_children.append(
                    html.Div(
                        className=StyleConstants.TREE["EXPAND_BUTTON_PLACEHOLDER"]
                    )
                )

            checkbox_classes = [StyleConstants.TREE["NODE_CHECKBOX"]]
            if has_selected_descendants:
                checkbox_classes.append(StyleConstants.TREE["PARENT_OF_SELECTED"])
            if is_selected:
                checkbox_classes.append(StyleConstants.TREE["SELECTED"])

            label_components.extend([
                dbc.Checkbox(
                    id={'type': f'{component_id}-node-checkbox', 'index': code},
                    value=is_selected,
                    className=" ".join(checkbox_classes)
                ),
                html.Span(label, className=StyleConstants.TREE["TREE_ITEM_LABEL"])
            ])

        container_children.append(
            html.Div(
                label_components,
                className=StyleConstants.TREE["D_FLEX_ALIGN_ITEMS_CENTER"]
            )
        )

        classes = [
            StyleConstants.TREE["TREE_ITEM"],
            f"{StyleConstants.TREE['LEVEL_PREFIX']}{level}"
        ]

        if custom_top_level:
            classes.append(StyleConstants.TREE.get("TOP_LEVEL_NODE", ""))
        if has_selected_descendants:
            classes.append(StyleConstants.TREE["HAS_SELECTED"])

        return html.Div(
            container_children,
            className=" ".join(classes),
            style={'marginLeft': f'{level * 10.4}px'},
            id={'type': f'{component_id}-tree-item', 'index': code}
        )

    @classmethod
    def create_tree(
        cls,
        tree_data: dict,
        component_id: str = "tree",
        level_indent: float = 10.4
    ) -> html.Div:
        """Create complete tree UI structure."""
        def create_subtree(code: str, level: int = 0) -> Optional[List[html.Div]]:
            node_data = tree_data['node_data'].get(code)
            if not node_data:
                return None

            tree_item = cls.create_tree_item(
                code=code,
                label=node_data['label'],
                level=level,
                is_selected=node_data['is_selected'],
                is_expanded=node_data['is_expanded'],
                has_children=bool(node_data['children']),
                has_selected_descendants=node_data['has_selected_descendants'],
                component_id=component_id,
                custom_top_level=node_data['is_custom']
            )

            items = [tree_item]
            if node_data['children'] and node_data['is_expanded']:
                child_items = []
                for child in node_data['children']:
                    subtree = create_subtree(child, level + 1)
                    if subtree:
                        child_items.extend(subtree)
                if child_items:
                    items.append(
                        dbc.Collapse(
                            html.Div(
                                child_items,
                                className=StyleConstants.TREE["TREE_CHILDREN"]
                            ),
                            id={'type': f'{component_id}-node-collapse',
                                'index': code},
                            is_open=True
                        )
                    )
            return items

        tree_items = [
            item for code in tree_data['top_level_nodes']
            if (items := create_subtree(code)) for item in items
        ]

        return html.Div(
            tree_items,
            className=StyleConstants.TREE.get('TREE_CONTAINER', 'tree-container')
        )