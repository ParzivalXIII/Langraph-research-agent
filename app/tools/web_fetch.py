"""Web Fetch Tool for enriching search results with full-page content.

This module provides WebFetchTool, which fetches and extracts content from
URLs to enrich research retrieval results. Supports both plain HTTP and
optional Playwright-based headless browser fetching for JS-rendered pages.
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.schemas.web_fetch import (
    FetchedPage,
    WebFetchConfig,
    WebFetchRequest,
    WebFetchResult,
)

logger = get_logger(__name__)


class WebFetchTool:
    """Fetch full-page content from URLs and extract markdown or JSON.

    This tool enriches Tavily search results by fetching the full page
    content for each URL and extracting clean markdown or structured JSON.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
    ):
        """Initialize WebFetchTool with configuration and HTTP client.

        Args:
            settings: Application settings (injected for testing)
        """
        self.settings = settings or get_settings()
        self.logger = logger
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: dict[str, float] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx AsyncClient.

        Returns:
            httpx.AsyncClient instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.settings.web_fetch_timeout_seconds,
                follow_redirects=True,
                limits=httpx.Limits(max_redirects=5),
            )
        return self._client

    def _parse_domain(self, url: str) -> str:
        """Extract domain from URL for rate-limit bucketing.

        Args:
            url: URL to parse

        Returns:
            Domain (netloc) from the URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url

    async def _wait_for_domain_rate_limit(
        self,
        domain: str,
        per_domain_limit: float,
    ) -> None:
        """Enforce per-domain rate limit using monotonic clock.

        Maintains spacing of at least 1/per_domain_limit seconds between
        requests to the same domain.

        Args:
            domain: Domain to rate-limit
            per_domain_limit: Requests per second (e.g., 1.0 = 1 req/s)
        """
        if per_domain_limit <= 0:
            return

        rate_limit_interval = 1.0 / per_domain_limit
        current_time = time.monotonic()
        last_time = self._last_request_time.get(domain, 0)

        if last_time > 0:
            elapsed = current_time - last_time
            if elapsed < rate_limit_interval:
                wait_time = rate_limit_interval - elapsed
                self.logger.info(
                    "rate_limit_wait",
                    domain=domain,
                    wait_ms=int(wait_time * 1000),
                )
                await asyncio.sleep(wait_time)

        # Update last request time
        self._last_request_time[domain] = time.monotonic()

    def _should_retry(
        self,
        http_status: Optional[int],
        error: Optional[str],
        retries_left: int,
    ) -> bool:
        """Determine if a request should be retried.

        Retries on 429 (Too Many Requests) and 5xx errors if retries remain.

        Args:
            http_status: HTTP status code (None if connection error)
            error: Error reason string
            retries_left: Number of retries remaining

        Returns:
            True if request should be retried
        """
        if retries_left <= 0:
            return False

        # Retry on rate limit (429) and server errors (5xx)
        if http_status is not None:
            return 429 <= http_status < 600

        # Retry on some transient errors
        if error in ("timeout", "fetch_error"):
            return True

        return False

    def _get_retry_after(self, response: Optional[httpx.Response]) -> Optional[float]:
        """Parse Retry-After header from response.

        Supports both delay-seconds and HTTP-date formats.

        Args:
            response: HTTP response object

        Returns:
            Delay in seconds, or None if no Retry-After header
        """
        if response is None:
            return None

        retry_after = response.headers.get("retry-after")
        if not retry_after:
            return None

        try:
            # Try parsing as seconds (most common)
            return float(retry_after)
        except ValueError:
            # Could be an HTTP-date, but we'll just use a default for now
            return None

    async def _fetch_with_playwright(
        self,
        url: str,
        timeout: float,
    ) -> bytes:
        """Fetch a URL using Playwright's headless browser.

        Renders JavaScript and returns the fully rendered HTML as bytes.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content as bytes

        Raises:
            WebFetchError: If import fails or browser cannot launch
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            from app.core.errors import WebFetchError

            raise WebFetchError(
                message="Playwright not available for headless fetching",
                status_code=0,
                details={"reason": "headless_unavailable", "url": url},
            )

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
                    content = await page.content()
                    return content.encode("utf-8")
                finally:
                    await page.close()
                    await browser.close()
        except Exception as e:
            from app.core.errors import WebFetchError

            self.logger.warning(
                "playwright_launch_failed",
                url=url,
                error=str(e),
            )
            raise WebFetchError(
                message=f"Playwright browser failed: {str(e)}",
                status_code=0,
                details={"reason": "headless_unavailable", "url": url},
            )

    def _should_use_headless(
        self,
        config: WebFetchConfig,
        global_enabled: bool,
    ) -> bool:
        """Determine if headless browser should be used for this request.

        Requires both global setting AND per-request config to be True.

        Args:
            config: Per-request configuration
            global_enabled: Global setting for headless support

        Returns:
            True if headless browser should be used
        """
        return global_enabled and config.use_headless


    async def _fetch_single(
        self,
        url: str,
        config: WebFetchConfig,
    ) -> FetchedPage:
        """Fetch content from a single URL with rate limiting and retries.

        Args:
            url: URL to fetch
            config: Fetch configuration

        Returns:
            FetchedPage with content or error
        """
        start_time = time.monotonic()
        client = await self._get_client()
        domain = self._parse_domain(url)
        max_retries = self.settings.web_fetch_max_retries
        retry_backoff = self.settings.web_fetch_retry_backoff
        per_domain_limit = self.settings.web_fetch_per_domain_rate_limit

        self.logger.info(
            "web_fetch_start",
            url=url,
            output_format=config.output_format,
        )

        # Determine if we should try headless browser
        should_try_headless = self._should_use_headless(
            config, self.settings.web_fetch_headless_enabled
        )

        # Try headless browser first if enabled
        if should_try_headless:
            try:
                # Wait for rate limit before playwright attempt
                await self._wait_for_domain_rate_limit(domain, per_domain_limit)

                self.logger.info(
                    "web_fetch_playwright_attempt",
                    url=url,
                    using_playwright=True,
                )

                content_bytes = await self._fetch_with_playwright(
                    url, config.timeout_seconds
                )

                # Process the content as we would for httpx response
                return await self._process_content(
                    url=url,
                    content_bytes=content_bytes,
                    http_status=200,
                    config=config,
                    start_time=start_time,
                )
            except Exception as e:
                # Fallback to httpx
                self.logger.warning(
                    "web_fetch_playwright_fallback",
                    url=url,
                    error=str(e),
                    headless_fallback_reason=str(type(e).__name__),
                )
        else:
            if config.use_headless and not self.settings.web_fetch_headless_enabled:
                self.logger.warning(
                    "web_fetch_headless_disabled",
                    url=url,
                    reason="global_setting_disabled",
                    using_playwright=False,
                )

        # Standard httpx path (primary or fallback)
        for attempt in range(max_retries + 1):
            try:
                # Wait for rate limit before each attempt
                await self._wait_for_domain_rate_limit(domain, per_domain_limit)

                response = await client.get(
                    url,
                    timeout=config.timeout_seconds,
                )

                http_status = response.status_code

                # Check if we should retry
                if self._should_retry(http_status, None, max_retries - attempt):
                    # Get retry delay
                    retry_after = self._get_retry_after(response)
                    if retry_after is not None:
                        delay = retry_after
                        self.logger.info(
                            "retry_attempt",
                            url=url,
                            attempt=attempt + 1,
                            reason=f"http_{http_status}",
                            wait_ms=int(delay * 1000),
                            wait_source="retry_after_header",
                        )
                    else:
                        # Exponential backoff with jitter
                        jitter = random.uniform(0, 0.1)
                        delay = (retry_backoff * (2 ** attempt)) + jitter
                        self.logger.info(
                            "retry_attempt",
                            url=url,
                            attempt=attempt + 1,
                            reason=f"http_{http_status}",
                            wait_ms=int(delay * 1000),
                            wait_source="exponential_backoff",
                        )

                    await asyncio.sleep(delay)
                    continue

                # Status OK, process the response
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")

                # Check for unsupported content types
                if not any(
                    ct in content_type.lower()
                    for ct in ("text/html", "application/xhtml", "text/plain")
                ):
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    self.logger.info(
                        "web_fetch_error",
                        url=url,
                        error_reason="unsupported_content_type",
                        content_type=content_type,
                        latency_ms=elapsed_ms,
                    )
                    return FetchedPage(
                        url=url,
                        fetched_at=datetime.now(),
                        http_status=http_status,
                        processing_ms=elapsed_ms,
                        error="unsupported_content_type",
                    )

                # Check response size
                content_bytes = response.content
                if len(content_bytes) > config.max_content_chars:
                    content_bytes = content_bytes[: config.max_content_chars]
                    truncated = True
                else:
                    truncated = False

                # Extract content based on format
                try:
                    if config.output_format == "markdown":
                        content = await self._extract_markdown(
                            content_bytes, config.max_content_chars
                        )
                    else:
                        content_dict = await self._extract_json(
                            content_bytes,
                            config.max_content_chars,
                            config.include_links,
                        )
                        content = str(content_dict)
                except Exception as e:
                    self.logger.info(
                        "web_fetch_error",
                        url=url,
                        error_reason="extraction_failed",
                        error=str(e),
                    )
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    return FetchedPage(
                        url=url,
                        fetched_at=datetime.now(),
                        http_status=http_status,
                        processing_ms=elapsed_ms,
                        error="extraction_failed",
                    )

                # Check if extraction was empty
                empty = not content or len(content.strip()) == 0

                elapsed_ms = int((time.monotonic() - start_time) * 1000)

                self.logger.info(
                    "web_fetch_complete",
                    url=url,
                    http_status=http_status,
                    extraction_format=config.output_format,
                    latency_ms=elapsed_ms,
                    content_length=len(content),
                    truncated=truncated,
                    empty=empty,
                )

                # Extract title from HTML
                try:
                    soup = BeautifulSoup(content_bytes, "html.parser")
                    title_tag = soup.find("title")
                    title = title_tag.get_text(strip=True) if title_tag else None
                except Exception:
                    title = None

                return FetchedPage(
                    url=url,
                    title=title,
                    content=content,
                    content_type=config.output_format,
                    fetched_at=datetime.now(),
                    http_status=http_status,
                    processing_ms=elapsed_ms,
                    content_length=len(content) if content else 0,
                    content_truncated=truncated,
                    empty_extraction=empty,
                    error=None,
                )

            except asyncio.TimeoutError:
                if self._should_retry(None, "timeout", max_retries - attempt):
                    jitter = random.uniform(0, 0.1)
                    delay = (retry_backoff * (2 ** attempt)) + jitter
                    self.logger.info(
                        "retry_attempt",
                        url=url,
                        attempt=attempt + 1,
                        reason="timeout",
                        wait_ms=int(delay * 1000),
                    )
                    await asyncio.sleep(delay)
                    continue

                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self.logger.info(
                    "web_fetch_error",
                    url=url,
                    error_reason="timeout",
                    latency_ms=elapsed_ms,
                )
                return FetchedPage(
                    url=url,
                    fetched_at=datetime.now(),
                    http_status=None,
                    processing_ms=elapsed_ms,
                    error="timeout",
                )

            except httpx.HTTPStatusError as e:
                retries_remaining = max_retries - attempt
                if self._should_retry(e.response.status_code, None, retries_remaining):
                    retry_after = self._get_retry_after(e.response)
                    if retry_after is not None:
                        delay = retry_after
                        self.logger.info(
                            "retry_attempt",
                            url=url,
                            attempt=attempt + 1,
                            reason=f"http_{e.response.status_code}",
                            wait_ms=int(delay * 1000),
                            wait_source="retry_after_header",
                        )
                    else:
                        jitter = random.uniform(0, 0.1)
                        delay = (retry_backoff * (2 ** attempt)) + jitter
                        self.logger.info(
                            "retry_attempt",
                            url=url,
                            attempt=attempt + 1,
                            reason=f"http_{e.response.status_code}",
                            wait_ms=int(delay * 1000),
                            wait_source="exponential_backoff",
                        )
                    await asyncio.sleep(delay)
                    continue

                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self.logger.info(
                    "web_fetch_error",
                    url=url,
                    error_reason="http_error",
                    http_status=e.response.status_code,
                    latency_ms=elapsed_ms,
                )
                return FetchedPage(
                    url=url,
                    fetched_at=datetime.now(),
                    http_status=e.response.status_code,
                    processing_ms=elapsed_ms,
                    error="http_error",
                )

            except httpx.TooManyRedirects:
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self.logger.info(
                    "web_fetch_error",
                    url=url,
                    error_reason="too_many_redirects",
                    latency_ms=elapsed_ms,
                )
                return FetchedPage(
                    url=url,
                    fetched_at=datetime.now(),
                    http_status=None,
                    processing_ms=elapsed_ms,
                    error="too_many_redirects",
                )

            except Exception as e:
                if self._should_retry(None, "fetch_error", max_retries - attempt):
                    jitter = random.uniform(0, 0.1)
                    delay = (retry_backoff * (2 ** attempt)) + jitter
                    self.logger.info(
                        "retry_attempt",
                        url=url,
                        attempt=attempt + 1,
                        reason="fetch_error",
                        wait_ms=int(delay * 1000),
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
                    continue

                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                self.logger.info(
                    "web_fetch_error",
                    url=url,
                    error_reason="fetch_error",
                    error=str(e),
                    latency_ms=elapsed_ms,
                )
                return FetchedPage(
                    url=url,
                    fetched_at=datetime.now(),
                    http_status=None,
                    processing_ms=elapsed_ms,
                    error="fetch_error",
                )

        # Should not reach here, but handle just in case
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return FetchedPage(
            url=url,
            fetched_at=datetime.now(),
            http_status=None,
            processing_ms=elapsed_ms,
            error="max_retries_exceeded",
        )

    async def _process_content(
        self,
        url: str,
        content_bytes: bytes,
        http_status: int,
        config: WebFetchConfig,
        start_time: float,
    ) -> FetchedPage:
        """Process fetched content (common logic for httpx and playwright).

        Args:
            url: The URL that was fetched
            content_bytes: Raw content bytes
            http_status: HTTP status code
            config: Fetch configuration
            start_time: Start time for elapsed calculation

        Returns:
            FetchedPage with processed content
        """
        # Check response size
        if len(content_bytes) > config.max_content_chars:
            content_bytes = content_bytes[: config.max_content_chars]
            truncated = True
        else:
            truncated = False

        # Extract content based on format
        try:
            if config.output_format == "markdown":
                content = await self._extract_markdown(
                    content_bytes, config.max_content_chars
                )
            else:
                content_dict = await self._extract_json(
                    content_bytes,
                    config.max_content_chars,
                    config.include_links,
                )
                content = str(content_dict)
        except Exception as e:
            self.logger.info(
                "web_fetch_error",
                url=url,
                error_reason="extraction_failed",
                error=str(e),
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return FetchedPage(
                url=url,
                fetched_at=datetime.now(),
                http_status=http_status,
                processing_ms=elapsed_ms,
                error="extraction_failed",
            )

        # Check if extraction was empty
        empty = not content or len(content.strip()) == 0

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        self.logger.info(
            "web_fetch_complete",
            url=url,
            http_status=http_status,
            extraction_format=config.output_format,
            latency_ms=elapsed_ms,
            content_length=len(content),
            truncated=truncated,
            empty=empty,
        )

        # Extract title from HTML
        try:
            soup = BeautifulSoup(content_bytes, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
        except Exception:
            title = None

        return FetchedPage(
            url=url,
            title=title,
            content=content,
            content_type=config.output_format,
            fetched_at=datetime.now(),
            http_status=http_status,
            processing_ms=elapsed_ms,
            content_length=len(content) if content else 0,
            content_truncated=truncated,
            empty_extraction=empty,
            error=None,
        )


    async def _extract_markdown(
        self,
        html_bytes: bytes,
        max_chars: int,
    ) -> str:
        """Extract markdown from HTML content.

        Args:
            html_bytes: Raw HTML bytes
            max_chars: Maximum characters to extract

        Returns:
            Markdown string
        """
        try:
            html_str = html_bytes.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_str, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract body or whole content
            content = soup.find("body") or soup
            markdown = markdownify(str(content), heading_style="underlined")

            # Clean up excessive whitespace
            lines = markdown.split("\n")
            cleaned = "\n".join(line.rstrip() for line in lines if line.strip())

            # Truncate if needed
            if len(cleaned) > max_chars:
                cleaned = cleaned[:max_chars] + "..."

            return cleaned
        except Exception as e:
            self.logger.error("markdown_extraction_failed", error=str(e))
            raise

    async def _extract_json(
        self,
        html_bytes: bytes,
        max_chars: int,
        include_links: bool = True,
    ) -> dict:
        """Extract JSON-structured content from HTML.

        Args:
            html_bytes: Raw HTML bytes
            max_chars: Maximum characters for body content
            include_links: Whether to include extracted links

        Returns:
            Dictionary with title, body, links
        """
        try:
            html_str = html_bytes.decode("utf-8", errors="ignore")
            soup = BeautifulSoup(html_str, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "No title"

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract body text
            body_elem = soup.find("body") or soup
            body_text = body_elem.get_text(separator=" ", strip=True)

            # Truncate body if needed
            if len(body_text) > max_chars:
                body_text = body_text[:max_chars] + "..."

            # Extract links if requested
            links = []
            if include_links:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href", "")
                    link_text = a_tag.get_text(strip=True)
                    if href and href.startswith(("http://", "https://", "/")):
                        links.append({"url": href, "text": link_text})

            return {
                "title": title,
                "body": body_text,
                "links": links,
            }
        except Exception as e:
            self.logger.error("json_extraction_failed", error=str(e))
            raise

    async def _feed_batch(
        self,
        urls: list[str],
        config: WebFetchConfig,
    ) -> list[FetchedPage]:
        """Orchestrate batch fetch using asyncio.gather.

        Args:
            urls: List of URLs to fetch
            config: Fetch configuration

        Returns:
            List of FetchedPage results
        """
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.settings.web_fetch_max_concurrency)

        async def fetch_with_semaphore(url: str) -> FetchedPage:
            async with semaphore:
                return await self._fetch_single(url, config)

        # Fetch all URLs concurrently
        results = await asyncio.gather(
            *[fetch_with_semaphore(url) for url in urls],
            return_exceptions=False,
        )

        return results

    async def fetch_batch(self, request: WebFetchRequest) -> WebFetchResult:
        """Fetch and extract content from a batch of URLs.

        Args:
            request: WebFetchRequest with URLs and configuration

        Returns:
            WebFetchResult with fetched pages and metadata
        """
        start_time = time.monotonic()
        urls = request.urls
        config = request.config

        self.logger.info(
            "web_fetch_batch_start",
            requested_count=len(urls),
            output_format=config.output_format,
        )

        try:
            # Fetch all URLs
            pages = await self._feed_batch(urls, config)

            # Count results
            fetched_count = sum(1 for page in pages if page.succeeded)
            failed_count = len(pages) - fetched_count
            total_ms = int((time.monotonic() - start_time) * 1000)

            self.logger.info(
                "web_fetch_batch_complete",
                requested_count=len(urls),
                fetched_count=fetched_count,
                failed_count=failed_count,
                total_ms=total_ms,
            )

            return WebFetchResult(
                requested_count=len(urls),
                fetched_count=fetched_count,
                failed_count=failed_count,
                total_ms=total_ms,
                pages=pages,
            )
        except Exception as e:
            self.logger.error(
                "web_fetch_batch_failed",
                error=str(e),
            )
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

