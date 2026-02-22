"""
Prometheus metrics for monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import redis
from app.config import settings

# from app.core.monitoring import redis_up, redis_latency_seconds

# -----------------------------------
# Request metrics
# -----------------------------------
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)

# -----------------------------------
# Database metrics
# -----------------------------------
db_connections = Gauge("db_connections_active", "Active database connections")

# -----------------------------------
# Cache metrics
# -----------------------------------
cache_hits = Counter("cache_hits_total", "Cache hits")
cache_misses = Counter("cache_misses_total", "Cache misses")

# -----------------------------------
# Authentication metrics
# -----------------------------------
auth_attempts_total = Counter(
    "auth_attempts_total", "Authentication attempts", ["status"]
)

# # -----------------------------------
# # Redis metrics (SYNC)
# # -----------------------------------
redis_up = Gauge("mdz_redis_up", "Redis availability (1 = up, 0 = down)")
redis_latency_seconds = Gauge(
    "mdz_redis_latency_seconds", "Redis ping latency in seconds"
)


def update_redis_metrics_sync():
    """Ping Redis using synchronous client and update metrics."""
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        start = time.time()
        # Real ping using Redis protocol (RESP)
        r.set("metrics:ping", "1", ex=5)
        r.get("metrics:ping")
        latency = time.time() - start
        redis_up.set(1)
        redis_latency_seconds.set(latency)
    except Exception:
        redis_up.set(0)
        redis_latency_seconds.set(0)


def get_metrics():
    """Generate Prometheus metrics output."""
    return generate_latest()
