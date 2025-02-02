from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from dash import Input, Output, State, html
import pandas as pd

from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.insurer_filters import filter_by_insurer
from data_process.table.data import get_data_table
from data_process.io import save_df_to_csv
from memory_profiler import profile

logger = get_logger(__name__)

empty_table = html.Div("No data available for the selected filters", className="text-center p-4")
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


def create_data_section(title: str, table_data: tuple) -> html.Div:
    return html.Div([
        html.Div(id='click-details'),  # Make sure this exists
        html.H3(table_data[1], className="table-title", style={"display": "none"}),
        html.H4(table_data[2], className="table-subtitle", style={"display": "none"}),
        table_data[0]
    ], className="data-section mb-8")


@dataclass
class ProcessedUIData:
    df: List[Dict[str, Any]]  # Converted Pandas DataFrame
    prev_ranks: Optional[Dict[str, Any]] = None
    current_ranks: Optional[Dict[str, Any]] = None

    def to_dict(self):
        """Convert dataclass to dictionary for processing."""
        return asdict(self)

@dataclass
class UISettings:
    selected_insurers: str
    top_n_list: List[int]
    split_mode: str
    toggle_show_market_share: bool
    toggle_show_change: bool
    period_type: str
    end_quarter: str
    filter_state: Dict[str, Any]

    def to_dict(self):
        """Convert UI settings dataclass to dictionary."""
        return asdict(self)


def setup_ui(app):
    @app.callback(
        Output('tables-container', 'children'),
        [Input('processed-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('selected-insurers-all-values', 'data'),
         Input('toggle-selected-market-share', 'data'),
         Input('toggle-selected-qtoq', 'data'),
         Input('table-split-mode', 'data')],
        [State('filter-state-store', 'data'),
         State('period-type', 'data'),
         State('end-quarter', 'value')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    def process_ui(
            processed_data_dict: Dict,
            top_n_list: List[int],
            selected_insurers: str,
            toggle_show_market_share: bool,
            toggle_show_change: bool,
            split_mode: str,
            filter_state: Dict,
            period_type: str,
            end_quarter: str,
        ) -> List:
        logger.info("Starting process_ui callback")

        try:
            # Convert raw dict to dataclass objects
            processed_data = ProcessedUIData(
                df=processed_data_dict.get('df', []),
                prev_ranks=processed_data_dict.get('prev_ranks'),
                current_ranks=processed_data_dict.get('current_ranks')
            )

            ui_settings = UISettings(
                selected_insurers=selected_insurers,
                top_n_list=top_n_list,
                split_mode=split_mode,
                toggle_show_market_share=toggle_show_market_share,
                toggle_show_change=toggle_show_change,
                period_type=period_type,
                end_quarter=end_quarter,
                filter_state=filter_state
            )

            # Handle empty processed data
            if not processed_data.df:
                logger.debug("Empty processed data received")
                return [empty_table]

            df = pd.DataFrame.from_records(processed_data.df)
            if df.empty:
                logger.debug("Empty DataFrame after conversion")
                return [empty_table]
            df['year_quarter'] = pd.to_datetime(df['year_quarter'])

            df = filter_by_insurer(
                df, ui_settings.filter_state['selected_metrics'], 
                ui_settings.selected_insurers, ui_settings.top_n_list, ui_settings.split_mode
            )
            # save_df_to_csv(df, "df_after_filter_insurers.csv")

            split_column = 'linemain' if ui_settings.split_mode == 'line' else 'insurer'

            # Get ordered values based on split mode
            if ui_settings.split_mode == 'line':
                ordered_values = [
                    line for line in ui_settings.filter_state['selected_lines'] 
                    if line in df[split_column].unique()
                ]
            else:
                ordered_values =  df['insurer'].unique()

            logger.debug(f"ordered_values {ordered_values} tables split by {ui_settings.split_mode}")

            # Create tables
            all_tables = []
            for value in ordered_values:

                df_filtered = df[df[split_column] == value]
                # save_df_to_csv(df_filtered, f"filtered_df_{value}.csv")
                table_data = get_data_table(
                    df=df_filtered,
                    split_mode=ui_settings.split_mode,
                    table_selected_metric=ui_settings.filter_state['selected_metrics'],
                    selected_linemains=ui_settings.filter_state['selected_lines'],
                    period_type=ui_settings.period_type,
                    number_of_insurers=ui_settings.top_n_list,
                    toggle_show_market_share=ui_settings.toggle_show_market_share,
                    toggle_show_change=ui_settings.toggle_show_change,
                    prev_ranks=processed_data.prev_ranks,
                    current_ranks=processed_data.current_ranks,
                )

                section = create_data_section(value, table_data)
                all_tables.append(section)

            logger.debug(f"Generated {len(ordered_values)} tables split by {ui_settings.split_mode}")
            return all_tables

        except Exception as e:
            logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
            return [html.Div([
                html.H3("Error"),
                html.P(str(e))
            ], className="error-container")]

        finally:
            logger.info("Completed process_ui callback")
