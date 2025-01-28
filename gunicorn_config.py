# gunicorn_config.py

import os

os.environ['DASH_PRUNE_ERRORS'] = 'False'

port = int(os.environ.get("PORT", 10000))
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 2  # Just use 2 workers instead of the CPU formula
threads = 1  # Reduce threads as well
worker_class = "gthread"
timeout = 120

# Access logging
accesslog = "-"
errorlog = "-"

# Don't preload on free tier to save memory
preload_app = False

# Max requests per worker
max_requests = 500
max_requests_jitter = 50