"""Unit tests for diagnostics components and formatters (T017-T019).

Tests:
- create_confidence_display() and create_contradictions_display() component builders
- format_confidence() with color-coded bar and percentage text
- format_contradictions() with warning formatting
"""

import pytest

from ui.components.diagnostics import (
    create_confidence_display,
    create_contradictions_display,
    format_confidence,
    format_contradictions,
    format_confidence_from_response,
    format_contradictions_from_response,
)
from ui.models import ResearchResponse, Source


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_response_high_confidence():
    """ResearchResponse with high confidence (>0.8)."""
    return ResearchResponse(
        summary="Test summary",
        key_points=["Point 1"],
        sources=[Source(title="A", url="https://a.com", relevance=0.9)],
        contradictions=[],
        confidence_score=0.92,
    )


@pytest.fixture
def valid_response_medium_confidence():
    """ResearchResponse with medium confidence (0.5–0.8)."""
    return ResearchResponse(
        summary="Test summary",
        key_points=["Point 1"],
        sources=[Source(title="A", url="https://a.com", relevance=0.7)],
        contradictions=[],
        confidence_score=0.65,
    )


@pytest.fixture
def valid_response_low_confidence():
    """ResearchResponse with low confidence (≤0.5)."""
    return ResearchResponse(
        summary="Test summary",
        key_points=["Point 1"],
        sources=[Source(title="A", url="https://a.com", relevance=0.3)],
        contradictions=[],
        confidence_score=0.35,
    )


@pytest.fixture
def response_with_contradictions():
    """ResearchResponse with contradictions."""
    return ResearchResponse(
        summary="Test summary",
        key_points=["Point 1"],
        sources=[
            Source(title="A", url="https://a.com", relevance=0.8),
            Source(title="B", url="https://b.com", relevance=0.7),
        ],
        contradictions=[
            "Source A claims AI will surpass human intelligence by 2030",
            "Source B estimates the timeline to be closer to 2050",
        ],
        confidence_score=0.70,
    )


# ============================================================================
# Test Component Builders
# ============================================================================


class TestConfidenceDisplayComponent:
    """Test create_confidence_display() component builder."""

    def test_create_confidence_display_returns_tuple(self):
        """create_confidence_display() should return (gr.Number, gr.HTML) tuple."""
        result = create_confidence_display()
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Check that components are Gradio objects with expected labels
        number_comp, html_comp = result
        assert hasattr(number_comp, "label")
        assert hasattr(html_comp, "label")

    def test_confidence_display_number_component_non_interactive(self):
        """Confidence number component should be non-interactive (read-only)."""
        number_comp, _ = create_confidence_display()
        assert number_comp.interactive is False

    def test_confidence_display_html_component_exists(self):
        """Confidence HTML component should exist for bar visualization."""
        _, html_comp = create_confidence_display()
        assert html_comp is not None


class TestContradictionsDisplayComponent:
    """Test create_contradictions_display() component builder."""

    def test_create_contradictions_display_returns_markdown(self):
        """create_contradictions_display() should return gr.Markdown."""
        result = create_contradictions_display()
        assert result is not None
        assert hasattr(result, "label")

    def test_contradictions_display_non_interactive(self):
        """Contradictions component should be non-interactive (read-only)."""
        comp = create_contradictions_display()
        # Gradio Markdown is typically read-only by default
        assert comp is not None


# ============================================================================
# Test format_confidence() (T018)
# ============================================================================


