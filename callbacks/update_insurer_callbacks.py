import json
import dash
from dash import Dash, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from typing import List, Dict, Set, Tuple, Any
from application.dropdown_components import create_insurer_dropdown
from config.default_values import MAX_DROPDOWNS
from config.logging_config import get_logger, log_callback

logger = get_logger(__name__)


def get_excluded_insurers(
    selected_insurers: List[str], 
    top_n_groups: Dict[str, List[str]]
) -> Tuple[Set[str], bool]:
    """Helper function to determine excluded insurers based on selections."""
    excluded_insurers = set()
    has_top_selection = False

    if not isinstance(selected_insurers, list) or not isinstance(top_n_groups, dict):
        logger.warning("Invalid input types for get_excluded_insurers")
        return set(), False

    for selected in (selected_insurers or []):  # Handle None case explicitly
        if not selected:
            continue

        if selected.startswith('top-'):
            has_top_selection = True
            group_key = selected.replace('-', '')  # Convert 'top-5' to 'top5'
            excluded_insurers.update(set(top_n_groups.get(f"{group_key}_insurers", [])))
        else:
            excluded_insurers.add(selected)

    return excluded_insurers, has_top_selection


def create_updated_dropdown(
    index: int,
    total_dropdowns: int,
    options: List[Dict[str, Any]],
    value: str = None,
    excluded_insurers: Set[str] = None,
    has_top_selection: bool = False
) -> Dict:
    """Create a dropdown with filtered options based on current selections."""
    if excluded_insurers is None:
        excluded_insurers = set()

    filtered_options = [
        opt for opt in options 
        if (
            opt['value'] not in excluded_insurers and
            (not has_top_selection or not opt['value'].startswith('top-') or value == opt['value'])
        )
    ]

    return create_insurer_dropdown(
        index=index,
        options=filtered_options,
        value=value,
        is_add_button=(index == total_dropdowns - 1),
        is_remove_button=(total_dropdowns > 1)
    )


def setup_insurers_callbacks(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-container', 'children'),
        Output('selected-insurers-all-values', 'data'),
        [Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
         Input('selected-insurers-add-btn', 'n_clicks'),
         Input({'type': 'remove-selected-insurers-btn', 'index': ALL}, 'n_clicks'),
         Input('insurer-options-store', 'data')],
        [State('selected-insurers-container', 'children'),
         State('selected-insurers-all-values', 'data')]
    )
    @log_callback
    def update_insurers_selections(
        selected_insurers: List[str],
        add_insurer_clicks: int,
        remove_insurer_clicks: List[int],
        insurer_options_store: Dict,
        existing_dropdowns: List,
        current_selected_insurers: List[str],
    ) -> List:
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE
        Updates insurer selection dropdowns based on user interactions.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            trigger_id = ctx.triggered[0]['prop_id']

            # Initialize if needed
            if not existing_dropdowns:
                logger.info("Initializing first dropdown")
                return [create_insurer_dropdown(
                    index=0,
                    options=insurer_options_store['insurer_options'],
                    is_add_button=True,
                    is_remove_button=False
                )], []

            # Clean up selected insurers
            selected_insurers = [v for v in (selected_insurers or []) if v is not None]
            logger.debug(f"Current selections: {selected_insurers}")

            # Handle remove button click
            if 'remove-selected-insurers-btn' in trigger_id:
                if len(existing_dropdowns) <= 1:
                    logger.debug("Cannot remove last dropdown")
                    raise PreventUpdate

                component_id = json.loads(trigger_id.split('.')[0])
                removed_index = int(component_id['index'])
                logger.info(f"Removing dropdown at index {removed_index}")

                # Preserve last selection if needed
                removed_value = selected_insurers[removed_index] if removed_index < len(selected_insurers) else None
                selected_insurers = [v for i, v in enumerate(selected_insurers) if i != removed_index]

                if removed_value and not [v for v in selected_insurers if v is not None]:
                    selected_insurers = [removed_value] + [None] * (len(existing_dropdowns) - 2)

                existing_dropdowns.pop(removed_index)

            # Handle add button click
            elif 'selected-insurers-add-btn' in trigger_id:
                if len(existing_dropdowns) >= MAX_DROPDOWNS:
                    logger.debug(f"Maximum dropdowns ({MAX_DROPDOWNS}) reached")
                    raise PreventUpdate

                logger.info("Adding new dropdown")
                # Update last dropdown to remove add button
                if existing_dropdowns:
                    last_index = len(existing_dropdowns) - 1
                    existing_dropdowns[last_index] = create_insurer_dropdown(
                        index=last_index,
                        options=insurer_options_store['insurer_options'],
                        value=selected_insurers[last_index] if last_index < len(selected_insurers) else None,
                        is_add_button=False,
                        is_remove_button=True
                    )
                existing_dropdowns.append(None)  # Placeholder for new dropdown

            # Process selections and update dropdowns
            top_n_groups = {
                'top5_insurers': insurer_options_store['top5'],
                'top10_insurers': insurer_options_store['top10'],
                'top20_insurers': insurer_options_store['top20']
            }

            # Track which dropdowns need to be removed
            dropdowns_to_remove = []
            for i, _ in enumerate(existing_dropdowns):
                current_selected = selected_insurers[i] if i < len(selected_insurers) else None
                other_selected = [v for i2, v in enumerate(selected_insurers) if i2 != i and v is not None]

                if not current_selected:
                    continue

                excluded_insurers, has_top_selection = get_excluded_insurers(other_selected, top_n_groups)

                # Check if current selection conflicts with others
                if (has_top_selection and current_selected.startswith('top-')) or \
                   (current_selected in excluded_insurers):
                    logger.info(f"Marking dropdown {i} for removal due to selection conflict")
                    dropdowns_to_remove.append(i)

            # Remove conflicting dropdowns
            for index in sorted(dropdowns_to_remove, reverse=True):
                existing_dropdowns.pop(index)
                if index < len(selected_insurers):
                    selected_insurers.pop(index)

            # Ensure at least one dropdown exists
            if not existing_dropdowns:
                logger.info("Restoring single dropdown after conflicts")
                return [create_insurer_dropdown(
                    index=0,
                    options=insurer_options_store['insurer_options'],
                    is_add_button=True,
                    is_remove_button=False
                )], [None]

            # Update remaining dropdowns
            updated_dropdowns = []
            for i in range(len(existing_dropdowns)):
                current_selected = selected_insurers[i] if i < len(selected_insurers) else None
                other_selected = [v for i2, v in enumerate(selected_insurers) if i2 != i and v is not None]
                excluded_insurers, has_top_selection = get_excluded_insurers(other_selected, top_n_groups)

                updated_dropdowns.append(create_updated_dropdown(
                    index=i,
                    total_dropdowns=len(existing_dropdowns),
                    options=insurer_options_store['insurer_options'],
                    value=current_selected,
                    excluded_insurers=excluded_insurers,
                    has_top_selection=has_top_selection
                ))

            logger.debug(f"Final state - Selections: {selected_insurers}, Dropdowns: {len(updated_dropdowns)}")

            # Only update values if they've changed
            final_values = selected_insurers if selected_insurers != current_selected_insurers else dash.no_update
            output = (updated_dropdowns, final_values)

            return output

        except Exception as e:
            logger.error(f"Error in update_insurers_selections: {str(e)}", exc_info=True)
            raise