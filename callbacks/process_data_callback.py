import pandas as pd
import dash
from dash import Input, Output, State, ALL
from typing import Tuple, Dict, List
from dash.exceptions import PreventUpdate
from config.logging_config import get_logger, track_callback, track_callback_end, memory_monitor
from data_process.calculate_growth import add_growth_rows
from data_process.calculate_market_share import add_market_share_rows
from data_process.calculate_metrics import calculate_metrics
from data_process.filter_insurers import process_insurers_data

logger = get_logger(__name__)


def setup_process_data_callback(app: dash.Dash):
    @app.callback(
        [Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data')],
        [Input('intermediate-data-store', 'data'),
         Input('selected-insurers-all-values', 'data'),
         Input('number-of-insurers', 'data')],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')]
    )
    def process_data(
            intermediate_data: Dict,
            selected_insurers: str,
            number_of_insurers: int,
            show_data_table: bool,
            current_filter_state: Dict,
            top_n_list: List[int] = [5, 10, 20]
    ) -> Tuple:
        """Second part of data processing: Insurer processing and metric calculations"""
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        start_time = track_callback('callbacks.process_data', 'process_data', ctx)
        memory_monitor.log_memory("start_process_data", logger)

        try:
            if not isinstance(intermediate_data, dict):
                logger.error(f"Invalid intermediate_data type: {type(intermediate_data)}")
                raise PreventUpdate
            logger.debug(f"selected_insurers {selected_insurers}")

            # Reconstruct DataFrame from intermediate data
            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            all_metrics = intermediate_data.get('all_metrics', [])
            business_type_checklist = intermediate_data.get('business_type_checklist', [])
            lines = intermediate_data.get('lines', [])
            period_type = intermediate_data.get('period_type', '')
            num_periods_selected = intermediate_data.get('num_periods_selected', 0)
            logger.debug(f"selected_insurers {selected_insurers}")
            logger.debug(f"yq before process_insurers_data {df['year_quarter'].unique()}")
            # Process insurers data
            df, prev_ranks, num_insurers = process_insurers_data(
                df=df,
                selected_insurers=selected_insurers,
                top_n_list=top_n_list,
                show_data_table=show_data_table,
                selected_metrics=all_metrics,
                number_of_insurers=number_of_insurers
            )
            logger.debug(f"yq unique process_insurers_data {df['year_quarter'].unique()}")
            # Step 1: Calculate metrics
            df = df.pipe(calculate_metrics, all_metrics, business_type_checklist)
            logger.debug(f"yq unique calculate_metrics {df['year_quarter'].unique()}")
            # Step 2: Add market share rows 
            df = df.pipe(add_market_share_rows, selected_insurers, all_metrics, show_data_table)
            logger.debug(f"yq add_market_share_rows {df['year_quarter'].unique()}")
            # Step 3: Add growth rows
            df = df.pipe(add_growth_rows, selected_insurers, show_data_table, num_periods_selected, period_type)
            logger.debug(f"yq add_growth_rows {df['year_quarter'].unique()}")
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

            result = (
                updated_filter_state,
                {'df': df.to_dict('records'), 'prev_ranks': prev_ranks}
            )

            track_callback_end('callbacks.process_data', 'process_data', start_time, result=result)
            memory_monitor.log_memory("end_process_data", logger)
            return result

        except Exception as e:
            logger.error(f"Error in process_data_part2: {str(e)}", exc_info=True)
            track_callback_end('callbacks.process_data', 'process_data', start_time, error=str(e))
            raise