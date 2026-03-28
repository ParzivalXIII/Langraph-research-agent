"""Unit tests for UI result rendering components.

Tests format_summary(), format_key_points(), format_sources_table(),
format_contradictions(), format_confidence() functions.
"""

import pytest

from ui.components.results import (
    format_confidence,
    format_contradictions,
    format_key_points,
    format_sources_table,
    format_summary,
)
from ui.models import ResearchResponse, Source


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_response():
    """Provide a valid ResearchResponse for testing."""
    return ResearchResponse(
        summary="AI agents are increasingly autonomous systems in 2026.",
        key_points=["Point 1: Multi-agent frameworks", "Point 2: Tool-using agents"],
        sources=[
            Source(title="Article 1", url="https://example.com/1", relevance=0.95),
            Source(title="Article 2", url="https://example.com/2", relevance=0.87),
        ],
        contradictions=["Source A says X, Source B says Y"],
        confidence_score=0.78,
    )


@pytest.fixture
def empty_response():
    """Provide a ResearchResponse with empty optional fields."""
    return ResearchResponse(
        summary="Some summary",
        key_points=[],
        sources=[],
        contradictions=[],
        confidence_score=0.5,
    )


# ============================================================================
# Test format_summary()
# ============================================================================


class TestFormatSummary:
    """Test format_summary() function."""

    def test_format_summary_valid(self, valid_response):
        """Valid summary should be returned as-is."""
        result = format_summary(valid_response)
        assert result == "AI agents are increasingly autonomous systems in 2026."

    # Note: Empty and whitespace-only summaries are prevented by Pydantic ResearchResponse model
    # (summary has min_length=1 constraint), so format_summary() will never receive an empty summary
    # in normal operation. The placeholder logic is defensive programming.

    def test_format_summary_multiline(self, valid_response):
        """Multiline summary should be preserved."""
        valid_response.summary = "Line 1\n\nLine 2\n\nLine 3"
        result = format_summary(valid_response)
        assert result == "Line 1\n\nLine 2\n\nLine 3"


# ============================================================================
# Test format_key_points()
# ============================================================================


class TestFormatKeyPoints:
    """Test format_key_points() function."""

    def test_format_key_points_valid(self, valid_response):
        """Valid key points should be formatted as bullet list."""
        result = format_key_points(valid_response)
        assert "• Point 1: Multi-agent frameworks" in result
        assert "• Point 2: Tool-using agents" in result
        lines = result.split("\n")
        assert len(lines) == 2

    def test_format_key_points_empty(self, empty_response):
        """Empty key_points should return placeholder."""
        result = format_key_points(empty_response)
        assert result == "(No key points available)"

    def test_format_key_points_single_item(self, valid_response):
        """Single item should still be formatted as bullet."""
        valid_response.key_points = ["Only point"]
        result = format_key_points(valid_response)
        assert result == "• Only point"

    def test_format_key_points_many_items(self, valid_response):
        """Many items should each get a bullet."""
        valid_response.key_points = [f"Point {i}" for i in range(10)]
        result = format_key_points(valid_response)
        lines = result.split("\n")
        assert len(lines) == 10
        assert all(line.startswith("•") for line in lines)


# ============================================================================
# Test format_sources_table()
# ============================================================================


class TestFormatSourcesTable:
    """Test format_sources_table() function."""

    def test_format_sources_table_valid(self, valid_response):
        """Valid sources should be formatted as table rows."""
        result = format_sources_table(valid_response)
        assert len(result) == 2
        # First row: [title, url, relevance_pct]
        assert result[0][0] == "Article 1"
        assert result[0][1] == "https://example.com/1"
        assert result[0][2] == "95%"
        # Second row
        assert result[1][0] == "Article 2"
        assert result[1][2] == "87%"

    def test_format_sources_table_empty(self, empty_response):
        """Empty sources should return empty list."""
        result = format_sources_table(empty_response)
        assert result == []

    def test_format_sources_table_relevance_formatting(self, valid_response):
        """Relevance scores should be formatted as integer percentages."""
        valid_response.sources = [
            Source(title="A", url="https://example.com/a", relevance=0.0),
            Source(title="B", url="https://example.com/b", relevance=1.0),
            Source(title="C", url="https://example.com/c", relevance=0.555),
        ]
        result = format_sources_table(valid_response)
        assert result[0][2] == "0%"
        assert result[1][2] == "100%"
        assert result[2][2] == "55%"  # 0.555 * 100 = 55.5 -> int = 55

    def test_format_sources_table_order_preserved(self, valid_response):
        """Source order from backend should be preserved (no re-sorting)."""
        valid_response.sources = [
            Source(title="Low Relevance", url="https://example.com/low", relevance=0.1),
            Source(title="High Relevance", url="https://example.com/high", relevance=0.9),
            Source(title="Medium Relevance", url="https://example.com/med", relevance=0.5),
        ]
        result = format_sources_table(valid_response)
        assert result[0][0] == "Low Relevance"
        assert result[1][0] == "High Relevance"
        assert result[2][0] == "Medium Relevance"


# ============================================================================
# Test format_contradictions()
# ============================================================================


class TestFormatContradictions:
    """Test format_contradictions() function.
    
    Note: format_contradictions() now delegates to diagnostics.format_contradictions()
    for enhanced formatting with warning indicators and markdown support.
    """

    def test_format_contradictions_valid(self, valid_response):
        """Valid contradictions should be formatted with warning icon."""
        result = format_contradictions(valid_response)
        assert "⚠️" in result
        assert "**Contradictions Detected:**" in result
        assert "Source A says X, Source B says Y" in result

    def test_format_contradictions_empty(self, empty_response):
        """Empty contradictions should return placeholder message."""
        result = format_contradictions(empty_response)
        assert result == "(No contradictions detected)" or result == ""

    def test_format_contradictions_multiple(self, valid_response):
        """Multiple contradictions should each be formatted."""
        valid_response.contradictions = [
            "Contradiction 1",
            "Contradiction 2",
            "Contradiction 3",
        ]
        result = format_contradictions(valid_response)
        assert "Contradiction 1" in result
        assert "Contradiction 2" in result
        assert "Contradiction 3" in result

    def test_format_contradictions_warning_header_only_once(self, valid_response):
        """Warning header should appear only once."""
        valid_response.contradictions = ["C1", "C2"]
        result = format_contradictions(valid_response)
        assert result.count("**Contradictions Detected:**") == 1


# ============================================================================
# Test format_confidence()
# ============================================================================


class TestFormatConfidence:
    """Test format_confidence() function."""

    def test_format_confidence_valid(self, valid_response):
        """Valid confidence score should be formatted as percentage."""
        result = format_confidence(valid_response)
        assert result == "78%"

    def test_format_confidence_boundary_values(self):
        """Boundary values 0.0 and 1.0 should format correctly."""
        response_low = ResearchResponse(
            summary="Test",
            key_points=[],
            sources=[],
            contradictions=[],
            confidence_score=0.0,
        )
        assert format_confidence(response_low) == "0%"

        response_high = ResearchResponse(
            summary="Test",
            key_points=[],
            sources=[],
            contradictions=[],
            confidence_score=1.0,
        )
        assert format_confidence(response_high) == "100%"

    def test_format_confidence_rounding(self):
        """Confidence scores should be truncated to integer percentage."""
        for score, expected_pct in [(0.125, "12%"), (0.875, "87%"), (0.999, "99%")]:
            response = ResearchResponse(
                summary="Test",
                key_points=[],
                sources=[],
                contradictions=[],
                confidence_score=score,
            )
            result = format_confidence(response)
            assert result == expected_pct
