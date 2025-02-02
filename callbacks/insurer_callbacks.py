import json
import time
from functools import wraps
from typing import List, Dict, Set, Any

import dash
from dash import Dash, ALL, Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from application.components.dropdown import create_dynamic_dropdown
from config.default_values import MAX_DROPDOWNS, DEFAULT_INSURER
from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.insurer_processor import InsurerDataProcessor

logger = get_logger(__name__)


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug(f"{func.__name__} took {(end - start) * 1000:.2f}ms to execute")
        return result
    return wrapper


@timer
def create_updated_dropdown(
    index: int,
    total_dropdowns: int,
    options: List[Dict[str, Any]],
    value: str = None,
    excluded_insurers: Set[str] = None,
    has_top_selection: bool = False
) -> Dict:
    """
    Create a dropdown with filtered options based on current selections.
    """
    if excluded_insurers is None:
        excluded_insurers = set()

    # Filter out options whose value is in the exclusion set unless it is the currently selected value
    filtered_options = [
        opt for opt in options
        if (opt['value'] not in excluded_insurers and
            (not has_top_selection or not opt['value'].startswith('top-') or value == opt['value']))
    ]

    logger.debug(f"Creating updated dropdown at index {index} with value {value} "
                 f"and {len(filtered_options)} filtered options.")
    return create_dynamic_dropdown(
        dropdown_type='selected-insurers',
        index=index,
        options=filtered_options,
        value=value,
        is_add_button=(index == total_dropdowns - 1),
        is_remove_button=(total_dropdowns > 1)
    )


