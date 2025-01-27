from typing import List, Dict, Optional
import json
import dash
from dash import Dash, html, dcc, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from constants.translations import translate
from application.button_components import ButtonStyleConstants
from callbacks.get_metrics import get_metric_options
from config.logging_config import get_logger, track_callback, track_callback_end


logger = get_logger(__name__)

class StyleConstants:
    FORM = {
        "DD": "dd-control",
    }




def create_primary_metric_dropdown(
    index: int,
    value: Optional[str] = None,
    options: List[Dict[str, str]] = None,
    is_add_button: bool = False,
    is_remove_button: bool = True
) -> html.Div:

    button_props = {
        'add': {
            'icon_class': "fas fa-plus",
            'button_id': "primary-metric-add-btn",
            'button_class': ButtonStyleConstants.BTN["ADD"]
        },
        'remove': {
            'icon_class': "fas fa-xmark",
            'button_id': {'type': 'remove-primary-metric-btn', 'index': str(index)},
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
                        id={'type': 'dynamic-primary-metric', 'index': index},
                        options=options,
                        value=value,
                        multi=False,
                        clearable=False,
                        placeholder="Select primary_metric",
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

'''def setup_sync_metrics_callback(app: Dash) -> None:
    @app.callback(
        Output('primary-metric-all-values', 'data'),
        [Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value')],
        State('primary-metric-all-values', 'data'),
    )
    def sync_metric_values(values: List[str], current_values: List[str]) -> List[str]:
        try:
            start_info = track_callback(__name__, 'sync_metric_values', dash.callback_context)
            
            new_values = [v for v in values if v is not None and v != '']
            if new_values == current_values:
                track_callback_end(__name__, 'sync_metric_values', start_info, 
                                 message_no_update="No changes in values")
                return dash.no_update
            
            track_callback_end(__name__, 'sync_metric_values', start_info, result=new_values)
            return new_values
        except Exception as e:
            track_callback_end(__name__, 'sync_metric_values', start_info, error=e)
            raise'''
            
def setup_metric_callbacks(app: Dash) -> None:
    @app.callback(
        [Output('primary-metric-container', 'children'),
         Output('secondary-y-metric', 'options'),
         Output('reporting-form-inter', 'data'),
         Output('primary-metric-all-values', 'data'),
        ],
        [Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
         Input('primary-metric-add-btn', 'n_clicks'),
         Input({'type': 'remove-primary-metric-btn', 'index': ALL}, 'n_clicks'),
         Input('reporting-form', 'data'),
         Input('insurance-lines-state', 'data'),
         Input('period-type', 'data'),
        ],
        [State('intermediate-data-store', 'data'),
         State('primary-metric-container', 'children'),
         State('secondary-y-metric', 'value'),
         State('primary-metric-all-values', 'data')]
    )
    def update_primary_metric_selections(
        primary_metric: List[str],
        add_primary_metric_clicks: int,
        remove_primary_metric_clicks: List[int],
        reporting_form: str,
        lines: List[str],
        period_type: str,
        intermediate_data: Dict,
        existing_dropdowns: List,
        secondary_metric: str,
        all_selected_primary_metric: List[str]
    ) -> List:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:
            start_info = track_callback(__name__, 'update_primary_metric_selections', ctx)
            
            primary_metric_options, secondary_metric_options, valid_selected_primary_metrics, secondary_metric_value = get_metric_options(reporting_form, primary_metric, secondary_metric)

            # Initialize if needed
            if not existing_dropdowns:
                return [create_primary_metric_dropdown(
                    index=0,
                    options=primary_metric_options,
                    is_add_button=True,
                    is_remove_button=False
                )]
            logger.debug(f"primary_metric{primary_metric}")
            logger.debug(f"reporting_form{reporting_form}")
            logger.debug(f"valid_selected_primary_metrics{valid_selected_primary_metrics}")

            # Clean up selected primary_metric
            primary_metric = [v for v in (primary_metric or []) if v is not None and v in valid_selected_primary_metrics] or valid_selected_primary_metrics            
            logger.debug(f"primary_metric{primary_metric}")
            trigger_id = ctx.triggered[0]['prop_id']


            if '.n_clicks' in trigger_id and 'intermediate-data-store' not in trigger_id:
                if 'remove-primary-metric-btn' in trigger_id:
                    # Prevent removing if it's the last dropdown
                    if len(existing_dropdowns) <= 1:
                        track_callback_end(__name__, 'update_primary_metric_selections', start_info, 
                                         message_no_update="Cannot remove last dropdown")
                        raise PreventUpdate

                    component_id = json.loads(trigger_id.split('.')[0])
                    removed_index = int(component_id['index'])

                    # Check if removing a dropdown with the only selected value
                    has_value_at_index = removed_index < len(primary_metric) and primary_metric[removed_index] is not None
                    other_values = [v for i, v in enumerate(primary_metric) if i != removed_index and v is not None]

                    if has_value_at_index and not other_values:
                        # If removing the only selected value, move it to the remaining empty dropdown
                        value_to_preserve = primary_metric[removed_index]
                        # Remove the dropdown at the specified index
                        existing_dropdowns.pop(removed_index)
                        # Find the first empty dropdown
                        empty_index = next((i for i, v in enumerate(primary_metric) if v is None), 0)
                        # Create updated dropdowns list with preserved value
                        return [
                            create_primary_metric_dropdown(
                                index=i,
                                options=primary_metric_options,
                                value=value_to_preserve if i == empty_index else None,
                                is_add_button=(i == len(existing_dropdowns) - 1),
                                is_remove_button=(len(existing_dropdowns) > 1)
                            ) for i in range(len(existing_dropdowns))
                        ]
                    else:
                        # Normal removal process
                        existing_dropdowns.pop(removed_index)
                        if removed_index < len(primary_metric):
                            primary_metric.pop(removed_index)

                    # Recreate all dropdowns with updated indices
                    updated_dropdowns = [
                        create_primary_metric_dropdown(
                            index=i,
                            options=primary_metric_options,
                            value=primary_metric[i] if i < len(primary_metric) else None,
                            is_add_button=(i == len(existing_dropdowns) - 1),
                            is_remove_button=(len(existing_dropdowns) > 1)
                        ) for i in range(len(existing_dropdowns))
                    ]

                    
                    output = (updated_dropdowns, secondary_metric_options, reporting_form, primary_metric)
                    track_callback_end(__name__, 'update_primary_metric_selections', start_info, result=output)
                    return output
                
                if 'primary-metric-add-btn' in trigger_id:
                    # Update last dropdown to remove add button
                    if existing_dropdowns:
                        last_index = len(existing_dropdowns) - 1
                        existing_dropdowns[last_index] = create_primary_metric_dropdown(
                            index=last_index,
                            options=primary_metric_options,
                            value=primary_metric[last_index] if last_index < len(primary_metric) else None,
                            is_add_button=False,
                            is_remove_button=True
                        )

                    # Add new dropdown with add button
                    filtered_options = [
                        opt for opt in primary_metric_options 
                        if ('value' in opt and opt['value'] not in primary_metric)
                    ]
                    new_dropdown = create_primary_metric_dropdown(
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
                current_selected = primary_metric[i] if i < len(primary_metric) else None
                other_selected = [v for j, v in enumerate(primary_metric) if j != i and v is not None]

                dropdown_options = [
                    opt for opt in primary_metric_options 
                    if opt['value'] not in other_selected
                ]

                if current_selected and not any(opt['value'] == current_selected for opt in dropdown_options):
                    dropdown_options.append({
                        'label': translate(current_selected),
                        'value': current_selected
                    })

                updated_dropdowns.append(create_primary_metric_dropdown(
                    index=i,
                    options=dropdown_options,
                    value=current_selected,
                    is_add_button=(i == len(existing_dropdowns) - 1),
                    is_remove_button=(len(existing_dropdowns) > 1)
                ))

            if primary_metric == all_selected_primary_metric:
                output = (updated_dropdowns, secondary_metric_options, reporting_form, primary_metric)
                track_callback_end(__name__, 'update_primary_metric_selections', start_info, result=output)
                return output

            output = (updated_dropdowns, secondary_metric_options, reporting_form, primary_metric)
            track_callback_end(__name__, 'update_primary_metric_selections', start_info, result=output)

            return output

        except Exception as e:
            track_callback_end(__name__, 'update_primary_metric_selections', start_info, error=e)
            logger.error(f"Error in update_primary_metric_selections: {str(e)}", exc_info=True)
            raise