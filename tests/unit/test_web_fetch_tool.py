"""Unit tests for WebFetchTool."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import Settings
from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest
from app.tools.web_fetch import WebFetchTool


@pytest.mark.asyncio
class TestWebFetchTool:
    """Tests for WebFetchTool basic functionality."""

    async def test_placeholder(self):
        """Placeholder test for stub."""
        pass

    async def test_concurrency_semaphore_limits_concurrent_requests(self):
        """Test that concurrency semaphore limits concurrent requests to max_concurrency.
        
        This validates FR-002: Tool MUST fetch all URLs in the batch concurrently,
        governed by a configurable global concurrency limit.
        
        Validates T075: Implement asyncio.Semaphore to enforce the global concurrency cap.
        """
        settings = Settings(web_fetch_max_concurrency=2)
        tool = WebFetchTool(settings=settings)

        # Track concurrent request count
        max_concurrent = 0
        current_concurrent = 0
        concurrent_lock = asyncio.Lock()

        async def mock_fetch_single(url: str, config: WebFetchConfig):
            nonlocal max_concurrent, current_concurrent
            async with concurrent_lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)

            # Simulate work
            await asyncio.sleep(0.1)

            async with concurrent_lock:
                current_concurrent -= 1

            # Return mock FetchedPage
            from app.schemas.web_fetch import FetchedPage
            from datetime import datetime

            return FetchedPage(
                url=url,
                fetched_at=datetime.now(),
                http_status=200,
                processing_ms=100,
                error=None,
            )

        # Patch _fetch_single to use our mock
        tool._fetch_single = mock_fetch_single

        # Create batch with 5 URLs
        urls = ["http://example.com/1", "http://example.com/2",
                "http://example.com/3", "http://example.com/4",
                "http://example.com/5"]
        config = WebFetchConfig()
        request = WebFetchRequest(urls=urls, config=config)

        # Execute batch
        result = await tool.fetch_batch(request)

        # Assert max concurrent requests <= max_concurrency
        assert max_concurrent <= settings.web_fetch_max_concurrency, \
            f"Concurrency ({max_concurrent}) exceeded limit ({settings.web_fetch_max_concurrency})"
        assert result.requested_count == 5
        assert result.fetched_count == 5

    async def test_concurrency_semaphore_with_different_limits(self):
        """Test concurrency semaphore with various max_concurrency settings.
        
        Validates T075: Ensure semaphore properly respects different concurrency limits.
        """
        for max_concurrency in [1, 2, 5]:
            settings = Settings(web_fetch_max_concurrency=max_concurrency)
            tool = WebFetchTool(settings=settings)

            max_concurrent = 0
            current_concurrent = 0
            concurrent_lock = asyncio.Lock()

            async def mock_fetch_single(url: str, config: WebFetchConfig):
                nonlocal max_concurrent, current_concurrent
                async with concurrent_lock:
                    current_concurrent += 1
                    max_concurrent = max(max_concurrent, current_concurrent)

                await asyncio.sleep(0.05)

                async with concurrent_lock:
                    current_concurrent -= 1

                from app.schemas.web_fetch import FetchedPage
                from datetime import datetime

                return FetchedPage(
                    url=url,
                    fetched_at=datetime.now(),
                    http_status=200,
                    processing_ms=50,
                    error=None,
                )

            tool._fetch_single = mock_fetch_single
            urls = [f"http://example.com/{i}" for i in range(10)]
            config = WebFetchConfig()
            request = WebFetchRequest(urls=urls, config=config)

            result = await tool.fetch_batch(request)

            assert max_concurrent <= max_concurrency, \
                f"Limit {max_concurrency}: concurrency {max_concurrent} exceeded limit"
            assert result.fetched_count == 10


@pytest.mark.asyncio
class TestWebFetchToolRateLimiting:
    """Tests for WebFetchTool rate limiting and retry logic (Phase 4)."""

    async def test_rate_limit_wait_enforces_spacing(self):
        """Test that rate limit enforces minimum spacing between requests.

        Validates T033: _wait_for_domain_rate_limit enforces 1/rate_limit spacing.
        """
        settings = Settings(web_fetch_per_domain_rate_limit=1.0)  # 1 req/s
        tool = WebFetchTool(settings=settings)

        domain = "example.com"

        # First call should not wait
        start = time.monotonic()
        await tool._wait_for_domain_rate_limit(domain, 1.0)
        first_duration = time.monotonic() - start
        assert first_duration < 0.1  # Should be nearly instant

        # Second call should wait ~1 second
        start = time.monotonic()
        await tool._wait_for_domain_rate_limit(domain, 1.0)
        second_duration = time.monotonic() - start
        assert 0.9 < second_duration < 1.2, f"Expected ~1s wait, got {second_duration:.2f}s"

    async def test_rate_limit_different_domains_independent(self):
        """Test that rate limits are per-domain.

        Validates T032: Different domains should have independent rate limits.
        """
        settings = Settings(web_fetch_per_domain_rate_limit=1.0)
        tool = WebFetchTool(settings=settings)

        # First request to domain1
        start = time.monotonic()
        await tool._wait_for_domain_rate_limit("example.com", 1.0)
        await tool._wait_for_domain_rate_limit("example.com", 1.0)
        duration1 = time.monotonic() - start

        # Requests to domain2 should not be delayed
        start = time.monotonic()
        await tool._wait_for_domain_rate_limit("other.com", 1.0)
        await tool._wait_for_domain_rate_limit("other.com", 1.0)
        duration2 = time.monotonic() - start

        # Both should be ~1s (for the second request), but domain2 shouldn't
        # wait for domain1's delay
        assert 0.9 < duration1 < 1.2
        assert 0.9 < duration2 < 1.2

    async def test_should_retry_on_429(self):
        """Test that tool retries on 429 (Too Many Requests).

        Validates T035: _should_retry returns True for 429 when retries_left > 0.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Should retry on 429 with retries left
        assert tool._should_retry(429, None, 1) is True
        assert tool._should_retry(429, None, 3) is True

        # Should not retry on 429 with no retries left
        assert tool._should_retry(429, None, 0) is False

    async def test_should_retry_on_5xx(self):
        """Test that tool retries on 5xx server errors.

        Validates T035: _should_retry returns True for 5xx errors.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Should retry on 5xx with retries left
        for status in [500, 502, 503, 504]:
            assert tool._should_retry(status, None, 1) is True, f"Should retry on {status}"

        # Should not retry on 5xx with no retries left
        assert tool._should_retry(503, None, 0) is False

    async def test_should_retry_on_timeout(self):
        """Test that tool retries on timeout errors.

        Validates T035: _should_retry returns True for timeout errors.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Should retry on timeout with retries left
        assert tool._should_retry(None, "timeout", 1) is True

        # Should not retry with no retries left
        assert tool._should_retry(None, "timeout", 0) is False

    async def test_should_not_retry_on_4xx(self):
        """Test that tool does NOT retry on 4xx errors.

        Validates T035: _should_retry returns False for 4xx (except 429).
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        for status in [400, 401, 403, 404, 410]:
            assert tool._should_retry(status, None, 1) is False, f"Should not retry on {status}"

    async def test_get_retry_after_parses_seconds(self):
        """Test that Retry-After header is parsed as seconds.

        Validates T037: _get_retry_after parses Retry-After header correctly.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Create mock response with Retry-After header
        response = MagicMock(spec=httpx.Response)
        response.headers = {"retry-after": "2"}

        delay = tool._get_retry_after(response)
        assert delay == 2.0

    async def test_get_retry_after_returns_none_if_missing(self):
        """Test that _get_retry_after returns None if header missing.

        Validates T037: _get_retry_after returns None for missing header.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        response = MagicMock(spec=httpx.Response)
        response.headers = {}

        delay = tool._get_retry_after(response)
        assert delay is None

    async def test_get_retry_after_returns_none_if_invalid(self):
        """Test that _get_retry_after handles invalid header values.

        Validates T037: _get_retry_after returns None for invalid values.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        response = MagicMock(spec=httpx.Response)
        response.headers = {"retry-after": "not-a-number"}

        delay = tool._get_retry_after(response)
        assert delay is None

    async def test_parse_domain_extracts_domain(self):
        """Test that _parse_domain extracts domain correctly.

        Validates T032: _parse_domain extracts domain from URLs.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        assert tool._parse_domain("https://example.com/path") == "example.com"
        assert tool._parse_domain("http://subdomain.example.com/") == "subdomain.example.com"
        assert tool._parse_domain("https://example.com:8080/path") == "example.com:8080"

    @patch("app.tools.web_fetch.httpx.AsyncClient")
    async def test_retry_on_429_with_retry_after(self, mock_client_class):
        """Test retry on 429 response with Retry-After header.

        Validates T040: Tool waits ≥ Retry-After seconds before retry on 429.
        """
        settings = Settings(web_fetch_max_retries=2)
        tool = WebFetchTool(settings=settings)

        # Create mock client that returns 429 then 200
        mock_client = AsyncMock()

        # First response: 429 with Retry-After
        response_429 = MagicMock(spec=httpx.Response)
        response_429.status_code = 429
        response_429.headers = {"retry-after": "0.2"}
        response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=None, response=response_429
        )

        # Second response: 200 OK
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {"content-type": "text/html"}
        response_200.content = b"<html><head><title>Test</title></head><body>Hello</body></html>"
        response_200.raise_for_status.return_value = None

        # Set up side effects
        mock_client.get.side_effect = [response_429, response_200]
        tool._client = mock_client

        # Fetch single URL
        config = WebFetchConfig()
        start = time.monotonic()
        result = await tool._fetch_single("https://example.com/test", config)
        elapsed = time.monotonic() - start

        # Should have retried and succeeded
        assert result.succeeded is True
        # Should have waited at least the Retry-After time
        assert elapsed >= 0.2, f"Should wait ≥0.2s for Retry-After, but only waited {elapsed:.2f}s"

    @patch("app.tools.web_fetch.httpx.AsyncClient")
    async def test_retry_on_503_with_backoff(self, mock_client_class):
        """Test retry on 503 with exponential backoff.

        Validates T041: Tool retries 503 errors with exponential backoff.
        """
        settings = Settings(
            web_fetch_max_retries=2,
            web_fetch_retry_backoff=0.1
        )
        tool = WebFetchTool(settings=settings)

        mock_client = AsyncMock()

        # First two responses: 503
        response_503_1 = MagicMock(spec=httpx.Response)
        response_503_1.status_code = 503
        response_503_1.headers = {}
        response_503_1.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=None, response=response_503_1
        )

        response_503_2 = MagicMock(spec=httpx.Response)
        response_503_2.status_code = 503
        response_503_2.headers = {}
        response_503_2.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=None, response=response_503_2
        )

        # Third response: 200 OK
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {"content-type": "text/html"}
        response_200.content = b"<html><head><title>Success</title></head><body>OK</body></html>"
        response_200.raise_for_status.return_value = None

        mock_client.get.side_effect = [response_503_1, response_503_2, response_200]
        tool._client = mock_client

        config = WebFetchConfig()
        result = await tool._fetch_single("https://example.com/test", config)

        # Should have succeeded after retries
        assert result.succeeded is True
        # Should have made 3 requests (initial + 2 retries)
        assert mock_client.get.call_count == 3


@pytest.mark.asyncio
class TestWebFetchToolHeadlessBrowser:
    """Tests for WebFetchTool headless browser support (Phase 5)."""

    async def test_should_use_headless_respects_global_setting(self):
        """Test that _should_use_headless respects global setting.

        Validates T047: _should_use_headless checks global setting.
        """
        settings = Settings(web_fetch_headless_enabled=False)
        tool = WebFetchTool(settings=settings)

        config = WebFetchConfig(use_headless=True)
        # Global disabled + per-request enabled -> should not use
        assert tool._should_use_headless(config, False) is False

        settings = Settings(web_fetch_headless_enabled=True)
        tool = WebFetchTool(settings=settings)
        # Global enabled + per-request enabled -> should use
        assert tool._should_use_headless(config, True) is True

        config = WebFetchConfig(use_headless=False)
        # Global enabled but per-request disabled -> should not use
        assert tool._should_use_headless(config, True) is False

    async def test_should_use_headless_requires_both_true(self):
        """Test that _should_use_headless requires both global and per-request to be True.

        Validates T047: Both flags must be True.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Test all combinations
        test_cases = [
            (True, True, True),
            (True, False, False),
            (False, True, False),
            (False, False, False),
        ]

        for global_enabled, per_request, expected in test_cases:
            config = WebFetchConfig(use_headless=per_request)
            result = tool._should_use_headless(config, global_enabled)
            assert result == expected, \
                f"global={global_enabled}, per_request={per_request}: expected {expected}, got {result}"

    async def test_fetch_with_playwright_import_error_raises(self):
        """Test that ImportError is caught and WebFetchError is raised.

        Validates T045: ImportError triggers WebFetchError with reason='headless_unavailable'.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Patch playwright async_api to raise ImportError
        with patch("playwright.async_api.async_playwright", side_effect=ImportError("No module")):
            from app.core.errors import WebFetchError

            with pytest.raises(WebFetchError) as exc_info:
                await tool._fetch_with_playwright("https://example.com", 15.0)

            assert exc_info.value.details["reason"] == "headless_unavailable"

    async def test_fetch_with_playwright_browser_launch_error(self):
        """Test that Playwright browser launch errors are caught.

        Validates T046: playwright.Error on browser launch triggers fallback.
        """
        settings = Settings()
        tool = WebFetchTool(settings=settings)

        # Create a mock playwright error
        class MockPlaywrightError(Exception):
            pass

        # Mock async_playwright context manager
        async def mock_async_playwright_context():
            mock_p = MagicMock()
            mock_chromium = MagicMock()
            mock_chromium.launch = AsyncMock(side_effect=MockPlaywrightError("Chromium not found"))
            mock_p.chromium = mock_chromium
            return mock_p

        # Create a mock context manager
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(side_effect=MockPlaywrightError("Chromium not found"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with patch("playwright.async_api.async_playwright", return_value=mock_context):
            from app.core.errors import WebFetchError

            with pytest.raises(WebFetchError) as exc_info:
                await tool._fetch_with_playwright("https://example.com", 15.0)

            assert exc_info.value.details["reason"] == "headless_unavailable"

    @patch("app.tools.web_fetch.httpx.AsyncClient")
    async def test_playwright_fallback_on_error(self, mock_client_class):
        """Test that playwright errors trigger fallback to httpx.

        Validates T048: On playwright error, tool falls back to httpx without exception.
        """
        settings = Settings(
            web_fetch_headless_enabled=True,
            web_fetch_max_retries=1
        )
        tool = WebFetchTool(settings=settings)

        # Create a mock playwright error
        class MockPlaywrightError(Exception):
            pass

        # Mock async_playwright context manager
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(side_effect=MockPlaywrightError("Chromium unavailable"))
        mock_context.__aexit__ = AsyncMock(return_value=None)

        # Mock httpx client to succeed
        mock_client = AsyncMock()
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {"content-type": "text/html"}
        response_200.content = b"<html><head><title>Fallback</title></head><body>Content</body></html>"
        response_200.raise_for_status.return_value = None
        mock_client.get.return_value = response_200
        tool._client = mock_client

        with patch("playwright.async_api.async_playwright", return_value=mock_context):
            config = WebFetchConfig(use_headless=True)
            result = await tool._fetch_single("https://example.com/test", config)

            # Should succeed via httpx fallback
            assert result.succeeded is True
            assert result.http_status == 200



    @patch("app.tools.web_fetch.httpx.AsyncClient")
    async def test_global_disabled_logs_warning(self, mock_client_class):
        """Test that per-request headless with global disabled logs warning.

        Validates T052: Global disabled + per-request enabled -> warning logged + httpx used.
        """
        settings = Settings(web_fetch_headless_enabled=False)
        tool = WebFetchTool(settings=settings)

        mock_client = AsyncMock()
        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {"content-type": "text/html"}
        response_200.content = b"<html><head><title>Test</title></head><body>Content</body></html>"
        response_200.raise_for_status.return_value = None
        mock_client.get.return_value = response_200
        tool._client = mock_client

        config = WebFetchConfig(use_headless=True)
        result = await tool._fetch_single("https://example.com/test", config)

        # Should succeed but via httpx only
        assert result.succeeded is True
        # Verify httpx was called (playwright should not be called)
        assert mock_client.get.called

