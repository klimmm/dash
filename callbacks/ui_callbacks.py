import dash
from dash import html
from dash import Input, Output, State
from typing import Dict, List
import pandas as pd
from data_process.table_data import get_data_table
from charting.chart import create_chart
from config.logging_config import memory_monitor, get_logger, track_callback, track_callback_end

logger = get_logger(__name__)


def setup_ui_callbacks(app):
    @app.callback(
        [Output('data-table', 'children'),
         Output('table-title', 'children'),
         Output('table-subtitle', 'children'),
         Output('table-title-chart', 'children'),
         Output('table-subtitle-chart', 'children'),
         Output('graph', 'figure')],
        [Input('processed-data-store', 'data'),
         Input('toggle-selected-market-share', 'data'),
         Input('toggle-selected-qtoq', 'data')],
        [State('filter-state-store', 'data'),
         State('period-type', 'data'),
         State('end-quarter', 'value'),
         State('number-of-insurers', 'data')],
        prevent_initial_call=True
    )
    def process_ui(
        processed_data: Dict,
        toggle_selected_market_share: bool,
        toggle_selected_qtoq: bool,
        filter_state: Dict,
        period_type: str,
        end_quarter: str,
        number_of_insurers: int
    ) -> List:
        """Update table based on processed data."""
        memory_monitor.log_memory("before_process_ui", logger)
        start_time = track_callback('main', 'process_ui', dash.callback_context)

        try:
            # Handle empty processed data
            if not processed_data['df']:
                empty_table = html.Div("No data available for the selected filters", className="text-center p-4")
                empty_chart = {
                    'data': [],
                    'layout': {
                        'title': 'No data available',
                        'xaxis': {'visible': False},
                        'yaxis': {'visible': False}
                    }
                }
                return empty_table, "No Data", "", "No Data", "", empty_chart

            df = pd.DataFrame.from_records(processed_data['df'])
            if df.empty:
                empty_table = html.Div("No data available for the selected filters", className="text-center p-4")
                empty_chart = {
                    'data': [],
                    'layout': {
                        'title': 'No data available',
                        'xaxis': {'visible': False},
                        'yaxis': {'visible': False}
                    }
                }
                return empty_table, "No Data", "", "No Data", "", empty_chart

            df['year_quarter'] = pd.to_datetime(df['year_quarter'])

            table_data = get_data_table(
                df=df,
                table_selected_metric=filter_state['selected_metrics'],
                selected_linemains=filter_state['selected_lines'],
                period_type=period_type,
                number_of_insurers=number_of_insurers,
                toggle_selected_market_share=toggle_selected_market_share,
                toggle_selected_qtoq=toggle_selected_qtoq,
                prev_ranks=processed_data['prev_ranks']
            )

            unique_insurers = df['insurer'].unique().tolist()
            if not unique_insurers:
                empty_table = html.Div("No insurers found in the data", className="text-center p-4")
                empty_chart = {
                    'data': [],
                    'layout': {
                        'title': 'No insurers found',
                        'xaxis': {'visible': False},
                        'yaxis': {'visible': False}
                    }
                }
                return empty_table, "No Data", "", "No Data", "", empty_chart

            main_insurer = unique_insurers[0]
            compare_insurers = unique_insurers[1:5]
            df = df[df['insurer'].isin([main_insurer] + compare_insurers)]

            if 'primary_y_metric' not in filter_state or not filter_state['primary_y_metric']:
                raise ValueError("No primary Y metric selected")

            df = df[df['metric'] == filter_state['primary_y_metric'][0]]

            chart_figure, _ = create_chart(
                chart_data=df,
                selected_linemains=filter_state['selected_lines'],
                main_insurer=main_insurer,
                compare_insurers=compare_insurers,
                primary_y_metric=filter_state['primary_y_metric'],
                secondary_y_metric=filter_state['secondary_y_metric'],
                period_type=period_type,
                start_quarter='2019Q1' if filter_state['reporting_form'] == '0420162' else '2022Q1',
                end_quarter=end_quarter
            )


            output = table_data[0], table_data[1], table_data[2], table_data[1], table_data[2], chart_figure
            return output

        except Exception as e:
            logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
            empty_table = html.Div(f"Error processing data: {str(e)}", className="text-center p-4 text-red-500")
            empty_chart = {
                'data': [],
                'layout': {
                    'title': 'Error processing data',
                    'xaxis': {'visible': False},
                    'yaxis': {'visible': False}
                }
            }

            output = empty_table, "Error", str(e), "Error", str(e), empty_chart
            track_callback_end('main', 'process_ui', start_time, result=output, error=str(e))
            return output

        finally:
            track_callback_end('main', 'process_ui', start_time, result=output)