def setup_insurer_selection(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-container', 'children'),
        Output('selected-insurers-all-values', 'data'),
        [
            Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
            Input('selected-insurers-add-btn', 'n_clicks'),
            Input({'type': 'remove-selected-insurers-btn', 'index': ALL}, 'n_clicks'),
            Input('intermediate-data-store', 'data')
        ],
        [
            State('selected-insurers-container', 'children'),
            State('selected-insurers-all-values', 'data'),
            State('insurance-lines-all-values', 'data'),
            State('metric-all-values', 'data')
        ]
    )
    @log_callback
    @timer
    def update_insurers_selections(
        selected_insurers: List[str],
        add_insurer_clicks: int,
        remove_insurer_clicks: List[int],
        intermediate_data: Dict,
        existing_dropdowns: List,
        current_selected_insurers: List[str],
        lines: List[str],
        primary_metrics: List[str],
    ) -> List:
        """
        @API_STABILITY: BACKWARDS_COMPATIBLE
        Updates insurer selection dropdowns based on user interactions.
        """
        logger.debug("Entered update_insurers_selections callback.")
        ctx = dash.callback_context
        if not ctx.triggered:
            logger.debug("No triggered input, preventing update.")
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id']
        logger.debug(f"Triggered by: {trigger_id}")

        try:

            # Rebuild DataFrame and options
            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            processor = InsurerDataProcessor(df)
            insurer_options = processor.get_insurer_options(all_metrics=primary_metrics, lines=lines)
            top_insurers = processor.get_consistently_top_insurers(all_metrics=primary_metrics, lines=lines)
            logger.debug(f"Insurer options obtained: {insurer_options}")

            # Initialize first dropdown if none exist
            if not existing_dropdowns:
                logger.debug("No existing dropdowns found; initializing first dropdown.")
                initial_dropdown = create_dynamic_dropdown(
                    dropdown_type='selected-insurers',
                    index=0,
                    options=insurer_options,
                    is_add_button=True,
                    is_remove_button=False
                )
                return [initial_dropdown], []

            # Filter selected insurers to only valid options
            valid_options = {opt['value'] for opt in insurer_options}
            selected_insurers = [v for v in (selected_insurers or []) if v in valid_options]
            if not selected_insurers:
                selected_insurers = [DEFAULT_INSURER]
            logger.debug(f"Filtered selected insurers: {selected_insurers}")

            # Process remove action
            if 'remove-selected-insurers-btn' in trigger_id:
                if len(existing_dropdowns) <= 1:
                    logger.debug("Attempted to remove last dropdown; update prevented.")
                    raise PreventUpdate

                comp_id = json.loads(trigger_id.split('.')[0])
                removed_index = int(comp_id['index'])
                logger.debug(f"Processing removal of dropdown at index {removed_index}.")
                removed_value = selected_insurers[removed_index] if removed_index < len(selected_insurers) else None
                selected_insurers = [v for i, v in enumerate(selected_insurers) if i != removed_index]
                # If removal leaves no valid selections, preserve the removed value as fallback
                if removed_value and all(v is None for v in selected_insurers):
                    selected_insurers = [removed_value] + [None] * (len(existing_dropdowns) - 2)
                existing_dropdowns.pop(removed_index)

            # Process add action
            elif 'selected-insurers-add-btn' in trigger_id:
                if len(existing_dropdowns) >= MAX_DROPDOWNS:
                    logger.debug(f"Maximum dropdowns ({MAX_DROPDOWNS}) reached; add action prevented.")
                    raise PreventUpdate

                logger.debug("Processing add action for a new dropdown.")
                # Update last dropdown: remove add button and enable removal
                last_index = len(existing_dropdowns) - 1
                existing_dropdowns[last_index] = create_dynamic_dropdown(
                    dropdown_type='selected-insurers',
                    index=last_index,
                    options=insurer_options,
                    value=selected_insurers[last_index] if last_index < len(selected_insurers) else None,
                    is_add_button=False,
                    is_remove_button=True
                )
                existing_dropdowns.append(None)  # Placeholder for the new dropdown

            # Prepare mapping for top insurer groups (preserving original mapping for backward compatibility)
            top_n_groups = {
                'top-5': top_insurers['top_5'],
                'top-10': top_insurers['top_10'],
                'top-20': top_insurers['top_10']  # Intentionally mapped as in original code
            }

            # Helper to compute exclusions for a given dropdown index
            def compute_exclusions(idx: int) -> (Set[str], bool):
                others = [v for j, v in enumerate(selected_insurers) if j != idx and v]
                exclusions = set()
                has_top = False
                for sel in others:
                    if sel.startswith('top-'):
                        has_top = True
                        exclusions.update(top_n_groups.get(sel, set()))
                    else:
                        exclusions.add(sel)
                return exclusions, has_top

            # Identify dropdowns with conflicting selections
            dropdowns_to_remove = []
            for i, _ in enumerate(existing_dropdowns):
                current_sel = selected_insurers[i] if i < len(selected_insurers) else None
                if not current_sel:
                    continue
                exclusions, has_top = compute_exclusions(i)
                if (has_top and current_sel.startswith('top-')) or (current_sel in exclusions):
                    logger.debug(f"Dropdown at index {i} marked for removal due to conflict with selection '{current_sel}'.")
                    dropdowns_to_remove.append(i)

            # Remove dropdowns with conflicts (from highest index to lowest to avoid reindexing issues)
            for index in sorted(dropdowns_to_remove, reverse=True):
                removed_val = selected_insurers.pop(index) if index < len(selected_insurers) else None
                existing_dropdowns.pop(index)
                logger.debug(f"Removed dropdown at index {index} with selection '{removed_val}'.")

            # Ensure at least one dropdown remains
            if not existing_dropdowns:
                logger.debug("All dropdowns removed due to conflicts; restoring single dropdown.")
                new_dropdown = create_dynamic_dropdown(
                    dropdown_type='selected-insurers',
                    index=0,
                    options=insurer_options,
                    is_add_button=True,
                    is_remove_button=False
                )
                return [new_dropdown], [None]

            # Update remaining dropdowns with recalculated exclusions
            updated_dropdowns = []
            for i, _ in enumerate(existing_dropdowns):
                current_sel = selected_insurers[i] if i < len(selected_insurers) else None
                exclusions, has_top = compute_exclusions(i)
                updated_dropdown = create_updated_dropdown(
                    index=i,
                    total_dropdowns=len(existing_dropdowns),
                    options=insurer_options,
                    value=current_sel,
                    excluded_insurers=exclusions,
                    has_top_selection=has_top
                )
                updated_dropdowns.append(updated_dropdown)

            logger.debug(f"Final state: selections = {selected_insurers}, dropdowns count = {len(updated_dropdowns)}")
            final_values = selected_insurers if selected_insurers != current_selected_insurers else dash.no_update

            logger.debug("Exiting update_insurers_selections callback successfully.")
            return updated_dropdowns, final_values

        except Exception as e:
            logger.error(f"Error in update_insurers_selections: {str(e)}", exc_info=True)
            raise