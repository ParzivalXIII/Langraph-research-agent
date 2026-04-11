"""Retrieval service for fetching and scoring web sources.

Handles source fetching from Tavily API and applies credibility scoring
algorithm from data-model.md (§Source Credibility).

Credibility Score Formula (data-model.md):
  credibility_score = (0.50 × domain_authority) + (0.30 × recency_boost) + (0.20 × citation_count_normalized)

  Where:
  - domain_authority: 0.8 for well-known tech/news/academic domains, 0.5 default
  - recency_boost: 1.0 if source published today, 0.9 if this week, 0.7 if this month, 0.5 otherwise
  - citation_count_normalized: Normalized to 0-1 based on typical citation patterns

  Threshold: Sources with credibility_score < 0.65 get flagged for lower confidence

Depth Parameter Mapping (from data-model.md §Tavily Search Parameter Mapping):
  basic: search_depth="basic", max_results=5 (typical latency <30s)
  intermediate: search_depth="advanced", max_results=10 (typical latency <60s)
  deep: search_depth="advanced", max_results=15+ (typical latency <120s)

Time Range Filter Mapping (from data-model.md):
  day: filter to 1-day-old sources
  week: filter to <7 day old sources
  month: filter to <30 day old sources
  year: filter to <365 day old sources
  all: no date filter
"""

from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.research import SourceRecord
from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest
from app.tools.tavily import TavilyTool
from app.tools.web_fetch import WebFetchTool

logger = get_logger(__name__)

# Depth parameter to Tavily API mapping (data-model.md)
# IMPORTANT: search_depth must be "basic" or "advanced" (strings), not integers
DEPTH_PARAMETERS = {
    "basic": {"search_depth": "basic", "max_results": 5},
    "intermediate": {"search_depth": "advanced", "max_results": 10},
    "deep": {"search_depth": "advanced", "max_results": 15},
}

# Time range parameter to days mapping
TIME_RANGE_DAYS = {
    "day": 0,  # Sources from today only (age_days <= 0)
    "week": 7,
    "month": 30,
    "year": 365,
    "all": None,
}

# Domain authority mapping for FOREX research (Phase 4+)
# Note: forexlive.com permanently redirects to investinglive.com (rebrand by Finance Magnates)
# Use investinglive.com as the actual domain for authority scoring
TRUSTED_DOMAINS = {
    "investinglive.com": 0.88,  # forexlive.com rebrand — live FX news + technical analysis
    "fxstreet.com": 0.87,  # Established FX analysis and news
    "reuters.com": 0.90,  # Tier-1 financial news (includes /markets/currencies/ coverage)
    "forex.com": 0.82,  # Broker-affiliated FX analysis (slightly lower trust)
}


