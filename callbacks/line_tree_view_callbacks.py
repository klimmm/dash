import json
import re
from typing import Dict, Any

import dash
from dash import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from config.callback_logging import log_callback
from config.default_values import DEFAULT_CHECKED_LINES, DEFAULT_REPORTING_FORM
from config.logging_config import get_logger

logger = get_logger(__name__)


def setup_line_tree_view(app: dash.Dash, lines_tree_162, lines_tree_158):
    @app.callback(
        [Output('expansion-state', 'data'),
         Output('expand-all-button', 'children')],
        [Input('expand-all-button', 'n_clicks'),
         Input({'type': 'insurance-line-expand', 'index': ALL}, 'n_clicks')],
        [State({'type': 'insurance-line-expand', 'index': ALL}, 'id'),
         State('expansion-state', 'data'),
         State('reporting-form', 'data')],
    )
    @log_callback
    def update_lines_checkbox_expansion_state(
        expand_all_clicks,
        expand_clicks,
        expand_ids,
        current_expansion_state,
        reporting_form
    ):
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate

        try:
            # Initialize current_expansion_state if None
            new_state = dict(current_expansion_state or {})
            if 'states' not in new_state:
                new_state['states'] = {}

            # Get correct insurance lines tree
            reporting_form = reporting_form or DEFAULT_REPORTING_FORM
            lines_tree = (
                lines_tree_162 if reporting_form == '0420162' 
                else lines_tree_158
            )

            trigger = ctx.triggered[0]
            logger.debug(f"trigger: {trigger}")

            prop_id = trigger['prop_id']
            logger.debug(f"prop_id: {prop_id}")

            match = re.match(r'^(.*?)\.n_clicks', prop_id)
            if not match:
                logger.debug(f"Could not find JSON part in prop_id: {prop_id}")
                return None

            json_part = match.group(1)
            # json_part = prop_id.split('.')[0]
            logger.debug(f"json_part: {json_part}")
            trigger_data = json.loads(json_part)
            logger.debug(f"trigger_data: {trigger_data}")
            trigger_id = json_part
            # trigger_id = trigger['prop_id'].split('.')[0]
            logger.debug(f"trigger_id: {trigger_id}")

            if 'expand-all-button' in trigger['prop_id']:
                # Handle expand/collapse all
                new_state['all_expanded'] = not new_state.get('all_expanded', False)

                for code in lines_tree.insurance_line_structure:
                    if lines_tree.get_children(code):
                        new_state['states'][code] = new_state['all_expanded']

                button_text = "Collapse All" if new_state['all_expanded'] else "Expand All"
            else:
                # Handle individual expand/collapse
                try:
                    trigger_line = json.loads(trigger_id).get('index')

                    for i, n_clicks in enumerate(expand_clicks):
                        if n_clicks:
                            code = expand_ids[i]['index']
                            new_state['states'][code] = not new_state['states'].get(code, False)

                    button_text = "Collapse All" if new_state.get('all_expanded', False) else "Expand All"

                    if trigger_line not in new_state['states']:
                        raise PreventUpdate

                except json.JSONDecodeError:
                    logger.debug(f"Failed to parse trigger_id: {trigger_id}")
                    raise PreventUpdate

            return new_state, button_text

        except dash.exceptions.PreventUpdate:
            raise  # Just re-raise PreventUpdate without logging
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise  # Re-raise unexpected errors

    @app.callback(
        Output("tree-container", "style"),
        [Input("collapse-button", "n_clicks")],
        [State("tree-container", "style")],
    )
    @log_callback
    def toggle_collapse_lines_checkbox(
            n_clicks: int, current_style: Dict[str, Any]) -> Dict[str, str]:
        ctx = dash.callback_context

        try:
            if not n_clicks:
                result = {"display": "none"}
                return result

            if current_style is None:
                current_style = {"display": "none"}

            current_display = current_style.get("display", "none")
            result = {
                **current_style,
                "display": "block" if current_display == "none" else "none"
            }
            return result

        except Exception as e:
            logger.exception("Error in toggle_collapse_lines_checkbox")
            raise

    @app.callback(
        Output('tree-container', 'children'),
        [Input('insurance-lines-all-values', 'data'),
         Input('expansion-state', 'data')],
        State('reporting-form', 'data'),
        prevent_initial_call=False
    )
    @log_callback
    def update_lines_checkbox_tree(line_state, expansion_state, reporting_form):
        ctx = dash.callback_context

        logger.debug("\n" + "=" * 50)
        logger.debug("TREE UPDATE CALLBACK")

        if reporting_form is None:
            reporting_form = DEFAULT_REPORTING_FORM

        lines_tree = lines_tree_162 if reporting_form == '0420162' else lines_tree_158

        if not ctx.triggered:
            logger.debug("Initial render")
            initial_tree = lines_tree.create_tree(
                {}, set(DEFAULT_CHECKED_LINES))
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
        tree = lines_tree.create_tree(
            expansion_state.get('states', {}), selected)
        logger.debug("Tree creation complete")
        logger.debug("=" * 50 + "\n")

        logger.debug(f"tree update {tree}")

        return tree