import os
import multiprocessing

# Get port from environment variable with a default of 10000
port = int(os.environ.get("PORT", 10000))

# Bind to 0.0.0.0 to listen on all interfaces
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"
timeout = 120

# Access logging
accesslog = "-"
errorlog = "-"

# Preload the application
preload_app = True

# Max requests per worker
max_requests = 1000
max_requests_jitter = 50