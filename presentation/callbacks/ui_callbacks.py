# presentation/callbacks/dropdown_callbacks.py
import dash
from dash import Output, Input
from typing import List


class UICallbacks:
    """Class for registering dropdown-related callbacks."""

    linked_groups = {
        'pivot-col': ['index-col'],
        'index-col': ['pivot-col']
    }

    def __init__(self, ui_config, button_service, context):
        """
        Initialize the callbacks with the unified UI configuration.

        Args:
            ui_config: The UIComponentConfigManager instance
            button_service: The button service instance
            context: The application context
        """
        self.button_service = button_service
        self.config = self.button_service.config
        self.ui_config = ui_config  # Store the unified config manager
        self.button_configs_items = self.ui_config.get_button_config().items()
        self.dash_callback = self.config.dash_callback
        self.logger = self.config.logger
        self.context = context
        self.context_attributes = self.button_service.context_attributes

    def register_callbacks(self, app):
        """Register all callbacks for button groups and global functionality."""
        # Define a factory function to capture the correct values
        def create_button_callback(button_group_id, button_config):
            @app.callback(
                [Output(group_id, "data", allow_duplicate=True) 
                 for group_id in [button_group_id] + self.linked_groups.get(button_group_id, [])],
                [Input(f"{button_group_id}-{btn['value']}", "n_clicks")
                 for btn in button_config['options']],
                prevent_initial_call=True
            )
            @self.dash_callback
            def update_button_data(*args):
                ctx = dash.callback_context
                if not ctx.triggered:
                    raise dash.exceptions.PreventUpdate
                triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
                buttons = button_config.get('options', [])
                inferred_type = type([btn.get('value') for btn in buttons][0])
                clicked_value = inferred_type(triggered_id[len(f"{button_group_id}-"):])
                self.button_service.process_input(button_group_id, clicked_value, self.context)
                # Gather outputs
                response = []
                if button_group_id in self.context_attributes:
                    attr_name = self.context_attributes[button_group_id]
                    response.append(getattr(self.context, attr_name))
                for linked_group in self.linked_groups.get(button_group_id, []):
                    linked_attr = self.context_attributes[linked_group]
                    response.append(getattr(self.context, linked_attr))
                return response
            # Return the function to satisfy Dash's callback expectations
            return update_button_data

        # Register callbacks for each button group from the unified config
        for group_id, config in self.ui_config.get_button_config().items():
            create_button_callback(group_id, config)

        @app.callback(
            Output('state-update-store', 'data'),
            [Input('selected-line-store', 'data'),
             Input('selected-metric-store', 'data')]
        )
        def update_state(lines, metrics):
            self.context.update_state(lines=lines, metrics=metrics)

        @app.callback(
            [Output('end-quarter', 'options'),
             Output('end-quarter', 'value')],
            [Input('end-quarter', 'value'),
             Input('reporting-form', 'data')]
        )
        @self.dash_callback
        def updated_quarter_options(end_q: str, reporting_form: str):
            self.context.update_state(end_q=end_q)
            self.context.update_state(
                end_q=end_q, reporting_form=reporting_form)
            quarter_options = self.button_service.get_period_options(
                reporting_form)
            return quarter_options, self.context.end_q

        @app.callback(
            [Output('selected-insurers-store', 'data'),
             Output('selected-insurers', 'value')],
            [Input('process-data-one-trigger', 'data'),
             Input('top-insurers', 'data'),
             Input('selected-insurers', 'value')],
            prevent_initial_call=True
        )
        @self.dash_callback
        def update_insurer_selections(data, top_insurers, insurers):
            triggered_id = dash.callback_context.triggered[0][
                'prop_id'].split('.', 1)[0]
            if 'selected-insurers' not in triggered_id:
                return self.context.insurers, self.context.insurers
            if not insurers:
                raise dash.exceptions.PreventUpdate
            else:
                self.button_service.process_input(
                    triggered_id, insurers[-1], self.context)
            return self.context.insurers, self.context.insurers

        @app.callback(
            [Output('selected-insurers', 'options'),
             Output('selected-insurers', 'disabled', allow_duplicate=True)],
            [Input('selected-insurers-store', 'data')],
            prevent_initial_call=True
        )
        @self.dash_callback
        def update_insurer_options(insurers: List[str]):
            options = self.button_service.get_insurer_options(
                self.context.processed_df, insurers, self.context.metrics)
            is_disabled = insurers[0].startswith('top-')
            return options, is_disabled