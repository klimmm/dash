# wsgi.py
from app import app, server

if __name__ == '__main__':
    app.run_server()