import logging
import os
import warnings

import dash  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import pandas as pd

from app import create_app_layout
from callbacks._setup import setup_all_callbacks
from config import (
     default_lines_dict,
     get_logger,
     LINES_158_DICTIONARY,
     LINES_162_DICTIONARY,
     setup_logging
)
from core import (
     get_available_quarters,
     get_year_quarter_options,
     load_insurance_dataframes,
     load_json,
     Tree
)
pd.options.mode.chained_assignment = None  # default='warn'
warnings.filterwarnings('ignore', category=FutureWarning)


dbc._js_dist = [
    {
        "relative_package_path": "_components/dash_bootstrap_components.min.js",
        "external_url": "https://unpkg.com/dash-bootstrap-components@1.6.0/dist/dash-bootstrap-components.min.js",
        "namespace": "dash_bootstrap_components"
    }
]

print("Starting application initialization...")

app = dash.Dash(
    __name__,
    url_base_pathname="/",
    assets_folder='assets',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    update_title=None
)

app._favicon = None  # prevent favicon errors

print("DBC version:", dbc.__version__)
print("Dash version:", dash.__version__)
print("Registered paths after init:", app.registered_paths)
print("DBC paths:", dbc._js_dist)

app.title = "Insurance Data Dashboard"

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
        <link rel="stylesheet" type="text/css" href="/assets/styles/main.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

df_158, df_162 = load_insurance_dataframes()

lines_tree_158 = Tree(load_json(LINES_158_DICTIONARY), default_lines_dict)
lines_tree_162 = Tree(load_json(LINES_162_DICTIONARY), default_lines_dict)

end_quarter_options_158 = get_year_quarter_options(df_158)
end_quarter_options_162 = get_year_quarter_options(df_162)
available_quarters_158 = get_available_quarters(df_158)
available_quarters_162 = get_available_quarters(df_162)

debug_handler = setup_logging(
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    log_file='app.log'
)

logger = get_logger(__name__)

app.layout = create_app_layout(lines_tree_158, lines_tree_162)

server = app.server

setup_all_callbacks(
    app,
    lines_tree_158, lines_tree_162,
    df_158, df_162,
    end_quarter_options_158, end_quarter_options_162,
    available_quarters_158, available_quarters_162,
    debug_handler
)


def main() -> None:
    try:
        port = int(os.environ.get("PORT", 8051))
        print(f"Starting server on port {port}...")
        app.run_server(
            host='0.0.0.0',
            port=port,
            debug=True
        )
    except Exception as e:
        print(f"Error during startup: {e}")
        raise


if __name__ == '__main__':
    main()