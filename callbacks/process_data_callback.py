import pandas as pd
import dash
from dash import Input, Output, State
from typing import Tuple, Dict, List
from config.logging_config import get_logger, track_callback, track_callback_end, memory_monitor
from data_process.calculate_growth import add_growth_rows
from data_process.calculate_market_share import add_market_share_rows
from data_process.filter_insurers import process_insurers_data
logger = get_logger(__name__)


def setup_process_data_callback(app: dash.Dash):
    @app.callback(
        [Output('filter-state-store', 'data'),
         Output('processed-data-store', 'data')],
        [Input('intermediate-data-store', 'data'),
         Input('selected-insurers-all-values', 'data')],
        [State('number-of-insurers', 'data'),
         State('show-data-table', 'data'),
         State('filter-state-store', 'data'),
         State('insurer-options-store', 'data')],
        prevent_initial_call=True
    )
    def process_data(
            intermediate_data: Dict,
            selected_insurers: str,
            top_n_list: List[int],
            show_data_table: bool,
            current_filter_state: Dict,
            insurer_options_store: Dict
    ) -> Tuple:
        """Second part of data processing: Insurer processing and metric calculations"""
        ctx = dash.callback_context

        start_time = track_callback('callbacks.process_data', 'process_data', ctx)

        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id']

        try:
            if not isinstance(intermediate_data, dict):
                logger.debug(f"Invalid intermediate_data type: {type(intermediate_data)}")
                track_callback_end('callbacks.process_data', 'process_data', start_time, message_no_update="invaid interm data")
                return dash.no_update, dash.no_update

            df = pd.DataFrame.from_records(intermediate_data.get('df', []))
            all_metrics = intermediate_data.get('all_metrics', [])
            business_type_checklist = intermediate_data.get('business_type_checklist', [])
            lines = intermediate_data.get('lines', [])
            period_type = intermediate_data.get('period_type', '')
            num_periods_selected = intermediate_data.get('num_periods_selected', 0)
            current_ranks = insurer_options_store['current_ranks']
            prev_ranks = insurer_options_store['prev_ranks']

            df = (process_insurers_data(df, all_metrics, selected_insurers, top_n_list)
                 .pipe(add_market_share_rows, selected_insurers, all_metrics, show_data_table)
                 .pipe(add_growth_rows, selected_insurers, show_data_table, num_periods_selected, period_type)
                 )
            if 999 not in top_n_list:
                df = df[~(df['insurer'] == 'total')]

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
                {'df': df.to_dict('records'), 'prev_ranks': prev_ranks, 'current_ranks': current_ranks}
            )

            track_callback_end('callbacks.process_data', 'process_data', start_time, result=result)
            # memory_monitor.log_memory("end_process_data", logger)
            return result

        except Exception as e:
            logger.error(f"Error in process_data: {str(e)}", exc_info=True)
            track_callback_end('callbacks.process_data', 'process_data', start_time, error=str(e))
            raise