class RetrievalService:
    """Service for retrieving and scoring web sources."""

    def __init__(self):
        """Initialize retrieval service with Tavily tool."""
        self.tavily_tool = TavilyTool()

    async def retrieve_sources(
        self,
        query: str,
        depth: str = "intermediate",
        max_sources: int = 10,
        time_range: str = "all",
        include_domains: list[str] | None = None,
        *,
        enrich: bool | None = None,
    ) -> list[SourceRecord]:
        """Retrieve sources from Tavily and apply credibility scoring.

        Maps depth parameter to Tavily search parameters per data-model.md
        (§Tavily Search Parameter Mapping).

        Args:
            query: Search query
            depth: Search depth (basic/intermediate/deep) - maps to Tavily search_depth
            max_sources: Maximum sources to retrieve (overrides depth default if larger)
            time_range: Time range filter (day/week/month/year/all) - filters source recency
            include_domains: Optional domain whitelist for Tavily (e.g., ['reuters.com']). If provided, restricts results to those domains.
            enrich: If True, fetch and enrich source snippets with full page content (optional).
                   If None, uses settings.enrich_sources_by_default. Default: None

        Returns:
            List of SourceRecords with credibility scores applied (at most max_sources items)
            If enrich=True, additionally enriches snippets with full-page content

        Raises:
            ExternalServiceError: If source retrieval fails
        """
        # Use settings default if enrich not explicitly provided
        if enrich is None:
            enrich = settings.enrich_sources_by_default
        # Validate depth parameter
        if depth not in DEPTH_PARAMETERS:
            logger.warning(
                "invalid_depth_parameter",
                depth=depth,
                valid_depths=list(DEPTH_PARAMETERS.keys()),
            )
            depth = "intermediate"  # Default to intermediate

        # Get depth-based parameters
        depth_params = DEPTH_PARAMETERS[depth]

        # Use max_sources parameter, respecting depth defaults
        # Override max_results if max_sources is explicitly set and larger than depth default
        effective_max_sources = max(max_sources, depth_params["max_results"])

        logger.info(
            "retrieval_start",
            query=query[:100],
            depth=depth,
            max_sources=effective_max_sources,
            time_range=time_range,
            search_depth=depth_params["search_depth"],
            include_domains=include_domains,
        )

        try:
            # Fetch raw sources from Tavily (passing depth-based parameters and domain filter)
            sources = await self.tavily_tool.search(
                query=query,
                depth=depth,
                max_sources=effective_max_sources,
                include_domains=include_domains,
            )

            # Filter sources by time_range if applicable
            if time_range != "all":
                sources = self._filter_by_time_range(sources, time_range)

            # Apply credibility scoring to each source
            scored_sources = []
            for source in sources:
                # Stop if we've reached max_sources
                if len(scored_sources) >= max_sources:
                    break

                source = self._apply_credibility_score(source)
                scored_sources.append(source)

                if (source.credibility_score or 0.0) < 0.65:
                    logger.warning(
                        "low_credibility_source",
                        url=source.url,
                        score=source.credibility_score,
                    )

            logger.info(
                "retrieval_complete",
                query=query[:100],
                sources_count=len(scored_sources),
                avg_credibility=(
                    sum(s.credibility_score or 0.0 for s in scored_sources) / len(scored_sources)
                    if scored_sources
                    else 0.0
                ),
                time_range=time_range,
                enrich=enrich,
            )

            # Enrich sources with full-page content if requested
            if enrich and scored_sources:
                try:
                    scored_sources = await self._enrich_sources(scored_sources)
                except Exception as exc:
                    logger.warning(
                        "enrichment_failed",
                        error=str(exc),
                        sources_count=len(scored_sources),
                    )
                    # Continue with non-enriched sources on enrichment failure

            return scored_sources

        except Exception as exc:
            logger.error(
                "retrieval_failed",
                query=query[:100],
                error=str(exc),
            )
            raise

    def _apply_credibility_score(self, source: SourceRecord) -> SourceRecord:
        """Apply credibility scoring algorithm to a source.

        Implements data-model.md (§Source Credibility) formula:
          credibility = (0.50 × domain_authority) + (0.30 × recency) + (0.20 × citations)

        Args:
            source: SourceRecord with basic data from Tavily

        Returns:
            SourceRecord with credibility_score updated
        """
        # Extract domain from URL
        try:
            from urllib.parse import urlparse

            domain = urlparse(str(source.url)).netloc.lower()
            # Remove www. prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = "unknown"

        # Calculate domain authority (0.0-1.0)
        domain_authority = TRUSTED_DOMAINS.get(domain, 0.5)

        # Calculate recency boost (simplified: assume recent if from Tavily)
        # In a real system, would parse publish date from source metadata
        recency_boost = 0.8  # Default assumption for Tavily results (relatively fresh)

        # Citation count normalized (placeholder: 0.6 default for web sources)
        # Real implementation would scrape citation count from domain
        citation_normalized = 0.6

        # Apply formula from data-model.md
        credibility_score = (
            (0.50 * domain_authority) + (0.30 * recency_boost) + (0.20 * citation_normalized)
        )

        # Clamp to [0.0, 1.0]
        credibility_score = max(0.0, min(1.0, credibility_score))

        # Update source with calculated score
        source.credibility_score = credibility_score

        logger.debug(
            "credibility_calculated",
            url=source.url,
            domain=domain,
            domain_authority=domain_authority,
            recency_boost=recency_boost,
            credibility_score=credibility_score,
        )

        return source

    def _filter_by_time_range(
        self,
        sources: list[SourceRecord],
        time_range: str,
    ) -> list[SourceRecord]:
        """Filter sources by time_range parameter (day/week/month/year/all).

        Applies time range filter per data-model.md (§Tavily Search Parameter Mapping):
          day: 1-day-old sources
          week: <7 day old sources
          month: <30 day old sources
          year: <365 day old sources
          all: no filtering

        Args:
            sources: List of sources to filter
            time_range: Time range filter (day/week/month/year/all)

        Returns:
            Filtered list of sources matching time range criteria
        """
        if time_range not in TIME_RANGE_DAYS or TIME_RANGE_DAYS[time_range] is None:
            # No filtering for 'all' or invalid time_range
            return sources

        max_age_days = TIME_RANGE_DAYS[time_range]
        current_time = datetime.now(timezone.utc).replace(
            tzinfo=None
        )  # Convert to naive for comparison

        filtered_sources = []
        for source in sources:
            # If no retrieved_at timestamp, assume it's recent (from Tavily)
            if not source.retrieved_at:
                filtered_sources.append(source)
                continue

            try:
                # Parse ISO 8601 timestamp and convert to naive datetime for comparison
                retrieved_time = datetime.fromisoformat(source.retrieved_at.replace("Z", "+00:00"))
                # Remove timezone info to match utcnow()
                retrieved_time = retrieved_time.replace(tzinfo=None)
                age_days = (current_time - retrieved_time).days

                if age_days <= max_age_days:
                    filtered_sources.append(source)
                else:
                    logger.debug(
                        "source_filtered_by_age",
                        url=source.url,
                        age_days=age_days,
                        max_age_days=max_age_days,
                    )
            except Exception as exc:
                # If timestamp parsing fails, include source (be permissive)
                logger.debug(
                    "source_parse_timestamp_error",
                    url=source.url,
                    error=str(exc),
                )
                filtered_sources.append(source)

        logger.info(
            "time_range_filter_applied",
            time_range=time_range,
            max_age_days=max_age_days,
            sources_before=len(sources),
            sources_after=len(filtered_sources),
        )

        return filtered_sources

    async def _enrich_sources(self, sources: list[SourceRecord]) -> list[SourceRecord]:
        """Enrich source snippets with full-page content using WebFetchTool.

        T055-T058: Implements enrichment pipeline
        - Instantiates WebFetchTool and fetches full page content for each URL
        - Maps FetchedPage fields to SourceRecord fields (title, snippet, retrieved_at)
        - Gracefully handles partial failures (skips failed URLs)
        - Only updates SourceRecord if fetch succeeded

        Args:
            sources: List of SourceRecord to enrich

        Returns:
            List of SourceRecord with enriched snippets and metadata

        Raises:
            Exception: Re-raised from WebFetchTool if unrecoverable error occurs
        """
        if not sources:
            return sources

        logger.info(
            "enrichment_start",
            sources_count=len(sources),
        )

        # Extract URLs from sources
        urls = [str(source.url) for source in sources]

        # Create WebFetchRequest for batch fetch
        config = WebFetchConfig()
        request = WebFetchRequest(urls=urls, config=config)

        # Fetch pages using WebFetchTool
        tool = WebFetchTool()
        try:
            result = await tool.fetch_batch(request)
        finally:
            await tool.close()

        # Map fetched pages back to sources (T057)
        fetched_by_url = {page.url: page for page in result.pages}

        enriched_sources = []
        for source in sources:
            source_url = str(source.url)
            fetched_page = fetched_by_url.get(source_url)

            # Skip enrichment if fetch failed (T058 - handle partial failures)
            if not fetched_page or not fetched_page.succeeded:
                logger.debug(
                    "enrichment_skipped_fetch_failed",
                    url=source_url,
                    error=fetched_page.error if fetched_page else "no_result",
                )
                enriched_sources.append(source)
                continue

            # Update SourceRecord fields from FetchedPage (T057)
            # Map title if available and non-empty
            if fetched_page.title:
                source.title = fetched_page.title

            # Map content to snippet (most important enrichment)
            if fetched_page.content:
                source.snippet = fetched_page.content

            # Map fetched_at to retrieved_at
            if fetched_page.fetched_at:
                source.retrieved_at = fetched_page.fetched_at.isoformat()

            logger.debug(
                "enrichment_updated_source",
                url=source_url,
                snippet_length=len(source.snippet),
            )

            enriched_sources.append(source)

        logger.info(
            "enrichment_complete",
            sources_count=len(enriched_sources),
            fetched_count=result.fetched_count,
            failed_count=result.failed_count,
        )

        return enriched_sources
