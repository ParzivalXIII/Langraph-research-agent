"""Tavily web search tool wrapper.

Provides async interface to Tavily API with error handling, result formatting,
and support for depth parameters (basic/intermediate/deep) mapped to search_depth.

From spec.md (§Evidence & Retrieval Plan):
- MVP Phase 1-2: Snippets only (from Tavily results)
- Phase 4: Full-text page fetching (deferred)

From data-model.md (§Tavily Parameters):
- basic (query only): search_depth="basic", max_results=5
- intermediate (standard): search_depth="advanced", max_results=10
- deep (comprehensive): search_depth="advanced", max_results=15
"""

import asyncio
from typing import Any
from functools import partial

from tavily import TavilyClient

from app.core.config import get_settings
from app.core.errors import TavilyError, retry_with_backoff
from app.core.logging import get_logger
from app.schemas.research import SourceRecord

logger = get_logger(__name__)

# Depth-to-parameter mapping from data-model.md
# IMPORTANT: search_depth must be "basic" or "advanced" (strings), not integers
DEPTH_PARAMETERS = {
    "basic": {"search_depth": "basic", "max_results": 5},
    "intermediate": {"search_depth": "advanced", "max_results": 10},
    "deep": {"search_depth": "advanced", "max_results": 15},
}


class TavilyTool:
    """Wrapper for Tavily web search with async support and error handling."""

    def __init__(self) -> None:
        """Initialize Tavily client with API key from settings."""
        self.client: Any = None  # TavilyClient or None
        settings = get_settings()
        if not settings.tavily_api_key:
            logger.warning(
                "tavily_api_key_not_configured",
                hint="Set TAVILY_API_KEY in .env for web search",
            )
        else:
            try:
                self.client = TavilyClient(api_key=settings.tavily_api_key)
            except Exception as exc:
                logger.error("tavily_client_initialization_error", error=str(exc))

    async def search(
        self,
        query: str,
        depth: str = "intermediate",
        max_sources: int = 10,
    ) -> list[SourceRecord]:
        """Search web using Tavily API and return structured SourceRecords.

        Maps depth parameter to Tavily search_depth and max_results according to
        data-model.md (§Tavily Parameters).

        Args:
            query: Search query string
            depth: Search depth (basic/intermediate/deep) from ResearchQuery
            max_sources: Maximum results to return (overrides depth default)

        Returns:
            List of SourceRecord objects with title, url, snippet content

        Raises:
            TavilyError: If API call fails after retries or if not configured
        """
        if not self.client:
            raise TavilyError(
                "Tavily client not configured. Set TAVILY_API_KEY environment variable.",
                status_code=None,
            )

        # Get depth parameters
        depth_params = DEPTH_PARAMETERS.get(depth, DEPTH_PARAMETERS["intermediate"])

        # Use max_sources if explicitly provided (override depth default)
        max_results: int = min(
            max_sources, max(depth_params["max_results"], max_sources)
        )

        logger.info(
            "tavily_search_start",
            query=query[:100],  # Log first 100 chars
            depth=depth,
            max_results=max_results,
        )

        try:
            # Wrap sync Tavily client call with retry logic using asyncio executor
            # Create a partial function with the search parameters pre-filled
            async def async_search() -> dict:
                """Wrap sync search in async context."""
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    partial(
                        self._sync_search,
                        query,
                        depth_params["search_depth"],
                        max_results,
                    ),
                )

            response = await retry_with_backoff(
                async_search, max_retries=3, base_delay=1.0
            )

            # Convert Tavily response to SourceRecords
            sources: list[SourceRecord] = []
            if isinstance(response, dict) and response is not None:
                results = response.get("results", [])
                for result in results:
                    try:
                        source = SourceRecord(
                            title=result.get("title", "Untitled"),
                            url=result.get("url", ""),
                            relevance=result.get(
                                "score", 0.0
                            ),  # Tavily returns 0-1 score
                            credibility_score=result.get(
                                "score", 0.5
                            ),  # Use Tavily score as initial credibility
                            snippet=result.get("content", ""),
                        )
                        sources.append(source)
                    except Exception as exc:
                        logger.warning(
                            "tavily_result_parse_error",
                            result=result,
                            error=str(exc),
                        )
                        continue

            logger.info(
                "tavily_search_complete",
                query=query[:100],
                sources_count=len(sources),
            )
            return sources

        except Exception as exc:
            logger.error(
                "tavily_search_failed",
                query=query[:100],
                error=str(exc),
            )
            raise TavilyError(
                f"Tavily search failed: {str(exc)}",
                status_code=getattr(exc, "status_code", None),
                details={"query": query},
            ) from exc

    def _sync_search(self, query: str, search_depth: str, max_results: int) -> dict:
        """Synchronous Tavily search wrapper (runs in retry loop).

        Args:
            query: Search query
            search_depth: Tavily search depth parameter (string: "basic" or "advanced")
            max_results: Maximum results to return

        Returns:
            Raw Tavily API response dict with 'results' key
        """
        if self.client is None:
            raise TavilyError(
                "Tavily client not initialized",
                status_code=None,
            )
        response = self.client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=False,  # Don't need Tavily's summarization
        )
        return response
