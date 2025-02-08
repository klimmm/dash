import json
from typing import List, Optional, Dict, Any, Tuple

import dash
from dash import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from application.components.lines_tree import DropdownTree
from config.callback_logging import log_callback, error_handler
from config.default_values import DEFAULT_REPORTING_FORM
from config.logging_config import get_logger, timer

logger = get_logger(__name__)


def setup_line_selection(app: dash.Dash, lines_tree_162, lines_tree_158):

    def get_tree(reporting_form: str):
        return lines_tree_162 if reporting_form == '0420162' else lines_tree_158

    @app.callback(
        Output('selected-lines-store', 'data'),
        [Input({'type': 'tree-dropdown-remove-tag', 'index': ALL}, 'n_clicks'),
         Input({'type': 'node-checkbox', 'index': ALL}, 'value'),
         Input('reporting-form-selected', 'data')],
        [State({'type': 'node-checkbox', 'index': ALL}, 'id'),
         State('selected-lines-store', 'data')],
        prevent_initial_call=True
    )
    @error_handler
    @timer
    @log_callback
    def update_line_selection(
        remove_clicks: List[int],
        checkbox_values: List[bool],
        reporting_form: str,
        checkbox_ids: List[Dict],
        current_state: List[str]
    ) -> List[str]:

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        tree = get_tree(reporting_form or DEFAULT_REPORTING_FORM)

        trigger = ctx.triggered[0]['prop_id']

        if 'reporting-form' in trigger:
            final_selected = tree.handle_parent_child_selections(
                current_state)
            return final_selected

        trigger_line = json.loads(trigger.rsplit('.', 1)[0]).get('index')

        if 'remove-tag' in trigger:

            if any(click for click in remove_clicks if click):
                final_selected = [line for line in current_state if line != trigger_line]
            else:
                final_selected = current_state
        else:
            new_selected = [id_dict['index'] for value, id_dict in zip(
                checkbox_values, checkbox_ids) if value]

            final_selected = tree.handle_parent_child_selections(
                new_selected, [trigger_line])

        logger.warning(f"final_selected {final_selected}")

        return final_selected

    @app.callback(
        [Output('nodes-expansion-state', 'data'),
         Output('tree-dropdown', 'children'),
         Output({'type': 'tree-dropdown-collapse', 'index': 'main'}, 'is_open')],
        [Input({'type': 'node-expand', 'index': ALL}, 'n_clicks'),
         Input('selected-lines-store', 'data'),
         Input({'type': 'tree-dropdown-remove-tag', 'index': ALL}, 'n_clicks'),
         Input({'type': 'tree-dropdown-header', 'index': 'header'}, 'n_clicks')],
        [State({'type': 'node-expand', 'index': ALL}, 'id'),
         State('nodes-expansion-state', 'data'),
         State('reporting-form-selected', 'data'),
         State({'type': 'tree-dropdown-collapse', 'index': 'main'}, 'is_open')],
        prevent_initial_call=True
    )
    @error_handler
    @timer
    @log_callback
    def update_tree_state(
        expand_clicks: List[Optional[int]],
        selected: List[str],
        remove_clicks: List[int],
        header_clicks: int,
        expand_ids: List[Dict[str, str]],
        expansion_state: Dict[str, Any],
        reporting_form: Optional[Dict[str, Any]],
        is_dropdown_open: bool
    ) -> Tuple[Dict[str, Any], Any, bool]:

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger = ctx.triggered[0]['prop_id']
        tree = get_tree(reporting_form or DEFAULT_REPORTING_FORM)

        if 'remove-tag' in trigger:
            pass
        elif 'tree-dropdown-header' in trigger:
            is_dropdown_open = not is_dropdown_open
        else:
            is_dropdown_open = is_dropdown_open

        if 'node-expand' in trigger:
            expansion_state.setdefault('states', {}).update({
                expand_ids[i]['index']: not expansion_state['states'].get(
                    expand_ids[i]['index'], False)
                for i, clicks in enumerate(expand_clicks) if clicks
            })
            # Update ancestors only for non-existing states
            expansion_state['states'].update({
                ancestor: True
                for item in selected
                for ancestor in tree.get_ancestors(item)
                if ancestor not in expansion_state['states']
            })
        else:
            # For other triggers, always update ancestor states
            expansion_state.setdefault('states', {}).update({
                ancestor: True
                for item in selected
                for ancestor in tree.get_ancestors(item)
            })

        # Create tree component
        tree_component = DropdownTree(
            tree=tree,
            expansion_state=expansion_state,
            selected=selected,
            is_open=is_dropdown_open
        )

        return expansion_state, tree_component, is_dropdown_open