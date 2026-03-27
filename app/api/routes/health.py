"""Health and metrics API routes.

Provides REST endpoints for monitoring service health status and operational metrics.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.services.health import HealthCheckService
from app.services.metrics import get_metrics_service

logger = get_logger(__name__)

# Initialize services
_health_service = HealthCheckService()

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns service status and health of dependencies (API, Tavily, database, cache).",
)
async def health_check():
    """
    Health check endpoint returning service status and checks.

    Returns:
        JSON with status, timestamp, version, and component checks.
        HTTP 200 if healthy, 503 if degraded/unhealthy.

    Example:
        {
            "status": "healthy",
            "timestamp": "2026-03-26T12:00:00Z",
            "version": "1.0.0",
            "checks": {
                "api": "healthy",
                "tavily": "healthy",
                "database": "healthy",
                "cache": "not_configured"
            }
        }
    """
    logger.debug("health_check_request")

    # Get comprehensive health status
    health_status = _health_service.get_health_status()

    # Determine HTTP status code based on overall health
    http_status = 200
    overall_status = health_status.get("status", "unhealthy")
    if overall_status == "unhealthy":
        http_status = 503
    elif overall_status == "degraded":
        http_status = 503  # Per spec: 503 for degraded too

    logger.info("health_check_response", status=overall_status, http_status=http_status)

    return JSONResponse(status_code=http_status, content=health_status)


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Operational metrics endpoint",
    description="Returns operational metrics including uptime, request counts, latency, API calls, and resource usage.",
)
async def get_metrics():
    """
    Operational metrics endpoint.

    Returns:
        JSON with uptime, request counts, latency, Tavily calls, cache hit rate, memory usage.

    Example:
        {
            "uptime_seconds": 86400,
            "requests_total": 1500,
            "requests_failed": 2,
            "average_latency_ms": 1200.5,
            "tavily_calls_total": 450,
            "cache_hit_rate": 0.65,
            "memory_usage_mb": 125.4
        }
    """
    logger.debug("metrics_request")
    metrics_service = get_metrics_service()
    metrics_dict = metrics_service.get_metrics()
    logger.info(
        "metrics_response",
        uptime_seconds=metrics_dict.get("uptime_seconds"),
        requests_total=metrics_dict.get("requests_total"),
    )
    return JSONResponse(status_code=200, content=metrics_dict)
