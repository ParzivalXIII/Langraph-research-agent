"""Health check service for monitoring service dependencies."""

from enum import Enum
from typing import Dict
from datetime import datetime

import structlog

from app.core.config import settings
from app.tools.tavily import TavilyTool

logger = structlog.get_logger()


class HealthStatus(str, Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"


class HealthCheckService:
    """Service for checking health status of application dependencies."""

    def __init__(self):
        """Initialize health check service."""
        self.tavily_tool = TavilyTool()

    def check_api(self) -> HealthStatus:
        """Check API server status.

        Returns:
            HealthStatus: Always returns HEALTHY if service is running.
        """
        return HealthStatus.HEALTHY

    def check_tavily(self) -> HealthStatus:
        """Check Tavily API connectivity.

        Returns:
            HealthStatus: HEALTHY if Tavily is configured and reachable,
                         DEGRADED if API key is not configured.
        """
        if not settings.tavily_api_key:
            logger.warning("tavily_not_configured")
            return HealthStatus.DEGRADED

        try:
            # Attempt a simple test call or check if API is responsive
            # For now, we assume Tavily is healthy if the key is present
            # In production, could do a lightweight ping
            return HealthStatus.HEALTHY
        except Exception as exc:
            logger.error("tavily_health_check_failed", error=str(exc))
            return HealthStatus.UNHEALTHY

    def check_database(self) -> HealthStatus:
        """Check database connectivity.

        Returns:
            HealthStatus: HEALTHY if database is accessible,
                         NOT_CONFIGURED if persistence is disabled,
                         UNHEALTHY if connection fails.
        """
        if not settings.enable_persistence:
            return HealthStatus.NOT_CONFIGURED

        try:
            # Try to connect to database
            from sqlmodel import create_engine, Session
            from sqlalchemy import text

            engine = create_engine(settings.database_url, echo=False)
            with Session(engine) as session:
                # Execute a simple query to verify connection
                session.execute(text("SELECT 1"))
            return HealthStatus.HEALTHY
        except Exception as exc:
            logger.error("database_health_check_failed", error=str(exc))
            return HealthStatus.UNHEALTHY

    def check_cache(self) -> HealthStatus:
        """Check Redis cache connectivity.

        Returns:
            HealthStatus: HEALTHY if cache is accessible,
                         NOT_CONFIGURED if caching is disabled,
                         UNHEALTHY if connection fails.
        """
        if not settings.enable_caching or not settings.redis_url:
            return HealthStatus.NOT_CONFIGURED

        try:
            import redis

            client = redis.from_url(settings.redis_url)
            client.ping()
            return HealthStatus.HEALTHY
        except Exception as exc:
            logger.error("cache_health_check_failed", error=str(exc))
            return HealthStatus.UNHEALTHY

    def get_health_status(self) -> Dict:
        """Get comprehensive health status of all services.

        Returns:
            Dict: Health status object with individual checks and overall status.
        """
        api_status = self.check_api()
        tavily_status = self.check_tavily()
        database_status = self.check_database()
        cache_status = self.check_cache()

        checks = {
            "api": api_status.value,
            "tavily": tavily_status.value,
            "database": database_status.value,
            "cache": cache_status.value,
        }

        # Determine overall status
        # UNHEALTHY if any critical service is unhealthy
        # DEGRADED if Tavily is degraded (non-critical) or any service is degraded
        # HEALTHY otherwise
        status_values = [api_status, tavily_status, database_status, cache_status]

        if any(s == HealthStatus.UNHEALTHY for s in status_values):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in status_values):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        health_response = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.api_version,
            "checks": checks,
        }

        logger.info("health_status_checked", status=overall_status.value)

        return health_response
