import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Import the server directly from app.py
from app import server

if __name__ == "__main__":
    server.run()