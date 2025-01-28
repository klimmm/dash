import pandas as pd
import dash
from dash import Input, Output, State
from typing import Tuple, Dict
from config.logging_config import get_logger, memory_monitor
from config.callback_logging import log_callback

from data_process.calculate_growth import add_growth_rows
from data_process.calculate_market_share import add_market_share_rows

logger = get_logger(__name__)

def setup_process_data_callback(app: dash.Dash):
    @app.callback(
        [Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data')],
        [Input('intermediate-data-store', 'data')],
        [State('selected-insurers-all-values', 'data'),
         State('show-data-table', 'data'),
         State('filter-state-store', 'data'),
         State('insurer-options-store', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    def process_data(
            intermediate_data: Dict,
            selected_insurers: str,
            show_data_table: bool,
            current_filter_state: Dict,
            insurer_options_store: Dict
    ) -> Tuple:
        """Second part of data processing: Insurer processing and metric calculations"""
        logger.info("Starting process_data callback")
        memory_monitor.log_memory("start_process_data", logger)

        ctx = dash.callback_context
        if not ctx.triggered:
            logger.warning("Callback context not triggered")
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id']
        logger.info(f"Callback triggered by: {trigger_id}")
        logger.debug(f"Selected insurers: {selected_insurers}")
        logger.debug(f"Show data table: {show_data_table}")
        logger.debug(f"Current filter state: {current_filter_state}")

        try:
            # Validate intermediate data
            if not isinstance(intermediate_data, dict):
                # logger.error(f"Invalid intermediate_data type: {type(intermediate_data)}")
                return dash.no_update, dash.no_update

            logger.info("Creating DataFrame from intermediate data")
            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            logger.debug(f"Initial DataFrame shape: {df.shape}")

            # Extract parameters from intermediate data
            all_metrics = intermediate_data.get('all_metrics', [])
            business_type_checklist = intermediate_data.get('business_type_checklist', [])
            lines = intermediate_data.get('lines', [])
            period_type = intermediate_data.get('period_type', '')
            num_periods_selected = intermediate_data.get('num_periods_selected', 0)

            logger.debug(f"Extracted metrics: {all_metrics}")
            logger.debug(f"Business types: {business_type_checklist}")
            logger.debug(f"Lines: {lines}")
            logger.debug(f"Period type: {period_type}")
            logger.debug(f"Number of periods: {num_periods_selected}")

            # Get ranks from insurer options store
            current_ranks = insurer_options_store['current_ranks']
            prev_ranks = insurer_options_store['prev_ranks']
            logger.debug(f"Current ranks count: {len(current_ranks)}")
            logger.debug(f"Previous ranks count: {len(prev_ranks)}")

            # Process data through pipeline
            logger.info("Starting data processing pipeline")
            
            logger.info("Adding market share calculations")
            df = add_market_share_rows(df, selected_insurers, all_metrics, show_data_table)
            logger.debug(f"DataFrame shape after market share: {df.shape}")
            
            logger.info("Adding growth calculations")
            df = add_growth_rows(df, selected_insurers, show_data_table, num_periods_selected, period_type)
            logger.debug(f"DataFrame shape after growth: {df.shape}")

            logger.info("Formatting date columns")
            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            # Update filter state
            logger.info("Updating filter state")
            updated_filter_state = {
                **(current_filter_state or {}),
                'primary_y_metric': all_metrics[0] if all_metrics else None,
                'secondary_y_metric': all_metrics[-1] if len(all_metrics) > 1 else None,
                'selected_metrics': all_metrics,
                'business_type_checklist': business_type_checklist,
                'selected_lines': lines,
                'show_data_table': bool(show_data_table),
                'reporting_form': intermediate_data.get('reporting_form'),
                'period_type': period_type,
            }
            logger.debug(f"Updated filter state: {updated_filter_state}")

            # Prepare final result
            logger.info("Preparing final result")
            result = (
                updated_filter_state,
                {'df': df.to_dict('records'), 'prev_ranks': prev_ranks, 'current_ranks': current_ranks}
            )

            memory_monitor.log_memory("end_process_data", logger)
            logger.info("Successfully completed process_data callback")
            return result

        except Exception as e:
            # logger.error(f"Error in process_data: {str(e)}", exc_info=True)
            logger.debug("Stack trace:", exc_info=True)
            memory_monitor.log_memory("error_process_data", logger)
            raise