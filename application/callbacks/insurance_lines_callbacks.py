import dash
from dash import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import json
from typing import Dict, Any
from config.logging_config import get_logger, track_callback, track_callback_end
from config.default_values import DEFAULT_CHECKED_LINES
logger = get_logger(__name__)


def setup_insurance_lines_callbacks(app: dash.Dash, insurance_lines_tree):
    """Initialize all callbacks for the checklist component"""

    @app.callback(
        [
            Output('insurance-lines-state', 'data'),
            Output('insurance-line-dropdown', 'value')
        ],
        [
            Input({'type': 'insurance-line-checkbox', 'index': ALL}, 'value'),
            Input('insurance-line-dropdown', 'value'),
            Input('detailize-button', 'n_clicks'),
            Input('clear-filters-button', 'n_clicks'),
        ],
        [
            State({'type': 'insurance-line-checkbox', 'index': ALL}, 'id'),
            State('insurance-lines-state', 'data')
        ],
        prevent_initial_call=True
    )
    def update_selection(
            checkbox_values,
            dropdown_value,
            detailize_clicks,
            clear_filters_btn,
            checkbox_ids,
            current_state):
        ctx = dash.callback_context
        start_time = track_callback('app.checklist', 'update_selection', ctx)
        if not ctx.triggered:
            track_callback_end(
                'app.checklist',
                'update_selection',
                start_time,
                message_no_update="not ctx.triggered")
            raise PreventUpdate

        logger.debug(f"current_state state {current_state}")
        trigger = ctx.triggered[0]
        trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
        # trigger_id = trigger['prop_id'].split('.')[0]

        logger.debug(f"current_state selected {current_state}")
        logger.debug(f"Trigger component: {trigger['prop_id']}")
        logger.debug(f"Trigger value: {trigger['value']}")

        # Initialize state if None with default lines
        if current_state is None:
            current_state = DEFAULT_CHECKED_LINES

        if trigger_id == 'clear-filters-button':
            final_selected = DEFAULT_CHECKED_LINES

        elif 'detailize-button' in trigger['prop_id']:  # detailize button
            logger.debug("Source: Detailize button")
            new_selected = current_state if current_state else DEFAULT_CHECKED_LINES
            final_selected = insurance_lines_tree.handle_parent_child_selections(
                new_selected, detailize=True)
        else:

            # trigger_line = json.loads(trigger['prop_id'].rsplit('.', 1)[0]).get('index')  # gets "3.1.1.1"
            # trigger_line = json.loads(trigger['prop_id'].split('.')[0]).get('index')
            if 'insurance-line-dropdown' in trigger['prop_id']:
                logger.debug(f"trigger_id {trigger_id}")
                logger.debug(f"trigger_id {trigger}")
                new_selected = [dropdown_value] if isinstance(dropdown_value, str) else (dropdown_value or DEFAULT_CHECKED_LINES)
                trigger_line = list(set(new_selected) - set(current_state))

                logger.debug(f"selecnew_selectedted {new_selected}")
                logger.debug(f"trigger_line {trigger_line}")

                final_selected = insurance_lines_tree.handle_parent_child_selections(
                    new_selected, trigger_line, detailize=False)
                # final_selected = new_selected

            elif 'insurance-line-checkbox' in trigger['prop_id']:
                logger.debug("Source: Checkbox click")
                if not any(checkbox_values):  # If all checkboxes are unchecked
                    logger.debug(f"selected {checkbox_values}")
                    new_selected = DEFAULT_CHECKED_LINES  # Keep default lines
                else:
                    new_selected = [
                        id_dict['index']
                        for value, id_dict in zip(checkbox_values, checkbox_ids)
                        if value
                    ]

                logger.debug(f"selected {new_selected}")
                logger.debug(f"trigger {trigger}")
                # prop_id = json.loads(trigger['prop_id'].split('.')[0]).get('type') if '{' in trigger['prop_id'] else trigger['prop_id'].split('.')[0]
                # prop_id = trigger['prop_id'].rsplit('.', 1)[0]# using rsplit to split from right side
                # logger.debug(f"prop_id {prop_id}")
                trigger_line = json.loads(
                    trigger['prop_id'].rsplit(
                        '.', 1)[0]).get('index')  # gets "3.1.1.1"
                logger.debug(f"trigger_line {trigger_line}")

                logger.debug(f"new_selected {new_selected}")
                logger.debug(f"current_state {current_state}")

                if trigger_line not in new_selected and trigger_line not in current_state:
                    logger.debug(f"PreventUpdate ")
                    track_callback_end(
                        'app.checklist',
                        'update_selection',
                        start_time,
                        message_no_update="trigger_line not in selected")
                    raise PreventUpdate
                trigger_line = [trigger_line]

                logger.debug(f"new_selected {new_selected}")
                logger.debug(f"trigger_line {trigger_line}")
                # logger.debug(f"detailize {detailize}")
                final_selected = insurance_lines_tree.handle_parent_child_selections(
                    new_selected, trigger_line, detailize=False)

        if not final_selected:  # If somehow we end up with empty selection
            final_selected = DEFAULT_CHECKED_LINES

        '''is_user_interaction = ('insurance-line-dropdown' in trigger['prop_id'] or 
                             'insurance-line-checkbox' in trigger['prop_id'])
        
        if not is_user_interaction and current_state == final_selected:
            track_callback_end('app.checklist', 'update_selection', start_time,
                             message_no_update="no change in selection")
            raise PreventUpdate'''
        
        # logger.debug(f"trigger {trigger}")

        # prop_id = trigger['prop_id'].split('.')[0]
        # logger.debug(f"prop_id {prop_id}")
        # trigger_line = json.loads(prop_id).get('index') if '{' in prop_id else prop_id
        # logger.debug(f"selected {selected}")

        # logger.debug(f"Pre-processed selection: {selected}")

        logger.debug(f"Final selection: {final_selected}")
        logger.debug("=" * 50 + "\n")

        # state.selected = set(final_selected)

        # result = state.to_store(), final_selected
        dropdown_value = final_selected[0] if isinstance(final_selected, list) and final_selected else final_selected

        result = final_selected, dropdown_value  # first for store, second for dropdown

        track_callback_end(
            'app.checklist',
            'update_selection',
            start_time,
            result=result)

        return result

    @app.callback(
        [
            Output('expansion-state', 'data'),
            Output('expand-all-button', 'children')
        ],
        [
            Input('expand-all-button', 'n_clicks'),
            Input({'type': 'insurance-line-expand', 'index': ALL}, 'n_clicks'),

        ],
        [
            State({'type': 'insurance-line-expand', 'index': ALL}, 'id'),
            State('expansion-state', 'data')
        ]
    )
    def update_expansion_state(
            expand_all_clicks,
            expand_clicks,
            expand_ids,
            current_expansion_state):
        ctx = dash.callback_context
        start_time = track_callback(
            'app.checklist', 'update_expansion_state', ctx)

        if not ctx.triggered:
            track_callback_end(
                'app.checklist',
                'Update_expansion_state',
                start_time,
                message_no_update="not ctx.triggered")
            raise PreventUpdate

        logger.debug(f"current_expansion_state {current_expansion_state}")
        trigger = ctx.triggered[0]
        logger.debug(f"Trigger update_expansion_state")
        trigger_id = trigger['prop_id'].split('.')[0]

        logger.debug(f"n clicks {expand_all_clicks}")
        logger.debug(f"Trigger component: {trigger['prop_id']}")
        logger.debug(f"Trigger value: {trigger['value']}")

        new_state = dict(current_expansion_state)

        if 'states' not in new_state:
            new_state['states'] = {}

        if 'expand-all-button' in trigger['prop_id']:
            logger.debug("Source: Expand/Collapse All button")
            new_state['all_expanded'] = not new_state.get(
                'all_expanded', False)
            logger.debug(
                f"Setting all_expanded to: {new_state['all_expanded']}")

            for code in insurance_lines_tree.insurance_line_structure:
                if insurance_lines_tree.get_children(code):
                    new_state['states'][code] = new_state['all_expanded']
            button_text = "Collapse All" if new_state['all_expanded'] else "Expand All"
        else:
            logger.debug("Source: Individual expand/collapse button")
            for i, n_clicks in enumerate(expand_clicks):
                if n_clicks:
                    code = expand_ids[i]['index']
                    new_state['states'][code] = not new_state['states'].get(
                        code, False)
                    logger.debug(
                        f"Toggled state for {code} to: {new_state['states'][code]}")
            button_text = "Collapse All" if new_state.get(
                'all_expanded', False) else "Expand All"

            new_lines_states = new_state['states'].keys()
            trigger_line = json.loads(
                trigger['prop_id'].rsplit(
                    '.', 1)[0]).get('index')  # gets "3.1.1.1"
            logger.debug(f"new_lines_states {list(new_lines_states)}")
            logger.debug(f"trigger_line {trigger_line}")

            if trigger_line not in new_lines_states:
                track_callback_end(
                    'app.checklist',
                    'Update_expansion_state',
                    start_time,
                    message_no_update="trigger_line not in new_lines_states")
                raise PreventUpdate

        result = new_state, button_text

        track_callback_end(
            'app.checklist',
            'update_expansion_state',
            start_time,
            result=result)

        return result

    @app.callback(
        Output("tree-container", "style"),
        [Input("collapse-button", "n_clicks")],
        [State("tree-container", "style")],
    )
    def toggle_collapse(
            n_clicks: int, current_style: Dict[str, Any]) -> Dict[str, str]:
        ctx = dash.callback_context
        start_time = track_callback(
            'app.app_layout', 'toggle_chart_config', ctx)

        try:
            if not n_clicks:
                result = {"display": "none"}
                track_callback_end(
                    'app.checklist',
                    'toggle_collapse',
                    start_time,
                    result=result)
                return result

            if current_style is None:
                current_style = {"display": "none"}

            current_display = current_style.get("display", "none")
            result = {
                **current_style,
                "display": "block" if current_display == "none" else "none"
            }

            track_callback_end(
                'app.checklist',
                'toggle_collapse',
                start_time,
                result=result)
            return result

        except Exception as e:
            track_callback_end(
                'app.checklist',
                'toggle_collapse',
                start_time,
                error=e)
            logger.exception("Error in toggle_collapse")
            raise

    @app.callback(
        Output('tree-container', 'children'),
        [
            Input('insurance-lines-state', 'data'),
            Input('expansion-state', 'data')
        ],
        [

            # State('tree-state', 'data')  # Add state to access previous tree
        ],

        prevent_initial_call=False
    )
    def update_tree(line_state, expansion_state):
        ctx = dash.callback_context
        start_time = track_callback('app.checklist', 'update_tree', ctx)

        logger.debug("\n" + "=" * 50)
        logger.debug("TREE UPDATE CALLBACK")

        # Handle initial render
        if not ctx.triggered:
            logger.debug("Initial render")
            initial_tree = insurance_lines_tree.create_tree(
                {}, set(DEFAULT_CHECKED_LINES))
            track_callback_end(
                'app.checklist',
                'update_tree',
                start_time,
                message_no_update="not ctx.triggered")
            return initial_tree

        logger.debug(f"Trigger: {ctx.triggered[0]['prop_id']}")

        # Handle missing states
        if line_state is None:
            line_state = DEFAULT_CHECKED_LINES
        if expansion_state is None:
            expansion_state = {'states': {}, 'all_expanded': False}

        selected = set(line_state)  # line_state is now just a lis

        logger.debug(f"expansion_state {expansion_state.get('states', {})}")
        logger.debug(f"line_state {line_state}")
        logger.debug(f"selected {selected}")
        tree = insurance_lines_tree.create_tree(
            expansion_state.get('states', {}), selected)
        logger.debug("Tree creation complete")
        logger.debug("=" * 50 + "\n")

        track_callback_end(
            'app.checklist',
            'update_tree',
            start_time,
            result=tree)
        logger.debug(f"tree update {tree}")

        return tree