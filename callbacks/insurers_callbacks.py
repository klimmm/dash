from typing import Dict, List, Optional, Tuple

import dash
import pandas as pd
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate

from application.components.button import format_button_id_value
from application.config.button_config import BUTTON_CONFIG
from callbacks.layout.buttons_callbacks import get_button_classes
from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer
from domain.insurers.operations import (
     get_insurer_options,
     get_rankings,
     get_top_insurers,
     process_insurers_df)

logger = get_logger(__name__)


@timer
def get_insurers_data(
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_insurers: int,
    metrics: List[str],
    split_mode: str
) -> Tuple[pd.DataFrame, List[
     Dict[str, str]], Dict[str, Dict[str, Dict[str, int]]]]:
    """Main function to process insurance data and return components."""
    # Get ranking metric and filter data
    ranking_metric = next(
        (m for m in metrics if m in df['metric']
         .unique()), None)
    filtered_df = df[
        ~df['insurer'].isin(['top-5', 'top-10', 'top-20', 'total']) &
        (df['metric'] == (ranking_metric or df['metric'].iloc[0]))]

    # Get quarters and latest data
    quarters = sorted(df['year_quarter']
                      .unique())[-2:]
    latest_df = filtered_df[filtered_df['year_quarter'] == quarters[-1]]

    # Process data based on top_insurers
    if top_insurers == 0:
        insurers_order = get_top_insurers(latest_df, 0)
        options = get_insurer_options(insurers_order)
        processed_df = process_insurers_df(
            df[df['insurer']
               .isin((selected_insurers or []) + ['total'])],
            latest_df, top_insurers, split_mode
        )
    else:
        options = []
        processed_df = process_insurers_df(df, latest_df,
                                           top_insurers, split_mode)
    # Sort and get rankings
    metrics_order = [m for m in metrics if m in processed_df['metric']
                     .unique()]
    metrics_order.extend(m for m in processed_df['metric']
                         .unique() if m not in metrics_order)
    processed_df['metric'] = pd.Categorical(processed_df['metric'],
                                            categories=metrics_order,
                                            ordered=True)
    sorted_df = processed_df.sort_values(['metric', 'insurer'])

    rankings = get_rankings(filtered_df, quarters)

    return sorted_df, options, rankings


def setup_insurer_selection(app: Dash) -> None:
    @app.callback(
        [Output(f"btn-top-insurers-{format_button_id_value(btn['value'])}",
                "className")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']] +
        [Output('top-n-rows', 'data'),
         Output('selected-insurers', 'style')],
        [Input(f"btn-top-insurers-{format_button_id_value(btn['value'])}",
               "n_clicks")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']],
        State('top-n-rows', 'data')
    )
    @log_callback
    @timer
    @error_handler
    def update_number_insurers_buttons(*args):
        """Update top insurers selection and handle custom dropdown vsbility"""
        ctx = dash.callback_context
        config = BUTTON_CONFIG['top-insurers']
        total_buttons = len(config['buttons'])
        # Get current value, defaulting to config default if none
        current_value = args[-1] if args[-1] is not None else config['default']
        if ctx.triggered:
            triggered = ctx.triggered[0]["prop_id"].split(".")[0]
            if triggered:
                button_index = next(
                    (i for i, btn in enumerate(config['buttons'])
                     if f"btn-top-insurers-{format_button_id_value(btn['value'])}"
                     == triggered),
                    None
                )
                if button_index is not None:
                    current_value = config['buttons'][button_index]['value']
        # Get index of current value in buttons list
        current_idx = next(
            (i for i, btn in enumerate(config['buttons'])
             if str(btn['value']) == str(current_value)),
            None
        )
        # Generate button classes using helper function
        button_classes = get_button_classes(
            total_buttons,
            current_idx,
            config['class_key']
        )
        # Handle dropdown visibility and value conversion
        try:
            val_int = int(current_value)
            is_valid_top_n = val_int in [5, 10, 20]
        except (ValueError, TypeError):
            val_int = 0
            is_valid_top_n = False
        dropdown_style = {'display': 'none'} if is_valid_top_n else None
        output_value = val_int if is_valid_top_n else 0
        return (*button_classes, output_value, dropdown_style)

    @app.callback(
        [Output('selected-insurers', 'value'),
         Output('selected-insurers', 'options'),
         Output('selected-insurers-store', 'data'),
         Output('filtered-insurers-data-store', 'data'),
         Output('rankings-data-store', 'data')],
        [Input('selected-insurers', 'value'),
         Input('processed-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('table-split-mode-selected', 'data')],
        [State('selected-insurers-store', 'data'),
         State('selected-lines-store', 'data'),
         State('metrics-store', 'data')]
    )
    @log_callback
    @timer
    @error_handler
    def update_insurer_selection(
        selected: Optional[List[str]],
        processed_data: Optional[Dict],
        top_n: int,
        split_mode: str,
        stored: List[str],
        lines: List[str],
        metrics: List[str]
    ):
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate

        df = pd.DataFrame.from_records(
            processed_data['df']) if processed_data else pd.DataFrame()

        if df.empty:
            return [], [], [], processed_data['df'], {}

        trigger_id = ctx.triggered[0]['prop_id']

        selected = [] if top_n != 0 or 'top-n-rows' in trigger_id else (
            selected or stored or [])

        df, options, rankings = get_insurers_data(
            df, selected, top_n, metrics, split_mode)

        return selected, options, selected, df.to_dict('records'), rankings