from dash import html
from dash import Input, Output, State
from typing import Dict, List
import pandas as pd
from data_process.table_data import get_data_table
from charting.chart import create_chart
from config.logging_config import get_logger, memory_monitor
from config.callback_logging import log_callback
from data_process.filter_insurers import process_insurers_data

logger = get_logger(__name__)

empty_table = html.Div("No data available for the selected filters", className="text-center p-4")
empty_chart = {
    'data': [],
    'layout': {
        'title': 'No data available',
        'xaxis': {'visible': False},
        'yaxis': {'visible': False}
    }
}

def setup_ui_callbacks(app):
    @app.callback(
        [Output('data-table', 'children'),
         Output('table-title', 'children'),
         Output('table-subtitle', 'children'),
         Output('table-title-chart', 'children'),
         Output('table-subtitle-chart', 'children'),
         Output('graph', 'figure')],
        [Input('processed-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-all-values', 'data'),
         Input('toggle-selected-market-share', 'data'),
         Input('toggle-selected-qtoq', 'data'),
        ],
        [State('filter-state-store', 'data'),
         State('period-type', 'data'),
         State('end-quarter', 'value')],
        prevent_initial_call=True
    )
    @log_callback
    def process_ui(
        processed_data: Dict,
        top_n_list: List[int],
        selected_insurers: str,
        toggle_selected_market_share: bool,
        toggle_selected_qtoq: bool,
        filter_state: Dict,
        period_type: str,
        end_quarter: str,
    ) -> List:
        """Update table based on processed data."""
        logger.info("Starting process_ui callback")
        logger.debug(f"Input parameters: top_n_list={top_n_list}, selected_insurers={selected_insurers}, "
                    f"toggle_market_share={toggle_selected_market_share}, toggle_qtoq={toggle_selected_qtoq}")
        logger.debug(f"Filter state: {filter_state}")
        logger.debug(f"Period type: {period_type}, End quarter: {end_quarter}")

        memory_monitor.log_memory("before_process_ui", logger)
        
        try:
            # Handle empty processed data
            if not processed_data['df']:
                logger.warning("Empty processed data received")
                return empty_table, "No Data", "", "No Data", "", empty_chart
            
            logger.info("Creating DataFrame from processed data")
            df = pd.DataFrame.from_records(processed_data['df'])
            
            if df.empty:
                logger.warning("Empty DataFrame after conversion")
                return empty_table, "No Data", "", "No Data", "", empty_chart
            
            logger.debug(f"DataFrame shape after initial creation: {df.shape}")
            
            # Convert year_quarter
            logger.debug("Converting year_quarter to datetime")
            df['year_quarter'] = pd.to_datetime(df['year_quarter'])
            
            # Process insurers data
            logger.info("Processing insurers data")
            logger.debug(f"Selected metrics: {filter_state['selected_metrics']}")
            df = process_insurers_data(df, filter_state['selected_metrics'], selected_insurers, top_n_list)
            logger.debug(f"DataFrame shape after processing insurers: {df.shape}")
            
            # Get table data
            logger.info("Generating table data")
            table_data = get_data_table(
                df=df,
                table_selected_metric=filter_state['selected_metrics'],
                selected_linemains=filter_state['selected_lines'],
                period_type=period_type,
                number_of_insurers=top_n_list,
                toggle_selected_market_share=toggle_selected_market_share,
                toggle_selected_qtoq=toggle_selected_qtoq,
                prev_ranks=processed_data['prev_ranks'],
                current_ranks=processed_data['current_ranks'],
            )
            
            logger.info("Successfully generated table data")
            output = table_data[0], table_data[1], table_data[2], table_data[1], table_data[2], empty_chart
            
            memory_monitor.log_memory("after_process_ui", logger)
            return output
            
        except Exception as e:
            logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
            logger.debug("Stack trace:", exc_info=True)
            output = empty_table, "Error", str(e), "Error", str(e), empty_chart
            return output
        finally:
            logger.info("Completed process_ui callback")