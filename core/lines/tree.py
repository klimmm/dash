import functools
from typing import Any, Dict, List, Optional, Set, Union

TreeStructureType = Dict[str, Dict[str, Union[str, Optional[List[str]]]]]
CacheType = Dict[str, Set[str]]


class Tree:
    def __init__(self,
                 tree_structure: TreeStructureType,
                 default_checked: Optional[Dict[Any, Any]] = None) -> None:
        self.tree_structure: TreeStructureType = tree_structure
        self.state: Dict[Any, Any] = default_checked or {}
        self._descendants_cache: CacheType = {}
        self._ancestors_cache: CacheType = {}

    @functools.lru_cache(maxsize=128)
    def get_children(self, parent: str) -> List[str]:
        """Get immediate children of a node."""
        children = self.tree_structure.get(parent, {}).get('children', [])
        return children if isinstance(children, list) else []

    def get_descendants(self, node: str) -> Set[str]:
        """Get all descendants (children, grandchildren, etc.) of a node."""
        if node not in self._descendants_cache:
            descendants = set()
            for child in self.get_children(node):
                descendants.add(child)
                descendants.update(self.get_descendants(child))
            self._descendants_cache[node] = descendants
        return self._descendants_cache[node]

    def get_ancestors(self, node: str) -> Set[str]:
        """Get all ancestors (parents, grandparents, etc.) of a node."""
        if node not in self._ancestors_cache:
            ancestors = set()
            for code, details in self.tree_structure.items():
                children = details.get('children', [])
                if children and node in children:
                    ancestors.add(code)
                    ancestors.update(self.get_ancestors(code))
            self._ancestors_cache[node] = ancestors
        return self._ancestors_cache[node]

    def handle_parent_child_selections(
        self,
        selected_nodes: List[str],
        trigger_node: Optional[List[str]] = None,
        detailize: bool = False
    ) -> List[str]:
        """Handle selection logic for parent-child relationships."""
        if not detailize:
            new_selected = selected_nodes.copy()
            for node in (trigger_node or []):
                descendants = self.get_descendants(node)
                ancestors = self.get_ancestors(node)
                new_selected = [node for node in new_selected if node
                                not in descendants and node not in ancestors]
        else:
            new_selected = []
            for node in selected_nodes:
                children = self.get_children(node)
                if children:
                    new_selected.extend(child for child in children
                                        if child not in new_selected)
                elif node not in new_selected:
                    new_selected.append(node)
        return new_selected

    def get_top_level_nodes(self) -> List[str]:
        """Get all root nodes (nodes without parents)."""
        return [code for code in self.tree_structure 
                if not self.get_ancestors(code)]

    def get_node_label(self, code: str) -> str:
        """Get the label for a given node."""
        label = self.tree_structure.get(code, {}).get('label', '')
        return str(label) if label is not None else ''

    def node_exists(self, code: str) -> bool:
        """Check if a node exists in the tree."""
        return code in self.tree_structure