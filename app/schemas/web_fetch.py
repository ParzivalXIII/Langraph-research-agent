"""Web Fetch and HTML Scraping Schemas.

Pydantic v2 models for WebFetchTool request/response contracts.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WebFetchConfig(BaseModel):
    """Configuration for a web fetch operation."""

    output_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'",
    )
    use_headless: bool = Field(
        default=False,
        description="Use Playwright headless browser for JS-rendered pages",
    )
    max_content_chars: int = Field(
        default=50000,
        description="Max characters to extract from page content",
    )
    timeout_seconds: int = Field(
        default=15,
        description="HTTP request timeout in seconds",
    )
    include_links: bool = Field(
        default=True,
        description="Include extracted links in JSON output",
    )


class WebFetchRequest(BaseModel):
    """Request to fetch and extract content from URLs."""

    urls: list[str] = Field(
        min_length=1,
        max_length=50,
        description="List of URLs to fetch (1-50 URLs)",
    )
    config: WebFetchConfig = Field(
        default_factory=WebFetchConfig,
        description="Fetch configuration",
    )


class FetchedPage(BaseModel):
    """Result of fetching a single URL."""

    url: str = Field(description="Original URL")
    title: Optional[str] = Field(default=None, description="Page title")
    content: Optional[str] = Field(default=None, description="Extracted page content")
    content_type: Optional[str] = Field(
        default=None, description="Content-Type header value"
    )
    fetched_at: datetime = Field(description="When the page was fetched")
    http_status: Optional[int] = Field(default=None, description="HTTP status code")
    processing_ms: int = Field(default=0, description="Processing time in milliseconds")
    content_length: int = Field(
        default=0, ge=0, description="Length of extracted content in bytes"
    )
    content_truncated: bool = Field(
        default=False, description="Whether content was truncated"
    )
    empty_extraction: bool = Field(
        default=False, description="Whether extraction produced no content"
    )
    error: Optional[str] = Field(default=None, description="Error reason if fetch failed")

    @property
    def succeeded(self) -> bool:
        """Check if fetch succeeded."""
        return self.error is None


class WebFetchResult(BaseModel):
    """Aggregate result from batch fetch operation."""

    requested_count: int = Field(description="Number of URLs requested")
    fetched_count: int = Field(description="Number of URLs fetched successfully")
    failed_count: int = Field(description="Number of URLs that failed")
    total_ms: int = Field(description="Total time in milliseconds")
    pages: list[FetchedPage] = Field(description="Fetched page results")
