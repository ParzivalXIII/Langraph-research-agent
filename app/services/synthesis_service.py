"""Synthesis service for generating research briefs and confidence assessments.

Handles LLM-based synthesis of retrieved sources into structured research briefs
and applies the confidence scoring algorithm from data-model.md (§Confidence Scoring Algorithm).

Confidence Score Formula (data-model.md):
  confidence_score = (0.40 × source_agreement) + (0.30 × source_quality) +
                     (0.20 × recency) + (0.10 × freshness) - (0.15 × contradiction_penalty)

  Clamped to [0.0, 1.0]

  Factors:
  - source_agreement: 0-1 based on how many sources agree (consensus ratio)
  - source_quality: Average credibility_score of sources
  - recency: 0-1 based on publication freshness
  - freshness: Time since retrieval (0=immediate, 1=old)
  - contradiction_penalty: Normalized penalty from processing service

Depth Control (Phase 4):
  - max_sources: Maximum sources to include in brief output (respects user constraint)
  - max_key_points: Capped at 10 per ResearchBrief schema
  - Latency tracking: synthesis_latency_ms logged for monitoring SLAs
    (basic <30s, intermediate <60s, deep <120s per data-model.md)
"""

import time
from typing import cast

from langchain_core.exceptions import LangChainException

from app.core.llm import get_llm_client
from app.core.logging import get_logger
from app.schemas.research import ConfidenceAssessment, ResearchBrief, SourceRecord
from app.services.processing_service import ProcessingService

logger = get_logger(__name__)


