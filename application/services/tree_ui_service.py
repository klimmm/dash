from typing import Dict, List, Set, Optional, Union, Any
from functools import lru_cache


class TreeUIService:
    """UI-specific tree functionality using composition instead of inheritance."""

    def __init__(self, structure_service, tree_config: Optional[dict] = None):
        self._cache = {'descendants': {}, 'ancestors': {}}
        # Accept an existing StructureService instance through dependency injection
        self._structure_service = structure_service
        self.use_custom_top_level = tree_config.get('use_custom_top_level') if tree_config else False

    @property
    def _tree_structure_dict(self):
        """Access the tree structure from the composed StructureService."""
        return self._structure_service._structure_dict

    @lru_cache(maxsize=128)
    def _get_children(self, parent: str) -> List[str]:
        """Get immediate children of a node."""
        return self._tree_structure_dict.get(parent, {}).get('children', [])

    def _get_ancestors(self, nodes: Union[str, Set[str]]) -> Set[str]:
        """Get all ancestors of given node(s)."""
        nodes_set = {nodes} if isinstance(nodes, str) else set(nodes)
        ancestors = set()

        for node in nodes_set:
            if node not in self._cache['ancestors']:
                parent_nodes = {
                    code for code, details in self._tree_structure_dict.items()
                    if node in details.get('children', [])
                }
                self._cache['ancestors'][node] = (
                    parent_nodes | self._get_ancestors(parent_nodes)
                    if parent_nodes else set()
                )
            ancestors.update(self._cache['ancestors'][node])
        return ancestors

    def _get_top_level_nodes(self) -> List[str]:
        """Get root nodes (nodes without parents)."""
        return [n for n in self._tree_structure_dict if not self._get_ancestors(n)]

    def _get_descendants(self, node: str) -> Set[str]:
        """Get all descendants of a node recursively."""
        if node not in self._cache['descendants']:
            children = set(self._get_children(node))
            self._cache['descendants'][node] = children.union(
                *(self._get_descendants(child) for child in children)
            )
        return self._cache['descendants'][node]

    def build_tree(
        self,
        reporting_form: List[str],
        new_tree_structure: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Any:
        """Build tree and clear caches."""
        # Delegate to the composed StructureService, but use its build_structure method
        result = self._structure_service.build_structure(reporting_form, new_tree_structure)
        self._clear_caches()
        return result

    def update_selections(
        self,
        selected_nodes: List[str],
        trigger_node: Optional[List[str]] = None,
        uncheck_ancestors: bool = True,
        uncheck_descendants: bool = True
    ) -> List[str]:
        """Update selections considering ancestors and descendants."""
        # Delegate to composed StructureService first
        selections = set(self._structure_service.update_selections(selected_nodes, trigger_node))

        if trigger_node:
            for node in trigger_node:
                if uncheck_ancestors:
                    selections -= self._get_ancestors(node)
                if uncheck_descendants:
                    selections -= self._get_descendants(node)

        return list(selections)

    def update_expansion_states(
        self,
        selected_nodes: Set[str],
        current_states: Optional[Dict[str, bool]] = None,
        expand_ancestors: bool = True
    ) -> Dict[str, bool]:
        """Update node expansion states."""
        states = current_states.copy() if current_states else {}

        if expand_ancestors:
            for node in selected_nodes:
                for ancestor in self._get_ancestors(node):
                    states.setdefault(ancestor, True)
        return states

    def prepare_tree_view_data(
        self,
        states: Optional[Dict[str, bool]] = None,
        selected: Optional[List[str]] = None
    ) -> Dict[str, Union[List[str], Dict[str, Dict]]]:
        """Prepare data structure for UI rendering."""
        states = states or {}
        selected = set(selected or [])
        top_level = self._get_top_level_nodes()

        return {
            'top_level_nodes': top_level,
            'node_data': {
                node: {
                    'label': self.get_node_label(node),
                    'children': self._get_children(node),
                    'is_expanded': states.get(node, False),
                    'is_selected': node in selected,
                    'has_selected_descendants': bool(
                        self._get_descendants(node) & selected
                    ),
                    'is_custom': self.use_custom_top_level and node in top_level
                }
                for node in self._tree_structure_dict
            }
        }
    
    def get_node_label(self, node: str) -> str:
        """Get the label for a node, delegating to StructureService."""
        return self._structure_service.get_node_label(node)

    def _clear_caches(self):
        """Clear all internal caches."""
        self._cache['descendants'].clear()
        self._cache['ancestors'].clear()
        self._get_children.cache_clear()
        
    # Delegate any other StructureService methods you need
    def __getattr__(self, name):
        """Delegate any other method calls to the StructureService instance."""
        return getattr(self._structure_service, name)