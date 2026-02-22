"""
Health check and readiness endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.core.database import get_db
from app.core.cache import cache

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=dict)
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/readiness", response_model=dict)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies all dependencies.

    Checks:
    - Database connectivity
    - Redis connectivity
    """
    checks = {
        "database": False,
        "cache": False,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # -------------------------
    # Database check
    # -------------------------
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    # -------------------------
    # Redis check
    # -------------------------
    try:
        key = "health:readiness"
        await cache.set(key, {"status": "ok"}, expire=10)
        result = await cache.get(key)
        checks["cache"] = result == {"status": "ok"}
    except Exception as e:
        checks["cache_error"] = str(e)

    overall_healthy = checks["database"] and checks["cache"]

    return {"status": "ready" if overall_healthy else "not_ready", "checks": checks}