class SynthesisService:
    """Service for synthesizing sources into research briefs with confidence metrics."""

    def __init__(self):
        """Initialize synthesis service with processing service."""
        self.processing_service = ProcessingService()

    async def synthesize_brief(
        self,
        query: str,
        sources: list[SourceRecord],
        max_sources: int = 10,
    ) -> ResearchBrief:
        """Synthesize sources into a research brief with confidence scoring.

        Orchestrates:
        1. Contradiction detection (processing service)
        2. Confidence calculation (this service)
        3. Summary generation (LLM-based, placeholder in MVP)
        4. Output capping to max_sources constraint (Phase 4)

        Tracks synthesis latency per data-model.md SLA targets:
        - basic: <30s, intermediate: <60s, deep: <120s

        Args:
            query: Original research query
            sources: Retrieved and scored sources
            max_sources: Maximum sources to include in output (Phase 4 depth control)

        Returns:
            ResearchBrief with summary, key_points, sources (capped to max_sources),
            contradictions, and confidence_score

        Raises:
            SynthesisError: If synthesis fails (logs but continues with fallback)
        """
        synthesis_start_time = time.time()

        logger.info(
            "synthesis_start",
            query=query[:100],
            sources_count=len(sources),
            max_sources=max_sources,
        )

        # Step 1: Detect contradictions
        contradictions, contradiction_penalty = (
            await self.processing_service.detect_contradictions(sources)
        )

        # Step 2: Calculate confidence score
        confidence_breakdown = self._calculate_confidence(
            sources=sources,
            contradiction_penalty=contradiction_penalty,
        )

        # Step 3: Generate summary (simplified for MVP)
        try:
            summary = await self._generate_summary(query, sources)
            key_points = await self._extract_key_points(sources)
        except Exception as exc:
            logger.warning(
                "synthesis_fallback_to_simple_summary",
                error=str(exc),
            )
            # Fallback for synthesis failures (per spec A2 error handling)
            summary = self._simple_summary_fallback(query, sources)
            key_points = [s.title for s in sources[:5]]

        # Step 4: Cap sources and key_points to max_sources constraint (Phase 4)
        # respects user-specified max_sources limit
        capped_sources = sources[:max_sources]  # Limit sources to max_sources

        # Cap key_points to min(10, max_sources) to match ResearchBrief schema
        # and respect the output constraint
        max_key_points = min(10, max_sources)
        capped_key_points = key_points[:max_key_points]

        # Construct brief
        brief = ResearchBrief(
            summary=summary,
            key_points=capped_key_points,
            sources=capped_sources,
            contradictions=[c.severity for c in contradictions],
            confidence_score=confidence_breakdown.final_score,
            confidence_breakdown=confidence_breakdown,
        )

        # Calculate synthesis latency for monitoring SLA targets
        synthesis_latency_ms = (time.time() - synthesis_start_time) * 1000

        logger.info(
            "synthesis_complete",
            query=query[:100],
            sources_count=len(capped_sources),
            key_points_count=len(capped_key_points),
            contradictions_count=len(contradictions),
            confidence_score=brief.confidence_score,
            synthesis_latency_ms=synthesis_latency_ms,
        )

        return brief

    def _calculate_confidence(
        self,
        sources: list[SourceRecord],
        contradiction_penalty: float,
    ) -> ConfidenceAssessment:
        """Calculate confidence score using formula from data-model.md.

        Formula (clamped to [0.0, 1.0]):
          confidence = (0.40 × agreement) + (0.30 × quality) +
                      (0.20 × recency) + (0.10 × freshness) -
                      (0.15 × contradiction_penalty)

        Args:
            sources: List of source records
            contradiction_penalty: Total penalty from contradictions (0.0-1.0)

        Returns:
            ConfidenceAssessment with breakdown of all factors
        """
        if not sources:
            return ConfidenceAssessment(
                source_agreement=0.0,
                source_quality=0.0,
                recency=0.0,
                freshness=0.0,
                contradiction_penalty=0.0,
                final_score=0.0,
            )

        # Factor 1: Source agreement (consensus ratio)
        # Simplified: assume sources agree if credibility > 0.65
        high_quality_sources = sum(
            1 for s in sources if (s.credibility_score or 0.0) >= 0.65
        )
        source_agreement = high_quality_sources / len(sources) if sources else 0.0

        # Factor 2: Source quality (average credibility)
        credibility_values = [s.credibility_score or 0.0 for s in sources]
        source_quality = sum(credibility_values) / len(sources) if sources else 0.0

        # Factor 3: Recency (simplified: assume current)
        recency = 0.9  # Default high recency for freshly retrieved sources

        # Factor 4: Freshness (time since retrieval, simplified to immediate)
        freshness = 1.0  # Newly retrieved, maximum freshness

        # Calculate final score using formula
        final_score = (
            (0.40 * source_agreement)
            + (0.30 * source_quality)
            + (0.20 * recency)
            + (0.10 * freshness)
            - (0.15 * contradiction_penalty)
        )

        # Clamp to [0.0, 1.0]
        final_score = max(0.0, min(1.0, final_score))

        breakdown = ConfidenceAssessment(
            source_agreement=source_agreement,
            source_quality=source_quality,
            recency=recency,
            freshness=freshness,
            contradiction_penalty=contradiction_penalty,
            final_score=final_score,
        )

        logger.debug(
            "confidence_calculated",
            source_agreement=source_agreement,
            source_quality=source_quality,
            recency=recency,
            freshness=freshness,
            contradiction_penalty=contradiction_penalty,
            final_score=final_score,
        )

        return breakdown

    async def _generate_summary(self, query: str, sources: list[SourceRecord]) -> str:
        """Generate research summary using LLM (OpenRouter via LangChain).

        Calls the configured LLM model via OpenRouter to synthesize source
        content into a coherent research summary.

        Prompt engineering:
        - Temperature set to 0.2 for deterministic, evidence-based synthesis
        - Instructs LLM to cite sources and avoid speculation
        - Limits to 200 words for conciseness

        Args:
            query: Research query
            sources: Retrieved sources with titles, snippets, URLs

        Returns:
            Synthesized summary string

        Raises:
            LangChainException: If LLM call fails (caught by caller for fallback)
            ValueError: If OPENROUTER_API_KEY not configured
        """
        if not sources:
            return f"No sources found for query: {query}"

        llm_start_time = time.time()

        # Format sources for LLM prompt
        formatted_sources = "\n".join(
            [
                f"- {s.title} (Credibility: {s.credibility_score:.2f})\n  Snippet: {s.snippet[:300]}"
                for s in sources[:5]
            ]
        )

        prompt = f"""You are a research analyst. Synthesize the following sources into a 
concise, evidence-based research summary (max 200 words). 
Cite sources and avoid speculation.

Research Query: {query}

Sources:
{formatted_sources}

Generate a brief summary that synthesizes key findings from these sources:"""

        try:
            llm = get_llm_client()
            response = await llm.ainvoke(prompt)
            # Extract string content from LLM response
            summary = cast(
                str, response.content if hasattr(response, "content") else str(response)
            )

            llm_latency_ms = (time.time() - llm_start_time) * 1000
            logger.info(
                "llm_summary_generated",
                query=query[:100],
                sources_count=len(sources),
                summary_length=len(summary),
                llm_latency_ms=llm_latency_ms,
            )

            return summary

        except (LangChainException, ValueError) as exc:
            logger.error(
                "llm_summary_generation_failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    async def _extract_key_points(self, sources: list[SourceRecord]) -> list[str]:
        """Extract key points from sources using LLM (OpenRouter via LangChain).

        Calls the configured LLM model to identify and extract the most important
        findings from the retrieved sources.

        Extraction strategy:
        - Focuses on evidence-based points from source content
        - Limits to 10 key points per ResearchBrief schema
        - Returns one point per line for easy parsing

        Args:
            sources: Retrieved sources with titles and snippets

        Returns:
            List of key point strings (max 10)

        Raises:
            LangChainException: If LLM call fails (caught by caller for fallback)
        """
        if not sources:
            return ["No sources available for key point extraction"]

        llm_start_time = time.time()

        # Format sources for extraction prompt
        formatted_sources = "\n".join(
            [f"- {s.title}: {s.snippet[:250]}" for s in sources[:7]]
        )

        prompt = f"""You are a research analyst. Extract the 5-10 most important key points 
from the following sources. Return only the key points, one per line, without numbering.
Focus on evidence-based findings.

Sources:
{formatted_sources}

Key points:"""

        try:
            llm = get_llm_client()
            response = await llm.ainvoke(prompt)
            # Extract string content from LLM response
            response_text: str = cast(
                str, response.content if hasattr(response, "content") else str(response)
            )

            # Parse response into individual key points
            key_points = [
                point.strip()
                for point in response_text.split("\n")
                if point.strip() and len(point.strip()) > 5
            ]

            # Ensure we don't exceed 10 key points
            key_points = key_points[:10]

            llm_latency_ms = (time.time() - llm_start_time) * 1000
            logger.info(
                "llm_key_points_extracted",
                sources_count=len(sources),
                key_points_count=len(key_points),
                llm_latency_ms=llm_latency_ms,
            )

            return key_points if key_points else ["No key points extracted"]

        except (LangChainException, ValueError) as exc:
            logger.error(
                "llm_key_point_extraction_failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

    def _simple_summary_fallback(self, query: str, sources: list[SourceRecord]) -> str:
        """Fallback summary generation if LLM fails (per spec A2 error handling).

        Returns minimal but valid summary without synthesis.

        Args:
            query: Research query
            sources: Retrieved sources

        Returns:
            Simple summary string
        """
        source_count = len(sources)
        url_list = "; ".join(str(s.url) for s in sources[:5])

        return (
            f"Based on {source_count} retrieved sources, here are findings on '{query}'. "
            f"Sources: {url_list}. "
            f"Detailed synthesis unavailable, but evidence has been retrieved for manual review."
        )
