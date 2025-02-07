from .layout.buttons_callbacks import setup_buttons
from .layout.data_table_callbacks import setup_data_table
from .layout.layout_callbacks import setup_sidebar, setup_debug_panel

from .lines_callbacks import setup_line_selection
from .metrics_callbacks import setup_metric_selection
from .process_data_callbacks import setup_process_data
from .insurers_callbacks import setup_insurer_selection
from .ui_callbacks import setup_ui


def setup_all_callbacks(
    app,
    lines_tree_162,
    lines_tree_158,
    df_162, df_158,
    end_quarter_options_162,
    end_quarter_options_158
):
    """
    Centralized function to set up all callbacks in the application.
    """
    setup_sidebar(app)
    setup_debug_panel(app)
    setup_buttons(app)
    # setup_data_table(app)

    setup_metric_selection(app)
    setup_line_selection(app, lines_tree_162, lines_tree_158)
    setup_process_data(app, df_162, df_158, end_quarter_options_162, end_quarter_options_158)
    setup_insurer_selection(app)
    setup_ui(app)