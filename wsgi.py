# wsgi.py

import sys
from pathlib import Path

current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import server

if __name__ == "__main__":
    server.run()