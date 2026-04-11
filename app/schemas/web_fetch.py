"""Web Fetch and HTML Scraping Schemas.

Pydantic v2 models for WebFetchTool request/response contracts.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class WebFetchConfig(BaseModel):
    """Configuration for a web fetch operation.

    Specifies output format, content limits, timeouts, and advanced options
    like headless browser rendering for JavaScript-heavy pages.

    Attributes:
        output_format: Output format ('markdown' or 'json'). Default: 'markdown'
        use_headless: Use Playwright headless browser for JS-rendered content.
                     Requires global web_fetch_headless_enabled=True. Default: False
        max_content_chars: Maximum characters to extract (100-50000). Default: 5000
        timeout_seconds: HTTP request timeout in seconds (1-120). Default: 15.0
        include_links: Include extracted links in JSON output. Default: False

    Example:
        >>> config = WebFetchConfig(output_format="markdown", max_content_chars=3000)
        >>> config.output_format
        'markdown'
    """

    output_format: str = Field(
        default="markdown",
        description="Output format: 'markdown' or 'json'",
    )
    use_headless: bool = Field(
        default=False,
        description="Use Playwright headless browser for JS-rendered pages",
    )
    max_content_chars: int = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Max characters to extract from page content (100-50000)",
    )
    timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=120.0,
        description="HTTP request timeout in seconds (1-120)",
    )
    include_links: bool = Field(
        default=False,
        description="Include extracted links in JSON output",
    )

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output_format is either markdown or json."""
        if v not in ("markdown", "json"):
            raise ValueError("output_format must be 'markdown' or 'json'")
        return v


class WebFetchRequest(BaseModel):
    """Request to fetch and extract content from URLs.

    Encapsulates a batch of URLs and shared configuration for web fetching.
    Validates URLs are valid HTTP/HTTPS and batch size is within limits (1-50).

    Attributes:
        urls: List of URLs to fetch (1-50 URLs required)
        config: Fetch configuration including format, timeout, and limits

    Raises:
        ValueError: If URLs are invalid, empty, or batch exceeds 50 URLs

    Example:
        >>> request = WebFetchRequest(
        ...     urls=["https://example.com", "https://github.com"],
        ...     config=WebFetchConfig(output_format="markdown")
        ... )
        >>> len(request.urls)
        2
    """

    urls: list[str] = Field(
        min_length=1,
        max_length=50,
        description="List of URLs to fetch (1-50 URLs)",
    )
    config: WebFetchConfig = Field(
        default_factory=WebFetchConfig,
        description="Fetch configuration",
    )

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        """Validate URLs are non-empty strings and have http/https scheme."""
        for url in v:
            if not url or not isinstance(url, str):
                raise ValueError("All URLs must be non-empty strings")
            if not re.match(r"^https?://", url, re.IGNORECASE):
                raise ValueError(
                    f"URL must be a valid HTTP/HTTPS URL: {url!r} (must start with http:// or https://)"
                )
        return v


class FetchedPage(BaseModel):
    """Result of fetching and extracting content from a single URL.

    Represents the outcome of a single fetch operation, including extracted
    content, metadata, and any error information. The `succeeded` property
    indicates whether the fetch was successful.

    Attributes:
        url: Original URL that was fetched
        title: Page title extracted from <title> or <h1> tag (None if unavailable)
        content: Extracted page content as markdown or JSON string (None if failed)
        content_type: Content-Type header from HTTP response
        fetched_at: ISO 8601 timestamp when page was successfully fetched
        http_status: HTTP status code (e.g., 200, 404, 500)
        processing_ms: Time spent extracting and converting content
        content_length: Byte length of extracted content
        content_truncated: Whether content was truncated to max_content_chars
        empty_extraction: Whether extraction produced zero content
        error: Error reason if fetch failed (e.g., 'timeout', 'http_error', 'parse_error')

    Properties:
        succeeded: bool - Returns True if error is None, False otherwise

    Example:
        >>> page = FetchedPage(
        ...     url="https://example.com",
        ...     title="Example Domain",
        ...     content="# Example Domain",
        ...     fetched_at=datetime.now(),
        ...     http_status=200,
        ... )
        >>> page.succeeded
        True
    """

    url: str = Field(description="Original URL")
    title: Optional[str] = Field(default=None, description="Page title")
    content: Optional[str] = Field(default=None, description="Extracted page content")
    content_type: Optional[str] = Field(default=None, description="Content-Type header value")
    fetched_at: datetime = Field(description="When the page was fetched")
    http_status: Optional[int] = Field(default=None, description="HTTP status code")
    processing_ms: int = Field(default=0, ge=0, description="Processing time in milliseconds")
    content_length: int = Field(default=0, ge=0, description="Length of extracted content in bytes")
    content_truncated: bool = Field(default=False, description="Whether content was truncated")
    empty_extraction: bool = Field(
        default=False, description="Whether extraction produced no content"
    )
    error: Optional[str] = Field(default=None, description="Error reason if fetch failed")

    @property
    def succeeded(self) -> bool:
        """Check if fetch succeeded."""
        return self.error is None


class WebFetchResult(BaseModel):
    """Aggregate result from batch fetch operation.

    Encapsulates the results of fetching multiple URLs in a single batch.
    Contains individual FetchedPage results along with aggregate metrics
    (success/failure counts, total processing time).

    Validates that counts are internally consistent:
    fetched_count + failed_count == requested_count and pages list length
    matches requested_count.

    Attributes:
        requested_count: Total number of URLs requested
        fetched_count: Number of URLs successfully fetched (error is None)
        failed_count: Number of URLs that failed to fetch
        total_ms: Total elapsed time in milliseconds for the batch operation
        pages: List of FetchedPage results (one per requested URL, in order)

    Properties:
        success_rate: float - Percentage of successful fetches (0.0-100.0)

    Example:
        >>> result = WebFetchResult(
        ...     requested_count=3,
        ...     fetched_count=2,
        ...     failed_count=1,
        ...     total_ms=5000,
        ...     pages=[...]
        ... )
        >>> result.fetched_count / result.requested_count
        0.6666...
    """

    requested_count: int = Field(ge=0, description="Number of URLs requested")
    fetched_count: int = Field(ge=0, description="Number of URLs fetched successfully")
    failed_count: int = Field(ge=0, description="Number of URLs that failed")
    total_ms: int = Field(ge=0, description="Total time in milliseconds")
    pages: list[FetchedPage] = Field(description="Fetched page results")

    @model_validator(mode="after")
    def validate_count_consistency(self) -> "WebFetchResult":
        """Validate that counts are consistent with pages list."""
        if self.fetched_count + self.failed_count != self.requested_count:
            raise ValueError(
                f"Count mismatch: fetched ({self.fetched_count}) + "
                f"failed ({self.failed_count}) != requested ({self.requested_count})"
            )
        if len(self.pages) != self.requested_count:
            raise ValueError(
                f"Pages count mismatch: {len(self.pages)} pages != "
                f"requested_count ({self.requested_count})"
            )
        return self
