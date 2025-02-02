from dataclasses import dataclass
from typing import Tuple, Dict, List, Any
import time

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from functools import wraps
import pandas as pd

from config.callback_logging import log_callback
from config.logging_config import get_logger, memory_monitor
from data_process.growth import calculate_growth
from data_process.market_share import calculate_market_share
from data_process.options import get_rankings
# from data_process.io import save_df_to_csv

logger = get_logger(__name__)


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper

    
@dataclass
class ProcessedData:
    df: List[Dict[str, Any]]
    prev_ranks: Dict[str, Any]
    current_ranks: Dict[str, Any]

    def to_dict(self):
        return {
            'df': self.df,
            'prev_ranks': self.prev_ranks,
            'current_ranks': self.current_ranks
        }


@timer
def create_processed_data(df: pd.DataFrame, 
                         prev_ranks: Dict[str, Any], 
                         current_ranks: Dict[str, Any]) -> Dict[str, Any]:
    records = df.to_dict('records')

    processed = ProcessedData(
        df=records,
        prev_ranks=prev_ranks,
        current_ranks=current_ranks
    )

    return processed.to_dict()


def setup_process_data(app: dash.Dash):
    @app.callback(
        [Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data')],
        [Input('intermediate-data-store', 'data')],
        [State('selected-insurers-all-values', 'data'),
         State('show-data-table', 'data'),
         State('filter-state-store', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    def process_data(
            intermediate_data: Dict,
            selected_insurers: str,
            show_data_table: bool,
            current_filter_state: Dict
    ) -> Tuple:
        """Second part of data processing: Insurer processing and metric calculations"""
        logger.info("Starting process_data callback")
        memory_monitor.log_memory("start_process_data", logger)

        ctx = dash.callback_context
        if not ctx.triggered:
            logger.debug("Callback context not triggered")
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id']
        logger.info(f"Callback triggered by: {trigger_id}")

        try:
            # Validate intermediate data
            if not isinstance(intermediate_data, dict):
                return dash.no_update, dash.no_update

            logger.info("Creating DataFrame from intermediate data")
            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            # save_df_to_csv(df, "df_before_market_share.csv")

            # Extract parameters
            all_metrics = intermediate_data.get('all_metrics', [])
            business_type_checklist = intermediate_data.get('business_type_checklist', [])
            lines = intermediate_data.get('lines', [])
            period_type = intermediate_data.get('period_type', '')
            num_periods_selected = intermediate_data.get('num_periods_selected', 0)

            logger.info("Processing data pipeline")

            # Retrieve insurer rankings
            rankings = get_rankings(df, all_metrics, lines)
            current_ranks = rankings.get('current_ranks', {})
            prev_ranks = rankings.get('prev_ranks', {})

            # Process data transformations
            df = calculate_market_share(df, selected_insurers, all_metrics, show_data_table)
            # save_df_to_csv(df, "df_after_market_share.csv")
            df = calculate_growth(df, selected_insurers, num_periods_selected, period_type)
            # save_df_to_csv(df, "df_after_growth.csv")

            df['year_quarter'] = df['year_quarter'].dt.strftime('%Y-%m-%d')

            # Update filter state
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


            processed_data = create_processed_data(df, prev_ranks, current_ranks)


            memory_monitor.log_memory("end_process_data", logger)
            logger.info("Successfully completed process_data callback")

            return updated_filter_state, processed_data

        except Exception as e:
            memory_monitor.log_memory("error_process_data", logger)
            logger.error(f"Error in process data: {str(e)}", exc_info=True)
            raise