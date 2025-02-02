import json
from typing import List, Dict, Set, Tuple, Any

import dash
from dash import Dash, ALL, Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np

from application.components.dropdown import create_dynamic_dropdown
from config.default_values import MAX_DROPDOWNS, DEFAULT_INSURER
from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.mappings import map_insurer
from data_process.options import get_insurers_and_options

logger = get_logger(__name__)
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
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

    return create_dynamic_dropdown(
        dropdown_type='selected-insurers',
        index=index,
        options=filtered_options,
        value=value,
        is_add_button=(index == total_dropdowns - 1),
        is_remove_button=(total_dropdowns > 1)
    )

@timer
def get_consistently_top_insurers(
    df: pd.DataFrame,
    all_metrics: List[str],
    lines: List[str]
) -> Dict[str, Set[str]]:
    try:
        # Extract arrays once
        data = df[['year_quarter', 'metric', 'insurer', 'linemain', 'value']].values
        year_quarters = data[:, 0]
        metrics = data[:, 1]
        insurers = data[:, 2]
        linemains = data[:, 3]
        values = data[:, 4].astype(np.float64)

        # Get metric and latest quarter using numpy
        latest_quarter = np.max(year_quarters)
        metric_to_use = next(m for m in all_metrics if m in np.unique(metrics))

        # Create base masks
        quarter_mask = year_quarters == latest_quarter
        metric_mask = metrics == metric_to_use
        exclude_mask = np.isin(insurers, ['total', 'top-5', 'top-10', 'top-20'])
        base_mask = quarter_mask & metric_mask & ~exclude_mask

        # Pre-allocate dictionary for results
        top_insurers_by_line = {
            line: {'top_5': set(), 'top_10': set(), 'top_20': set()}
            for line in lines
        }

        # Process each line using numpy operations
        for line in lines:
            # Create line mask and combine with base mask
            line_mask = base_mask & (linemains == line)
            
            # Get masked data
            line_insurers = insurers[line_mask]
            line_values = values[line_mask]
            
            if len(line_insurers) > 0:
                # Sort using numpy
                sort_indices = np.argsort(-line_values)
                sorted_insurers = line_insurers[sort_indices]
                
                # Fill sets efficiently
                top_insurers_by_line[line]['top_5'] = set(sorted_insurers[:5])
                top_insurers_by_line[line]['top_10'] = set(sorted_insurers[:10])
                top_insurers_by_line[line]['top_20'] = set(sorted_insurers[:20])

        # Calculate intersections efficiently
        consistent_top_performers = {
            ranking: set.intersection(*(
                top_insurers_by_line[line][ranking]
                for line in lines
                if top_insurers_by_line[line][ranking]  # Only include non-empty sets
            )) if all(top_insurers_by_line[line][ranking] for line in lines) else set()
            for ranking in ['top_5', 'top_10', 'top_20']
        }

        return consistent_top_performers

    except Exception as e:
        logger.error(f"Error finding consistently top insurers: {str(e)}", exc_info=True)
        return {'top_5': set(), 'top_10': set(), 'top_20': set()}
    return consistent_top_performers

    
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
         State('primary-metric-all-values', 'data')
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
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            trigger_id = ctx.triggered[0]['prop_id']
            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            insurer_options = get_insurers_and_options(df, primary_metrics, lines)
            top_insurers = get_consistently_top_insurers(df, primary_metrics, lines)

            logger.debug(f"insurer_options: {insurer_options}")
            if not existing_dropdowns:
                logger.debug("Initializing first dropdown")
                return [create_dynamic_dropdown(
                    dropdown_type='selected-insurers',
                    index=0,
                    options=insurer_options,
                    is_add_button=True,
                    is_remove_button=False
                )], []

            logger.debug(f"selected_insurers {selected_insurers}")
            logger.debug(f"insurer_options: {insurer_options}")

            selected_insurers = [v for v in (selected_insurers or []) if
                                 v in {opt['value']
                                 for opt in insurer_options}]

            logger.debug(f"selected_insurers: {selected_insurers}")
            # If no valid selections, use default
            if not selected_insurers:
                selected_insurers = [DEFAULT_INSURER]
            logger.debug(f"Current selections: {selected_insurers}")

            # Handle remove button click
            if 'remove-selected-insurers-btn' in trigger_id:
                if len(existing_dropdowns) <= 1:
                    logger.debug("Cannot remove last dropdown")
                    raise PreventUpdate

                component_id = json.loads(trigger_id.split('.')[0])
                removed_index = int(component_id['index'])
                logger.debug(f"Removing dropdown at index {removed_index}")

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

                logger.debug("Adding new dropdown")
                # Update last dropdown to remove add button
                if existing_dropdowns:
                    last_index = len(existing_dropdowns) - 1
                    existing_dropdowns[last_index] = create_dynamic_dropdown(
                        dropdown_type='selected-insurers',
                        index=last_index,
                        options=insurer_options,
                        value=selected_insurers[last_index] if last_index < len(selected_insurers) else None,
                        is_add_button=False,
                        is_remove_button=True
                    )
                existing_dropdowns.append(None)  # Placeholder for new dropdown

            # Process selections and update dropdowns
            top_n_groups = {
                'top-5':  top_insurers['top_5'],
                'top-10': top_insurers['top_10'],
                'top-20': top_insurers['top_10']
            }

            # Track which dropdowns need to be removed
            dropdowns_to_remove = []
            for i, dropdown in enumerate(existing_dropdowns):
                current_selected = selected_insurers[i] if i < len(selected_insurers) else None
                other_selected = [v for i2, v in enumerate(selected_insurers) if i2 != i and v is not None]

                if not current_selected:
                    continue

                # Calculate excluded insurers directly
                excluded_insurers = set()
                has_top_selection = False
                for selected in (other_selected or []):  # Handle None case explicitly
                    if not selected:
                        continue
                    if selected.startswith('top-'):
                        has_top_selection = True
                        excluded_insurers.update(set(top_n_groups.get(selected, [])))
                    else:
                        excluded_insurers.add(selected)

                # Check if current selection conflicts with others
                if (has_top_selection and current_selected.startswith('top-')) or \
                   (current_selected in excluded_insurers):
                    logger.debug(f"Marking dropdown {i} for removal due to selection conflict")
                    dropdowns_to_remove.append(i)

            # Remove conflicting dropdowns
            for index in sorted(dropdowns_to_remove, reverse=True):
                existing_dropdowns.pop(index)
                if index < len(selected_insurers):
                    selected_insurers.pop(index)

            # Ensure at least one dropdown exists
            if not existing_dropdowns:
                logger.debug("Restoring single dropdown after conflicts")
                return [create_dynamic_dropdown(
                    dropdown_type='selected-insurers',
                    index=0,
                    options=insurer_options,
                    is_add_button=True,
                    is_remove_button=False
                )], [None]

            # Update remaining dropdowns
            updated_dropdowns = []
            for i, dropdown in enumerate(existing_dropdowns):
                current_selected = selected_insurers[i] if i < len(selected_insurers) else None
                other_selected = [v for i2, v in enumerate(selected_insurers) if i2 != i and v is not None]

                # Calculate excluded insurers for updated dropdown
                excluded_insurers = set()
                has_top_selection = False
                for selected in (other_selected or []):
                    if not selected:
                        continue
                    if selected.startswith('top-'):
                        has_top_selection = True
                        excluded_insurers.update(set(top_n_groups.get(selected, [])))
                    else:
                        excluded_insurers.add(selected)

                updated_dropdowns.append(create_updated_dropdown(
                    index=i,
                    total_dropdowns=len(existing_dropdowns),
                    options=insurer_options,
                    value=current_selected,
                    excluded_insurers=excluded_insurers,
                    has_top_selection=has_top_selection
                ))


            logger.debug(f"options: {insurer_options}")
            logger.debug(f"Final state - Selections: {selected_insurers}, Dropdowns: {len(updated_dropdowns)}")

            # Only update values if they've changed
            final_values = selected_insurers if selected_insurers != current_selected_insurers else dash.no_update

            output = (updated_dropdowns, final_values)

            return output

        except Exception as e:
            logger.error(f"Error in update_insurers_selections: {str(e)}", exc_info=True)
            raise