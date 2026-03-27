"""API endpoint tests for research routes.

Tests POST /research endpoint with mocked services and various input scenarios.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.research import ResearchBrief, SourceRecord


class TestResearchEndpoint:
    """Tests for POST /research endpoint."""

    @pytest.mark.asyncio
    async def test_post_research_success(self, api_client, mock_tavily_client):
        """Test successful research request."""
        # Create a mock brief with valid data
        mock_brief = ResearchBrief(
            summary="Quantum computing represents a paradigm shift in computational theory. These systems leverage quantum mechanical principles to process information exponentially faster than classical computers.",
            key_points=[
                "Quantum computers use superposition",
                "Entanglement is key property",
            ],
            sources=[
                SourceRecord(
                    title="Quantum Computing Fundamentals Guide",
                    url="https://example.com",
                    relevance=0.9,
                    credibility_score=0.85,
                    snippet="Quantum computing content",
                )
            ],
            confidence_score=0.82,
        )

        # Mock the research agent
        with patch(
            "app.api.routes.research._research_agent.process_query",
            new_callable=AsyncMock,
        ) as mock_agent:
            mock_agent.return_value = mock_brief

            response = api_client.post(
                "/research/",
                json={
                    "query": "What is quantum computing?",
                    "depth": "intermediate",
                    "max_sources": 10,
                    "time_range": "all",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["summary"] is not None
            assert len(data["key_points"]) >= 1
            assert len(data["sources"]) >= 1
            assert 0.0 <= data["confidence_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_post_research_invalid_query_too_short(self, api_client):
        """Test request with invalid (too short) query."""
        response = api_client.post(
            "/research/",
            json={
                "query": "ab",  # Too short (minimum 3 chars)
                "depth": "basic",
                "max_sources": 5,
                "time_range": "all",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_post_research_invalid_depth(self, api_client):
        """Test request with invalid depth parameter."""
        response = api_client.post(
            "/research/",
            json={
                "query": "quantum computing",
                "depth": "ultra_deep",  # Invalid depth
                "max_sources": 10,
                "time_range": "all",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_research_invalid_max_sources(self, api_client):
        """Test request with invalid max_sources."""
        # Test too high
        response = api_client.post(
            "/research/",
            json={
                "query": "quantum computing",
                "depth": "basic",
                "max_sources": 100,  # Exceeds max of 50
                "time_range": "all",
            },
        )

        assert response.status_code == 422

        # Test too low
        response = api_client.post(
            "/research/",
            json={
                "query": "quantum computing",
                "depth": "basic",
                "max_sources": 0,  # Below minimum of 1
                "time_range": "all",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_research_service_error_handling(self, api_client):
        """Test endpoint handles service errors gracefully."""
        from app.core.errors import TavilyError

        # Mock agent to raise TavilyError with rate limit
        with patch(
            "app.api.routes.research._research_agent.process_query",
            new_callable=AsyncMock,
        ) as mock_agent:
            mock_agent.side_effect = TavilyError(
                "API rate limit exceeded", status_code=429
            )

            response = api_client.post(
                "/research/",
                json={
                    "query": "test query",
                    "depth": "basic",
                    "max_sources": 5,
                    "time_range": "all",
                },
            )

            # Should return 429 Too Many Requests for rate limit errors
            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_post_research_with_different_depths(self, api_client):
        """Test endpoint handles all depth values."""
        mock_brief = ResearchBrief(
            summary="This comprehensive research brief covers multiple aspects of the topic with sufficient detail and depth for understanding.",
            key_points=["Point 1"],
            sources=[
                SourceRecord(
                    title="Research Article Title",
                    url="https://example.com",
                    relevance=0.9,
                    credibility_score=0.8,
                    snippet="Test",
                )
            ],
            confidence_score=0.8,
        )

        with patch(
            "app.api.routes.research._research_agent.process_query",
            new_callable=AsyncMock,
        ) as mock_agent:
            mock_agent.return_value = mock_brief

            for depth in ["basic", "intermediate", "deep"]:
                response = api_client.post(
                    "/research/",
                    json={
                        "query": "test query",
                        "depth": depth,
                        "max_sources": 10,
                        "time_range": "all",
                    },
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_post_research_with_time_range(self, api_client):
        """Test endpoint handles time_range parameter."""
        mock_brief = ResearchBrief(
            summary="This comprehensive research brief covers multiple aspects of the topic with sufficient detail and depth for understanding.",
            key_points=["Point 1"],
            sources=[
                SourceRecord(
                    title="Research Article Title",
                    url="https://example.com",
                    relevance=0.9,
                    credibility_score=0.8,
                    snippet="Test",
                )
            ],
            confidence_score=0.8,
        )

        with patch(
            "app.api.routes.research._research_agent.process_query",
            new_callable=AsyncMock,
        ) as mock_agent:
            mock_agent.return_value = mock_brief

            for time_range in ["all", "day", "week", "month", "year"]:
                response = api_client.post(
                    "/research/",
                    json={
                        "query": "recent news",
                        "depth": "basic",
                        "max_sources": 5,
                        "time_range": time_range,
                    },
                )

                assert response.status_code == 200


class TestResearchEndpointResponseFormat:
    """Tests for response format compliance."""

    @pytest.mark.asyncio
    async def test_response_matches_schema(self, api_client):
        """Test that response matches ResearchBrief schema."""
        from app.schemas.research import ResearchBrief

        mock_brief = ResearchBrief(
            summary="A comprehensive research finding of at least 50 characters in length.",
            key_points=["Finding 1", "Finding 2"],
            sources=[
                SourceRecord(
                    title="Academic Article",
                    url="https://example.com/article",
                    relevance=0.85,
                    credibility_score=0.80,
                    snippet="Research content here",
                )
            ],
            confidence_score=0.85,
        )

        with patch(
            "app.api.routes.research._research_agent.process_query",
            new_callable=AsyncMock,
        ) as mock_agent:
            mock_agent.return_value = mock_brief

            response = api_client.post(
                "/research/",
                json={
                    "query": "test research",
                    "depth": "intermediate",
                    "max_sources": 10,
                    "time_range": "all",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all required fields are present
            assert "summary" in data
            assert "key_points" in data
            assert "sources" in data
            assert "confidence_score" in data

            # Verify types
            assert isinstance(data["summary"], str)
            assert isinstance(data["key_points"], list)
            assert isinstance(data["sources"], list)
            assert isinstance(data["confidence_score"], float)

            # Verify source format
            if data["sources"]:
                source = data["sources"][0]
                assert "title" in source
                assert "url" in source
                assert "relevance" in source
                assert "credibility_score" in source
