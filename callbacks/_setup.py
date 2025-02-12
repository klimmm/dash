from typing import List, Set

import dash  # type: ignore
import pandas as pd
from callbacks import (
    setup_buttons,
    setup_debug_panel,
    setup_filters_summary,
    setup_insurer_selection,
    setup_line_selection,
    setup_metric_selection,
    setup_process_data,
    setup_sidebar,
    setup_table
)
from core.lines.tree import Tree
from core.period.options import YearQuarter, YearQuarterOption


def setup_all_callbacks(
    app: dash.Dash,
    lines_tree_158: Tree,
    lines_tree_162: Tree,
    df_158: pd.DataFrame,
    df_162: pd.DataFrame,
    end_quarter_options_158: List[YearQuarterOption],
    end_quarter_options_162: List[YearQuarterOption],
    available_quarters_158: Set[YearQuarter],
    available_quarters_162: Set[YearQuarter],
    debug_handler
) -> None:
    """
    Centralized function to set up all callbacks in the application.
    """
    setup_sidebar(app)
    setup_debug_panel(app, debug_handler)
    setup_buttons(app)
    # setup_data_table(app)

    setup_metric_selection(app)
    setup_line_selection(app, lines_tree_158, lines_tree_162)
    setup_process_data(
        app, 
        df_158, df_162,
        end_quarter_options_158, end_quarter_options_162,
        available_quarters_158, available_quarters_162
    )
    setup_insurer_selection(app)
    setup_table(app)
    setup_filters_summary(app)