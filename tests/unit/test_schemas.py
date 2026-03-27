"""Unit tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.research import (
    ResearchQuery,
    ResearchBrief,
    SourceRecord,
    ConfidenceAssessment,
    ErrorResponse,
)

# ============================================================================
# ResearchQuery Schema Tests
# ============================================================================


class TestResearchQuery:
    """Test cases for ResearchQuery schema validation."""

    def test_valid_query_with_defaults(self):
        """Test creating a ResearchQuery with valid input and defaults."""
        query = ResearchQuery(query="What is artificial intelligence?")

        assert query.query == "What is artificial intelligence?"
        assert query.depth == "intermediate"
        assert query.max_sources == 10
        assert query.time_range == "all"

    def test_valid_query_with_all_parameters(self):
        """Test creating a ResearchQuery with all parameters specified."""
        query = ResearchQuery(
            query="recent quantum computing advances",
            depth="deep",
            max_sources=20,
            time_range="month",
        )

        assert query.depth == "deep"
        assert query.max_sources == 20
        assert query.time_range == "month"

    def test_invalid_query_too_short(self):
        """Test that query shorter than 3 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery(query="ab")

        assert "at least 3 characters" in str(exc_info.value).lower()

    def test_invalid_query_too_long(self):
        """Test that query longer than 500 characters is rejected."""
        long_query = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            ResearchQuery(query=long_query)

        assert "at most 500 characters" in str(exc_info.value).lower()

    def test_invalid_depth_value(self):
        """Test that invalid depth value is rejected."""
        with pytest.raises(ValidationError):
            ResearchQuery(
                query="test query",
                depth="ultra_deep",  # Invalid
            )

    def test_invalid_max_sources_below_min(self):
        """Test that max_sources < 1 is rejected."""
        with pytest.raises(ValidationError):
            ResearchQuery(query="test", max_sources=0)

    def test_invalid_max_sources_above_max(self):
        """Test that max_sources > 50 is rejected."""
        with pytest.raises(ValidationError):
            ResearchQuery(query="test", max_sources=51)

    def test_invalid_time_range_value(self):
        """Test that invalid time_range value is rejected."""
        with pytest.raises(ValidationError):
            ResearchQuery(
                query="test query",
                time_range="century",  # Invalid
            )


# ============================================================================
# SourceRecord Schema Tests
# ============================================================================


class TestSourceRecord:
    """Test cases for SourceRecord schema validation."""

    def test_valid_source_record(self, sample_source_record_data):
        """Test creating a valid SourceRecord."""
        source = SourceRecord(**sample_source_record_data)

        assert source.title == sample_source_record_data["title"]
        assert source.relevance == sample_source_record_data["relevance"]

    def test_source_record_url_validation(self):
        """Test that invalid URL is rejected."""
        with pytest.raises(ValidationError):
            SourceRecord(
                title="Test Article",
                url="not-a-valid-url",  # Invalid
                relevance=0.8,
            )

    def test_source_record_relevance_boundaries(self):
        """Test relevance score boundaries (0.0-1.0)."""
        # Valid boundaries
        source = SourceRecord(
            title="Test Article Title",
            url="https://example.com",
            relevance=0.0,
        )
        assert source.relevance == 0.0

        source = SourceRecord(
            title="Test Article Title",
            url="https://example.com",
            relevance=1.0,
        )
        assert source.relevance == 1.0

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            SourceRecord(
                title="Test Article Title",
                url="https://example.com",
                relevance=1.5,
            )

    def test_source_record_title_too_short(self):
        """Test that title shorter than 5 characters is rejected."""
        with pytest.raises(ValidationError):
            SourceRecord(
                title="Hi",  # Too short
                url="https://example.com",
                relevance=0.8,
            )


# ============================================================================
# ResearchBrief Schema Tests
# ============================================================================


