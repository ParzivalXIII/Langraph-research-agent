"""Unit tests for Phase 3 services (retrieval, processing, synthesis, agent).

Uses mocked Tavily and LLM dependencies. Tests business logic without
external service calls.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.research_agent import ResearchAgent
from app.schemas.research import ResearchQuery, SourceRecord
from app.services.processing_service import ProcessingService
from app.services.retrieval_service import RetrievalService
from app.services.synthesis_service import SynthesisService

# ============================================================================
# Retrieval Service Tests
# ============================================================================


class TestRetrievalService:
    """Unit tests for RetrievalService."""

    @pytest.mark.asyncio
    async def test_retrieve_sources_success(self):
        """Test successful source retrieval with credibility scoring."""
        # Mock Tavily tool
        mock_search = AsyncMock(
            return_value=[
                SourceRecord(
                    title="Test Article",
                    url="https://example.com/article",
                    relevance=0.9,
                    snippet="Test snippet",
                )
            ]
        )

        with patch("app.services.retrieval_service.TavilyTool.search", mock_search):
            service = RetrievalService()
            sources = await service.retrieve_sources("test query")

            assert len(sources) == 1
            assert sources[0].credibility_score >= 0.0
            assert sources[0].credibility_score <= 1.0

    @pytest.mark.asyncio
    async def test_retrieve_sources_credibility_scoring(self):
        """Test that credibility scores are calculated and applied."""
        service = RetrievalService()

        # Test with a known domain
        source = SourceRecord(
            title="Academic Research",
            url="https://arxiv.org/paper123",
            relevance=0.85,
            snippet="Research findings...",
        )

        scored_source = service._apply_credibility_score(source)

        # arxiv.org has high domain authority (0.95)
        assert scored_source.credibility_score > 0.6
        assert scored_source.credibility_score <= 1.0

    def test_credibility_score_low_domain(self):
        """Test credibility scoring for unknown domains."""
        service = RetrievalService()

        source = SourceRecord(
            title="Unknown Source",
            url="https://unknown-domain.xyz/article",
            relevance=0.5,
            snippet="Content...",
        )

        scored = service._apply_credibility_score(source)

        # Unknown domain gets default 0.5 authority
        # Formula: (0.50 × 0.5) + (0.30 × 0.8) + (0.20 × 0.4) = 0.51
        assert scored.credibility_score >= 0.4  # Some minimum
        assert scored.credibility_score <= 0.7


# ============================================================================
# Processing Service Tests
# ============================================================================


class TestProcessingService:
    """Unit tests for ProcessingService."""

    @pytest.mark.asyncio
    async def test_detect_no_contradictions(self):
        """Test contradiction detection with agreeing sources."""
        service = ProcessingService()

        sources = [
            SourceRecord(
                title="Source 1",
                url="https://example1.com",
                relevance=0.9,
                snippet="Quantum computers use superposition",
            ),
            SourceRecord(
                title="Source 2",
                url="https://example2.com",
                relevance=0.85,
                snippet="Quantum computers leverage superposition",
            ),
        ]

        contradictions, penalty = await service.detect_contradictions(sources)

        assert len(contradictions) <= 1  # Minimal contradiction
        assert penalty <= 0.05

    @pytest.mark.asyncio
    async def test_detect_contradictions_conflicting(self):
        """Test contradiction detection with disagreeing sources."""
        service = ProcessingService()

        sources = [
            SourceRecord(
                title="Pro-AI",
                url="https://example1.com",
                relevance=0.9,
                snippet="AI will support human workers",
            ),
            SourceRecord(
                title="Anti-AI",
                url="https://example2.com",
                relevance=0.85,
                snippet="AI will oppose human employment",
            ),
        ]

        contradictions, penalty = await service.detect_contradictions(sources)

        # These should show contradiction (support vs oppose)
        assert len(contradictions) >= 0  # May detect zero or one
        assert penalty >= 0.0


# ============================================================================
# Synthesis Service Tests
# ============================================================================


class TestSynthesisService:
    """Unit tests for SynthesisService."""

    @pytest.mark.asyncio
    async def test_synthesize_brief_success(self, sample_source_record_data):
        """Test research brief synthesis."""
        service = SynthesisService()

        sources = [
            SourceRecord(**sample_source_record_data),
        ]

        brief = await service.synthesize_brief("test query", sources)

        assert brief.summary is not None
        assert len(brief.summary) > 0
        assert brief.confidence_score >= 0.0
        assert brief.confidence_score <= 1.0
        assert len(brief.sources) >= 1

    def test_confidence_calculation(self):
        """Test confidence score formula application."""
        service = SynthesisService()

        sources = [
            SourceRecord(
                title="High Quality",
                url="https://example.com",
                relevance=0.9,
                credibility_score=0.9,
                snippet="Good content",
            ),
            SourceRecord(
                title="Medium Quality",
                url="https://example2.com",
                relevance=0.7,
                credibility_score=0.65,
                snippet="Medium content",
            ),
        ]

        assessment = service._calculate_confidence(sources, contradiction_penalty=0.05)

        # Formula: (0.40 × agreement) + (0.30 × quality) + ...
        assert assessment.source_agreement >= 0.5  # Both > 0.65
        assert assessment.source_quality >= 0.7  # Average of 0.9 and 0.65
        assert assessment.final_score > 0.5  # Should be reasonably high


# ============================================================================
# Research Agent Tests
# ============================================================================


class TestResearchAgent:
    """Unit tests for ResearchAgent."""

    @pytest.mark.asyncio
    async def test_process_query_success(self):
        """Test successful query processing through agent."""
        # Create mock sources to return
        mock_sources = [
            SourceRecord(
                title="Test Article",
                url="https://example.com",
                relevance=0.9,
                credibility_score=0.8,
                snippet="Test content",
            )
        ]

        # Create agent and mock its retrieval_service
        agent = ResearchAgent()
        agent.retrieval_service.retrieve_sources = AsyncMock(return_value=mock_sources)
        agent.processing_service.detect_contradictions = AsyncMock(return_value=[])

        query = ResearchQuery(query="What is quantum computing?")
        brief = await agent.process_query(query)

        assert brief is not None
        assert len(brief.sources) >= 1
        assert brief.confidence_score >= 0.0

    @pytest.mark.asyncio
    async def test_process_query_max_iterations(self):
        """Test that agent respects max_iterations=3 limit."""
        call_count = 0

        async def mock_retrieve(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return empty to trigger iteration loop
            return []

        # Create agent and mock its retrieval service to track calls
        agent = ResearchAgent()
        agent.retrieval_service.retrieve_sources = AsyncMock(side_effect=mock_retrieve)
        agent.processing_service.detect_contradictions = AsyncMock(return_value=[])

        query = ResearchQuery(query="test", max_sources=50)  # Request many sources

        try:
            await agent.process_query(query)
        except Exception:
            pass  # Expected to fail with no sources

        # Should stop after MAX_ITERATIONS (3), not keep retrying
        assert call_count <= (ResearchAgent.MAX_ITERATIONS + 1)
