from typing import Dict, List

from dash import Input, Output, State, html
import pandas as pd

from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.insurer_filters import filter_by_insurer
from data_process.table.data import get_data_table
from data_process.io import save_df_to_csv

logger = get_logger(__name__)

empty_table = html.Div("No data available for the selected filters", className="text-center p-4")


def create_data_section(title: str, table_data: tuple) -> html.Div:
    """Create a section with title and table data.

    Args:
        title: Section title (line or insurer name)
        table_data: Tuple containing (table, title, subtitle) from get_data_table

    Returns:
        html.Div containing the formatted section
    """
    return html.Div([
        html.H3(table_data[1], className="table-title", style={"display": "none"}),
        html.H4(table_data[2], className="table-subtitle", style={"display": "none"}),
        table_data[0]
    ], className="data-section mb-8")


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
    def process_ui(
            processed_data: Dict,
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
                # Handle empty processed data
                if not processed_data['df']:
                    logger.debug("Empty processed data received")
                    return [empty_table]

                df = pd.DataFrame.from_records(processed_data['df'])

                if df.empty:
                    logger.debug("Empty DataFrame after conversion")
                    return [empty_table]

                # Convert year_quarter
                df['year_quarter'] = pd.to_datetime(df['year_quarter'])
                logger.debug(f"split_mode {split_mode}")

                number_of_insurers = 20
                # Process insurers data
                df = filter_by_insurer(df, filter_state['selected_metrics'], 
                                     selected_insurers, top_n_list, split_mode)
                save_df_to_csv(df, "df_after_filter_insurers.csv")

                # Determine split column and order based on split mode
                split_column = 'linemain' if split_mode == 'line' else 'insurer'

                # Get the order from selected values
                if split_mode == 'line':
                    # Use the order from selected_lines
                    ordered_values = [line for line in filter_state['selected_lines'] 
                                      if line in df[split_column].unique()]
                else:
                    # Use the order from selected_insurers (already a list)
                    first_year_quarter = df['year_quarter'].max()
                    first_metric = df['metric'].iloc[0]

                    filtered_df = df[
                        (df['year_quarter'] == first_year_quarter) & 
                        (df['metric'] == first_metric)
                    ]

                    # Get both frequency and total value for each insurer
                    insurer_stats = filtered_df.groupby('insurer').agg({
                        'value': 'sum'
                    })
                    logger.debug(f"insurer_stats {insurer_stats} ")

                    sorted_insurers = insurer_stats.sort_values(
                        by=['value'], 
                        ascending=[False]
                    ).index.tolist()

                    ordered_values = [ins for ins in sorted_insurers]

                logger.debug(f"selected_insurers {selected_insurers} ")
                logger.debug(f"ordered_values {ordered_values} tables split by {split_mode}")
                # Create tables for each value in the specified order
                all_tables = []
                for value in ordered_values:
                    # Filter data for current value
                    df_filtered = df[df[split_column] == value]

                    # Get table data
                    table_data = get_data_table(
                        df=df_filtered,
                        split_mode=split_mode,
                        table_selected_metric=filter_state['selected_metrics'],
                        selected_linemains=filter_state['selected_lines'],
                        period_type=period_type,
                        number_of_insurers=top_n_list,
                        toggle_show_market_share=toggle_show_market_share,
                        toggle_show_change=toggle_show_change,
                        prev_ranks=processed_data['prev_ranks'],
                        current_ranks=processed_data['current_ranks'],
                    )

                    # Create section using generic function
                    section = create_data_section(value, table_data)
                    all_tables.append(section)

                logger.debug(f"Generated {len(ordered_values)} tables split by {split_mode}")
                return all_tables

            except Exception as e:
                logger.error(f"Error in process_ui: {str(e)}", exc_info=True)
                return [html.Div([
                    html.H3("Error"),
                    html.P(str(e))
                ], className="error-container")]

            finally:
                logger.info("Completed process_ui callback")