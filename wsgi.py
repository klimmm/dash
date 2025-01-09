import sys
from pathlib import Path

# Get the absolute path of the current directory
current_dir = str(Path(__file__).parent.absolute())

# Add the current directory to the Python path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import from the specific file
from dash_app import server

if __name__ == "__main__":
    server.run()