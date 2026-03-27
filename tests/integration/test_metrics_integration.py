"""Integration tests for MetricsService with FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.metrics import get_metrics_service
import app.services.metrics as metrics_module

# ============================================================================
# Module-level setup/teardown
# ============================================================================


def pytest_configure(config):
    """Reset the global metrics instance before integration tests."""
    # Clear the global metrics instance so tests start fresh
    metrics_module._metrics_instance = None


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_metrics():
    """Auto-reset metrics before each test."""
    service = get_metrics_service()
    service.requests_total = 0
    service.requests_failed = 0
    service.total_latency_ms = 0.0
    service.tavily_calls_total = 0
    service.cache_hits = 0
    service.cache_misses = 0
    yield
    # Optionally reset after test too
    service.requests_total = 0
    service.requests_failed = 0
    service.total_latency_ms = 0.0
    service.tavily_calls_total = 0
    service.cache_hits = 0
    service.cache_misses = 0


@pytest.fixture
def metrics_service():
    """Get the metrics service singleton."""
    service = get_metrics_service()
    # Reset metrics for isolated tests
    service.requests_total = 0
    service.requests_failed = 0
    service.total_latency_ms = 0.0
    service.tavily_calls_total = 0
    service.cache_hits = 0
    service.cache_misses = 0
    return service


# ============================================================================
# Integration Tests: Metrics Recording via API
# ============================================================================


class TestMetricsRecordingViaAPI:
    """Test that metrics are recorded correctly when requests go through the API."""

    def test_metrics_recorded_for_health_endpoint(self, client, metrics_service):
        """Test that a request to /health is recorded in metrics."""
        initial_requests = metrics_service.requests_total

        # Make a request to the health endpoint
        response = client.get("/health")
        assert response.status_code in [200, 503]

        # Check that request was recorded
        assert metrics_service.requests_total == initial_requests + 1
        assert metrics_service.total_latency_ms > 0

    def test_metrics_recorded_for_root_endpoint(self, client, metrics_service):
        """Test that a request to / is recorded in metrics."""
        initial_requests = metrics_service.requests_total

        response = client.get("/")
        assert response.status_code == 200

        assert metrics_service.requests_total == initial_requests + 1

    def test_metrics_success_flag_for_healthy_response(self, client, metrics_service):
        """Test that successful responses (2xx) are marked as success."""
        metrics_service.requests_total = 0
        metrics_service.requests_failed = 0

        # Make a successful request
        response = client.get("/")
        assert response.status_code == 200

        # Check success flag
        assert metrics_service.requests_total == 1
        assert metrics_service.requests_failed == 0

    def test_metrics_multiple_requests_accumulate(self, client, metrics_service):
        """Test that multiple requests accumulate in metrics."""
        metrics_service.requests_total = 0
        metrics_service.requests_failed = 0
        metrics_service.total_latency_ms = 0.0

        # Make multiple requests
        for i in range(5):
            response = client.get("/")
            assert response.status_code == 200

        assert metrics_service.requests_total == 5

    def test_metrics_latency_recorded(self, client, metrics_service):
        """Test that request latency is recorded."""
        metrics_service.requests_total = 0
        metrics_service.total_latency_ms = 0.0

        # Make a request
        response = client.get("/")
        assert response.status_code == 200

        # Check that latency was recorded
        assert metrics_service.requests_total == 1
        assert metrics_service.total_latency_ms > 0
        # Latency should be reasonable (not more than 1 second for local test)
        assert metrics_service.total_latency_ms < 1000


# ============================================================================
# Integration Tests: Metrics Endpoint
# ============================================================================


class TestMetricsEndpoint:
    """Test the /metrics endpoint returns current metrics."""

    def test_metrics_endpoint_returns_200(self, client):
        """Test that /metrics endpoint returns 200 OK."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_json_structure(self, client):
        """Test that /metrics endpoint returns correct JSON structure."""
        response = client.get("/metrics")
        data = response.json()

        # Check required fields
        required_fields = [
            "uptime_seconds",
            "requests_total",
            "requests_failed",
            "average_latency_ms",
            "tavily_calls_total",
            "cache_hit_rate",
            "memory_usage_mb",
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_metrics_endpoint_field_types(self, client):
        """Test that /metrics endpoint returns correct field types."""
        response = client.get("/metrics")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert isinstance(data["requests_total"], int)
        assert isinstance(data["requests_failed"], int)
        assert isinstance(data["average_latency_ms"], (int, float))
        assert isinstance(data["tavily_calls_total"], int)
        assert isinstance(data["cache_hit_rate"], (int, float))
        assert isinstance(data["memory_usage_mb"], (int, float))

    def test_metrics_endpoint_reflects_requests(self, client):
        """Test that /metrics reflects requests made to the API."""
        # Make a request to trigger metrics
        response = client.get("/")
        assert response.status_code == 200

        # Now check metrics
        response = client.get("/metrics")
        data = response.json()

        # At minimum, the "/" request should be recorded
        assert data["requests_total"] >= 1

        # Make another metrics call to ensure previous metrics call is recorded
        response2 = client.get("/metrics")
        data2 = response2.json()

        # Now we should have at least 2 total requests
        assert data2["requests_total"] >= 2

    def test_metrics_endpoint_cache_hit_rate_valid_range(self, client):
        """Test that cache hit rate is always between 0.0 and 1.0."""
        response = client.get("/metrics")
        data = response.json()

        cache_hit_rate = data["cache_hit_rate"]
        assert 0.0 <= cache_hit_rate <= 1.0

    def test_metrics_endpoint_no_failure_on_zero_metrics(self, client):
        """Test that /metrics works correctly with zero metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        # All numeric fields should be >= 0
        assert data["uptime_seconds"] >= 0
        assert data["requests_total"] >= 0
        assert data["requests_failed"] >= 0
        assert data["average_latency_ms"] >= 0.0
        assert data["tavily_calls_total"] >= 0
        assert data["cache_hit_rate"] >= 0.0
        assert data["memory_usage_mb"] >= 0.0


# ============================================================================
# Integration Tests: Metrics Service Recording Methods
# ============================================================================


class TestMetricsServiceIntegration:
    """Test MetricsService methods in an integrated context."""

    def test_record_request_integration(self, metrics_service):
        """Test record_request method with realistic latency values."""
        # Simulate requests with different latencies
        latencies = [50.0, 100.5, 200.3]

        for latency in latencies:
            metrics_service.record_request(latency_ms=latency, success=True)

        assert metrics_service.requests_total == 3
        assert metrics_service.requests_failed == 0

        expected_avg = sum(latencies) / len(latencies)
        actual_avg = metrics_service.get_average_latency_ms()
        assert abs(actual_avg - expected_avg) < 0.1

    def test_cache_operations_integration(self, metrics_service):
        """Test cache operations with realistic hit/miss pattern."""
        # Simulate a realistic cache usage pattern
        operations = [
            ("hit", 1),
            ("hit", 1),
            ("miss", 1),
            ("hit", 1),
            ("miss", 1),
            ("miss", 1),
        ]

        for op_type, _ in operations:
            if op_type == "hit":
                metrics_service.record_cache_hit()
            else:
                metrics_service.record_cache_miss()

        # 3 hits out of 6 = 50%
        assert metrics_service.cache_hits == 3
        assert metrics_service.cache_misses == 3
        hit_rate = metrics_service.get_cache_hit_rate()
        assert abs(hit_rate - 0.5) < 0.01

    def test_tavily_calls_integration(self, metrics_service):
        """Test Tavily call recording."""
        # Simulate multiple Tavily calls
        for _ in range(10):
            metrics_service.record_tavily_call()

        assert metrics_service.tavily_calls_total == 10

    def test_mixed_operations_integration(self, metrics_service):
        """Test mixed operations recording."""
        # Simulate a complete workflow

        # Some API requests
        metrics_service.record_request(latency_ms=150.0, success=True)
        metrics_service.record_request(latency_ms=250.0, success=True)
        metrics_service.record_request(latency_ms=300.0, success=False)

        # Some Tavily calls
        metrics_service.record_tavily_call()
        metrics_service.record_tavily_call()

        # Some cache operations
        metrics_service.record_cache_hit()
        metrics_service.record_cache_hit()
        metrics_service.record_cache_miss()

        # Verify all metrics
        assert metrics_service.requests_total == 3
        assert metrics_service.requests_failed == 1
        assert abs(metrics_service.get_average_latency_ms() - 233.33) < 1.0
        assert metrics_service.tavily_calls_total == 2
        assert abs(metrics_service.get_cache_hit_rate() - (2.0 / 3.0)) < 0.01


# ============================================================================
# Integration Tests: Health and Metrics Together
# ============================================================================


class TestHealthAndMetricsTogether:
    """Test health and metrics endpoints working together."""

    def test_health_and_metrics_endpoints_coexist(self, client):
        """Test that both /health and /metrics endpoints work."""
        health_response = client.get("/health")
        assert health_response.status_code in [200, 503]

        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200

    def test_health_endpoint_call_recorded_in_metrics(self, client, metrics_service):
        """Test that calling /health increments request counter in /metrics."""
        metrics_service.requests_total = 0

        # Call health endpoint
        health_response = client.get("/health")
        assert health_response.status_code in [200, 503]

        # Call metrics endpoint (this call is recorded after response is built)
        metrics_response = client.get("/metrics")
        data = metrics_response.json()

        # At minimum, the /health request should be recorded
        assert data["requests_total"] >= 1

        # Make another request to confirm the /metrics call from above is now recorded
        second_metrics = client.get("/metrics")
        second_data = second_metrics.json()

        # Now we should have at least 2 calls recorded
        # (the /health call + the first /metrics call made above)
        assert second_data["requests_total"] >= 2

    def test_multiple_requests_show_in_metrics(self, client):
        """Test that multiple API calls are reflected in metrics."""
        # Make several API calls
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200

        # Check metrics
        response = client.get("/metrics")
        data = response.json()

        # Should have at least 3 requests recorded (3 root calls)
        # Note: The /metrics call from above is not yet fully recorded
        assert data["requests_total"] >= 3

        # Make another metrics call to ensure all previous requests are recorded
        final_metrics = client.get("/metrics")
        final_data = final_metrics.json()

        # Now we should have at least 4 total requests
        # (3 root calls + 1 metrics call from above)
        assert final_data["requests_total"] >= 4
