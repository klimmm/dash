from typing import Any, cast, Dict, List, Optional, Tuple

import dash  # type: ignore
import pandas as pd
from dash import Dash, Input, Output, State  # type: ignore
from dash.exceptions import PreventUpdate  # type: ignore

from config.logging import log_callback, error_handler, get_logger, timer
from core.insurers.operations import (
     get_insurer_options,
     get_rankings,
     get_top_insurers,
     process_insurers_df
)

logger = get_logger(__name__)


@timer
def get_insurers_data(
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_insurers: int,
    metrics: List[str],
    split_mode: str,
    num_periods_selected: int
) -> Tuple[pd.DataFrame, List[
     Dict[str, str]], Dict[str, Dict[str, Dict[str, int]]]
     ]:
    """Main function to process insurance data and return components."""
    # Get ranking metric and filter data

    ranking_metric = next(
        (m for m in metrics if m in df['metric'].unique()), None)
    filtered_df = df[
        ~df['insurer'].isin(['top-5', 'top-10', 'top-20', 'total']) &
        (df['metric'] == (ranking_metric or df['metric'].iloc[0]))
    ]

    # Get quarters and latest data
    quarters = sorted(df['year_quarter'].unique())[-2:]
    latest_df = filtered_df[filtered_df['year_quarter'] == quarters[-1]]

    # Process data based on top_insurers
    if top_insurers == 0:
        insurers_order = get_top_insurers(latest_df, 0)
        options = get_insurer_options(insurers_order)
        processed_df = process_insurers_df(
            df[df['insurer'].isin((selected_insurers or []) + ['total'])],
            latest_df, top_insurers, split_mode)
    else:
        options = []
        processed_df = process_insurers_df(
            df, latest_df, top_insurers, split_mode
        )
    # Sort and get rankings
    df_metrics = processed_df['metric'].unique()
    metrics_order = [m for m in metrics if m in df_metrics]
    metrics_order.extend(m for m in df_metrics if m not in metrics_order)

    processed_df['metric'] = pd.Categorical(
        processed_df['metric'], categories=metrics_order, ordered=True
    )
    sorted_df = processed_df.sort_values(['metric', 'insurer'])

    rankings = get_rankings(filtered_df, quarters)
    recent_periods = (df['year_quarter']
                      .drop_duplicates()
                      .sort_values(ascending=False)
                      .iloc[:num_periods_selected])

    sorted_df = sorted_df[
            sorted_df['year_quarter'].isin(recent_periods)].copy()

    return sorted_df, options, rankings


def setup_insurer_selection(app: Dash) -> None:
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
         State('metrics-store', 'data'),
         State('periods-data-table-selected', 'data')]
    )
    @log_callback
    @timer
    @error_handler
    def update_insurer_selection(
        selected: Optional[List[str]],
        processed_data: Optional[Dict[str, Any]],
        top_n: int,
        split_mode: str,
        stored: List[str],
        lines: List[str],
        metrics: List[str],
        num_periods_selected: int
    ) -> Tuple[
        List[str], List[Dict[str, str]], List[str], List[Dict[str, Any]],
        Dict[str, Dict[str, Dict[str, int]]]
         ]:
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate

        if processed_data is None:
            return [], [], [], [], {}

        df = pd.DataFrame.from_records(processed_data['df'])

        if df.empty:
            # Cast the df records to the expected type
            records = cast(List[Dict[str, Any]], processed_data['df'])
            return [], [], [], records, {}

        trigger_id = ctx.triggered[0]['prop_id']

        df, options, rankings = get_insurers_data(
            df, selected, top_n, metrics, split_mode, num_periods_selected)

        selected = (
            [f'top-{top_n}'] if top_n in [5, 10, 20] else
            ([] if 'top-n-rows' in trigger_id else (selected or stored or []))
        )

        if top_n in [5, 10, 20]:
            options = [{'label': f'Топ-{top_n}', 'value': f'top-{top_n}'}]

        logger.debug(f"top_n {top_n}")
        logger.debug(f"selected {selected}")
        # Cast the df records to the expected type
        records = cast(List[Dict[str, Any]], df.to_dict('records'))

        return selected, options, selected, records, rankings