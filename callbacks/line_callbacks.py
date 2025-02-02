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
        """Get appropriate insurance lines tree based on reporting form."""
        logger.debug(f"Getting tree for reporting form: {reporting_form}")
        tree = insurance_lines_tree_162 if reporting_form == '0420162' else insurance_lines_tree_158
        logger.debug(f"Selected tree type: {'162' if reporting_form == '0420162' else '158'}")
        return tree

    def _process_detailize(current_state: List[str], dropdown_index: Optional[int], 
                          insurance_lines_tree) -> List[str]:
        """Process detailize request for global or specific dropdown."""
        logger.info(f"Processing detailize - Index: {dropdown_index}, Current state: {current_state}")

        try:
            if dropdown_index is not None:
                # Handle individual dropdown detailize
                if dropdown_index >= len(current_state) or current_state[dropdown_index] is None:
                    logger.debug(f"Invalid dropdown index {dropdown_index} for detailize")
                    return current_state

                selected_line = current_state[dropdown_index]
                logger.debug(f"Detailizing line: {selected_line}")

                detailed = insurance_lines_tree.handle_parent_child_selections(
                    [selected_line], detailize=True)
                logger.debug(f"detailed: {detailed}")

                if detailed != [selected_line]:
                    logger.info(f"Detailed selection changed for index {dropdown_index}")
                    result = [] 
                    # [line for line in current_state if line != selected_line]
                    for item in detailed:
                        if item not in result:
                            result.append(item)
                    result.append(selected_line)
                    return result
                return current_state


            # Handle global detailize
            logger.debug("Processing global detailize")
            result = insurance_lines_tree.handle_parent_child_selections(
                current_state or DEFAULT_CHECKED_LINES, detailize=True)

            logger.info(f"Global detailize complete. Results: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in detailize processing: {str(e)}",
                         exc_info=True)
            raise

    def _process_checkbox_selection(checkbox_values: List[bool],
                                    checkbox_ids: List[Dict],
                                    current_state: List[str], trigger_id: str,
                                    insurance_lines_tree) -> List[str]:
        """Process checkbox selection changes."""
        logger.debug("Processing checkbox selection")
        logger.debug(f"Checkbox values: {checkbox_values}")
        logger.debug(f"Current state: {current_state}")
        try:
            if not any(checkbox_values):
                logger.debug("No checkboxes selected, using defaults")
                return DEFAULT_CHECKED_LINES

            new_selected = [
                id_dict['index']
                for value, id_dict in zip(checkbox_values, checkbox_ids)
                if value
            ]
            logger.debug(f"New selection: {new_selected}")

            trigger_line = json.loads(trigger_id).get('index')
            if (trigger_line not in new_selected
                    and trigger_line not in current_state):
                logger.debug(
                    f"Preventing update due to invalid trigger line state: {trigger_line}"
                )
                raise PreventUpdate

            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, [trigger_line], detailize=False)
            logger.debug(f"Checkbox selection complete. Results: {result}")
            return result

        except PreventUpdate:
            # Log at debug level since this is expected behavior
            logger.debug("Update prevented - normal operation")
            raise
        except Exception as e:
            logger.error(f"Error in checkbox selection: {str(e)}",
                         exc_info=True)
            raise

    def _process_dynamic_selection(insurance_line: List[str], current_state: List[str],
                                 insurance_lines_tree) -> List[str]:
        """Process dynamic insurance line selection."""
        logger.info("Processing dynamic selection")
        logger.debug(f"Insurance line: {insurance_line}")
        logger.debug(f"Current state: {current_state}")

        try:
            # Filter out None values and get new selected values
            new_selected = (
                [insurance_line] if isinstance(insurance_line, str)
                else [x for x in (insurance_line or DEFAULT_CHECKED_LINES) if x is not None]
            )

            # If no valid selections, use defaults
            if not new_selected:
                logger.debug("No valid selections, using defaults")
                return DEFAULT_CHECKED_LINES

            trigger_line = list(set(new_selected) - set(current_state))
            logger.debug(f"new_selected: {new_selected}")

            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, trigger_line, detailize=False)

            logger.debug(f"Dynamic selection complete. Results: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in dynamic selection: {str(e)}", exc_info=True)
            raise

    def _update_dropdowns(dropdowns: List, selected_lines: List[str], 
                         options: List[Dict], options_extended: List[Dict] = None) -> Tuple[List, List[str]]:
        """Update dropdowns based on current selection state."""
        try:
            valid_selections = []

            for value in selected_lines:
                if value is None:
                    continue

                # First check regular options
                if any(opt['value'] == value for opt in options):
                    valid_selections.append(value)
                    continue

                # Then check extended options
                if options_extended and any(opt['value'] == value for opt in options_extended):
                    # Get label from extended options for the dropdown
                    ext_opt = next(opt for opt in options_extended if opt['value'] == value)
                    # Add to available options with proper label
                    if ext_opt:
                        options.append({
                            'label': ext_opt['label'],
                            'value': value
                        })
                        valid_selections.append(value)
                        continue

                logger.debug(f"No valid option found for {value} - removing selection")

            # If no valid selections remain, use default
            if not valid_selections:
                logger.debug("No valid selections remain, using DEFAULT_CHECKED_LINES")
                valid_selections = DEFAULT_CHECKED_LINES

            # Create dropdowns for valid selections
            result = []
            for i in range(len(valid_selections)):
                current_value = valid_selections[i]
                logger.debug(f"Processing dropdown {i} - Current value: {current_value}")

                other_selected = [v for j, v in enumerate(valid_selections) 
                                if j != i and v is not None]

                available_options = [opt for opt in options 
                                   if opt['value'] not in other_selected]

                result.append(create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=i,
                    options=available_options,
                    value=current_value,
                    is_add_button=(i == len(valid_selections) - 1),
                    is_remove_button=(len(valid_selections) > 1),
                    is_detalize_button=True
                ))

            return result, valid_selections

        except Exception as e:
            logger.error(f"Error in dropdown update: {str(e)}", exc_info=True)
            raise

    def _handle_remove_dropdown(existing_dropdowns: List, insurance_line: List[str],
                              removed_index: int, options: List[Dict]) -> tuple:
        """Handle dropdown removal while preserving selections."""
        logger.info(f"Processing dropdown removal for index: {removed_index}")

        try:
            # Don't prevent removal of the last dropdown - just reset to default
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
                return [default_dropdown], DEFAULT_CHECKED_LINES  # Return single list, not nested

            # Remove the dropdown and its corresponding value
            existing_dropdowns.pop(removed_index)
            if removed_index < len(insurance_line):
                insurance_line.pop(removed_index)

            # Clean up any trailing empty dropdowns
            while (len(existing_dropdowns) > len([x for x in insurance_line if x is not None]) + 1):
                existing_dropdowns.pop()

            # Update the remaining dropdowns
            updated_dropdowns, valid_selections = _update_dropdowns(existing_dropdowns, insurance_line, options)
            return updated_dropdowns, valid_selections  # Return the tuple directly

        except Exception as e:
            logger.error(f"Error in dropdown removal: {str(e)}", exc_info=True)
            raise

    def _handle_add_dropdown(existing_dropdowns: List, insurance_line: List[str],
                           options: List[Dict]) -> None:
        """Handle adding new dropdown."""
        logger.info("Processing add dropdown request")

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

            filtered_options = [opt for opt in options 
                              if opt.get('value') not in insurance_line]

            existing_dropdowns.append(create_dynamic_dropdown(
                dropdown_type='insurance-line',
                index=len(existing_dropdowns),
                options=filtered_options,
                value=None,
                is_add_button=True,
                is_remove_button=True,
                is_detalize_button=True
            ))

            logger.info(f"Added new dropdown. Total count: {len(existing_dropdowns)}")

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
    ) -> tuple:
        """Update insurance lines based on user interactions."""
        logger.info("Starting insurance lines update")

        try:
            ctx = dash.callback_context
            if not ctx.triggered:
                logger.debug("No trigger context")
                raise PreventUpdate

            reporting_form = reporting_form or DEFAULT_REPORTING_FORM
            insurance_lines_tree = _get_tree(reporting_form)
            initial_dropdowns = existing_dropdowns
            trigger = ctx.triggered[0]
            trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
            logger.debug(f"insurance_line : {insurance_line}")


            logger.debug(f"Trigger: {trigger}")
            logger.debug(f"Trigger prop_id: {trigger['prop_id']}")
            logger.debug(f"Trigger id : {trigger['prop_id'].rsplit('.', 1)[0]}")
            # Initialize state
            current_state = current_state or DEFAULT_CHECKED_LINES

            insurance_line = insurance_line if insurance_line[0] is not None else current_state

            # Process based on trigger type
            if 'detailize-button' in trigger['prop_id']:
                final_selected = _process_detailize(current_state, None, insurance_lines_tree)
            elif 'dropdown-detalize-btn' in trigger['prop_id']:
                dropdown_index = int(json.loads(trigger_id)['index'])
                final_selected = _process_detailize(current_state, dropdown_index, insurance_lines_tree)
            elif 'insurance-line-checkbox' in trigger['prop_id']:
                final_selected = _process_checkbox_selection(
                    checkbox_values, checkbox_ids, current_state, trigger_id, insurance_lines_tree)
            elif 'dynamic-insurance-line' in trigger['prop_id']:
                final_selected = _process_dynamic_selection(
                    insurance_line, current_state, insurance_lines_tree)
            else:
                final_selected = current_state

            logger.debug(f"final_selected : {final_selected}")
            # Ensure valid selection
            final_selected = final_selected or DEFAULT_CHECKED_LINES
            insurance_line = [v for v in (final_selected or []) if v is not None]
            if not insurance_line:
                insurance_line = DEFAULT_CHECKED_LINES

            insurance_line_options = get_insurance_line_options(reporting_form, level=2)
            insurance_line_options_extended = get_insurance_line_options(reporting_form, level=5)

            # Handle no existing dropdowns
            if not existing_dropdowns:
                logger.debug("Creating initial dropdown")
                return [create_dynamic_dropdown(
                    dropdown_type='insurance-line',
                    index=0,
                    options=insurance_line_options,
                    is_add_button=True,
                    is_remove_button=False,
                    is_detalize_button=True
                )], insurance_line

            # Handle add/remove operations
            if '.n_clicks' in trigger['prop_id'] and 'intermediate-data-store' not in trigger['prop_id']:

                if 'remove-insurance-line-btn' in trigger['prop_id']:
                    removed_index = int(json.loads(trigger_id.split('.')[0])['index'])
                    remove_result = _handle_remove_dropdown(
                        existing_dropdowns, insurance_line, removed_index, insurance_line_options)
                    if remove_result:
                        return remove_result
                elif 'insurance-line-add-btn' in trigger['prop_id']:
                    _handle_add_dropdown(existing_dropdowns, insurance_line, insurance_line_options)
                    return existing_dropdowns, insurance_line 


            # Update dropdowns and get valid selections
            updated_dropdowns, valid_selections = _update_dropdowns(
                existing_dropdowns, insurance_line, insurance_line_options, insurance_line_options_extended)
            logger.debug(f"insurance_line{valid_selections}")  # Use valid selections here
            logger.debug(f"current_state{current_state}")  # Use valid selections here
            logger.debug(f"updated_dropdowns{updated_dropdowns}")  # Use valid selections here
            logger.debug(f"initial_dropdowns{initial_dropdowns}")  # Use valid selections here
            '''if valid_selections == current_state:
                logger.debug(f"initial_dropdowns=current {initial_dropdowns == existing_dropdowns}")  
                if initial_dropdowns == existing_dropdowns:

                    return dash.no_update, dash.no_update
                else:
                    return updated_dropdowns, dash.no_update'''

            logger.info("Insurance lines update complete")
            return updated_dropdowns, valid_selections

        except PreventUpdate:
            logger.debug("Update prevented in line selection - normal operation")
            raise

        except Exception as e:
            logger.error(f"Error in insurance lines update: {str(e)}", exc_info=True)
            raise

    return update_line_selection