"""Gunicorn configuration tuned for Render's free tier (512 MB, 1 vCPU)."""
import multiprocessing
import os

# Bind to whatever PORT Render injects.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Conservative worker count for the free tier — go higher only on paid plans.
workers = int(os.environ.get("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count())))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Render sits behind a proxy that already terminates TLS.
forwarded_allow_ips = "*"
proxy_allow_ips = "*"

# Help workers recycle memory periodically.
max_requests = 1000
max_requests_jitter = 100
