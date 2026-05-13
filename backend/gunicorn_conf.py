import multiprocessing
import os

# Add project root (parent of backend/) to Python path
# so that `backend.app.xxx` imports resolve correctly
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
pythonpath = [_project_root]
