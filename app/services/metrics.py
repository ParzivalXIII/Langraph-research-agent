"""Metrics tracking service for operational monitoring."""

import psutil
import structlog
from datetime import datetime
from typing import Dict, Optional

logger = structlog.get_logger()


class MetricsService:
    """Service for tracking application metrics."""

    def __init__(self):
        """Initialize metrics service with baseline values."""
        self.start_time = datetime.utcnow()
        self.requests_total = 0
        self.requests_failed = 0
        self.total_latency_ms = 0.0
        self.tavily_calls_total = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.process = psutil.Process()

    def record_request(self, latency_ms: float, success: bool = True) -> None:
        """Record a request completion.

        Args:
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded (default: True)
        """
        self.requests_total += 1
        if not success:
            self.requests_failed += 1
        self.total_latency_ms += latency_ms
        logger.debug(
            "request_recorded",
            requests_total=self.requests_total,
            requests_failed=self.requests_failed,
        )

    def record_tavily_call(self) -> None:
        """Record a Tavily API call."""
        self.tavily_calls_total += 1
        logger.debug("tavily_call_recorded", tavily_calls=self.tavily_calls_total)

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.cache_misses += 1

    def get_uptime_seconds(self) -> int:
        """Get application uptime in seconds.

        Returns:
            int: Seconds since application started
        """
        return int((datetime.utcnow() - self.start_time).total_seconds())

    def get_average_latency_ms(self) -> float:
        """Get average request latency in milliseconds.

        Returns:
            float: Average latency, or 0.0 if no requests recorded
        """
        if self.requests_total == 0:
            return 0.0
        return self.total_latency_ms / self.requests_total

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate (0.0-1.0).

        Returns:
            float: Cache hit rate as fraction, or 0.0 if no cache operations
        """
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops == 0:
            return 0.0
        return self.cache_hits / total_cache_ops

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB.

        Returns:
            float: Memory usage in MB
        """
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as exc:
            logger.warning("memory_usage_retrieval_failed", error=str(exc))
            return 0.0

    def get_metrics(self) -> Dict:
        """Get comprehensive metrics.

        Returns:
            Dict: Metrics object with all operational signals
        """
        metrics = {
            "uptime_seconds": self.get_uptime_seconds(),
            "requests_total": self.requests_total,
            "requests_failed": self.requests_failed,
            "average_latency_ms": round(self.get_average_latency_ms(), 2),
            "tavily_calls_total": self.tavily_calls_total,
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
            "memory_usage_mb": round(self.get_memory_usage_mb(), 2),
        }

        logger.info(
            "metrics_collected",
            uptime_seconds=metrics["uptime_seconds"],
            requests_total=metrics["requests_total"],
            average_latency_ms=metrics["average_latency_ms"],
        )

        return metrics

    def get_full_status(self) -> Dict:
        """Get full status report including health and metrics.

        This method is typically called by the /health endpoint.

        Returns:
            Dict: Status object with timestamp, version, metrics
        """
        from app.core.config import settings

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.api_version,
            "metrics": self.get_metrics(),
        }


# Global metrics instance
_metrics_instance: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """Get or create the global metrics service instance.

    Returns:
        MetricsService: Singleton metrics service
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsService()
    return _metrics_instance
