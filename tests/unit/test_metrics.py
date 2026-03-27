"""Unit tests for MetricsService."""

import time
from unittest.mock import patch, MagicMock


from app.services.metrics import MetricsService, get_metrics_service

# ============================================================================
# MetricsService Unit Tests
# ============================================================================


class TestMetricsServiceBasics:
    """Test basic functionality of MetricsService."""

    def test_service_initialization(self):
        """Test that MetricsService initializes with correct default values."""
        service = MetricsService()

        assert service.start_time is not None
        assert service.requests_total == 0
        assert service.requests_failed == 0
        assert service.total_latency_ms == 0.0
        assert service.tavily_calls_total == 0
        assert service.cache_hits == 0
        assert service.cache_misses == 0

    def test_get_uptime_seconds(self):
        """Test uptime calculation in seconds."""
        service = MetricsService()

        # Should be almost 0 at start
        uptime = service.get_uptime_seconds()
        assert uptime == 0  # Exact 0 or very close (< 1 second)

    def test_get_uptime_after_delay(self):
        """Test uptime after a delay."""
        service = MetricsService()
        time.sleep(0.1)  # Sleep 100ms

        uptime = service.get_uptime_seconds()
        # Should be close to 0 (due to integer conversion)
        # After 100ms, it's still < 1 second so int() makes it 0
        assert uptime >= 0


class TestMetricsRecording:
    """Test recording of individual metrics."""

    def test_record_request_successful(self):
        """Test recording a successful request."""
        service = MetricsService()

        service.record_request(latency_ms=150.5, success=True)

        assert service.requests_total == 1
        assert service.requests_failed == 0
        assert service.total_latency_ms == 150.5

    def test_record_request_failed(self):
        """Test recording a failed request."""
        service = MetricsService()

        service.record_request(latency_ms=500.0, success=False)

        assert service.requests_total == 1
        assert service.requests_failed == 1
        assert service.total_latency_ms == 500.0

    def test_record_multiple_requests(self):
        """Test recording multiple requests."""
        service = MetricsService()

        service.record_request(latency_ms=100.0, success=True)
        service.record_request(latency_ms=200.0, success=True)
        service.record_request(latency_ms=300.0, success=False)

        assert service.requests_total == 3
        assert service.requests_failed == 1
        assert service.total_latency_ms == 600.0

    def test_record_tavily_call(self):
        """Test recording Tavily API calls."""
        service = MetricsService()

        service.record_tavily_call()
        service.record_tavily_call()

        assert service.tavily_calls_total == 2

    def test_record_cache_hit(self):
        """Test recording cache hits."""
        service = MetricsService()

        service.record_cache_hit()
        service.record_cache_hit()

        assert service.cache_hits == 2

    def test_record_cache_miss(self):
        """Test recording cache misses."""
        service = MetricsService()

        service.record_cache_miss()
        service.record_cache_miss()
        service.record_cache_miss()

        assert service.cache_misses == 3


class TestMetricsCalculations:
    """Test metric calculations and getters."""

    def test_get_average_latency_single_request(self):
        """Test average latency with a single request."""
        service = MetricsService()

        service.record_request(latency_ms=100.0, success=True)

        avg_latency = service.get_average_latency_ms()
        assert avg_latency == 100.0

    def test_get_average_latency_multiple_requests(self):
        """Test average latency with multiple requests."""
        service = MetricsService()

        service.record_request(latency_ms=100.0, success=True)
        service.record_request(latency_ms=200.0, success=True)
        service.record_request(latency_ms=300.0, success=False)

        avg_latency = service.get_average_latency_ms()
        expected = (100.0 + 200.0 + 300.0) / 3
        assert abs(avg_latency - expected) < 0.01  # Account for floating point

    def test_get_average_latency_no_requests(self):
        """Test average latency with no requests returns 0.0."""
        service = MetricsService()

        avg_latency = service.get_average_latency_ms()
        assert avg_latency == 0.0

    def test_get_cache_hit_rate_no_operations(self):
        """Test cache hit rate with no cache operations returns 0.0."""
        service = MetricsService()

        hit_rate = service.get_cache_hit_rate()
        assert hit_rate == 0.0

    def test_get_cache_hit_rate_all_hits(self):
        """Test cache hit rate when all operations are hits."""
        service = MetricsService()

        service.record_cache_hit()
        service.record_cache_hit()
        service.record_cache_hit()

        hit_rate = service.get_cache_hit_rate()
        assert hit_rate == 1.0

    def test_get_cache_hit_rate_all_misses(self):
        """Test cache hit rate when all operations are misses."""
        service = MetricsService()

        service.record_cache_miss()
        service.record_cache_miss()

        hit_rate = service.get_cache_hit_rate()
        assert hit_rate == 0.0

    def test_get_cache_hit_rate_mixed(self):
        """Test cache hit rate with mixed hits and misses."""
        service = MetricsService()

        # 3 hits and 1 miss = 75% hit rate
        service.record_cache_hit()
        service.record_cache_hit()
        service.record_cache_hit()
        service.record_cache_miss()

        hit_rate = service.get_cache_hit_rate()
        assert abs(hit_rate - 0.75) < 0.01  # Account for floating point

    @patch("app.services.metrics.psutil.Process")
    def test_get_memory_usage_mb(self, mock_process_class):
        """Test memory usage retrieval."""
        # Mock psutil to return a predictable memory value
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        # 100 MB = 100 * 1024 * 1024 bytes
        mock_memory_info.rss = 100 * 1024 * 1024
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        service = MetricsService()
        memory_mb = service.get_memory_usage_mb()

        assert memory_mb == 100.0

    def test_get_memory_usage_mb_error_handling(self):
        """Test memory usage error handling when psutil fails."""
        service = MetricsService()

        # Mock the process after creation to simulate error
        original_memory_info = service.process.memory_info
        service.process.memory_info = MagicMock(
            side_effect=Exception("Permission denied")
        )

        memory_mb = service.get_memory_usage_mb()

        # Should return 0.0 on error
        assert memory_mb == 0.0

        # Restore original
        service.process.memory_info = original_memory_info


