"""Unit tests for WebFetchTool."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

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
