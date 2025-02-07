from typing import Dict, List, Optional

import dash
import pandas as pd
from dash import Dash, Input, Output, State
from dash.exceptions import PreventUpdate

from application.style.style_constants import StyleConstants
from application.config.components_config import BUTTON_CONFIG
from config.callback_logging import log_callback, error_handler
from config.logging_config import get_logger, timer, timerx
from domain.insurers.operations import get_filtered_df_options_rankings

logger = get_logger(__name__)


def setup_insurer_selection(app: Dash) -> None:
    @app.callback(
        [Output(f"btn-top-insurers-{btn['value']}", "className")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']] +
        [Output('top-n-rows', 'data'),
         Output('selected-insurers', 'style')],
        [Input(f"btn-top-insurers-{btn['value']}", "n_clicks")
         for btn in BUTTON_CONFIG['top-insurers']['buttons']],
        State('top-n-rows', 'data')
    )
    @log_callback
    @timerx
    @error_handler
    def update_number_insurers_buttons(*args):
        ctx = dash.callback_context
        config = BUTTON_CONFIG['top-insurers']
        current_value = args[
            -1] if args[-1] is not None else config['default_state']
        button_classes = [
            StyleConstants.BTN[config['class_key']]] * config['total_buttons']

        if ctx.triggered:
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if triggered_id:
                current_value = triggered_id.split('btn-top-insurers-')[1]

        current_idx = next((i for i, btn in enumerate(config['buttons'])
                           if str(btn['value']) == str(current_value)), None)

        if current_idx is not None:
            button_classes[
             current_idx] = StyleConstants.BTN[f"{config['class_key']}_ACTIVE"]

        val_int = int(current_value) if str(current_value).isdigit() else 0
        dropdown_style = {
            'display': 'none'} if val_int in [5, 10, 20] else None

        return (*button_classes, 
                val_int if val_int in [5, 10, 20] else 0, dropdown_style)

    @app.callback(
        [Output('selected-insurers', 'value'),
         Output('selected-insurers', 'options'),
         Output('selected-insurers-store', 'data'),
         Output('filtered-insurers-data-store', 'data'),
         Output('rankings-data-store', 'data')],
        [Input('selected-insurers', 'value'),
         Input('processed-data-store', 'data'),
         Input('top-n-rows', 'data'),
         Input('table-split-mode', 'data')],
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

        df, options, rankings = get_filtered_df_options_rankings(
            df, metrics, lines, selected, top_n, split_mode)

        return selected, options, selected, df.to_dict('records'), rankings