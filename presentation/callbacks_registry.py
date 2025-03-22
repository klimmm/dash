# presentation/callbacks_registry.py
from typing import Dict, Any, Tuple, List
import dash

from presentation.callbacks import (
     ButtonStatesCallbacks,
     DataProcessingCallbacks,
     UICallbacks,
     LayoutCallbacks,
     TreeCallbacks
)
from presentation.components_registry import Components


class CallbacksRegistry:
    def __init__(
        self,
        services,
        config
    ):
        """Initialize the registry with services and utilities."""
        self.services = services
        self.config = config
        self.logger = config.logger

        self.data_processing = DataProcessingCallbacks(
            services.processor_orchestrator
        )
        self.button = ButtonStatesCallbacks(
            config,
            services.ui_configs['controls_config'],
        )
        self.ui = UICallbacks(
            services.ui_configs['controls_config'],
            services.ui_service,
            services.context
        )
        self.layout = LayoutCallbacks(config)
        self.components = Components(
            config,
            services.ui_configs,
            services.formatting_facade,
            services.context
        )

    def register_all_callbacks(self, app: dash.Dash,
                               components: Dict[str, Any]) -> None:
        """
        Register callbacks for all components.

        Args:
            app: The Dash application
            components: Dictionary of UI components
        """
        self.layout.register_callbacks(app, components)
        self.button.register_callbacks(app)
        self.ui.register_callbacks(app)
        self.data_processing.register_callbacks(app)
        for service_name, service in self.services.tree_services.items():
            callback_obj = TreeCallbacks(service)
            setattr(self, service_name, callback_obj)
            callback_obj.register_callbacks(app)

    def create_all_components(self, st: str
                              ) -> Tuple[Dict[str, Any], List[Any]]:

        self.components.create_dropdown_components()
        self.components.create_tree_components()
        button_components = self.components.create_button_components()
        sidebar_components = self.components.create_sidebar_components()
        viz_components = self.components.create_visualization_components()
        filters_summary_components = self.components.create_filters_summary_components()
        debug_components = self.components.create_debug_components()
        stores = self.components.create_all_stores()
        components = {
            **button_components,
            **sidebar_components,
            **viz_components,
            **filters_summary_components,
            **debug_components
        }

        return components, stores