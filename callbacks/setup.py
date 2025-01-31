from .buttons_callbacks import setup_single_choice_buttons, setup_multi_choice_buttons
from .insurer_callbacks import setup_insurer_selection
from .layout_callbacks import setup_sidebar, setup_debug_panel, setup_resize_observer
from .line_callbacks import setup_line_selection
from .line_tree_view_callbacks import setup_line_tree_view
from .metrics_callbacks import setup_metric_selection
from .prepare_data_callbacks import setup_prepare_data
from .process_data_callbacks import setup_process_data
from .ui_callbacks import setup_ui

def setup_all_callbacks(app, lines_tree_162, lines_tree_158, df_162, df_158):
    """
    Centralized function to set up all callbacks in the application.
    """
    # Layout and UI setup
    setup_sidebar(app)
    setup_debug_panel(app)
    setup_resize_observer(app)
    setup_ui(app)

    # Button callbacks
    setup_single_choice_buttons(app)
    setup_multi_choice_buttons(app)

    # Data selection callbacks
    setup_metric_selection(app)
    setup_line_selection(app, lines_tree_162, lines_tree_158)
    setup_line_tree_view(app, lines_tree_162, lines_tree_158)
    setup_insurer_selection(app)

    # Data processing callbacks
    setup_prepare_data(app, df_162, df_158)
    setup_process_data(app)