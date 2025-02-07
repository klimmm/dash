# tree.py - Data structure handling
from typing import Dict, List, Set, Optional, Union
import functools

from config.default_values import DEFAULT_CHECKED_LINES
from config.logging_config import get_logger
from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY
from domain.io import load_json


class Tree:
    """Tree data structure for managing hierarchical line data."""
    def __init__(self, line_structure: Dict[str, Dict[str, Union[str, Optional[List[str]]]]], 
                 default_checked: Optional[Dict] = None):
        self.line_structure = line_structure
        self.state = default_checked or []
        self._descendants_cache = {}
        self._ancestors_cache = {}

    @functools.lru_cache(maxsize=128)
    def get_children(self, parent: str) -> List[str]:
        """Get immediate children of a node."""
        return self.line_structure.get(parent, {}).get('children', []) or []

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
                if category in (details.get('children', []) or []):
                    ancestors.add(code)
                    ancestors.update(self.get_ancestors(code))
            self._ancestors_cache[category] = ancestors
        return self._ancestors_cache[category]

    def handle_parent_child_selections(self, selected_lines: List[str], 
                                     trigger_line: List[str] = None, 
                                     detailize: bool = False) -> List[str]:
        """Handle selection logic for parent-child relationships."""
        if not detailize:
            new_selected = selected_lines.copy()
            for category in (trigger_line or []):
                descendants = self.get_descendants(category)
                ancestors = self.get_ancestors(category)
                new_selected = [line for line in new_selected 
                              if line not in descendants and line not in ancestors]
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
        return self.line_structure.get(code, {}).get('label', '')

    def node_exists(self, code: str) -> bool:
        """Check if a node exists in the tree."""
        return code in self.line_structure


lines_tree_162 = Tree(load_json(LINES_162_DICTIONARY), DEFAULT_CHECKED_LINES)
lines_tree_158 = Tree(load_json(LINES_158_DICTIONARY), DEFAULT_CHECKED_LINES)