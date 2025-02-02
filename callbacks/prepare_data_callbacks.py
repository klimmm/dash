from dataclasses import dataclass
import time
from typing import List, Dict, Tuple, Any

import dash
from dash.dependencies import Input, Output, State
from functools import wraps

from config.callback_logging import log_callback
from config.logging_config import get_logger
from data_process.metrics_options import get_checklist_config
from data_process.metrics_processor import get_required_metrics, calculate_metrics
from data_process.period_filters import filter_by_period_type
from data_process.top_n import add_top_n_rows
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
class IntermediateData:
    df: List[Dict[str, Any]]
    selected_metrics: List[str]
    business_type_selection: List[str]
    required_metrics: List[str]
    lines: List[str]
    period_type: str
    num_periods_selected: int
    reporting_form: str

    def to_dict(self):
        return {
            'df': self.df,
            'selected_metrics': self.selected_metrics,
            'business_type_selection': self.business_type_selection,
            'required_metrics': self.required_metrics,
            'lines': self.lines,
            'period_type': self.period_type,
            'num_periods_selected': self.num_periods_selected,
            'reporting_form': self.reporting_form
        }


@timer
def prepare_intermediate_data(df, selected_metrics, business_type_selection, required_metrics, lines, period_type, num_periods_selected, reporting_form):
    records = df.to_dict('records')

    intermediate_data = IntermediateData(
        df=records,
        selected_metrics=selected_metrics,
        business_type_selection=business_type_selection,
        required_metrics=required_metrics,
        lines=lines,
        period_type=period_type,
        num_periods_selected=num_periods_selected,
        reporting_form=reporting_form
    )
    return intermediate_data.to_dict()


@timer
def filter_lines_and_metrics(df, lines, metrics):
    return df[df['linemain'].isin(lines) & df['metric'].isin(metrics)]


def setup_prepare_data(app: dash.Dash, df_162, df_158, end_quarter_options_162, end_quarter_options_158):
    @app.callback(
        [Output('end-quarter', 'options'),
         Output('business-type-checklist-container', 'children'),
         Output('intermediate-data-store', 'data')
        ],
        [Input('metric-all-values', 'data'),
         Input('business-type-checklist', 'value'),
         Input('number-of-periods-data-table', 'data'),
         Input('end-quarter', 'value'),
         Input('insurance-lines-all-values', 'data'),
         Input('period-type', 'data'),
         Input('reporting-form', 'data'),
        ],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')]
    )
    @log_callback
    @timer
    def prepare_data(
            selected_metrics: List[str],
            current_business_type_selection: List[str],
            num_periods_selected: int,
            end_quarter: str,
            lines: List[str],
            period_type: str,
            reporting_form: str,
            show_data_table: bool,
            current_filter_state: Dict
    ) -> Tuple:
        """First part of data processing: Initial filtering and setup"""

        try:
            df = df_162 if reporting_form == '0420162' else df_158
            end_quarter_options = end_quarter_options_162 if reporting_form == '0420162' else end_quarter_options_158

            checklist_component, business_type_selection = get_checklist_config(
                selected_metrics, reporting_form, current_business_type_selection
            )
            required_metrics = get_required_metrics(selected_metrics, business_type_selection)

            df = (filter_lines_and_metrics(df, lines, required_metrics)
                  .pipe(filter_by_period_type, end_quarter, num_periods_selected, period_type)
                  .pipe(add_top_n_rows)
                  .pipe(calculate_metrics, selected_metrics, required_metrics)
                 )

            intermediate_data = prepare_intermediate_data(
                df=df,
                selected_metrics=selected_metrics,
                business_type_selection=business_type_selection,
                required_metrics=required_metrics,
                lines=lines,
                period_type=period_type,
                num_periods_selected=num_periods_selected,
                reporting_form=reporting_form
            )

            return (
                end_quarter_options,
                [checklist_component],
                intermediate_data  # Convert to dict before returning
            )

        except Exception as e:
            logger.error(f"Error in prepare data: {str(e)}", exc_info=True)
            raise