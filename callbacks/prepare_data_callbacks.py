from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Any

import dash
from dash.dependencies import Input, Output, State

from config.callback_logging import log_callback
from config.default_values import TOP_N_LIST
from config.logging_config import get_logger
from data_process.metrics_options import get_checklist_config
from data_process.metrics_processor import get_required_metrics, calculate_metrics
from data_process.period_filters import filter_by_period, filter_by_period_type
from data_process.options import get_year_quarter_options
from data_process.top_n import add_top_n_rows
from data_process.io import save_df_to_csv
from constants.metrics import METRICS


logger = get_logger(__name__)

def timer(func):
    import time
    from functools import wraps
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
    all_metrics: List[str]
    business_type_checklist: List[str]
    required_metrics: List[str]
    lines: List[str]
    period_type: str
    num_periods_selected: int
    reporting_form: str

    def to_dict(self):
        # Avoid using asdict() which creates unnecessary deep copies
        return {
            'df': self.df,
            'all_metrics': self.all_metrics,
            'business_type_checklist': self.business_type_checklist,
            'required_metrics': self.required_metrics,
            'lines': self.lines,
            'period_type': self.period_type,
            'num_periods_selected': self.num_periods_selected,
            'reporting_form': self.reporting_form
        }


def setup_prepare_data(app: dash.Dash, df_162, df_158, end_quarter_options_162, end_quarter_options_158):
    @app.callback(
        [Output('end-quarter', 'options'),
         Output('business-type-checklist-container', 'children'),
         Output('intermediate-data-store', 'data')
        ],
        [Input('primary-metric-all-values', 'data'),
         Input('business-type-checklist', 'value'),
         Input('number-of-periods-data-table', 'data'),
         Input('end-quarter', 'value'),
         Input('insurance-lines-all-values', 'data'),
         Input('period-type', 'data'),
         Input('secondary-y-metric', 'value'),
         Input('reporting-form', 'data'),
        ],
        [State('show-data-table', 'data'),
         State('filter-state-store', 'data')]
    )
    @log_callback
    @timer
    def prepare_data(
            primary_metrics: List[str],
            current_business_type_selection: List[str],
            num_periods_selected: int,
            end_quarter: str,
            lines: List[str],
            period_type: str,
            secondary_metric: str,
            reporting_form: str,
            show_data_table: bool,
            current_filter_state: Dict
    ) -> Tuple:
        """First part of data processing: Initial filtering and setup"""

        try:
            df = df_162 if reporting_form == '0420162' else df_158
            end_quarter_options = end_quarter_options_162 if reporting_form == '0420162' else end_quarter_options_158

            selected_metrics = (primary_metrics or []) + (
                [secondary_metric] if isinstance(secondary_metric, str) else (secondary_metric or [])
            )
            checklist_component, business_type_selection = get_checklist_config(
                selected_metrics, reporting_form, current_business_type_selection
            )
            required_metrics = get_required_metrics(selected_metrics, business_type_selection)

            df = (df.loc[df['linemain'].isin(lines) & df['metric'].isin(required_metrics)]
                  .pipe(filter_by_period_type, end_quarter, num_periods_selected, period_type)
                  .pipe(add_top_n_rows)
                  .pipe(calculate_metrics, selected_metrics, required_metrics)
                 )

            save_df_to_csv(df, "df_after_prepare.csv")

            intermediate_data = IntermediateData(
                df=df.to_dict('records'),
                all_metrics=selected_metrics,
                business_type_checklist=business_type_selection,
                required_metrics=required_metrics,
                lines=lines,
                period_type=period_type,
                num_periods_selected=num_periods_selected,
                reporting_form=reporting_form
            )

            return (
                end_quarter_options,
                [checklist_component],
                intermediate_data.to_dict()  # Convert to dict before returning
            )

        except Exception as e:
            logger.error(f"Error in prepare data: {str(e)}", exc_info=True)
            raise