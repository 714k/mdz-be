"""
mdz Backend - FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

# from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import CONTENT_TYPE_LATEST
import time

from app.config import settings
from app.core.logging import configure_logging, logger

from app.core.cache import cache
from app.core.database import engine, Base
from app.core.monitoring import (
    get_metrics,
    http_requests_total,
    http_request_duration_seconds,
    update_redis_metrics_sync,
)
from app.api.v1 import auth, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("application_starting", version=settings.APP_VERSION)
    configure_logging()

    # Initialize Redis
    await cache.connect()
    logger.info("REDIS::STATUS::CONNECTED")
    print(settings.REDIS_URL)

    # Create database tables (development only)
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created")

    yield

    # Shutdown
    await cache.disconnect()
    logger.info("REDIS::STATUS::DISCONNECTED")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    if settings.ENVIRONMENT == "production":
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# Request Logging & Metrics Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and collect metrics."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{duration:.3f}s",
    )

    # Metrics
    http_requests_total.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method, endpoint=request.url.path
    ).observe(duration)

    return response


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router, prefix=settings.API_V1_PREFIX)


# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    update_redis_metrics_sync()
    return Response(get_metrics(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/cache-test")
async def cache_test():
    await cache.set("victor:test", {"hello": "world"})
    return {"saved": True}
