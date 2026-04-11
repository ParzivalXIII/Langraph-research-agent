"""Web Fetch Tool for enriching search results with full-page content.

This module provides WebFetchTool, which fetches and extracts content from
URLs to enrich research retrieval results.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from app.core.config import Settings, get_settings
from app.core.errors import WebFetchError
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

    async def _fetch_single(
        self,
        url: str,
        config: WebFetchConfig,
    ) -> FetchedPage:
        """Fetch content from a single URL.

        Args:
            url: URL to fetch
            config: Fetch configuration

        Returns:
            FetchedPage with content or error
        """
        start_time = time.monotonic()
        client = await self._get_client()

        try:
            self.logger.info(
                "web_fetch_start",
                url=url,
                output_format=config.output_format,
            )

            response = await client.get(
                url,
                timeout=config.timeout_seconds,
            )
            response.raise_for_status()

            http_status = response.status_code
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
                    content = await self._extract_markdown(content_bytes, config.max_content_chars)
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
        except httpx.RedirectLoop:
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

