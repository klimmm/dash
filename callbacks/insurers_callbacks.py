from typing import Any, cast, Dict, List, Optional, Tuple

import dash  # type: ignore
import pandas as pd
from dash import Dash, Input, Output, State  # type: ignore
from dash.exceptions import PreventUpdate  # type: ignore

from config.logging import log_callback, error_handler, get_logger, timer
from core.insurers.operations import filter_and_sort_by_insurer, reindex_and_sort
from core.insurers.options import get_insurer_options
from core.insurers.helpers import split_metric_column, add_rank_column
logger = get_logger(__name__)
from core.io import save_df_to_csv


@timer
def filter_df(df, num_periods_selected):
    df = df[df['year_quarter'].isin(df['year_quarter'].sort_values(ascending=False).unique()[:num_periods_selected])].copy()
    return df


@timer
def get_latest_df(df, metrics):
    ranking_metric = next(
        (m for m in metrics if m in df['metric'].unique()), None)
    latest_df = df[
        ~df['insurer'].isin(['top-5', 'top-10', 'top-20', 'total']) &
        (df['metric'] == (ranking_metric or df['metric'].iloc[0])) &
        (df['year_quarter'] == df['year_quarter'].max())
    ]
    return latest_df


@timer
def get_insurers_data(
    df: pd.DataFrame,
    selected_insurers: List[str],
    top_insurers: int,
    metrics: List[str],
    split_mode: str,
    pivot_column: str,
    num_periods_selected: int
) -> Tuple[pd.DataFrame, List[
     Dict[str, str]], Dict[str, Dict[str, Dict[str, int]]]
     ]:
    """Main function to process insurance data and return components."""
    df = split_metric_column(df)
    df = add_rank_column(df)
    latest_df = get_latest_df(df, metrics)
    options = get_insurer_options(latest_df) if top_insurers == 0 else []
    save_df_to_csv(df, "before_filter.csv")
    filtered_df = filter_and_sort_by_insurer(
        df, latest_df, top_insurers, selected_insurers, split_mode, pivot_column)
    save_df_to_csv(filtered_df, "before_reindex.csv")
    sorted_df = reindex_and_sort(filtered_df, metrics, use_all=(
        split_mode == 'insurer' or split_mode == 'metric_base' or top_insurers == 0))
    logger.debug(f"sorted_df {sorted_df}")
    save_df_to_csv(sorted_df, "sorted_df_sfter_reindex.csv")

    sorted_df = filter_df(sorted_df, num_periods_selected)

    return sorted_df, options


def setup_insurer_selection(app: Dash) -> None:
    @app.callback(
        [Output('selected-insurers', 'value'),
         Output('selected-insurers', 'options'),
         Output('selected-insurers-store', 'data'),
         Output('filtered-insurers-data-store', 'data')],
        [Input('selected-insurers', 'value'),
         Input('top-insurers-selected', 'data'),
         Input('table-split-mode-selected', 'data')],
        [
         State('processed-data-store', 'data'),
         State('selected-insurers-store', 'data'),
         State('selected-lines-store', 'data'),
         State('metrics-store', 'data'),
         State('pivot-column-selected', 'data'),
         State('periods-data-table-selected', 'data')]
    )
    @log_callback
    @timer
    @error_handler
    def update_insurer_selection(
        selected: Optional[List[str]],
        top_n: int,
        split_mode: str,
        processed_data: Optional[Dict[str, Any]],
        stored: List[str],
        lines: List[str],
        metrics: List[str],
        pivot_column: str,
        num_periods_selected: int
    ) -> Tuple[
        List[str], List[Dict[str, str]], List[str], List[Dict[str, Any]],
        Dict[str, Dict[str, Dict[str, int]]]
         ]:
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate

        if processed_data is None:
            return [], [], [], []

        df = pd.DataFrame.from_records(processed_data['df'])

        if df.empty:
            # Cast the df records to the expected type
            records = cast(List[Dict[str, Any]], processed_data['df'])
            return [], [], [], records

        trigger_id = ctx.triggered[0]['prop_id']

        df, options = get_insurers_data(
            df, selected, top_n, metrics, split_mode, pivot_column, num_periods_selected)

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

        return selected, options, selected, records