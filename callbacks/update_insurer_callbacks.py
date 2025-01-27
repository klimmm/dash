from typing import List, Dict, Optional
import json
import dash
from dash import Dash, html, dcc, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from config.logging_config import get_logger, track_callback, track_callback_end
from data_process.data_utils import map_insurer
from application.button_components import ButtonStyleConstants
from dash import no_update

logger = get_logger(__name__)

class StyleConstants:
    FORM = {
        "DD": "dd-control",
    }

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

'''def setup_sync_insurers_callback(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-all-values', 'data'),
        [Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value')],
        State('selected-insurers-all-values', 'data'),
    )
    def sync_insurer_values(values: List[str], current_values: List[str]) -> List[str]:
        try:
            start_info = track_callback(__name__, 'sync_insurer_values', dash.callback_context)
            logger.warning(f"selected_insurers input {values}")
            new_values = [v for v in values if v is not None and v != '']
            if new_values == current_values:
                track_callback_end(__name__, 'sync_metric_values', start_info, 
                                 message_no_update="No changes in values")
                return dash.no_update
            
            track_callback_end(__name__, 'sync_insurer_values', start_info, result=new_values)
            return new_values
        except Exception as e:
            track_callback_end(__name__, 'sync_insurer_values', start_info, error=e)
            raise'''

def setup_insurers_callbacks(app: Dash) -> None:
    @app.callback(
        Output('selected-insurers-container', 'children'),
        Output('selected-insurers-all-values', 'data'),
        [Input({'type': 'dynamic-selected-insurers', 'index': ALL}, 'value'),
         Input('selected-insurers-add-btn', 'n_clicks'),
         Input({'type': 'remove-selected-insurers-btn', 'index': ALL}, 'n_clicks'),
         Input('insurer-options-store', 'data')],
        [State('selected-insurers-container', 'children'),
         State('selected-insurers-all-values', 'data'),
        ]
    )
    def update_insurers_selections(
        selected_insurers: List[str],
        add_insurer_clicks: int,
        remove_insurer_clicks: List[int],
        insurer_options_store: Dict,
        existing_dropdowns: List,
        current_selected_insurers: List[str],
    ) -> List:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            start_info = track_callback(__name__, 'update_insurers_selections', ctx)
            insurer_options = insurer_options_store['insurer_options'] # since it's coming directly from the store
            top5_insurers = insurer_options_store['top5']
            top10_insurers = insurer_options_store['top10']
            top20_insurers = insurer_options_store['top20']

            logger.warning(f"selected_insurers{selected_insurers}")
            logger.warning(f"top20_insurers{top20_insurers}")
            # If selected_insurers is not empty, filter based on the first selection
            if selected_insurers:
                filter_list = None
                if 'top-5' in selected_insurers:
                    filter_list = top5_insurers
                    
                elif 'top-10' in selected_insurers:
                    filter_list = top10_insurers
                elif 'top-20' in selected_insurers:
                    filter_list = top20_insurers
                
                if filter_list:
                    insurer_options_add = [option for option in insurer_options if option['value'] not in filter_list and option['value'] not in ['top-5', 'top-10', 'top-20']]
                    displayed_insurers =  filter_list
                else:
                    insurer_options_add = insurer_options
                    displayed_insurers = None

            else:
                insurer_options_add = insurer_options
                displayed_insurers = None
            logger.warning(f"insurer_options_add{insurer_options_add}")
            

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
                        track_callback_end(__name__, 'update_insurers_selections', start_info, 
                                         message_no_update="Cannot remove last dropdown")                        
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
                    updated_dropdowns = [
                        create_insurer_dropdown(
                            index=i,
                            options=insurer_options,
                            value=selected_insurers[i] if i < len(selected_insurers) else None,
                            is_add_button=(i == len(existing_dropdowns) - 1),
                            is_remove_button=(len(existing_dropdowns) > 1)
                        ) for i in range(len(existing_dropdowns))
                    ]
                    output = updated_dropdowns, selected_insurers
                    track_callback_end(__name__, 'update_insurers_selections', start_info, result=output)
                
                    return output
                
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

                if current_selected in ['top-5', 'top-10', 'top-20']:
                    dropdown_options = [
                        opt for opt in insurer_options 
                    ]
                    dd_value=current_selected
                
                else:
                        dropdown_options = [
                            opt for opt in insurer_options_add 
                            if opt['value'] not in other_selected
                        ]
                        if displayed_insurers is not None:
                            dd_value=current_selected if current_selected not in displayed_insurers else None
                        else:
                            dd_value=current_selected

                
                
                if current_selected and not any(opt['value'] == current_selected for opt in dropdown_options):
                    dropdown_options.append({
                        'label': map_insurer(current_selected),
                        'value': current_selected
                    })

                updated_dropdowns.append(create_insurer_dropdown(
                    index=i,
                    options=dropdown_options,
                    value=dd_value,
                    is_add_button=(i == len(existing_dropdowns) - 1),
                    is_remove_button=(len(existing_dropdowns) > 1)
                ))

            logger.warning(f"updated_dropdowns output {selected_insurers}")
            if current_selected_insurers == selected_insurers:
                output = updated_dropdowns, dash.no_update
                track_callback_end(__name__, 'update_insurers_selections', start_info, result=output)
                return output
            output = updated_dropdowns, selected_insurers

            track_callback_end(__name__, 'update_insurers_selections', start_info, result=output)

            return output

        except Exception as e:
            track_callback_end(__name__, 'update_insurers_selections', start_info, error=e)
            logger.error(f"Error in update_insurers_selections: {str(e)}", exc_info=True)
            raise

