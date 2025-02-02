import json
from typing import List, Optional, Dict, Tuple

import dash
from dash import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from application.components.dropdown import create_dynamic_dropdown
from config.callback_logging import log_callback
from config.default_values import DEFAULT_CHECKED_LINES, DEFAULT_REPORTING_FORM
from config.logging_config import get_logger
from data_process.options import get_insurance_line_options

logger = get_logger(__name__)


def setup_line_selection(app: dash.Dash, insurance_lines_tree_162, insurance_lines_tree_158):
    """
    Sets up callbacks for insurance line selection management.
    @API_STABILITY: BACKWARDS_COMPATIBLE.
    """
    logger.info("Initializing insurance lines callbacks")

    def _get_tree(reporting_form: str):
        """Select the appropriate insurance lines tree based on reporting form."""
        logger.info("Entering _get_tree")
        logger.debug(f"Reporting form: {reporting_form}")
        tree = insurance_lines_tree_162 if reporting_form == '0420162' else insurance_lines_tree_158
        logger.debug(f"Selected tree: {'162' if reporting_form == '0420162' else '158'}")
        logger.info("Exiting _get_tree")
        return tree

    def _process_detailize(current_state: List[str], dropdown_index: Optional[int], insurance_lines_tree) -> List[str]:
        """Process detailize request for global or specific dropdown."""
        logger.info(f"Entering _process_detailize with dropdown_index: {dropdown_index} and current_state: {current_state}")
        try:
            if dropdown_index is not None:
                if dropdown_index >= len(current_state) or current_state[dropdown_index] is None:
                    logger.debug(f"Invalid dropdown index {dropdown_index} for detailize")
                    return current_state
                selected_line = current_state[dropdown_index]
                logger.debug(f"Detailizing line: {selected_line}")
                detailed = insurance_lines_tree.handle_parent_child_selections([selected_line], detailize=True)
                logger.debug(f"Detailed result: {detailed}")
                if detailed != [selected_line]:
                    logger.info(f"Detailed selection changed for index {dropdown_index}")
                    # Deduplicate detailed list while preserving order
                    result = list(dict.fromkeys(detailed))
                    result.append(selected_line)
                    logger.info(f"Exiting _process_detailize with result: {result}")
                    return result
                logger.info("Exiting _process_detailize without changes")
                return current_state
            else:
                logger.debug("Processing global detailize")
                result = insurance_lines_tree.handle_parent_child_selections(
                    current_state or DEFAULT_CHECKED_LINES, detailize=True)
                logger.info(f"Global detailize complete. Results: {result}")
                logger.info("Exiting _process_detailize")
                return result
        except Exception as e:
            logger.error(f"Error in detailize processing: {str(e)}", exc_info=True)
            raise

    def _process_checkbox_selection(checkbox_values: List[bool],
                                    checkbox_ids: List[Dict],
                                    current_state: List[str], trigger_id: str,
                                    insurance_lines_tree) -> List[str]:
        """Process checkbox selection changes."""
        logger.info("Entering _process_checkbox_selection")
        logger.debug(f"Checkbox values: {checkbox_values}, Current state: {current_state}")
        try:
            if not any(checkbox_values):
                logger.debug("No checkboxes selected, using defaults")
                return DEFAULT_CHECKED_LINES

            new_selected = [
                id_dict['index'] for value, id_dict in zip(checkbox_values, checkbox_ids) if value
            ]
            logger.debug(f"New selection from checkboxes: {new_selected}")
            trigger_line = json.loads(trigger_id).get('index')
            if (trigger_line not in new_selected and trigger_line not in current_state):
                logger.debug(f"Preventing update due to invalid trigger line state: {trigger_line}")
                raise PreventUpdate
            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, [trigger_line], detailize=False)
            logger.info(f"Exiting _process_checkbox_selection with result: {result}")
            return result
        except PreventUpdate:
            logger.debug("Update prevented in checkbox selection")
            raise
        except Exception as e:
            logger.error(f"Error in checkbox selection: {str(e)}", exc_info=True)
            raise

    def _process_dynamic_selection(insurance_line: List[str], current_state: List[str],
                                   insurance_lines_tree) -> List[str]:
        """Process dynamic insurance line selection."""
        logger.info("Entering _process_dynamic_selection")
        logger.debug(f"Insurance line input: {insurance_line}, Current state: {current_state}")
        try:
            # Normalize selection: if string, wrap it in a list; otherwise filter out None values.
            new_selected = (
                [insurance_line] if isinstance(insurance_line, str)
                else [x for x in (insurance_line or DEFAULT_CHECKED_LINES) if x is not None]
            )
            if not new_selected:
                logger.debug("No valid dynamic selections, using defaults")
                return DEFAULT_CHECKED_LINES
            trigger_line = list(set(new_selected) - set(current_state))
            logger.debug(f"Dynamic new_selected: {new_selected}, Trigger line: {trigger_line}")
            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, trigger_line, detailize=False)
            logger.info(f"Exiting _process_dynamic_selection with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in dynamic selection: {str(e)}", exc_info=True)
            raise

    def _update_dropdowns(dropdowns: List, selected_lines: List[str],
                          options: List[Dict], options_extended: Optional[List[Dict]] = None) -> Tuple[List, List[str]]:
        """Update dropdowns based on current selection state."""
        logger.info("Entering _update_dropdowns")
        try:
            valid_selections = []
            for value in selected_lines:
                if value is None:
                    continue
                if any(opt['value'] == value for opt in options):
                    valid_selections.append(value)
                    continue
                if options_extended and any(opt['value'] == value for opt in options_extended):
                    ext_opt = next(opt for opt in options_extended if opt['value'] == value)
                    if ext_opt:
                        options.append({
                            'label': ext_opt['label'],
                            'value': value
                        })
                        valid_selections.append(value)
                        continue
                logger.debug(f"No valid option found for {value} - removing selection")
            if not valid_selections:
                logger.debug("No valid selections remain, using DEFAULT_CHECKED_LINES")
                valid_selections = DEFAULT_CHECKED_LINES

            updated_dropdowns = []
            for i, current_value in enumerate(valid_selections):
                logger.debug(f"Processing dropdown {i} with current value: {current_value}")
                other_selected = [v for j, v in enumerate(valid_selections) if j != i and v is not None]
                available_options = [opt for opt in options if opt['value'] not in other_selected]
                updated_dropdowns.append(create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=i,
                    options=available_options,
                    value=current_value,
                    is_add_button=(i == len(valid_selections) - 1),
                    is_remove_button=(len(valid_selections) > 1),
                    is_detalize_button=True
                ))
            logger.info("Exiting _update_dropdowns")
            return updated_dropdowns, valid_selections
        except Exception as e:
            logger.error(f"Error in dropdown update: {str(e)}", exc_info=True)
            raise

    def _handle_remove_dropdown(existing_dropdowns: List, insurance_line: List[str],
                                removed_index: int, options: List[Dict]) -> Tuple[List, List[str]]:
        """Handle dropdown removal while preserving selections."""
        logger.info(f"Entering _handle_remove_dropdown for index: {removed_index}")
        try:
            if len(existing_dropdowns) <= 1:
                logger.debug("Removing last dropdown, resetting to default")
                default_dropdown = create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=0,
                    options=options,
                    value=DEFAULT_CHECKED_LINES[0],
                    is_add_button=True,
                    is_remove_button=False
                )
                logger.info("Exiting _handle_remove_dropdown with default dropdown")
                return [default_dropdown], DEFAULT_CHECKED_LINES

            existing_dropdowns.pop(removed_index)
            if removed_index < len(insurance_line):
                insurance_line.pop(removed_index)
            # Remove any extra dropdowns if necessary
            while len(existing_dropdowns) > len([x for x in insurance_line if x is not None]) + 1:
                existing_dropdowns.pop()
            updated_dropdowns, valid_selections = _update_dropdowns(existing_dropdowns, insurance_line, options)
            logger.info(f"Exiting _handle_remove_dropdown with updated selections: {valid_selections}")
            return updated_dropdowns, valid_selections
        except Exception as e:
            logger.error(f"Error in dropdown removal: {str(e)}", exc_info=True)
            raise

    def _handle_add_dropdown(existing_dropdowns: List, insurance_line: List[str],
                             options: List[Dict]) -> None:
        """Handle adding a new dropdown."""
        logger.info("Entering _handle_add_dropdown")
        try:
            if existing_dropdowns:
                last_idx = len(existing_dropdowns) - 1
                logger.debug(f"Updating last dropdown at index {last_idx}")
                existing_dropdowns[last_idx] = create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=last_idx,
                    options=options,
                    value=insurance_line[last_idx] if last_idx < len(insurance_line) else None,
                    is_add_button=False,
                    is_remove_button=True,
                    is_detalize_button=True
                )
            filtered_options = [opt for opt in options if opt.get('value') not in insurance_line]
            existing_dropdowns.append(create_dynamic_dropdown(
                dropdown_type='insurance-line',
                index=len(existing_dropdowns),
                options=filtered_options,
                value=None,
                is_add_button=True,
                is_remove_button=True,
                is_detalize_button=True
            ))
            logger.info(f"Exiting _handle_add_dropdown. Total dropdowns: {len(existing_dropdowns)}")
        except Exception as e:
            logger.error(f"Error in add dropdown: {str(e)}", exc_info=True)
            raise

    @app.callback(
        [
            Output('insurance-line-container', 'children'),
            Output('insurance-lines-all-values', 'data'),
        ],
        [
            Input({'type': 'insurance-line-checkbox', 'index': ALL}, 'value'),
            Input({'type': 'dynamic-insurance-line', 'index': ALL}, 'value'),
            Input('insurance-line-add-btn', 'n_clicks'),
            Input({'type': 'remove-insurance-line-btn', 'index': ALL}, 'n_clicks'),
            Input('detailize-button', 'n_clicks'),
            Input({'type': 'dropdown-detalize-btn', 'index': ALL}, 'n_clicks'),
            Input('reporting-form', 'data'),
        ],
        [
            State({'type': 'insurance-line-checkbox', 'index': ALL}, 'id'),
            State('insurance-line-container', 'children'),
            State('insurance-lines-all-values', 'data')
        ],
        prevent_initial_call=True
    )
    @log_callback
    def update_line_selection(
            checkbox_values: List[bool],
            insurance_line: List[str],
            add_clicks: int,
            remove_clicks: List[int],
            detilize_button: int,
            detailize_clicks: List[int],
            reporting_form: str,
            checkbox_ids: List[Dict],
            existing_dropdowns: List,
            current_state: List[str]
    ) -> Tuple[List, List[str]]:
        """Update insurance lines based on user interactions."""
        logger.info("Entering update_line_selection")
        try:
            ctx = dash.callback_context
            if not ctx.triggered:
                logger.debug("No trigger context available, preventing update")
                raise PreventUpdate

            reporting_form = reporting_form or DEFAULT_REPORTING_FORM
            insurance_lines_tree = _get_tree(reporting_form)
            initial_dropdowns = existing_dropdowns
            trigger = ctx.triggered[0]
            trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
            logger.debug(f"Trigger received: {trigger}")
            current_state = current_state or DEFAULT_CHECKED_LINES
            # Use current_state if insurance_line is empty or its first element is None.
            insurance_line = insurance_line if (insurance_line and insurance_line[0] is not None) else current_state

            # Process based on trigger type.
            if 'detailize-button' in trigger['prop_id']:
                final_selected = _process_detailize(current_state, None, insurance_lines_tree)
            elif 'dropdown-detalize-btn' in trigger['prop_id']:
                dropdown_index = int(json.loads(trigger_id)['index'])
                final_selected = _process_detailize(current_state, dropdown_index, insurance_lines_tree)
            elif 'insurance-line-checkbox' in trigger['prop_id']:
                final_selected = _process_checkbox_selection(
                    checkbox_values, checkbox_ids, current_state, trigger_id, insurance_lines_tree)
            elif 'dynamic-insurance-line' in trigger['prop_id']:
                final_selected = _process_dynamic_selection(insurance_line, current_state, insurance_lines_tree)
            else:
                final_selected = current_state

            final_selected = final_selected or DEFAULT_CHECKED_LINES
            insurance_line = [v for v in final_selected if v is not None]
            if not insurance_line:
                insurance_line = DEFAULT_CHECKED_LINES

            insurance_line_options = get_insurance_line_options(reporting_form, level=2)
            insurance_line_options_extended = get_insurance_line_options(reporting_form, level=5)

            if not existing_dropdowns:
                logger.debug("No existing dropdowns found, creating initial dropdown")
                initial_dropdown = create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=0,
                    options=insurance_line_options,
                    is_add_button=True,
                    is_remove_button=False,
                    is_detalize_button=True
                )
                logger.info("Exiting update_line_selection with initial dropdown")
                return [initial_dropdown], insurance_line

            if '.n_clicks' in trigger['prop_id'] and 'intermediate-data-store' not in trigger['prop_id']:
                if 'remove-insurance-line-btn' in trigger['prop_id']:
                    removed_index = int(json.loads(trigger_id.split('.')[0])['index'])
                    logger.debug(f"Remove button clicked for index: {removed_index}")
                    return _handle_remove_dropdown(existing_dropdowns, insurance_line, removed_index, insurance_line_options)
                elif 'insurance-line-add-btn' in trigger['prop_id']:
                    logger.debug("Add button clicked, handling add dropdown")
                    _handle_add_dropdown(existing_dropdowns, insurance_line, insurance_line_options)
                    logger.info("Exiting update_line_selection after adding dropdown")
                    return existing_dropdowns, insurance_line

            updated_dropdowns, valid_selections = _update_dropdowns(
                existing_dropdowns, insurance_line, insurance_line_options, insurance_line_options_extended)
            logger.debug(f"Updated dropdowns: {updated_dropdowns}")
            logger.info("Exiting update_line_selection with updated dropdowns")
            return updated_dropdowns, valid_selections

        except PreventUpdate:
            logger.debug("Update prevented in update_line_selection")
            raise
        except Exception as e:
            logger.error(f"Error in insurance lines update: {str(e)}", exc_info=True)
            raise

    return update_line_selection