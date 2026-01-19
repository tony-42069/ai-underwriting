"""
Health check endpoints for monitoring.
"""

import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    checks: Dict[str, Dict[str, Any]]


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str
    message: Optional[str] = None
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


start_time = time.time()


def get_system_info() -> Dict[str, Any]:
    """Get system information for health check."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
    }


@router.get("/", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Comprehensive health check endpoint.

    Returns the health status of all system components including
    database connections, system resources, and service status.
    """
    checks = {}
    overall_status = "healthy"

    mongo_status = "healthy"
    mongo_latency = None
    try:
        from db.mongodb import MongoDB

        start = time.time()
        if MongoDB.client:
            await MongoDB.db.command("ping")
            mongo_latency = round((time.time() - start) * 1000, 2)
        else:
            mongo_status = "unhealthy"
            overall_status = "degraded"
    except Exception as e:
        mongo_status = "unhealthy"
        mongo_latency = None
        logger.error(f"MongoDB health check failed: {e}")
        overall_status = "unhealthy"

    checks["mongodb"] = {
        "status": mongo_status,
        "latency_ms": mongo_latency,
    }

    system_info = get_system_info()
    system_status = "healthy"

    if system_info["cpu_percent"] > 90:
        system_status = "degraded"
        overall_status = "degraded" if overall_status == "healthy" else overall_status

    if system_info["memory_percent"] > 90:
        system_status = "unhealthy"
        overall_status = "unhealthy"

    if system_info["disk_percent"] > 90:
        system_status = "unhealthy"
        overall_status = "unhealthy"

    checks["system"] = {
        "status": system_status,
        "details": system_info,
    }

    uptime_seconds = round(time.time() - start_time, 2)

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        checks=checks,
    )


@router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.

    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe() -> Dict[str, str]:
    """
    Kubernetes readiness probe.

    Returns 200 if the application is ready to serve traffic.
    """
    try:
        from db.mongodb import MongoDB

        if MongoDB.client:
            await MongoDB.db.command("ping")
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": "Database not connected"}

    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    Basic metrics endpoint.

    Returns system and application metrics.
    """
    system_info = get_system_info()

    uptime_seconds = time.time() - start_time

    return {
        "uptime_seconds": uptime_seconds,
        "cpu_percent": system_info["cpu_percent"],
        "memory_percent": system_info["memory_percent"],
        "disk_percent": system_info["disk_percent"],
        "timestamp": datetime.utcnow().isoformat(),
    }