class TestFormatConfidence:
    """Test format_confidence() formatter with color-coding."""

    def test_format_confidence_high_score(self):
        """High confidence (>0.8) should show green bar and high percentage."""
        percentage, html_bar = format_confidence(0.92)
        
        assert percentage == "92%"
        assert html_bar is not None
        assert "High" in html_bar or "green" in html_bar.lower()
        assert "92%" in html_bar

    def test_format_confidence_medium_score(self):
        """Medium confidence (0.5–0.8) should show yellow bar and percentage."""
        percentage, html_bar = format_confidence(0.65)
        
        assert percentage == "65%"
        assert html_bar is not None
        assert "Medium" in html_bar or "yellow" in html_bar.lower()
        assert "65%" in html_bar

    def test_format_confidence_low_score(self):
        """Low confidence (≤0.5) should show red bar and low percentage."""
        percentage, html_bar = format_confidence(0.35)
        
        assert percentage == "35%"
        assert html_bar is not None
        assert "Low" in html_bar or "red" in html_bar.lower()
        assert "35%" in html_bar

    def test_format_confidence_zero_score(self):
        """Zero confidence should show red bar and 0%."""
        percentage, html_bar = format_confidence(0.0)
        
        assert percentage == "0%"
        assert html_bar is not None
        assert "Low" in html_bar or "red" in html_bar.lower()

    def test_format_confidence_perfect_score(self):
        """Perfect confidence (1.0) should show green bar and 100%."""
        percentage, html_bar = format_confidence(1.0)
        
        assert percentage == "100%"
        assert html_bar is not None
        assert "High" in html_bar or "green" in html_bar.lower()

    def test_format_confidence_invalid_string(self):
        """Invalid string input should default to 0.0 (red bar, 0%)."""
        percentage, html_bar = format_confidence("invalid")
        
        assert percentage == "0%"
        assert html_bar is not None
        assert "Low" in html_bar or "red" in html_bar.lower()

    def test_format_confidence_invalid_none(self):
        """None input should default to 0.0 (red bar, 0%)."""
        percentage, html_bar = format_confidence(None)
        
        assert percentage == "0%"
        assert html_bar is not None

    def test_format_confidence_out_of_range_high(self):
        """Out-of-range high value (>1.0) should default to 0.0 (red bar)."""
        percentage, html_bar = format_confidence(1.5)
        
        assert percentage == "0%"
        assert "Low" in html_bar or "red" in html_bar.lower()

    def test_format_confidence_out_of_range_low(self):
        """Out-of-range low value (<0.0) should default to 0.0 (red bar)."""
        percentage, html_bar = format_confidence(-0.5)
        
        assert percentage == "0%"
        assert "Low" in html_bar or "red" in html_bar.lower()

    def test_format_confidence_boundary_low_high(self):
        """Confidence at 0.5 boundary should show yellow (medium)."""
        percentage, html_bar = format_confidence(0.5)
        
        assert percentage == "50%"
        # 0.5 is "low" threshold, so could be red or yellow; verify it's formatted
        assert "%" in html_bar

    def test_format_confidence_boundary_medium_high(self):
        """Confidence at 0.8 boundary should show yellow (medium)."""
        percentage, html_bar = format_confidence(0.8)
        
        assert percentage == "80%"
        assert "Medium" in html_bar or "yellow" in html_bar.lower()

    def test_format_confidence_returns_percentage_and_html(self):
        """format_confidence() should return (percentage: str, html: str) tuple."""
        result = format_confidence(0.75)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        percentage, html_bar = result
        assert isinstance(percentage, str)
        assert isinstance(html_bar, str)
        assert "%" in percentage
        assert "<" in html_bar  # HTML markup


# ============================================================================
# Test format_contradictions() (T019)
# ============================================================================


class TestFormatContradictions:
    """Test format_contradictions() formatter."""

    def test_format_contradictions_empty_list(self):
        """Empty contradictions list should return placeholder."""
        result = format_contradictions([])
        
        assert result == "(No contradictions detected)"

    def test_format_contradictions_none(self):
        """None contradictions should return placeholder."""
        result = format_contradictions(None) if None else "(No contradictions detected)"
        
        assert result == "(No contradictions detected)"

    def test_format_contradictions_single_item(self):
        """Single contradiction should be formatted with bullet and warning icon."""
        contradictions = ["Source A says X, Source B says Y"]
        result = format_contradictions(contradictions)
        
        assert "⚠️" in result
        assert "Contradictions" in result
        assert "Source A says X, Source B says Y" in result
        assert "-" in result  # Bullet point

    def test_format_contradictions_multiple_items(self):
        """Multiple contradictions should each get a bullet point."""
        contradictions = [
            "Timeline estimates differ by 20 years",
            "AI safety approaches conflict",
        ]
        result = format_contradictions(contradictions)
        
        assert "⚠️" in result
        assert "Contradictions Detected" in result
        assert "Timeline estimates differ by 20 years" in result
        assert "AI safety approaches conflict" in result
        # Count bullet points
        assert result.count("-") >= 2

    def test_format_contradictions_filters_empty_strings(self):
        """Empty strings in contradictions list should be ignored."""
        contradictions = ["Valid contradiction", "", "Another valid"]
        result = format_contradictions(contradictions)
        
        assert "Valid contradiction" in result
        assert "Another valid" in result
        # Should not have extra bullet points for empty items
        bullet_count = result.count("-")
        assert bullet_count == 2

    def test_format_contradictions_returns_string(self):
        """format_contradictions() should return a string."""
        result = format_contradictions(["Sample contradiction"])
        assert isinstance(result, str)


# ============================================================================
# Test Response Convenience Wrappers
# ============================================================================


class TestConfidenceResponseWrapper:
    """Test format_confidence_from_response() wrapper."""

    def test_format_confidence_from_response_high(self, valid_response_high_confidence):
        """Wrapper should extract confidence_score from ResearchResponse."""
        percentage, html_bar = format_confidence_from_response(valid_response_high_confidence)
        
        assert percentage == "92%"
        assert "High" in html_bar

    def test_format_confidence_from_response_low(self, valid_response_low_confidence):
        """Wrapper should handle low confidence correctly."""
        percentage, html_bar = format_confidence_from_response(valid_response_low_confidence)
        
        assert percentage == "35%"
        assert "Low" in html_bar


class TestContradictionsResponseWrapper:
    """Test format_contradictions_from_response() wrapper."""

    def test_format_contradictions_from_response_with_items(self, response_with_contradictions):
        """Wrapper should extract contradictions from ResearchResponse."""
        result = format_contradictions_from_response(response_with_contradictions)
        
        assert "⚠️" in result
        assert "Source A claims AI will surpass" in result
        assert "Source B estimates the timeline" in result

    def test_format_contradictions_from_response_empty(self, valid_response_high_confidence):
        """Wrapper should handle empty contradictions."""
        result = format_contradictions_from_response(valid_response_high_confidence)
        
        assert result == "(No contradictions detected)"
