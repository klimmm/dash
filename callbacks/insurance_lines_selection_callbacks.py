import dash
import json
from dash import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from typing import List, Optional, Dict
from application.dropdown_components import create_insurance_line_dropdown
from config.default_values import DEFAULT_CHECKED_LINES, DEFAULT_REPORTING_FORM
from config.logging_config import get_logger, log_callback
from constants.translations import translate
from data_process.insurance_line_options import get_insurance_line_options
logger = get_logger(__name__)


def setup_insurance_lines_callbacks(app: dash.Dash, insurance_lines_tree_162, insurance_lines_tree_158):
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

                if detailed != [selected_line]:
                    logger.info(f"Detailed selection changed for index {dropdown_index}")
                    return list(set(current_state + detailed) - {selected_line})
                return current_state

            # Handle global detailize
            logger.debug("Processing global detailize")
            result = insurance_lines_tree.handle_parent_child_selections(
                current_state or DEFAULT_CHECKED_LINES, detailize=True)

            logger.info(f"Global detailize complete. Results: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in detailize processing: {str(e)}", exc_info=True)
            raise

    def _process_checkbox_selection(checkbox_values: List[bool], checkbox_ids: List[Dict], 
                                  current_state: List[str], trigger_id: str,
                                  insurance_lines_tree) -> List[str]:
        """Process checkbox selection changes."""
        logger.info("Processing checkbox selection")
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
            if trigger_line not in new_selected and trigger_line not in current_state:
                logger.warning(f"Invalid trigger line state: {trigger_line}")
                raise PreventUpdate

            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, [trigger_line], detailize=False)

            logger.info(f"Checkbox selection complete. Results: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in checkbox selection: {str(e)}", exc_info=True)
            raise

    def _process_dynamic_selection(insurance_line: List[str], current_state: List[str],
                                 insurance_lines_tree) -> List[str]:
        """Process dynamic insurance line selection."""
        logger.info("Processing dynamic selection")
        logger.debug(f"Insurance line: {insurance_line}")
        logger.debug(f"Current state: {current_state}")

        try:
            new_selected = ([insurance_line] if isinstance(insurance_line, str) 
                          else (insurance_line or DEFAULT_CHECKED_LINES))
            trigger_line = list(set(new_selected) - set(current_state))

            result = insurance_lines_tree.handle_parent_child_selections(
                new_selected, trigger_line, detailize=False)

            logger.info(f"Dynamic selection complete. Results: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in dynamic selection: {str(e)}", exc_info=True)
            raise

    def _update_dropdowns(dropdowns: List, selected_lines: List[str], 
                         options: List[Dict], options_extended: None = List[Dict]) -> List:
        """Update dropdowns based on current selection state."""
        logger.info("Updating dropdowns")
        logger.debug(f"Current dropdowns: {len(dropdowns)}")
        logger.debug(f"Selected lines: {len(selected_lines)}")

        try:
            # Ensure enough dropdowns
            while len(dropdowns) < len(selected_lines):
                logger.debug(f"Adding dropdown: {len(dropdowns)}")
                dropdowns.append(None)

            result = []
            for i, _ in enumerate(dropdowns):
                current_value = selected_lines[i] if i < len(selected_lines) else None
                logger.debug(f"Processing dropdown {i} - Current value: {current_value}")

                # Get other selected values
                other_selected = [v for j, v in enumerate(selected_lines) 
                                if j != i and v is not None]

                # Filter available options
                available_options = [opt for opt in options 
                                   if opt['value'] not in other_selected]
                logger.debug(f"available_options: {available_options}")
                # Preserve current selection if valid

                # Preserve current selection if valid
                if current_value and not any(opt['value'] == current_value for opt in available_options):
                    logger.debug(f"Looking for extended option for {current_value}")
                    # Try to find matching option in extended options
                    extended_option = next((opt for opt in available_options 
                                          if opt['value'] == current_value), None)
                    if extended_option:
                        logger.debug(f"Found extended option: {extended_option}")
                        available_options.append({
                            'label': extended_option['label'],
                            'value': current_value
                        })
                    else:
                        logger.debug(f"No extended option found for {current_value}")
                        available_options.append({
                            'label': translate(current_value),
                            'value': current_value
                        })

                if current_value and not any(opt['value'] == current_value 
                                           for opt in available_options):

                    logger.debug(f"Preserving value for dropdown {i}: {current_value}")
                    available_options.append({
                        'label': translate(current_value),
                        'value': current_value
                    })

                result.append(create_insurance_line_dropdown(
                    index=i,
                    options=available_options,
                    value=current_value,
                    is_add_button=(i == len(dropdowns) - 1),
                    is_remove_button=(len(dropdowns) > 1)
                ))

            logger.info(f"Dropdown update complete. Total dropdowns: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Error in dropdown update: {str(e)}", exc_info=True)
            raise

    def _handle_remove_dropdown(existing_dropdowns: List, insurance_line: List[str],
                              removed_index: int, options: List[Dict]) -> tuple:
        """Handle dropdown removal while preserving selections."""
        logger.info(f"Processing dropdown removal for index: {removed_index}")

        try:
            if len(existing_dropdowns) <= 1:
                logger.warning("Attempted to remove last dropdown")
                raise PreventUpdate

            has_value = (removed_index < len(insurance_line) and 
                        insurance_line[removed_index] is not None)
            other_values = [v for i, v in enumerate(insurance_line) 
                          if i != removed_index and v is not None]

            if has_value and not other_values:
                logger.debug("Preserving last selected value")
                value_to_preserve = insurance_line[removed_index]
                existing_dropdowns.pop(removed_index)

                empty_index = next((i for i, v in enumerate(insurance_line) 
                                  if v is None), 0)
                preserved_values = [value_to_preserve if i == empty_index 
                                  else None for i in range(len(existing_dropdowns))]

                return (_update_dropdowns(existing_dropdowns, preserved_values, options),
                       insurance_line)

            existing_dropdowns.pop(removed_index)
            if removed_index < len(insurance_line):
                insurance_line.pop(removed_index)

            logger.info("Dropdown removal complete")
            return None

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

                existing_dropdowns[last_idx] = create_insurance_line_dropdown(
                    index=last_idx,
                    options=options,
                    value=insurance_line[last_idx] if last_idx < len(insurance_line) else None,
                    is_add_button=False,
                    is_remove_button=True
                )

            filtered_options = [opt for opt in options 
                              if opt.get('value') not in insurance_line]

            existing_dropdowns.append(create_insurance_line_dropdown(
                index=len(existing_dropdowns),
                options=filtered_options,
                value=None,
                is_add_button=True,
                is_remove_button=True
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
    def update_insurance_lines(
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

            trigger = ctx.triggered[0]
            trigger_id = trigger['prop_id'].rsplit('.', 1)[0]
            logger.debug(f"Trigger: {trigger['prop_id']}")

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

            # Ensure valid selection
            final_selected = final_selected or DEFAULT_CHECKED_LINES
            insurance_line = [v for v in (final_selected or []) if v is not None] 
            insurance_line_options = get_insurance_line_options(reporting_form, level=2)
            insurance_line_options_extended = get_insurance_line_options(reporting_form, level=5)

            # Handle no existing dropdowns
            if not existing_dropdowns:
                logger.debug("Creating initial dropdown")
                return [create_insurance_line_dropdown(
                    index=0,
                    options=insurance_line_options,
                    is_add_button=True,
                    is_remove_button=False
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


            # Update dropdowns
            updated_dropdowns = _update_dropdowns(
                existing_dropdowns, insurance_line, insurance_line_options, insurance_line_options_extended)

            logger.info("Insurance lines update complete")
            logger.info(f"insurance_line{insurance_line}")
            return updated_dropdowns, insurance_line

        except Exception as e:
            logger.error(f"Error in insurance lines update: {str(e)}", exc_info=True)
            raise

    return update_insurance_lines