from typing import List, Tuple, Dict
import json
import dash
from dash import Dash, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from config.logging_config import get_logger, track_callback, track_callback_end
from application.filters import create_insurer_dropdown
from data_process.data_utils import map_insurer


logger = get_logger(__name__)

def setup_sync_insurers_callback(app: Dash) -> None:
    """Setup callback for syncing metric values"""

    @app.callback(
        Output('selected-insurers-all-values', 'data'),
        [Input('selected-insurers', 'value'),
         Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value')]
    )
    def sync_metric_values(main_value: str, dynamic_values: List[str]) -> List[str]:
        return [main_value] + [v for v in dynamic_values if v is not None]

def setup_insurers_callbacks(app: Dash) -> None:
    @app.callback(
        [Output('selected-insurers', 'options'),
         Output('selected-insurers', 'value'),
         Output('selected-insurers-container', 'children')],
        [Input('selected-insurers', 'value'),
         Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
         Input('selected-insurers-add-btn', 'n_clicks'),
         Input({'type': 'remove-selected-insurers-btn', 'index': ALL}, 'n_clicks'),
         Input('intermediate-data-store', 'data')],
        [State('selected-insurers-container', 'children')],
    )
    def update_metric_selections(
        selected_insurer: str,
        selected_dynamic_insurers: List[str],
        add_insurer_clicks: int,
        remove_insurer_clicks: List[int],
        intermediate_data: Dict,
        existing_dropdowns: List
    ) -> Tuple:
        """Update metric dropdowns based on user interactions"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            insurer_options = intermediate_data.get('insurer_options', [])

            logger.debug(f"insurer_options {insurer_options}")
            logger.debug(f"selected_insurer {selected_insurer}")
            logger.debug(f"selected_dynamic_insurers {selected_dynamic_insurers}")
            # Initialize dropdowns if None
            existing_dropdowns = existing_dropdowns or []
            selected_dynamic_insurers = [v for v in (selected_dynamic_insurers or []) if v is not None]
            all_selected_insurers = (selected_dynamic_insurers or []) + [selected_insurer]

            # Handle remove button click
            if '.n_clicks' in ctx.triggered[0]['prop_id'] and '"type":"remove-selected-insurers-btn"' in ctx.triggered[0]['prop_id']:
                component_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
                removed_index = component_id['index']

                if ctx.triggered[0]['value'] is not None:
                    selected_dynamic_insurers = [v for i, v in enumerate(selected_dynamic_insurers) if i != removed_index]
                    existing_dropdowns = [
                        d for i, d in enumerate(existing_dropdowns) if i != removed_index
                    ]

            # Handle add button click
            if 'selected-insurers-add-btn' in ctx.triggered[0]['prop_id']:
                new_selected_insurers_dropdown = create_insurer_dropdown(
                    index=len(existing_dropdowns),
                    options=[opt for opt in insurer_options if opt['value'] not in all_selected_insurers],
                    value=None
                )
                existing_dropdowns.append(new_selected_insurers_dropdown)

            # Update existing dropdowns
            updated_selected_insurers_dropdowns = []
            for i, _ in enumerate(existing_dropdowns):
                current_selected_insurer = selected_dynamic_insurers[i] if i < len(selected_dynamic_insurers) else None
                other_insurers_selected = [v for v in all_selected_insurers if v != current_selected_insurer]

                insurer_dropdown_options = [
                    opt for opt in insurer_options 
                    if opt['value'] not in other_insurers_selected
                ]

                if current_selected_insurer and not any(opt['value'] == current_selected_insurer for opt in insurer_dropdown_options):
                    insurer_dropdown_options.append({
                        'label': map_insurer(current_selected_insurer),
                        'value': current_selected_insurer
                    })

                updated_selected_insurers_dropdowns.append(create_insurer_dropdown(
                    index=i,
                    options=insurer_dropdown_options,
                    value=current_selected_insurer
                ))

            # Filter primary metric options
            filtered_selected_insurer_options = [
                opt for opt in insurer_options 
                if opt['value'] not in selected_dynamic_insurers
            ]

            if selected_insurer and not any(opt['value'] == selected_insurer for opt in filtered_selected_insurer_options):
                filtered_selected_insurer_options.append({
                    'label': map_insurer(selected_insurer),
                    'value': selected_insurer
                })

            return (
                filtered_selected_insurer_options,
                selected_insurer,
                updated_selected_insurers_dropdowns
            )

        except Exception as e:
            logger.error(f"Error in update_metric_dropdowns: {str(e)}", exc_info=True)
            raise