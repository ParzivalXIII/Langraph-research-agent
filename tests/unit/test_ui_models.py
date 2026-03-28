"""Unit tests for Pydantic data models (UI layer).

Tests ResearchQuery, ResearchRequest, ResearchResponse, Source, and Diagnostics
validation rules per data-model.md.
"""

import pytest
from pydantic import ValidationError

from ui.models import (
    Diagnostics,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    Source,
)


# ============================================================================
# Test ResearchQuery Validation
# ============================================================================


class TestResearchQuery:
    """Test ResearchQuery model validation."""

    def test_valid_query(self):
        """Valid query with all required fields should pass."""
        data = {
            "query": "What are AI agents?",
            "depth": "intermediate",
            "max_sources": 5,
            "time_range": "month",
        }
        query = ResearchQuery.model_validate(data)
        assert query.query == "What are AI agents?"
        assert query.depth == "intermediate"

    def test_query_empty_string_fails(self):
        """Empty query string should raise ValidationError."""
        data = {
            "query": "",
            "depth": "basic",
            "max_sources": 5,
            "time_range": "all",
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        # Check that validation failed (either min_length or field_validator)
        assert len(exc_info.value.errors()) > 0

    def test_query_whitespace_only_fails(self):
        """Query with only whitespace should raise ValidationError."""
        data = {
            "query": "   \n\t  ",
            "depth": "basic",
            "max_sources": 5,
            "time_range": "all",
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        assert "whitespace" in str(exc_info.value).lower()

    def test_query_whitespace_stripped(self):
        """Query with leading/trailing whitespace should be stripped."""
        data = {
            "query": "  What is quantum computing?  ",
            "depth": "basic",
            "max_sources": 5,
            "time_range": "all",
        }
        query = ResearchQuery.model_validate(data)
        assert query.query == "What is quantum computing?"
        assert query.query == query.query.strip()

    def test_invalid_depth_fails(self):
        """Invalid depth value should raise ValidationError."""
        data = {
            "query": "test query",
            "depth": "advanced",  # Invalid: only basic, intermediate, deep allowed
            "max_sources": 5,
            "time_range": "all",
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("depth",) for e in errors)

    def test_max_sources_below_minimum_fails(self):
        """max_sources < 3 should raise ValidationError."""
        data = {
            "query": "test query",
            "depth": "basic",
            "max_sources": 2,  # Below minimum of 3
            "time_range": "all",
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_sources",) for e in errors)

    def test_max_sources_above_maximum_fails(self):
        """max_sources > 10 should raise ValidationError."""
        data = {
            "query": "test query",
            "depth": "basic",
            "max_sources": 11,  # Above maximum of 10
            "time_range": "all",
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_sources",) for e in errors)

    def test_max_sources_valid_range(self):
        """max_sources in [3, 10] should pass."""
        for count in [3, 5, 10]:
            data = {
                "query": "test query",
                "depth": "basic",
                "max_sources": count,
                "time_range": "all",
            }
            query = ResearchQuery.model_validate(data)
            assert query.max_sources == count

    def test_invalid_time_range_fails(self):
        """Invalid time_range value should raise ValidationError."""
        data = {
            "query": "test query",
            "depth": "basic",
            "max_sources": 5,
            "time_range": "century",  # Invalid
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery.model_validate(data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("time_range",) for e in errors)


# ============================================================================
# Test Source Validation
# ============================================================================


class TestSource:
    """Test Source model validation."""

    def test_valid_source(self):
        """Valid source with all required fields should pass."""
        source = Source(
            title="Example Article",
            url="https://example.com/article",
            relevance=0.85,
        )
        assert source.title == "Example Article"
        assert source.relevance == 0.85

    def test_empty_title_fails(self):
        """Empty title should raise ValidationError."""
        with pytest.raises(ValidationError):
            Source(title="", url="https://example.com", relevance=0.5)

    def test_empty_url_fails(self):
        """Empty URL should raise ValidationError."""
        with pytest.raises(ValidationError):
            Source(title="Example", url="", relevance=0.5)

    def test_relevance_below_zero_fails(self):
        """Relevance < 0.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            Source(title="Example", url="https://example.com", relevance=-0.1)

    def test_relevance_above_one_fails(self):
        """Relevance > 1.0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            Source(title="Example", url="https://example.com", relevance=1.1)

    def test_relevance_boundary_values(self):
        """Relevance at boundaries 0.0 and 1.0 should pass."""
        for rel in [0.0, 1.0]:
            source = Source(title="Example", url="https://example.com", relevance=rel)
            assert source.relevance == rel


# ============================================================================
# Test ResearchResponse Validation
# ============================================================================


class TestResearchResponse:
    """Test ResearchResponse model validation."""

    def test_valid_response(self):
        """Valid response with all required fields should pass."""
        data = {
            "summary": "This is a comprehensive summary",
            "key_points": ["Point 1", "Point 2"],
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1", "relevance": 0.9}
            ],
            "contradictions": ["Contradiction 1"],
            "confidence_score": 0.78,
        }
        response = ResearchResponse.model_validate(data)
        assert response.summary == "This is a comprehensive summary"
        assert len(response.key_points) == 2
        assert response.confidence_score == 0.78

    def test_empty_summary_fails(self):
        """Empty summary should raise ValidationError."""
        data = {
            "summary": "",
            "key_points": [],
            "sources": [],
            "contradictions": [],
            "confidence_score": 0.5,
        }
        with pytest.raises(ValidationError) as exc_info:
            ResearchResponse.model_validate(data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("summary",) for e in errors)

    def test_key_points_with_empty_string_fails(self):
        """Key points list with empty string items should raise ValidationError."""
        data = {
            "summary": "Valid summary",
            "key_points": ["Valid point", ""],  # Empty string in list
            "sources": [],
            "contradictions": [],
            "confidence_score": 0.5,
        }
        with pytest.raises(ValidationError):
            ResearchResponse.model_validate(data)

    def test_contradictions_with_empty_string_fails(self):
        """Contradictions list with empty string items should raise ValidationError."""
        data = {
            "summary": "Valid summary",
            "key_points": [],
            "sources": [],
            "contradictions": ["Valid contradiction", ""],  # Empty string
            "confidence_score": 0.5,
        }
        with pytest.raises(ValidationError):
            ResearchResponse.model_validate(data)

    def test_confidence_out_of_range_fails(self):
        """Confidence score outside [0.0, 1.0] should raise ValidationError."""
        for invalid_score in [-0.1, 1.1]:
            data = {
                "summary": "Valid summary",
                "key_points": [],
                "sources": [],
                "contradictions": [],
                "confidence_score": invalid_score,
            }
            with pytest.raises(ValidationError):
                ResearchResponse.model_validate(data)

    def test_empty_optional_arrays_pass(self):
        """Empty key_points, sources, and contradictions should pass."""
        data = {
            "summary": "Valid summary",
            "key_points": [],
            "sources": [],
            "contradictions": [],
            "confidence_score": 0.5,
        }
        response = ResearchResponse.model_validate(data)
        assert response.key_points == []
        assert response.sources == []
        assert response.contradictions == []

    def test_invalid_source_in_sources_list_fails(self):
        """Invalid source object in sources list should raise ValidationError."""
        data = {
            "summary": "Valid summary",
            "key_points": [],
            "sources": [
                {"title": "", "url": "https://example.com", "relevance": 0.5}  # Empty title
            ],
            "contradictions": [],
            "confidence_score": 0.5,
        }
        with pytest.raises(ValidationError):
            ResearchResponse.model_validate(data)


# ============================================================================
# Test Diagnostics Validation
# ============================================================================


class TestDiagnostics:
    """Test Diagnostics model validation."""

    def test_valid_diagnostics(self):
        """Valid diagnostics with all required fields should pass."""
        data = {
            "request_payload": {"query": "test", "depth": "basic", "max_sources": 5, "time_range": "all"},
            "response_status": "success",
            "error_message": "",
            "response_shape": {"summary": "str"},
            "execution_time_ms": 100,
        }
        diag = Diagnostics.model_validate(data)
        assert diag.response_status == "success"
        assert diag.execution_time_ms == 100

    def test_valid_response_statuses(self):
        """All valid response_status values should pass."""
        valid_statuses = ["success", "timeout", "http_error", "validation_error", "unknown_error"]
        for status in valid_statuses:
            diag = Diagnostics(
                request_payload={},
                response_status=status,
            )
            assert diag.response_status == status
