from typing import Dict, Any, Tuple, List, Optional
from dash import html
import dash_bootstrap_components as dbc
from presentation.style_constants import StyleConstants


class SidebarComponent:
    def __init__(self, config, sidebar_config):
        self.logger = config.logger
        self.sidebar_config = sidebar_config

    def create_components(self, components: Dict[str, Any], 
                          storage_type: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        self.logger.debug("Creating sidebar components")
        return {'sidebar': self.create_sidebar(components, self.sidebar_config)}, {}

    def create_sidebar(self, components):
        sidebar_config = self.sidebar_config
        btn = html.Button(
            html.I(className=StyleConstants.SIDEBAR_ICON),
            id='sidebar-button',
            title='Toggle Sidebar',
            className=StyleConstants.BTN["SIDEBAR_HIDE"]
        )

        return dbc.Col(
            [btn, self._create_filter_panel(components, sidebar_config)],
            id='sidebar',
            className=StyleConstants.SIDEBAR
        )

    def _create_filter_panel(self, components_dict, sidebar_config):
        panels = []
        for section in sidebar_config:
            self.logger.warning(f"section {section}")
            content = []
            for row in section["rows"]:
                self.logger.warning(f"row {row}")
                processed = self._process_row(row, components_dict)
                content.extend(self._create_filter_row(processed))

            panels.append(self._create_collapsible_section(
                section["label"],
                content,
                section.get("open", True)
            ))

        return html.Div(panels, className=StyleConstants.FILTER_PANEL)

    def _process_row(self, row, components_dict):
        processed = []
        for item in row:
            label, key, lwidth, cwidth, *style = (*item, None)[:5]
            component = components_dict.get(key)
            processed.append((label, component, lwidth, cwidth, style[0]))
        return processed

    def _create_filter_row(self, items: List[Tuple[str, Any, int, int, 
                                                  Optional[Dict]]]) -> List:
        row = []
        for label_text, comp, lwidth, cwidth, style in items:
            if label_text and lwidth:
                row.append(html.Label(
                    label_text,
                    style={"width": f"{lwidth}%"},
                    className=StyleConstants.FILTER_LABEL
                ))

            if cwidth == 0 and lwidth > 0:
                cwidth = 100 - lwidth

            if cwidth > 0:
                comp_style = {"width": f"{cwidth}%", "display": "inline-block"}
                if style:
                    comp_style.update(style)

                if hasattr(comp, 'style') and comp.style:
                    comp = comp.__class__(
                        *(comp.children if hasattr(comp, 'children') else []),
                        **{k: v for k, v in comp._real_props.items() 
                           if k != 'style'},
                        style={**comp.style, **comp_style}
                    )
                else:
                    comp.style = comp_style

            row.append(comp)
        return row

    def _create_collapsible_section(self, label: str, content: List[Any], 
                                  open_default: bool = True) -> html.Div:
        section_id = f"section-{label.lower().replace(' ', '-').replace('/', '-')}"
        icon = (StyleConstants.COLLAPSE_ICON_UP if open_default 
                else StyleConstants.COLLAPSE_ICON_DOWN)

        return html.Div([
            html.Div([
                html.Span(label, className=StyleConstants.FILTER_SECTION_TITLE),
                html.I(className=icon)
            ],
                id={'type': 'collapse-header', 'index': section_id},
                className=StyleConstants.FILTER_SECTION_HEADER
            ),
            html.Div(
                content,
                id={'type': 'collapse-content', 'index': section_id},
                className=StyleConstants.FILTER_SECTION_CONTENT,
                style={'display': 'block' if open_default else 'none'}
            )
        ], className=StyleConstants.FILTER_SECTION)