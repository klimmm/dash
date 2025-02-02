import logging
import os

import dash
import dash_bootstrap_components as dbc

from application import create_app_layout, lines_tree_162, lines_tree_158
from callbacks.setup import setup_all_callbacks
from config import setup_logging, setup_callback_logging, get_logger
from data_process import load_insurance_dataframes, get_year_quarter_options

logger = get_logger(__name__)
setup_logging(console_level=logging.DEBUG, file_level=logging.DEBUG)
setup_callback_logging()

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

app.layout = create_app_layout()

server = app.server

df_162, df_158 = load_insurance_dataframes()
end_quarter_options_162 = get_year_quarter_options(df_162)
end_quarter_options_158 = get_year_quarter_options(df_158)
setup_all_callbacks(app, lines_tree_162, lines_tree_158, df_162, df_158,
                    end_quarter_options_162, end_quarter_options_158)


def main():
    try:
        port = int(os.environ.get("PORT", 8051))
        print(f"Starting server on port {port}...")
        app.run_server(
            host='0.0.0.0',
            port=port,
            debug=False
        )
    except Exception as e:
        print(f"Error during startup: {e}")
        raise


if __name__ == '__main__':
    main()