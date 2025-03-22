import dash
from dash import Input, Output, State, ALL
import json
from typing import Dict, List, Tuple, Any
from presentation.components.tree_component import TreeComponent


class TreeCallbacks:
    """Registers callbacks for tree components and handles tree data preparation."""

    def __init__(self, service):
        """Initialize with a reference to the tree service."""
        # TreePresenter functionality
        self.service = service
        self.component_id = service.component_id
        self.tree_component = TreeComponent

        self.logger = service.logger
        self.config = service.config
        self.dash_callback = self.config.dash_callback

    def handle_interaction(
        self,
        trigger: str,
        checkbox_values: List[bool],
        expand_clicks: List[int],
        reporting_form: List[str],
        checkbox_ids: List[Dict[str, str]],
        expand_ids: List[Dict[str, str]],
        current_selected: List[str],
        expansion_state: Dict[str, Dict[str, bool]]
    ) -> Tuple[List[str], Dict[str, Dict[str, bool]], Any]:
        """Handle user interactions with the tree."""

        # Use the cached component_id
        component_id = self.component_id
        selected = current_selected.copy() if current_selected else []
        states = expansion_state.get('states', {}).copy() if expansion_state else {}

        # Handle different types of interactions
        if 'reporting-form' in trigger:
            self.service.build_tree(reporting_form)
            selected = self.service.update_selections(selected)

        elif f'{component_id}-node-checkbox' in trigger:
            trigger_node = json.loads(trigger.rsplit('.', 1)[0]).get('index')
            selected = self.service.update_selections(selected, trigger_node)

        elif f'{component_id}-node-expand' in trigger:
            for i, clicks in enumerate(expand_clicks):
                if clicks and expand_ids[i]['index'] in json.loads(
                        trigger.rsplit('.', 1)[0]).get('index', ''):
                    index = expand_ids[i]['index']
                    states[index] = not states.get(index, False)

        selected = self.service.get_ordered_nodes(selected)
        states = self.service.update_expansion_states(set(selected), states)
        tree_data = self.service.prepare_tree_view_data(states, set(selected))

        # Create tree component
        tree_component = self.tree_component.create_tree(
            tree_data,
            component_id=self.component_id
        )

        return selected, {'states': states}, tree_component

    def register_callbacks(self, app) -> None:
        """Register callbacks for tree selection."""
        @app.callback(
            [Output(f'selected-{self.component_id}-store', 'data'),
             Output(f'expansion-state-{self.component_id}', 'data'),
             Output(f'{self.component_id}-tree', 'children')],
            [Input({'type': f'{self.component_id}-node-checkbox', 'index': ALL}, 'value'),
             Input({'type': f'{self.component_id}-node-expand', 'index': ALL}, 'n_clicks'),
             Input('reporting-form', 'data')],
            [State({'type': f'{self.component_id}-node-checkbox', 'index': ALL}, 'id'),
             State({'type': f'{self.component_id}-node-expand', 'index': ALL}, 'id'),
             State(f'selected-{self.component_id}-store', 'data'),
             State(f'expansion-state-{self.component_id}', 'data')],
            prevent_initial_call=False
        )
        @self.dash_callback
        def update_tree(
            checkbox_values,
            expand_clicks,
            reporting_form,
            checkbox_ids,
            expand_ids,
            current_selected,
            expansion_state
        ):
            """Callback for tree updates triggered by user interactions."""
            # Get trigger
            trigger = dash.callback_context.triggered[0]['prop_id']

            # Use the handle_interaction method
            selected, expansion_state, tree_component = self.handle_interaction(
                trigger=trigger,
                checkbox_values=checkbox_values,
                expand_clicks=expand_clicks,
                reporting_form=reporting_form,
                checkbox_ids=checkbox_ids,
                expand_ids=expand_ids,
                current_selected=current_selected,
                expansion_state=expansion_state
            )

            return selected, expansion_state, tree_component