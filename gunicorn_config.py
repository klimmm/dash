# gunicorn_config.py

import os

os.environ['DASH_PRUNE_ERRORS'] = 'False'

workers = 1      # Single worker for one user
threads = 2      # Can handle 2 concurrent tasks
worker_class = "gthread"
timeout = 120

port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"

accesslog = "-"
errorlog = "-"

preload_app = False
max_requests = 500
max_requests_jitter = 50