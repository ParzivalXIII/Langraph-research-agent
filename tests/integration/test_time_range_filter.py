"""Integration tests for time_range filtering in retrieval service.

Tests from Phase 4 (US2 - Depth Control):
- T032: Integration tests for time_range parameter
- Verify time_range parameter is honored correctly
- Verify recent sources are preferred when time_range is specified
- Test with realistic timestamps and filtering logic
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.retrieval_service import RetrievalService
from app.schemas.research import SourceRecord


class TestTimeRangeIntegration:
    """Integration tests for time_range filtering."""

    @pytest.mark.asyncio
    async def test_time_range_day_filters_correctly(self):
        """Test that time_range='day' only includes today's sources."""
        retrieval_service = RetrievalService()

        # Create sources with various ages
        today = datetime.utcnow()
        today_source = SourceRecord(
            title="Today's News",
            url="https://example.com/today",
            relevance=0.95,
            snippet="Today's content",
            retrieved_at=today.isoformat() + "Z",
        )
        yesterday_source = SourceRecord(
            title="Yesterday's News",
            url="https://example.com/yesterday",
            relevance=0.9,
            snippet="Yesterday's content",
            retrieved_at=(today - timedelta(days=1)).isoformat() + "Z",
        )
        week_old_source = SourceRecord(
            title="Week Old",
            url="https://example.com/week",
            relevance=0.8,
            snippet="Week old content",
            retrieved_at=(today - timedelta(days=7)).isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[today_source, yesterday_source, week_old_source],
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="day",
            )

            # Should only include today's source
            urls = {str(s.url) for s in sources}
            assert "https://example.com/today" in urls
            assert "https://example.com/yesterday" not in urls
            assert "https://example.com/week" not in urls
            assert len(sources) == 1

    @pytest.mark.asyncio
    async def test_time_range_week_filters_correctly(self):
        """Test that time_range='week' includes last 7 days."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        today_source = SourceRecord(
            title="Today",
            url="https://example.com/today",
            relevance=0.95,
            snippet="Today",
            retrieved_at=today.isoformat() + "Z",
        )
        three_days_old = SourceRecord(
            title="3 Days Old",
            url="https://example.com/3days",
            relevance=0.9,
            snippet="3 days",
            retrieved_at=(today - timedelta(days=3)).isoformat() + "Z",
        )
        seven_days_old = SourceRecord(
            title="7 Days Old",
            url="https://example.com/7days",
            relevance=0.85,
            snippet="7 days",
            retrieved_at=(today - timedelta(days=7)).isoformat() + "Z",
        )
        eight_days_old = SourceRecord(
            title="8 Days Old",
            url="https://example.com/8days",
            relevance=0.8,
            snippet="8 days",
            retrieved_at=(today - timedelta(days=8)).isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[today_source, three_days_old, seven_days_old, eight_days_old],
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="week",
            )

            urls = {str(s.url) for s in sources}
            # Should include today, 3 days, and 7 days (within 7 day range)
            assert "https://example.com/today" in urls
            assert "https://example.com/3days" in urls
            assert "https://example.com/7days" in urls
            # Should exclude 8 days old
            assert "https://example.com/8days" not in urls
            assert len(sources) == 3

    @pytest.mark.asyncio
    async def test_time_range_month_filters_correctly(self):
        """Test that time_range='month' includes last 30 days."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        recent = SourceRecord(
            title="Recent",
            url="https://example.com/recent",
            relevance=0.95,
            snippet="Recent",
            retrieved_at=(today - timedelta(days=15)).isoformat() + "Z",
        )
        at_boundary = SourceRecord(
            title="At Boundary",
            url="https://example.com/boundary",
            relevance=0.9,
            snippet="At boundary",
            retrieved_at=(today - timedelta(days=30)).isoformat() + "Z",
        )
        old = SourceRecord(
            title="Old Source",
            url="https://example.com/old",
            relevance=0.8,
            snippet="Old",
            retrieved_at=(today - timedelta(days=35)).isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[recent, at_boundary, old],
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="month",
            )

            urls = {str(s.url) for s in sources}
            assert "https://example.com/recent" in urls
            assert "https://example.com/boundary" in urls
            assert "https://example.com/old" not in urls
            assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_time_range_year_filters_correctly(self):
        """Test that time_range='year' includes last 365 days."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        recent = SourceRecord(
            title="Recent",
            url="https://example.com/recent",
            relevance=0.95,
            snippet="Recent",
            retrieved_at=(today - timedelta(days=100)).isoformat() + "Z",
        )
        almost_year = SourceRecord(
            title="Almost Year",
            url="https://example.com/almostyear",
            relevance=0.9,
            snippet="Almost year",
            retrieved_at=(today - timedelta(days=364)).isoformat() + "Z",
        )
        older = SourceRecord(
            title="Older",
            url="https://example.com/older",
            relevance=0.8,
            snippet="Older",
            retrieved_at=(today - timedelta(days=400)).isoformat() + "Z",
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[recent, almost_year, older],
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="year",
            )

            urls = {str(s.url) for s in sources}
            assert "https://example.com/recent" in urls
            assert "https://example.com/almostyear" in urls
            assert "https://example.com/older" not in urls
            assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_time_range_all_includes_all_sources(self):
        """Test that time_range='all' includes all sources regardless of age."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        sources_list = [
            SourceRecord(
                title="Today",
                url="https://example.com/1",
                relevance=0.95,
                snippet="Today",
                retrieved_at=today.isoformat() + "Z",
            ),
            SourceRecord(
                title="Very Old",
                url="https://example.com/2",
                relevance=0.7,
                snippet="Very old",
                retrieved_at=(today - timedelta(days=1000)).isoformat() + "Z",
            ),
            SourceRecord(
                title="Year Ago",
                url="https://example.com/3",
                relevance=0.8,
                snippet="Year ago",
                retrieved_at=(today - timedelta(days=365)).isoformat() + "Z",
            ),
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=sources_list,
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="all",
            )

            # Should include all sources
            urls = {str(s.url) for s in sources}
            assert "https://example.com/1" in urls
            assert "https://example.com/2" in urls
            assert "https://example.com/3" in urls
            assert len(sources) == 3

    @pytest.mark.asyncio
    async def test_time_range_with_missing_timestamps(self):
        """Test that sources without timestamps are treated as recent."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        source_with_timestamp = SourceRecord(
            title="With Timestamp",
            url="https://example.com/with",
            relevance=0.9,
            snippet="With timestamp",
            retrieved_at=(today - timedelta(days=45)).isoformat() + "Z",
        )
        source_without_timestamp = SourceRecord(
            title="Without Timestamp",
            url="https://example.com/without",
            relevance=0.8,
            snippet="Without timestamp",
            retrieved_at=None,  # No timestamp - assume recent
        )

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=[source_with_timestamp, source_without_timestamp],
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=10,
                time_range="month",
            )

            urls = {str(s.url) for s in sources}
            # Old source should be filtered out
            assert "https://example.com/with" not in urls
            # Source without timestamp should be included (treated as recent)
            assert "https://example.com/without" in urls
            assert len(sources) == 1

    @pytest.mark.asyncio
    async def test_combined_time_range_and_max_sources(self):
        """Test time_range and max_sources working together."""
        retrieval_service = RetrievalService()

        today = datetime.utcnow()
        # Create 10 recent sources (all within month)
        recent_sources = [
            SourceRecord(
                title=f"Source {i}",
                url=f"https://example.com/recent/{i}",
                relevance=0.9,
                snippet=f"Content {i}",
                retrieved_at=(today - timedelta(days=10)).isoformat() + "Z",
            )
            for i in range(10)
        ]
        # Add 5 old sources (outside month)
        old_sources = [
            SourceRecord(
                title=f"Old Source {i}",
                url=f"https://example.com/old/{i}",
                relevance=0.7,
                snippet=f"Old content {i}",
                retrieved_at=(today - timedelta(days=45)).isoformat() + "Z",
            )
            for i in range(5)
        ]

        with patch.object(
            retrieval_service.tavily_tool,
            "search",
            new_callable=AsyncMock,
            return_value=recent_sources + old_sources,
        ):
            sources = await retrieval_service.retrieve_sources(
                query="test",
                depth="intermediate",
                max_sources=7,
                time_range="month",
            )

            # Should have 7 sources (max_sources limit) from recent sources only
            assert len(sources) == 7
            for source in sources:
                assert "https://example.com/recent/" in str(source.url)
                assert "https://example.com/old/" not in str(source.url)
