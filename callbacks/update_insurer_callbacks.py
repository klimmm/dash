from typing import List, Dict, Optional
import json
import dash
from dash import Dash, html, dcc, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from config.logging_config import get_logger
from application.dropdown_components import StyleConstants
from data_process.data_utils import map_insurer
from application.button_components import ButtonStyleConstants

logger = get_logger(__name__)


def create_insurer_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = True
) -> html.Div:

    button_props = {
        'add': {
            'icon_class': "fas fa-plus",
            'button_id': "selected-insurers-add-btn",
            'button_class': ButtonStyleConstants.BTN["ADD"]
        },
        'remove': {
            'icon_class': "fas fa-xmark",
            'button_id': {'type': 'remove-selected-insurers-btn', 'index': str(index)},
            'button_class': ButtonStyleConstants.BTN["REMOVE"]
        }
    }

    return html.Div(
        className="d-flex align-items-center w-100",
        children=[
            html.Div(
                className="dash-dropdown flex-grow-1",
                children=[
                    dcc.Dropdown(
                        id={'type': 'dynamic-selected-insurers', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select insurer",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,
                        searchable=False
                    )
                ]
            ),
            html.Button(
                children=html.I(className=button_props['remove']['icon_class']), 
                id=button_props['remove']['button_id'],
                className=button_props['remove']['button_class'],
                n_clicks=0
            ) if is_remove_button else html.Div(
                className=button_props['remove']['button_class'],
                style={'visibility': 'hidden'}
            ),
            html.Button(
                children=html.I(className=button_props['add']['icon_class']),
                id=button_props['add']['button_id'],
                className=button_props['add']['button_class'],
                n_clicks=0
            ) if is_add_button else html.Div(
                className=button_props['add']['button_class'],
                style={'visibility': 'hidden'}
            ),
        ]
    )


def setup_insurers_callbacks(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-container', 'children'),
        [Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
         Input('selected-insurers-add-btn', 'n_clicks'),
         Input({'type': 'remove-selected-insurers-btn', 'index': ALL}, 'n_clicks'),
         Input('intermediate-data-store', 'data')],
        [State('selected-insurers-container', 'children')]
    )
    def update_insurers_selections(
        selected_insurers: List[str],
        add_insurer_clicks: int,
        remove_insurer_clicks: List[int],
        intermediate_data: Dict,
        existing_dropdowns: List
    ) -> List:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            insurer_options = intermediate_data.get('insurer_options', [])

            # Initialize if needed
            if not existing_dropdowns:
                return [create_insurer_dropdown(
                    index=0,
                    options=insurer_options,
                    is_add_button=True,
                    is_remove_button=False
                )]

            # Clean up selected insurers
            selected_insurers = [v for v in (selected_insurers or []) if v is not None]

            trigger_id = ctx.triggered[0]['prop_id']

            if '.n_clicks' in trigger_id and 'intermediate-data-store' not in trigger_id:
                if 'remove-selected-insurers-btn' in trigger_id:
                    # Prevent removing if it's the last dropdown
                    if len(existing_dropdowns) <= 1:
                        raise PreventUpdate

                    component_id = json.loads(trigger_id.split('.')[0])
                    removed_index = int(component_id['index'])

                    # Check if removing a dropdown with the only selected value
                    has_value_at_index = removed_index < len(selected_insurers) and selected_insurers[removed_index] is not None
                    other_values = [v for i, v in enumerate(selected_insurers) if i != removed_index and v is not None]

                    if has_value_at_index and not other_values:
                        # If removing the only selected value, move it to the remaining empty dropdown
                        value_to_preserve = selected_insurers[removed_index]
                        # Remove the dropdown at the specified index
                        existing_dropdowns.pop(removed_index)
                        # Find the first empty dropdown
                        empty_index = next((i for i, v in enumerate(selected_insurers) if v is None), 0)
                        # Create updated dropdowns list with preserved value
                        return [
                            create_insurer_dropdown(
                                index=i,
                                options=insurer_options,
                                value=value_to_preserve if i == empty_index else None,
                                is_add_button=(i == len(existing_dropdowns) - 1),
                                is_remove_button=(len(existing_dropdowns) > 1)
                            ) for i in range(len(existing_dropdowns))
                        ]
                    else:
                        # Normal removal process
                        existing_dropdowns.pop(removed_index)
                        if removed_index < len(selected_insurers):
                            selected_insurers.pop(removed_index)

                    # Recreate all dropdowns with updated indices
                    return [
                        create_insurer_dropdown(
                            index=i,
                            options=insurer_options,
                            value=selected_insurers[i] if i < len(selected_insurers) else None,
                            is_add_button=(i == len(existing_dropdowns) - 1),
                            is_remove_button=(len(existing_dropdowns) > 1)
                        ) for i in range(len(existing_dropdowns))
                    ]

                if 'selected-insurers-add-btn' in trigger_id:
                    # Update last dropdown to remove add button
                    if existing_dropdowns:
                        last_index = len(existing_dropdowns) - 1
                        existing_dropdowns[last_index] = create_insurer_dropdown(
                            index=last_index,
                            options=insurer_options,
                            value=selected_insurers[last_index] if last_index < len(selected_insurers) else None,
                            is_add_button=False,
                            is_remove_button=True
                        )

                    # Add new dropdown with add button
                    filtered_options = [
                        opt for opt in insurer_options 
                        if ('value' in opt and opt['value'] not in selected_insurers)
                    ]
                    new_dropdown = create_insurer_dropdown(
                        index=len(existing_dropdowns),
                        options=filtered_options,
                        value=None,
                        is_add_button=True,
                        is_remove_button=True
                    )
                    existing_dropdowns.append(new_dropdown)

            # Update existing dropdowns with filtered options
            updated_dropdowns = []
            for i, _ in enumerate(existing_dropdowns):
                current_selected = selected_insurers[i] if i < len(selected_insurers) else None
                other_selected = [v for j, v in enumerate(selected_insurers) if j != i and v is not None]

                dropdown_options = [
                    opt for opt in insurer_options 
                    if opt['value'] not in other_selected
                ]

                if current_selected and not any(opt['value'] == current_selected for opt in dropdown_options):
                    dropdown_options.append({
                        'label': map_insurer(current_selected),
                        'value': current_selected
                    })

                updated_dropdowns.append(create_insurer_dropdown(
                    index=i,
                    options=dropdown_options,
                    value=current_selected,
                    is_add_button=(i == len(existing_dropdowns) - 1),
                    is_remove_button=(len(existing_dropdowns) > 1)
                ))

            return updated_dropdowns

        except Exception as e:
            logger.error(f"Error in update_insurers_selections: {str(e)}", exc_info=True)
            raise


def setup_sync_insurers_callback(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-all-values', 'data'),
        [Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value')]
    )
    def sync_metric_values(values: List[str]) -> List[str]:
        values = [v for v in values if v is not None and v != '']
        return values