# presentation/callbacks/dropdown_callbacks.py
from typing import Dict, List, Tuple, Any
from dash.development.base_component import Component
from dash import dcc, html
from presentation.components import (
    DropdownComponent,
    ButtonComponent,
    SidebarComponent,
    DebugComponent,
    FiltersSummaryComponent
)



class Components:
    """Class for registering dropdown-related callbacks."""
    linked_groups = {
        'pivot-col': ['index-col'],
        'index-col': ['pivot-col']
    }

    def __init__(
        self,
        config,
        ui_configs,
        formatting_service,
        context
    ):
        """
        """
        self.config = config
        self.ui_config = ui_configs['controls_config']
        self.tree_config = ui_configs['tree_config']
        self.sidebar_config = ui_configs['sidebar_config']
        self.filters_summary_config = ui_configs['filters_summary_config']
        self.logger = config.logger
        self.st = config.app_config.DEFAULT_STORAGE_TYPE
        self.fmt = formatting_service
        self.context = context
        self.components = {}
        self.stores = []

    def create_all_stores(self) -> Tuple[Dict[str, Any], List[dcc.Store]]:
        stores = []
        stores.append(dcc.Store(id='process-data-one-trigger'))
        stores.append(dcc.Store(id='process-data-two-trigger'))
        stores.append(dcc.Store(id='state-update-store'))
        stores.append(dcc.Store(id='selected-insurers-store', storage_type=self.st))
        stores.append(dcc.Store(id='selected-value-types', storage_type=self.st)),
        stores.append(dcc.Store(id='selected-view-modes', storage_type=self.st))
        self.stores.extend(stores)
        for group_id, config in self.ui_config.get_button_config().items():
            default_value = config.get('value')
            stores.extend(
                [dcc.Store(
                    id=f"{group_id}",
                    data=default_value,
                    storage_type=self.st
                )])
        for component_id, config in self.tree_config.get_all_configs().items():
            stores.extend([
                dcc.Store(
                    id=f'expansion-state-{component_id}',
                    data={'states': config['default_expansions']},
                    storage_type=self.st
                ),
                dcc.Store(
                    id=f'selected-{component_id}-store',
                    data=config['default_checked'],
                    storage_type=self.st
                )
            ])        
        stores.extend([dcc.Store(id='viewport-size', data='desktop')])
        return stores

    def create_button_components(self):
        components = {}

        for group_id, config in self.ui_config.get_button_config().items():
            default_value = config.get('value')
            buttons = [
                ButtonComponent.create_button(
                    label=btn.get('label', str(btn['value'])),
                    button_id=f"{group_id}-{btn['value']}",
                    group_id=group_id,
                    is_active=btn['value'] == default_value or (isinstance(
                        default_value, list) and btn['value'] in default_value),
                    hidden=btn.get('hidden', False)
                )
                for btn in config.get('options', [])
            ]

            components[group_id] = ButtonComponent.create_button_group(buttons)

        self.components.update(components)
        return components

    def create_dropdown_components(
        self
    ) -> tuple[Dict[str, Component], List]:
        components = {}
        dropdown_configs = self.ui_config.get_dropdown_config()
        for name, config in dropdown_configs.items():
            components[name] = DropdownComponent.create_dropdown(**config)
        self.components.update(components)
        return components

    def create_tree_components(self) -> Tuple[Dict[str, html.Div], List[dcc.Store]]:
        """Create tree component and stores."""
        components = {}

        for component_id, config in self.tree_config.get_all_configs().items():
            components.update({f"{component_id}_tree":
                              html.Div(id=f"{component_id}-tree")})
        self.components.update(components)
        return components

    def create_sidebar_components(self) -> tuple[Dict[str, Component], List]:
        sidebar_component = SidebarComponent(self.config, self.sidebar_config)
        return {'sidebar': sidebar_component.create_sidebar(self.components)}

    def create_debug_components(self) -> tuple[Dict[str, Component], List]:
        debug_component = DebugComponent(self.config)

        return debug_component.create_components(self.components)

    def create_visualization_components(self) -> tuple[Dict[str, Component], List]:
        components = {'vizual_container': dcc.Loading(id="tables-container", type="default")}
        return components


    def create_filters_summary_components(self) -> html.Div:
        """Generate filters summary content"""

        filter_summary = FiltersSummaryComponent(self.fmt, self.context)
        first_row = html.Div(filter_summary._format_row(
            self.filters_summary_config.structure["first_row"]) + [html.Br()])

        second_row = html.Div(
            filter_summary._format_row(self.filters_summary_config.structure["second_row"]),
            id="filters-summary-second-row",
            style={'display': 'none'}  # Hidden by default
        )

        return {'filters_summary': html.Div([first_row, second_row], id="filters-summary", className="filters-summary")}


