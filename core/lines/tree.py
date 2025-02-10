import functools
from typing import Any, Dict, List, Optional, Set, Union

LineStructureType = Dict[str, Dict[str, Union[str, Optional[List[str]]]]]
CacheType = Dict[str, Set[str]]


class Tree:
    def __init__(self,
                 line_structure: LineStructureType,
                 default_checked: Optional[Dict[Any, Any]] = None) -> None:
        self.line_structure: LineStructureType = line_structure
        self.state: Dict[Any, Any] = default_checked or {}
        self._descendants_cache: CacheType = {}
        self._ancestors_cache: CacheType = {}

    @functools.lru_cache(maxsize=128)
    def get_children(self, parent: str) -> List[str]:
        """Get immediate children of a node."""
        children = self.line_structure.get(parent, {}).get('children', [])
        return children if isinstance(children, list) else []

    def get_descendants(self, category: str) -> Set[str]:
        """Get all descendants (children, grandchildren, etc.) of a node."""
        if category not in self._descendants_cache:
            descendants = set()
            for child in self.get_children(category):
                descendants.add(child)
                descendants.update(self.get_descendants(child))
            self._descendants_cache[category] = descendants
        return self._descendants_cache[category]

    def get_ancestors(self, category: str) -> Set[str]:
        """Get all ancestors (parents, grandparents, etc.) of a node."""
        if category not in self._ancestors_cache:
            ancestors = set()
            for code, details in self.line_structure.items():
                children = details.get('children', [])
                if children and category in children:
                    ancestors.add(code)
                    ancestors.update(self.get_ancestors(code))
            self._ancestors_cache[category] = ancestors
        return self._ancestors_cache[category]

    def handle_parent_child_selections(
        self,
        selected_lines: List[str],
        trigger_line: Optional[List[str]] = None,
        detailize: bool = False
    ) -> List[str]:
        """Handle selection logic for parent-child relationships."""
        if not detailize:
            new_selected = selected_lines.copy()
            for category in (trigger_line or []):
                descendants = self.get_descendants(category)
                ancestors = self.get_ancestors(category)
                new_selected = [line for line in new_selected if line
                                not in descendants and line not in ancestors]
        else:
            new_selected = []
            for category in selected_lines:
                children = self.get_children(category)
                if children:
                    new_selected.extend(child for child in children
                                        if child not in new_selected)
                elif category not in new_selected:
                    new_selected.append(category)
        return new_selected

    def get_top_level_nodes(self) -> List[str]:
        """Get all root nodes (nodes without parents)."""
        return [code for code in self.line_structure 
                if not self.get_ancestors(code)]

    def get_node_label(self, code: str) -> str:
        """Get the label for a given node."""
        label = self.line_structure.get(code, {}).get('label', '')
        return str(label) if label is not None else ''

    def node_exists(self, code: str) -> bool:
        """Check if a node exists in the tree."""
        return code in self.line_structure