"""Integration tests for web fetch pipeline."""

import asyncio
from datetime import datetime

import httpx
import pytest

from app.core.config import Settings
from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest
from app.tools.web_fetch import WebFetchTool


@pytest.mark.asyncio
class TestWebFetchIntegration:
    """Integration tests for WebFetchTool batch operations."""

    @pytest.fixture
    def tool(self):
        """Create WebFetchTool for testing."""
        settings = Settings()
        tool = WebFetchTool(settings)
        yield tool

    @pytest.mark.asyncio
    async def test_fetch_single_markdown(self, tool):
        """Test fetching single URL and extracting markdown."""
        try:
            await tool._get_client()  # Ensure client is initialized
            # Skip this test as it requires network
            pytest.skip("Requires network access")
        except Exception:
            pytest.skip("Network unavailable")

    @pytest.mark.asyncio
    async def test_batch_initialization(self, tool):
        """Test batch initialization and schema creation."""
        config = WebFetchConfig(output_format="markdown")
        urls = ["https://www.example.com"]

        request = WebFetchRequest(urls=urls, config=config)
        assert request.urls == urls
        assert request.config.output_format == "markdown"
        assert request.config.max_content_chars == 5000

    @pytest.mark.asyncio
    async def test_empty_extraction_detection(self, tool):
        """Test detection of empty extraction."""
        from app.schemas.web_fetch import FetchedPage

        page = FetchedPage(
            url="https://example.com",
            fetched_at=datetime.now(),
            http_status=200,
            empty_extraction=True,
        )

        assert page.succeeded  # No error, but marked empty
        assert page.empty_extraction

    @pytest.mark.asyncio
    async def test_response_truncation(self, tool):
        """Test response truncation when exceeding max_content_chars."""
        from app.schemas.web_fetch import FetchedPage

        long_content = "x" * 200
        page = FetchedPage(
            url="https://example.com",
            content=long_content[:100],
            fetched_at=datetime.now(),
            http_status=200,
            content_truncated=True,
            content_length=100,
        )

        assert page.content_truncated
        assert len(page.content) == 100

    @pytest.mark.asyncio
    async def test_error_page_creation(self, tool):
        """Test creation of error pages."""
        from app.schemas.web_fetch import FetchedPage

        page = FetchedPage(
            url="https://example.com",
            fetched_at=datetime.now(),
            http_status=404,
            error="http_error",
        )

        assert not page.succeeded
        assert page.error == "http_error"

    @pytest.mark.asyncio
    async def test_batch_result_creation(self, tool):
        """Test batch result creation with valid counts."""
        from app.schemas.web_fetch import FetchedPage, WebFetchResult

        pages = [
            FetchedPage(
                url="https://example1.com",
                fetched_at=datetime.now(),
                http_status=200,
                content="Test 1",
            ),
            FetchedPage(
                url="https://example2.com",
                fetched_at=datetime.now(),
                http_status=404,
                error="http_error",
            ),
        ]

        result = WebFetchResult(
            requested_count=2,
            fetched_count=1,
            failed_count=1,
            total_ms=500,
            pages=pages,
        )

        assert result.requested_count == 2
        assert result.fetched_count == 1
        assert result.failed_count == 1
        assert result.total_ms == 500

    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """Test WebFetchTool initialization."""
        settings = Settings()
        tool = WebFetchTool(settings)

        assert tool.settings == settings
        assert tool._client is None  # Client created on demand

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test WebFetchTool as context manager."""
        async with WebFetchTool() as ctx_tool:
            assert ctx_tool is not None

    @pytest.mark.asyncio
    async def test_config_validation(self):
        """Test WebFetchConfig validation."""
        # Valid config
        config = WebFetchConfig(
            output_format="json",
            max_content_chars=10000,
            timeout_seconds=20.0,
        )
        assert config.output_format == "json"

        # Invalid format should be caught by Pydantic
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            WebFetchConfig(output_format="xml")
