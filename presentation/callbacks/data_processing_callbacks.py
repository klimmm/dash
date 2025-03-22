from typing import List
import dash
import pandas as pd
from dash import Input, Output, State, html
from presentation.components import create_visual_section


class DataProcessingCallbacks:
    def __init__(self,
                 data_processing_service):
        self.data_processing_service = data_processing_service
        self.config = data_processing_service.config
        self.logger = self.config.logger
        self.default_values = self.config.default_values
        self.dash_callback = self.config.dash_callback

    def register_callbacks(self, app: dash.Dash) -> None:
        @app.callback(
            Output('process-data-one-trigger', 'data'),
            [Input('end-quarter', 'value'),
             Input('period-type', 'data'),
             Input('number-of-periods', 'data'),
             Input('selected-line-store', 'data'),
             Input('selected-metric-store', 'data'),
             Input('view-metrics', 'data')],
            [State('reporting-form', 'data')],
            prevent_initial_call=False
        )
        @self.dash_callback
        def process_data_one(*args) -> List[pd.Timestamp]:
            quarters = self.data_processing_service.process_dashboard_data()
            return quarters

        @app.callback(
            Output('process-data-two-trigger', 'data'),
            [Input('selected-insurers-store', 'data'),
             Input('pivot-col', 'data'),
             Input('index-col', 'data')],
            prevent_initial_call=True
        )
        @self.dash_callback
        def process_data_two(*args) -> List[pd.Timestamp]:
            quarters = self.data_processing_service.prepare_visualization_data()
            return quarters

        @app.callback(
            Output('tables-container', 'children'),
            [Input('process-data-two-trigger', 'data'),
             Input('view-mode', 'data'),
             Input('viewport-size', 'data')],
            prevent_initial_call=True
        )
        @self.dash_callback
        def render_visualization_components(
            data_trigger,
            view_mode,
            viewport_size
        ):
            """Master callback for rendering visualization components."""
            try:

                visualization_sections = self.data_processing_service.create_visualizations(
                    viewport_size=viewport_size,
                )
                if not visualization_sections:
                    return create_visual_section()

                # Create visual sections from data
                sections = []
                for section_data in visualization_sections:
                    visual_section = create_visual_section(
                        table=section_data['table'],
                        charts=section_data['charts']
                    )
                    sections.append(visual_section)
                return html.Div(sections, className="visualization-grid")

            except Exception as e:
                self.logger.error(f"Error rendering visualization: {str(e)}")
                return create_visual_section()