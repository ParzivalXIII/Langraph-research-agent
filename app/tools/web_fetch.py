"""Web Fetch Tool for enriching search results with full-page content.

This module provides WebFetchTool, which fetches and extracts content from
URLs to enrich research retrieval results.
"""

from app.schemas.web_fetch import WebFetchRequest, WebFetchResult


class WebFetchTool:
    """Fetch full-page content from URLs and extract markdown or JSON.

    This tool enriches Tavily search results by fetching the full page
    content for each URL and extracting clean markdown or structured JSON.
    """

    async def fetch_batch(self, request: WebFetchRequest) -> WebFetchResult:
        """Fetch and extract content from a batch of URLs.

        Args:
            request: WebFetchRequest with URLs and configuration

        Returns:
            WebFetchResult with fetched pages and metadata
        """
        raise NotImplementedError("fetch_batch not yet implemented")
