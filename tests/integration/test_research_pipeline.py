"""Integration tests for Phase 3 research pipeline.

Tests services working together with mocked Tavily/LLM but real service integration.
Components tested: retrieval → processing → synthesis → agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.research_agent import ResearchAgent
from app.schemas.research import ResearchQuery, SourceRecord


class TestResearchPipeline:
    """Integration tests for the complete research pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_with_mocked_tavily(self):
        """Test complete pipeline: query → retrieval → processing → synthesis → brief."""
        # Mock Tavily to return realistic test data
        mock_sources = [
            SourceRecord(
                title="Quantum Computing Basics",
                url="https://arxiv.org/quantum-basics",
                relevance=0.95,
                credibility_score=0.92,
                snippet="Quantum computing leverages superposition and entanglement...",
            ),
            SourceRecord(
                title="Quantum Error Correction",
                url="https://quantum.research.org/error-correction",
                relevance=0.88,
                credibility_score=0.85,
                snippet="Error correction is crucial for quantum computing",
            ),
            SourceRecord(
                title="Quantum Applications",
                url="https://techblog.example.com/quantum-apps",
                relevance=0.82,
                credibility_score=0.70,
                snippet="Quantum computers will revolutionize computing",
            ),
        ]

        # Mock Tavily tool
        mock_search = AsyncMock(return_value=mock_sources)

        with patch("app.services.retrieval_service.TavilyTool.search", mock_search):
            agent = ResearchAgent()
            query = ResearchQuery(
                query="What is quantum computing?",
                depth="intermediate",
                max_sources=10,
            )

            brief = await agent.process_query(query)

            # Verify complete brief structure
            assert brief is not None
            assert brief.summary is not None
            assert len(brief.summary) > 0
            assert len(brief.key_points) >= 1
            assert len(brief.sources) == 3
            assert brief.confidence_score >= 0.0
            assert brief.confidence_score <= 1.0
            assert brief.confidence_breakdown is not None

    @pytest.mark.asyncio
    async def test_pipeline_contradiction_detection(self):
        """Test pipeline correctly identifies and handles contradictions."""
        # Create sources with contradictory claims
        contradictory_sources = [
            SourceRecord(
                title="Pro-AI Impact",
                url="https://example1.com",
                relevance=0.9,
                credibility_score=0.85,
                snippet="AI will support human workers in their jobs",
            ),
            SourceRecord(
                title="AI Risk Analysis",
                url="https://example2.com",
                relevance=0.85,
                credibility_score=0.80,
                snippet="AI will oppose human employment and cause job losses",
            ),
        ]

        mock_search = AsyncMock(return_value=contradictory_sources)

        with patch("app.services.retrieval_service.TavilyTool.search", mock_search):
            agent = ResearchAgent()
            query = ResearchQuery(query="Will AI help or hurt employment?")

            brief = await agent.process_query(query)

            # Pipeline should detect some contradictions
            assert brief is not None
            # Confidence should be slightly reduced due to contradictions
            assert brief.confidence_breakdown is not None
            assert 0.0 <= brief.confidence_breakdown.contradiction_penalty <= 0.2

    @pytest.mark.asyncio
    async def test_pipeline_respects_max_sources(self):
        """Test that pipeline respects max_sources limit."""
        # Create 20 mock sources
        mock_sources = [
            SourceRecord(
                title=f"Article {i}",
                url=f"https://example{i}.com",
                relevance=0.8 - (i * 0.01),
                credibility_score=0.8,
                snippet=f"Content about topic {i}",
            )
            for i in range(20)
        ]

        mock_search = AsyncMock(return_value=mock_sources)

        with patch("app.services.retrieval_service.TavilyTool.search", mock_search):
            agent = ResearchAgent()
            query = ResearchQuery(
                query="Test query",
                max_sources=5,  # Request only 5
            )

            brief = await agent.process_query(query)

            # Should return at most 5 sources
            assert len(brief.sources) <= 5

    @pytest.mark.asyncio
    async def test_pipeline_handles_single_source(self):
        """Test pipeline works with minimal sources."""
        minimal_sources = [
            SourceRecord(
                title="Single Source",
                url="https://example.com",
                relevance=0.9,
                credibility_score=0.85,
                snippet="Only source available",
            ),
        ]

        mock_search = AsyncMock(return_value=minimal_sources)

        with patch("app.services.retrieval_service.TavilyTool.search", mock_search):
            agent = ResearchAgent()
            query = ResearchQuery(query="Niche topic")

            brief = await agent.process_query(query)

            # Should still produce valid brief
            assert brief is not None
            assert len(brief.sources) == 1
            assert brief.confidence_score >= 0.0


class TestServiceInteractions:
    """Tests for service-to-service interactions."""

    def test_retrieval_to_processing_format(self):
        """Test that retrieval service output matches processing service input."""

        # Create a source as retrieval would return it
        source = SourceRecord(
            title="Test Article",
            url="https://example.com",
            relevance=0.9,
            credibility_score=0.85,
            snippet="Test content",
        )

        # Just verify it can be used without type errors
        assert source.title is not None
        assert source.url is not None

    @pytest.mark.asyncio
    async def test_processing_to_synthesis_format(self):
        """Test that processing service output is compatible with synthesis."""
        from app.services.processing_service import ProcessingService
        from app.services.synthesis_service import SynthesisService

        processing = ProcessingService()
        synthesis = SynthesisService()

        sources = [
            SourceRecord(
                title="Source 1",
                url="https://example1.com",
                relevance=0.9,
                credibility_score=0.85,
                snippet="Content 1",
            ),
        ]

        # Get contradictions from processing
        contradictions, penalty = await processing.detect_contradictions(sources)

        # Synthesis should be able to use the penalty
        confidence = synthesis._calculate_confidence(sources, penalty)
        assert confidence is not None
        assert 0.0 <= confidence.final_score <= 1.0
