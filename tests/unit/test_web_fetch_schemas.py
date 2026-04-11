"""Unit tests for web fetch schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.web_fetch import (
    WebFetchConfig,
    WebFetchRequest,
    FetchedPage,
    WebFetchResult,
)


class TestWebFetchConfig:
    """Tests for WebFetchConfig schema."""

    def test_default_config(self):
        """Test WebFetchConfig with default values."""
        cfg = WebFetchConfig()
        assert cfg.output_format == "markdown"
        assert cfg.use_headless is False
        assert cfg.max_content_chars == 5000
        assert cfg.timeout_seconds == 15.0
        assert cfg.include_links is False

    def test_custom_config(self):
        """Test WebFetchConfig with custom values."""
        cfg = WebFetchConfig(
            output_format="json",
            use_headless=True,
            max_content_chars=25000,
            timeout_seconds=30.0,
            include_links=True,
        )
        assert cfg.output_format == "json"
        assert cfg.use_headless is True
        assert cfg.max_content_chars == 25000
        assert cfg.timeout_seconds == 30.0
        assert cfg.include_links is True

    def test_invalid_output_format(self):
        """Test that invalid output_format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WebFetchConfig(output_format="xml")
        assert "output_format must be 'markdown' or 'json'" in str(exc_info.value)

    def test_max_content_chars_bounds(self):
        """Test max_content_chars validation."""
        # Valid upper bound
        cfg = WebFetchConfig(max_content_chars=50000)
        assert cfg.max_content_chars == 50000

        # Invalid: too small
        with pytest.raises(ValidationError):
            WebFetchConfig(max_content_chars=50)

        # Invalid: too large
        with pytest.raises(ValidationError):
            WebFetchConfig(max_content_chars=100000)

    def test_timeout_seconds_bounds(self):
        """Test timeout_seconds validation."""
        # Valid
        cfg = WebFetchConfig(timeout_seconds=60.0)
        assert cfg.timeout_seconds == 60.0

        # Invalid: too small
        with pytest.raises(ValidationError):
            WebFetchConfig(timeout_seconds=0.5)

        # Invalid: too large
        with pytest.raises(ValidationError):
            WebFetchConfig(timeout_seconds=200.0)

    def test_config_json_serialization(self):
        """Test config can serialize to/from JSON."""
        cfg = WebFetchConfig(output_format="json", timeout_seconds=20.0)
        json_data = cfg.model_dump_json()
        cfg2 = WebFetchConfig.model_validate_json(json_data)
        assert cfg2.output_format == "json"
        assert cfg2.timeout_seconds == 20.0


class TestWebFetchRequest:
    """Tests for WebFetchRequest schema."""

    def test_single_url(self):
        """Test WebFetchRequest with single URL."""
        req = WebFetchRequest(urls=["https://example.com"])
        assert len(req.urls) == 1
        assert req.urls[0] == "https://example.com"
        assert req.config.output_format == "markdown"

    def test_max_urls(self):
        """Test WebFetchRequest with 50 URLs (max)."""
        urls = [f"https://example{i}.com" for i in range(50)]
        req = WebFetchRequest(urls=urls)
        assert len(req.urls) == 50

    def test_too_many_urls(self):
        """Test that >50 URLs raises ValidationError."""
        urls = [f"https://example{i}.com" for i in range(51)]
        with pytest.raises(ValidationError):
            WebFetchRequest(urls=urls)

    def test_empty_urls(self):
        """Test that empty URL list raises ValidationError."""
        with pytest.raises(ValidationError):
            WebFetchRequest(urls=[])

    def test_empty_url_string(self):
        """Test that empty string URL raises ValidationError."""
        with pytest.raises(ValidationError):
            WebFetchRequest(urls=[""])

    def test_custom_config(self):
        """Test WebFetchRequest with custom config."""
        cfg = WebFetchConfig(output_format="json", timeout_seconds=30)
        req = WebFetchRequest(urls=["https://example.com"], config=cfg)
        assert req.config.output_format == "json"
        assert req.config.timeout_seconds == 30

    def test_request_json_round_trip(self):
        """Test request serialization and deserialization."""
        req = WebFetchRequest(
            urls=["https://example1.com", "https://example2.com"],
            config=WebFetchConfig(output_format="json"),
        )
        json_data = req.model_dump_json()
        req2 = WebFetchRequest.model_validate_json(json_data)
        assert req2.urls == req.urls
        assert req2.config.output_format == "json"


