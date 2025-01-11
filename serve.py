# serve.py
from pathlib import Path
from app import app

# Ensure assets are properly served
app.server.static_folder = str(Path(__file__).parent / "assets")
app.server.static_url_path = '/assets'

server = app.server

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')