class TestResearchBrief:
    """Test cases for ResearchBrief schema validation."""

    def test_valid_brief(self, sample_source_record_data):
        """Test creating a valid ResearchBrief."""
        brief = ResearchBrief(
            summary="Recent advances in quantum computing show significant progress.",
            key_points=[
                "Enhanced qubit count",
                "Improved error correction",
            ],
            sources=[SourceRecord(**sample_source_record_data)],
            confidence_score=0.85,
        )

        assert len(brief.key_points) == 2
        assert brief.confidence_score == 0.85
        assert len(brief.sources) == 1

    def test_brief_summary_too_short(self, sample_source_record_data):
        """Test that summary shorter than 50 characters is rejected."""
        with pytest.raises(ValidationError):
            ResearchBrief(
                summary="Short",  # Too short
                key_points=["Point 1"],
                sources=[SourceRecord(**sample_source_record_data)],
                confidence_score=0.8,
            )

    def test_brief_no_key_points(self, sample_source_record_data):
        """Test that brief with no key points is rejected."""
        with pytest.raises(ValidationError):
            ResearchBrief(
                summary="Valid summary with sufficient length for testing.",
                key_points=[],  # Empty list not allowed
                sources=[SourceRecord(**sample_source_record_data)],
                confidence_score=0.8,
            )

    def test_brief_no_sources(self):
        """Test that brief with no sources is rejected."""
        with pytest.raises(ValidationError):
            ResearchBrief(
                summary="Valid summary with sufficient length for testing.",
                key_points=["Point 1"],
                sources=[],  # Empty sources not allowed
                confidence_score=0.8,
            )

    def test_brief_confidence_score_boundaries(self, sample_source_record_data):
        """Test confidence_score boundaries."""
        # Valid at 0.0
        brief = ResearchBrief(
            summary="Valid summary with sufficient length for testing purposes.",
            key_points=["Point"],
            sources=[SourceRecord(**sample_source_record_data)],
            confidence_score=0.0,
        )
        assert brief.confidence_score == 0.0

        # Invalid: negative
        with pytest.raises(ValidationError):
            ResearchBrief(
                summary="Valid summary with sufficient length for testing purposes.",
                key_points=["Point"],
                sources=[SourceRecord(**sample_source_record_data)],
                confidence_score=-0.1,
            )


# ============================================================================
# ConfidenceAssessment Schema Tests
# ============================================================================


class TestConfidenceAssessment:
    """Test cases for ConfidenceAssessment schema validation."""

    def test_valid_assessment(self):
        """Test creating a valid ConfidenceAssessment."""
        assessment = ConfidenceAssessment(
            source_agreement=0.9,
            source_quality=0.85,
            recency=0.8,
            freshness=1.0,
            contradiction_penalty=0.05,
            final_score=0.85,
        )

        assert assessment.final_score == 0.85

    def test_assessment_all_scores_between_0_and_1(self):
        """Test that all scores must be between 0.0 and 1.0."""
        valid_score = 0.5

        # Test invalid source_agreement
        with pytest.raises(ValidationError):
            ConfidenceAssessment(
                source_agreement=1.5,  # Invalid
                source_quality=valid_score,
                recency=valid_score,
                freshness=valid_score,
                contradiction_penalty=valid_score,
                final_score=valid_score,
            )


# ============================================================================
# ErrorResponse Schema Tests
# ============================================================================


class TestErrorResponse:
    """Test cases for ErrorResponse schema validation."""

    def test_valid_error_response(self):
        """Test creating a valid ErrorResponse."""
        error = ErrorResponse(
            error_code="INVALID_INPUT",
            message="Query parameter is invalid",
        )

        assert error.error_code == "INVALID_INPUT"
        assert error.message == "Query parameter is invalid"
        assert error.details is None

    def test_error_response_with_details(self):
        """Test ErrorResponse with optional details."""
        error = ErrorResponse(
            error_code="TAVILY_API_ERROR",
            message="External API call failed",
            details={"status_code": 502, "retry_after": 60},
        )

        assert error.details["status_code"] == 502
