# main.py

import os
import warnings
import dash
import dash_bootstrap_components as dbc
import pandas as pd
from flask import Flask

from presentation.app_layout import create_app_layout
from application.bootstrap import initialize_application
from presentation.callbacks_registry import CallbacksRegistry

pd.options.mode.chained_assignment = None  # default='warn'
warnings.filterwarnings('ignore', category=FutureWarning)

# DBC configuration
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


services, config = initialize_application()
storage_type = config.app_config.DEFAULT_STORAGE_TYPE

callbacks_registry = CallbacksRegistry(services, config)

components, stores = callbacks_registry.create_all_components(storage_type)

app.layout = create_app_layout(components, stores)

callbacks_registry.register_all_callbacks(app, components)

server: Flask = app.server


def main() -> None:
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