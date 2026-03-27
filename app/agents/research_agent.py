"""Research agent using LangChain for orchestrated query processing.

Implements bounded agent with max_iterations=3, coordinating:
1. Query validation & preparation
2. Tavily search via retrieval service
3. Source contradiction detection via processing service
4. Synthesis via synthesis service
5. Result formatting

From spec.md (§Bounded Autonomy):
- Max iterations: 3 (per T020 in tasks.md)
- Deterministic outputs only (no creative synthesis)
- Retrieval-first approach (evidence before analysis)
"""

from app.core.errors import AppError
from app.core.logging import get_logger
from app.schemas.research import ResearchBrief, ResearchQuery
from app.services.processing_service import ProcessingService
from app.services.retrieval_service import RetrievalService
from app.services.synthesis_service import SynthesisService

logger = get_logger(__name__)


class ResearchAgent:
    """Bounded research agent with max 3 iterations."""

    MAX_ITERATIONS = 3

    def __init__(self):
        """Initialize research agent with service dependencies."""
        self.retrieval_service = RetrievalService()
        self.processing_service = ProcessingService()
        self.synthesis_service = SynthesisService()

    async def process_query(self, research_query: ResearchQuery) -> ResearchBrief:
        """Process research query through retrieval → processing → synthesis pipeline.

        Implements bounded agent with max_iterations=3:
        - Iteration 1: Validate query, fetch sources
        - If sources < 3 AND iterations < 3: Refine query (optional retry)
        - Iteration 2+: Fetch additional sources or use existing
        - Final: Process contradictions and synthesize brief

        Args:
            research_query: ResearchQuery with user's research request

        Returns:
            ResearchBrief with complete findings

        Raises:
            AppError subclass if processing fails
        """
        logger.info(
            "research_agent_start",
            query=research_query.query,
            depth=research_query.depth,
            max_sources=research_query.max_sources,
            iterations_limit=self.MAX_ITERATIONS,
        )

        all_sources = []
        iteration = 0

        while (
            iteration < self.MAX_ITERATIONS
            and len(all_sources) < research_query.max_sources
        ):
            iteration += 1
            logger.info(
                "research_agent_iteration",
                iteration=iteration,
                query=research_query.query,
                sources_so_far=len(all_sources),
            )

            try:
                # Fetch sources for this iteration (passing depth and time_range)
                sources = await self.retrieval_service.retrieve_sources(
                    query=research_query.query,
                    depth=research_query.depth,
                    max_sources=research_query.max_sources - len(all_sources),
                    time_range=research_query.time_range,
                )

                # Deduplicate by URL
                source_urls = {s.url for s in all_sources}
                new_sources = [s for s in sources if s.url not in source_urls]

                all_sources.extend(new_sources)

                logger.info(
                    "research_agent_iteration_complete",
                    iteration=iteration,
                    new_sources=len(new_sources),
                    total_sources=len(all_sources),
                )

                # Stop if we have enough sources
                if len(all_sources) >= research_query.max_sources:
                    break

                # If insufficient sources after iteration 1, could optionally refine query
                # For MVP, just continue to next iteration if possible

            except Exception as exc:
                logger.error(
                    "research_agent_iteration_error",
                    iteration=iteration,
                    error=str(exc),
                )
                if iteration >= self.MAX_ITERATIONS:
                    # All iterations exhausted, raise error
                    raise
                # Otherwise continue to next iteration

        # Ensure minimum sources or fail gracefully
        if not all_sources:
            logger.warning(
                "research_agent_no_sources_retrieved",
                query=research_query.query,
            )
            raise AppError(
                message=f"No sources retrieved for query: {research_query.query}",
                error_code="NO_SOURCES_ERROR",
            )

        logger.info(
            "research_agent_retrieval_complete",
            total_iterations=iteration,
            total_sources=len(all_sources),
        )

        # Synthesize brief from all collected sources
        # Pass max_sources constraint for output capping (Phase 4 depth control)
        brief = await self.synthesis_service.synthesize_brief(
            query=research_query.query,
            sources=all_sources,
            max_sources=research_query.max_sources,
        )

        logger.info(
            "research_agent_complete",
            query=research_query.query,
            sources_count=len(all_sources),
            confidence_score=brief.confidence_score,
        )

        return brief