class TestFetchedPage:
    """Tests for FetchedPage schema."""

    def test_minimal_success_page(self):
        """Test minimal successful fetch."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            fetched_at=now,
        )
        assert page.url == "https://example.com"
        assert page.title is None
        assert page.content is None
        assert page.error is None
        assert page.succeeded is True

    def test_success_page_with_content(self):
        """Test successful fetch with content."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            title="Example Page",
            content="# Example\n\nThis is content.",
            http_status=200,
            content_type="text/html",
            fetched_at=now,
            processing_ms=100,
            content_length=28,
        )
        assert page.succeeded is True
        assert page.title == "Example Page"
        assert page.content_length == 28

    def test_failed_page(self):
        """Test failed fetch with error."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            fetched_at=now,
            error="timeout",
        )
        assert page.succeeded is False
        assert page.error == "timeout"

    def test_truncated_content(self):
        """Test page with truncated content."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            fetched_at=now,
            content="truncated",
            content_truncated=True,
            content_length=9,
        )
        assert page.content_truncated is True

    def test_empty_extraction(self):
        """Test page with empty extraction."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            fetched_at=now,
            empty_extraction=True,
        )
        assert page.empty_extraction is True
        assert page.succeeded is True  # extraction failed but fetch succeeded

    def test_page_json_round_trip(self):
        """Test page serialization and deserialization."""
        now = datetime.now()
        page = FetchedPage(
            url="https://example.com",
            title="Test",
            content="Test content",
            http_status=200,
            fetched_at=now,
            processing_ms=50,
            content_length=12,
        )
        json_data = page.model_dump_json()
        page2 = FetchedPage.model_validate_json(json_data)
        assert page2.url == page.url
        assert page2.title == page.title
        assert page2.http_status == page.http_status


class TestWebFetchResult:
    """Tests for WebFetchResult schema."""

    def test_minimal_result(self):
        """Test minimal result with one page."""
        now = datetime.now()
        page = FetchedPage(url="https://example.com", fetched_at=now)
        result = WebFetchResult(
            requested_count=1,
            fetched_count=1,
            failed_count=0,
            total_ms=100,
            pages=[page],
        )
        assert result.requested_count == 1
        assert result.fetched_count == 1
        assert result.failed_count == 0

    def test_mixed_result_success_and_failures(self):
        """Test result with both successful and failed fetches."""
        now = datetime.now()
        pages = [
            FetchedPage(url="https://example1.com", title="Page1", fetched_at=now),
            FetchedPage(url="https://example2.com", title="Page2", fetched_at=now),
            FetchedPage(url="https://example3.com", error="timeout", fetched_at=now),
        ]
        result = WebFetchResult(
            requested_count=3,
            fetched_count=2,
            failed_count=1,
            total_ms=300,
            pages=pages,
        )
        assert result.requested_count == 3
        assert result.fetched_count == 2
        assert result.failed_count == 1
        assert len(result.pages) == 3

    def test_count_mismatch_validation(self):
        """Test that count mismatch raises ValidationError."""
        now = datetime.now()
        pages = [
            FetchedPage(url="https://example1.com", fetched_at=now),
            FetchedPage(url="https://example2.com", fetched_at=now),
        ]
        # Requested 3 but fetched+failed = 2+1=3 but only 2 pages
        with pytest.raises(ValidationError) as exc_info:
            WebFetchResult(
                requested_count=3,
                fetched_count=2,
                failed_count=1,
                total_ms=100,
                pages=pages,
            )
        # Will catch pages count mismatch first
        assert ("Count mismatch" in str(exc_info.value) or 
                "Pages count mismatch" in str(exc_info.value))

    def test_pages_count_mismatch_validation(self):
        """Test that pages count mismatch raises ValidationError."""
        now = datetime.now()
        pages = [
            FetchedPage(url="https://example1.com", fetched_at=now),
            FetchedPage(url="https://example2.com", fetched_at=now),
        ]
        # Requested 3 but only 2 pages
        with pytest.raises(ValidationError) as exc_info:
            WebFetchResult(
                requested_count=3,
                fetched_count=2,
                failed_count=1,
                total_ms=100,
                pages=pages,
            )
        assert "Pages count mismatch" in str(exc_info.value)

    def test_result_json_round_trip(self):
        """Test result serialization and deserialization."""
        now = datetime.now()
        pages = [
            FetchedPage(
                url="https://example.com",
                title="Test",
                content="Test",
                fetched_at=now,
            ),
        ]
        result = WebFetchResult(
            requested_count=1,
            fetched_count=1,
            failed_count=0,
            total_ms=100,
            pages=pages,
        )
        json_data = result.model_dump_json()
        result2 = WebFetchResult.model_validate_json(json_data)
        assert result2.requested_count == result.requested_count
        assert result2.fetched_count == result.fetched_count
        assert len(result2.pages) == 1

    def test_large_batch_result(self):
        """Test result with 50 URLs (max batch)."""
        now = datetime.now()
        pages = [
            FetchedPage(
                url=f"https://example{i}.com",
                title=f"Page {i}",
                content=f"Content {i}",
                fetched_at=now,
            )
            for i in range(50)
        ]
        result = WebFetchResult(
            requested_count=50,
            fetched_count=50,
            failed_count=0,
            total_ms=5000,
            pages=pages,
        )
        assert result.requested_count == 50
        assert len(result.pages) == 50

    def test_all_failed_batch(self):
        """Test result where all fetches failed."""
        now = datetime.now()
        pages = [
            FetchedPage(url=f"https://example{i}.com", error="timeout", fetched_at=now)
            for i in range(5)
        ]
        result = WebFetchResult(
            requested_count=5,
            fetched_count=0,
            failed_count=5,
            total_ms=1000,
            pages=pages,
        )
        assert result.failed_count == 5
        assert all(not page.succeeded for page in result.pages)
