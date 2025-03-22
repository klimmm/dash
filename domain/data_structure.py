import json
from typing import Dict, List, Union, Any
import pandas as pd


class DataStructure:
    def __init__(self, config, structure_config=None, **_):
        self.logger = config.logger
        self.config = config
        self.structure_config = structure_config or {}
        self.component_id = structure_config['component_id']
        self.data_source_map = structure_config['data_source_map']
        self.multi = structure_config.get('multi', True)
        self.app_config = config.app_config
        self._structure_dict = {}
        self._node_labels = {}
        self.build_structure(config.default_values.REPORTING_FORM)

    def build_structure(
        self,
        reporting_form: List[str],
        new_structure: Dict[str, Dict[str, Any]] = None
    ):
        if new_structure:
            self._structure_dict = new_structure
        else:
            data_source = getattr(
                self.app_config,
                self.data_source_map.get(reporting_form, {})
            )
            with open(data_source, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._structure_dict = {
                    k: {'children': v.get('children', [])}
                    for k, v in data.items()
                }
                self._node_labels = {
                    k: v['label']
                    for k, v in data.items()
                    if 'label' in v
                }
        if self.logger:
            self.logger.debug(f"Structure nodes: {len(self._structure_dict)}")
        return self
        
    def get_node_label(self, code: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(code, list):
            return [self._node_labels.get(n, n) for n in code]
        return self._node_labels.get(code, code)

    def get_ordered_nodes(
        self,
        selected_nodes: List[str] = None,
        df: pd.DataFrame = None
    ) -> List[str]:
        has_parent = {
            child
            for node in self._structure_dict.values()
            for child in node.get('children', [])
        }
        ordered_nodes = []

        def _traverse(node: str):
            if node in self._structure_dict:
                ordered_nodes.append(node)
                for child in self._structure_dict[node].get('children', []):
                    _traverse(child)
        roots = [n for n in self._structure_dict if n not in has_parent]
        for root in roots:
            _traverse(root)
        if selected_nodes is not None:
            ordered_nodes = [n for n in ordered_nodes if n in set(selected_nodes)]
        if df is not None:
            ordered_nodes = [
                n for n in ordered_nodes
                if n in set(df[self.component_id].unique())
            ]
        return ordered_nodes

    def update_selections(
        self,
        current_selected: List[str],
        trigger_node: str = None
    ) -> List[str]:
        if not trigger_node:
            return current_selected
        valid_nodes = set(self._structure_dict.keys())
        if not self.multi:
            return list({trigger_node} & valid_nodes)
        new_selected = (
            set(current_selected) - {trigger_node}
            if trigger_node in current_selected
            else set(current_selected) | {trigger_node}
        )
        return list(new_selected & valid_nodes)