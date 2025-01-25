from dash import dcc, html
from typing import List, Tuple, Dict, Optional
import json
import dash
from dash import Dash, ALL
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from config.logging_config import get_logger, track_callback, track_callback_end
from application.style_config import StyleConstants
from callbacks.get_available_metrics import get_metric_options, get_checklist_config
logger = get_logger(__name__)


def create_metric_dropdown(index: int, options: List[Dict], value: Optional[str]) -> html.Div:
    return html.Div(
        className="d-flex align-items-center w-100 mb-1 pr-1",
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
                        placeholder="Select primary metric",
                        className=StyleConstants.FORM["DD"],
                        optionHeight=18,

                    )
                ]
            ),
            html.Button(
                "✕",
                id={'type': 'remove-primary-metric-btn', 'index': index},
                className=StyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )


def setup_sync_metrics_callback(app: Dash) -> None:
    """Setup callback for syncing metric values"""

    @app.callback(
        Output('primary-metric-all-values', 'data'),
        [Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value')]
    )
    def sync_metric_values(main_value: str, dynamic_values: List[str]) -> List[str]:
        return [main_value] + [v for v in dynamic_values if v is not None]


def setup_metric_callbacks(app: Dash) -> None:
    """Setup callbacks for managing primary and secondary metric dropdowns"""

    @app.callback(
        [Output('primary-metric', 'options'),
         Output('primary-metric', 'value'),
         Output('primary-metric-container', 'children'),
         Output('secondary-y-metric', 'options'),
         Output('secondary-y-metric', 'value')],
        [Input('reporting-form', 'data'),
         Input('primary-metric', 'value'),
         Input({'type': 'dynamic-primary-metric', 'index': ALL}, 'value'),
         Input('primary-metric-add-btn', 'n_clicks'),
         Input({'type': 'remove-primary-metric-btn', 'index': ALL}, 'n_clicks')],
        [State('primary-metric-container', 'children'),
         State('secondary-y-metric', 'value')]
    )
    def update_metric_selections(
        reporting_form: str,
        selected_primary_metric: str,
        selected_dynamic_metrics: List[str],
        add_metric_clicks: int,
        remove_metric_clicks: List[int],
        existing_dropdowns: List,
        secondary_metric: str
    ) -> Tuple:
        """Update metric dropdowns based on user interactions"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        try:

            # Initialize dropdowns if None
            existing_dropdowns = existing_dropdowns or []
            logger.warning(f"existing_dropdowns {existing_dropdowns}")
            selected_dynamic_metrics = [v for v in (selected_dynamic_metrics or []) if v is not None]
            all_selected_primary_metric = [selected_primary_metric] + selected_dynamic_metrics

            # Get initial metric options
            primary_metric_options, secondary_metric_options, valid_selected_primary_metrics, secondary_metric_value = (
                get_metric_options(reporting_form, all_selected_primary_metric, secondary_metric)
            )
            # Get all selected values
            valid_selected_dynamic_metrics = [v for v in valid_selected_primary_metrics if v != valid_selected_primary_metrics[0]]

            # Handle remove button click
            if '.n_clicks' in ctx.triggered[0]['prop_id'] and '"type":"remove-primary-metric-btn"' in ctx.triggered[0]['prop_id']:
                component_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
                removed_index = component_id['index']

                if ctx.triggered[0]['value'] is not None:
                    valid_selected_dynamic_metrics = [v for i, v in enumerate(valid_selected_dynamic_metrics) if i != removed_index]
                    existing_dropdowns = [
                        d for i, d in enumerate(existing_dropdowns) if i != removed_index
                    ]

            # Handle add button click
            if 'primary-metric-add-btn' in ctx.triggered[0]['prop_id']:
                new_primary_metric_dropdown = create_metric_dropdown(
                    index=len(existing_dropdowns),
                    options=[opt for opt in primary_metric_options if opt['value'] not in valid_selected_primary_metrics],
                    value=None
                )
                existing_dropdowns.append(new_primary_metric_dropdown)

            # Update existing dropdowns
            updated_primary_metric_dropdowns = []
            for i, _ in enumerate(existing_dropdowns):
                current_primary_metric = valid_selected_dynamic_metrics[i] if i < len(valid_selected_dynamic_metrics) else None
                other_primary_metric_selected = [v for v in valid_selected_primary_metrics if v != current_primary_metric]

                primary_metric_dropdown_options = [
                    opt for opt in primary_metric_options 
                    if opt['value'] not in other_primary_metric_selected
                ]

                updated_primary_metric_dropdowns.append(create_metric_dropdown(
                    index=i,
                    options=primary_metric_dropdown_options,
                    value=current_primary_metric
                ))

            # Filter primary metric options
            filtered_primary_metric_options = [
                opt for opt in primary_metric_options 
                if opt['value'] not in valid_selected_dynamic_metrics
            ]

            return (
                filtered_primary_metric_options,
                valid_selected_primary_metrics[0],
                updated_primary_metric_dropdowns,
                secondary_metric_options,
                secondary_metric_value[0] if secondary_metric_value else []
            )

        except Exception as e:
            logger.error(f"Error in update_metric_dropdowns: {str(e)}", exc_info=True)
            raise



def create_insurer_dropdown(index: int, options: List[Dict], value: Optional[str]) -> html.Div:
    return html.Div(
        className="d-flex align-items-center w-100 mb-1 pr-1",
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
                        optionHeight=18

                    )
                ]
            ),
            html.Button(
                "✕",
                id={'type': 'remove-selected-insurers-btn', 'index': index},
                className=StyleConstants.BTN["REMOVE"],
                n_clicks=0
            )
        ]
    )


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

            logger.warning(f"insurer_options {insurer_options}")
            logger.warning(f"selected_insurer {selected_insurer}")
            logger.warning(f"selected_dynamic_insurers {selected_dynamic_insurers}")
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

            return (
                filtered_selected_insurer_options,
                selected_insurer,
                updated_selected_insurers_dropdowns
            )

        except Exception as e:
            logger.error(f"Error in update_metric_dropdowns: {str(e)}", exc_info=True)
            raise