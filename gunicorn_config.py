import os

# Get port from environment variable with a default of 10000
port = int(os.environ.get("PORT", 10000))

# Bind to 0.0.0.0 to listen on all interfaces
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 4
threads = 4
timeout = 120

# Access logging
accesslog = "-"
errorlog = "-"

# Preload the application
preload_app = True

# Worker class
worker_class = "sync"