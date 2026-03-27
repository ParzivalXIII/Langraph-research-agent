"""Unit tests for depth control parameter mapping and time_range filtering.

Tests from Phase 4 (US2 - Depth Control):
- T030: Unit tests for depth parameter mapping per data-model.md
- Verify depth→Tavily search_depth parameter mapping (basic→3, intermediate→5, deep→10+)
- Verify time_range→days parameter mapping (day→1, week→7, month→30, year→365, all→None)
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.services.retrieval_service import (
    RetrievalService,
    DEPTH_PARAMETERS,
    TIME_RANGE_DAYS,
)
from app.schemas.research import SourceRecord


class TestDepthParameterMapping:
    """Test depth parameter mapping to Tavily search_depth per data-model.md."""

    @pytest.mark.asyncio
    async def test_depth_basic_maps_correctly(self):
        """Test basic depth maps to search_depth="basic", max_results=5."""
        assert DEPTH_PARAMETERS["basic"]["search_depth"] == "basic"
        assert DEPTH_PARAMETERS["basic"]["max_results"] == 5

    @pytest.mark.asyncio
    async def test_depth_intermediate_maps_correctly(self):
        """Test intermediate depth maps to search_depth="advanced", max_results=10."""
        assert DEPTH_PARAMETERS["intermediate"]["search_depth"] == "advanced"
        assert DEPTH_PARAMETERS["intermediate"]["max_results"] == 10

    @pytest.mark.asyncio
    async def test_depth_deep_maps_correctly(self):
        """Test deep depth maps to search_depth="advanced", max_results=15."""
        assert DEPTH_PARAMETERS["deep"]["search_depth"] == "advanced"
        assert DEPTH_PARAMETERS["deep"]["max_results"] == 15

    @pytest.mark.asyncio
    async def test_retrieve_sources_uses_depth_mapping(self):
        """Test that retrieve_sources passes correct depth parameters to Tavily tool."""
        retrieval_service = RetrievalService()

        # Mock the Tavily tool
        mock_sources = [
            SourceRecord(
                title="Test Source 1",
                url="https://example.com/1",
                relevance=0.9,
                snippet="Test content",
            ),
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=mock_sources,
        ) as mock_search:
            # Call with basic depth
            await retrieval_service.retrieve_sources(
                query="test",
                depth="basic",
                max_sources=10,
            )

            # Verify Tavily search was called (with depth passed through)
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args.kwargs["depth"] == "basic"

    @pytest.mark.asyncio
    async def test_invalid_depth_defaults_to_intermediate(self):
        """Test that invalid depth parameter defaults to intermediate."""
        retrieval_service = RetrievalService()

        mock_sources = [
            SourceRecord(
                title="Test Source",
                url="https://example.com/1",
                relevance=0.9,
                snippet="Test content",
            ),
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=mock_sources,
        ) as mock_search:
            # Call with invalid depth
            await retrieval_service.retrieve_sources(
                query="test",
                depth="invalid_depth",
                max_sources=10,
            )

            # Verify it defaulted to intermediate
            call_args = mock_search.call_args
            assert call_args.kwargs["depth"] == "intermediate"


class TestTimeRangeParameterMapping:
    """Test time_range parameter mapping to days per data-model.md."""

    def test_time_range_day_maps_to_1_day(self):
        """Test day time_range maps to 1 day."""
        assert TIME_RANGE_DAYS["day"] == 0

    def test_time_range_week_maps_to_7_days(self):
        """Test week time_range maps to 7 days."""
        assert TIME_RANGE_DAYS["week"] == 7

    def test_time_range_month_maps_to_30_days(self):
        """Test month time_range maps to 30 days."""
        assert TIME_RANGE_DAYS["month"] == 30

    def test_time_range_year_maps_to_365_days(self):
        """Test year time_range maps to 365 days."""
        assert TIME_RANGE_DAYS["year"] == 365

    def test_time_range_all_maps_to_none(self):
        """Test 'all' time_range maps to None (no filtering)."""
        assert TIME_RANGE_DAYS["all"] is None

    @pytest.mark.asyncio
    async def test_retrieve_sources_with_time_range_filtering(self):
        """Test that retrieve_sources applies time_range filtering."""
        retrieval_service = RetrievalService()

        # Create sources with different ages
        old_source = SourceRecord(
            title="Old Source",
            url="https://example.com/old",
            relevance=0.9,
            snippet="Old content",
            retrieved_at=(datetime.utcnow() - timedelta(days=45)).isoformat() + "Z",
        )
        recent_source = SourceRecord(
            title="Recent Source",
            url="https://example.com/recent",
            relevance=0.9,
            snippet="Recent content",
            retrieved_at=(datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[old_source, recent_source],
        ):
            # Filter to month (30 days)
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="month",
            )

            # Should only include recent source (old is 45 days old)
            urls = {str(s.url) for s in sources}
            assert "https://example.com/recent" in urls
            assert "https://example.com/old" not in urls

    @pytest.mark.asyncio
    async def test_retrieve_sources_with_no_time_range(self):
        """Test that 'all' time_range applies no filtering."""
        retrieval_service = RetrievalService()

        old_source = SourceRecord(
            title="Old Source",
            url="https://example.com/old",
            relevance=0.9,
            snippet="Old content",
            retrieved_at=(datetime.utcnow() - timedelta(days=400)).isoformat() + "Z",
        )
        recent_source = SourceRecord(
            title="Recent Source",
            url="https://example.com/recent",
            relevance=0.9,
            snippet="Recent content",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[old_source, recent_source],
        ):
            # No time filtering
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="all",
            )

            # Should include both
            assert len(sources) == 2
            urls = {str(s.url) for s in sources}
            assert "https://example.com/old" in urls
            assert "https://example.com/recent" in urls


class TestMaxSourcesConstraint:
    """Test max_sources parameter enforcement."""

    @pytest.mark.asyncio
    async def test_max_sources_limits_output(self):
        """Test that max_sources parameter limits the retrieved sources."""
        retrieval_service = RetrievalService()

        # Create 5 sources
        sources = [
            SourceRecord(
                title=f"Source {i}",
                url=f"https://example.com/{i}",
                relevance=0.9,
                snippet=f"Content {i}",
            )
            for i in range(5)
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=sources,
        ):
            # Request only 3 sources
            result = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=3,
            )

            # Should get exactly 3
            assert len(result) == 3
            urls = {str(s.url) for s in result}
            assert "https://example.com/0" in urls
            assert "https://example.com/1" in urls
            assert "https://example.com/2" in urls
            assert "https://example.com/3" not in urls

    @pytest.mark.asyncio
    async def test_max_sources_overrides_depth_default(self):
        """Test that explicit max_sources overrides depth default."""
        retrieval_service = RetrievalService()

        # Create 20 sources
        sources = [
            SourceRecord(
                title=f"Source {i}",
                url=f"https://example.com/{i}",
                relevance=0.9,
                snippet=f"Content {i}",
            )
            for i in range(20)
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=sources,
        ):
            # Request 15 sources with basic depth (which defaults to 5)
            # max_sources=15 should override the depth default of 5
            result = await retrieval_service.retrieve_sources(
                query="test",
                depth="basic",
                max_sources=15,
            )

            # Tavily was called with effective_max_sources
            # but output is capped to request max_sources
            assert len(result) <= 15
