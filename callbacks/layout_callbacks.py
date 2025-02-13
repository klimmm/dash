from datetime import datetime
from typing import Any, Dict, List, Tuple

import dash  # type: ignore
import pandas as pd
from dash import Input, Output, State, html  # type: ignore

from app.style_constants import StyleConstants
from config.logging import log_callback, get_logger, timer, error_handler
from constants.translations import translate
from core.lines.mapper import map_line
from core.insurers.mapper import map_insurer

logger = get_logger(__name__)


def convert_to_quarter_format(date_input, period_type):
    # If input is already a Timestamp or datetime, use it directly
    if isinstance(date_input, (pd.Timestamp, datetime)):
        date = date_input
    else:
        # If it's a string, parse it
        date = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')

    if period_type == 'ytd':
        # Calculate which quarter (in months)
        month = date.month
        quarter_month = ((month - 1) // 3 + 1) * 3
        return f"{quarter_month}M'{date.year}"
    else:
        quarter = (date.month - 1) // 3 + 1
        # Format as 1Q'2023, 2Q'2023, etc.
        return f"{quarter}Q'{date.year}"


def create_filters_summary(
    df: pd.DataFrame,
    reporting_form: str,
    selected_lines: List[str],
    selected_metrics: List[str],
    selected_insurers: List[str],
    start_quarter: str,
    end_quarter: str,
    period_type: str,
    second_row_displayed: bool = False
) -> html.Div:

    periods = list(df['year_quarter'].unique())
    title_displayed = html.Div([
        f"{translate(reporting_form)} | ",
        f"{', '.join(convert_to_quarter_format(period, period_type) for period in periods)}",
        html.Br()
    ])
    if second_row_displayed:
        title_hidden = html.Div([
            f"Вид страхования: {', '.join(map_line(line) for line in selected_lines)} | ",
            f"Показатель: {', '.join(translate(metric) for metric in selected_metrics)} | ",
            f"Страховщик: {', '.join(map_insurer(insurer) for insurer in selected_insurers)}"
        ], id='filters-summary-second-row', className="filters-summary-second-row")
    else:
        title_hidden = html.Div([])

    return html.Div([title_displayed, title_hidden], className="filters-summary")


def setup_sidebar(app: dash.Dash) -> None:
    """Setup callbacks for sidebar toggle functionality."""

    SIDEBAR_EXPANDED_CLASS = StyleConstants.SIDEBAR
    SIDEBAR_COLLAPSED_CLASS = StyleConstants.SIDEBAR_COLLAPSED
    BUTTON_SHOW_CLASS = StyleConstants.BTN["SIDEBAR_HIDE"]
    BUTTON_HIDE_CLASS = StyleConstants.BTN["SIDEBAR_SHOW"]

    @app.callback(
        [Output('sidebar', 'className'),
         Output('sidebar-button', 'children'),
         Output('sidebar-button', 'className')],
        [Input('sidebar-button', 'n_clicks')],
        [State('sidebar', 'className')]
    )
    @log_callback
    def toggle_sidebar_button(
        sidebar_clicks: int,
        current_class: str
    ) -> Tuple[str, str, str]:
        """
        Toggle sidebar visibility and update related elements.
        """
        ctx = dash.callback_context
        try:
            if not ctx.triggered or not sidebar_clicks:
                return (
                    SIDEBAR_EXPANDED_CLASS,
                    "Скрыть фильтры",
                    BUTTON_HIDE_CLASS
                )

            is_expanded = current_class and "collapsed" not in current_class

            if is_expanded:
                new_state = (
                    SIDEBAR_COLLAPSED_CLASS,
                    "Показать фильтры",
                    BUTTON_SHOW_CLASS
                )
            else:
                new_state = (
                    SIDEBAR_EXPANDED_CLASS,
                    "Скрыть фильтры",
                    BUTTON_HIDE_CLASS
                )

            logger.debug(f"sidebar_clicks {sidebar_clicks}, cur_class {current_class}")
            logger.debug(f"trigger {ctx.triggered[0]}, new state {new_state}")
            return new_state

        except Exception:
            logger.exception("Error in toggle_sidebar")
            raise


def setup_filters_summary(app: dash.Dash) -> None:
    @app.callback(
        Output('filters-summary', 'children'),
        [Input('filtered-insurers-data-store', 'data'),
         Input('selected-insurers-store', 'data'),
         Input('sidebar', 'className'),
         Input('filter-state-store', 'data')],
        prevent_initial_call=True
    )
    @log_callback
    @timer
    @error_handler
    def filters_summary(
        processed_data: Dict,
        selected_insurers: str,
        sidebar_classname: str,
        filter_state: Dict
    ) -> List[Any]:
        """Process UI updates and generate tables.

        Returns:
            List of table components for the UI
        """
        if not processed_data:
            return ""
        if selected_insurers is None:
            return ""

        df = pd.DataFrame.from_records(processed_data).assign(
            year_quarter=lambda x: pd.to_datetime(x['year_quarter']))

        selected_metrics = filter_state['selected_metrics']
        selected_lines = filter_state['selected_lines']
        reporting_form = filter_state['reporting_form']
        end_quarter = filter_state['end_quarter']
        start_quarter = filter_state['start_quarter']
        period_type = filter_state['period_type']
        second_row_displayed = sidebar_classname == 'sidebar collapsed'
        filters_summary = create_filters_summary(
            df, reporting_form, selected_lines, selected_metrics,
            selected_insurers, start_quarter, end_quarter,
            period_type, second_row_displayed
        )

        return filters_summary