class TestMetricsGetMetrics:
    """Test the comprehensive get_metrics() method."""

    def test_get_metrics_empty(self):
        """Test get_metrics with no recorded data."""
        service = MetricsService()

        metrics = service.get_metrics()

        assert "uptime_seconds" in metrics
        assert "requests_total" in metrics
        assert "requests_failed" in metrics
        assert "average_latency_ms" in metrics
        assert "tavily_calls_total" in metrics
        assert "cache_hit_rate" in metrics
        assert "memory_usage_mb" in metrics

        assert metrics["requests_total"] == 0
        assert metrics["requests_failed"] == 0
        assert metrics["average_latency_ms"] == 0.0
        assert metrics["tavily_calls_total"] == 0
        assert metrics["cache_hit_rate"] == 0.0

    def test_get_metrics_with_data(self):
        """Test get_metrics with recorded data."""
        service = MetricsService()

        # Record some data
        service.record_request(latency_ms=100.0, success=True)
        service.record_request(latency_ms=200.0, success=False)
        service.record_tavily_call()
        service.record_cache_hit()
        service.record_cache_miss()

        metrics = service.get_metrics()

        assert metrics["requests_total"] == 2
        assert metrics["requests_failed"] == 1
        assert metrics["average_latency_ms"] == 150.0
        assert metrics["tavily_calls_total"] == 1
        assert metrics["cache_hit_rate"] == 0.5

    def test_get_metrics_types(self):
        """Test that metrics returns correct data types."""
        service = MetricsService()
        service.record_request(latency_ms=100.5, success=True)

        metrics = service.get_metrics()

        assert isinstance(metrics["uptime_seconds"], int)
        assert isinstance(metrics["requests_total"], int)
        assert isinstance(metrics["requests_failed"], int)
        assert isinstance(metrics["average_latency_ms"], float)
        assert isinstance(metrics["tavily_calls_total"], int)
        assert isinstance(metrics["cache_hit_rate"], float)
        assert isinstance(metrics["memory_usage_mb"], float)

    def test_get_metrics_values_rounded(self):
        """Test that float values in metrics are rounded to 2 decimal places."""
        service = MetricsService()
        service.record_request(latency_ms=123.456789, success=True)

        metrics = service.get_metrics()

        # Should be rounded to 2 decimal places
        assert metrics["average_latency_ms"] == 123.46


class TestMetricsSingleton:
    """Test the singleton pattern for MetricsService."""

    def test_get_metrics_service_returns_singleton(self):
        """Test that get_metrics_service returns the same instance."""
        service1 = get_metrics_service()
        service2 = get_metrics_service()

        assert service1 is service2

    def test_singleton_persists_data(self):
        """Test that singleton instance persists data across calls."""
        # Clear the singleton
        import app.services.metrics as metrics_module

        metrics_module._metrics_instance = None

        # Get first instance and record data
        service1 = get_metrics_service()
        service1.record_request(latency_ms=100.0, success=True)

        # Get second instance (should be same singleton)
        service2 = get_metrics_service()

        # Data should be the same
        assert service2.requests_total == 1
        assert service2.total_latency_ms == 100.0
