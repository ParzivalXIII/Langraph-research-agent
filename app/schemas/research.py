"""Pydantic schemas for research agent data models."""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

# ============================================================================
# Research Query Schema
# ============================================================================


class ResearchQuery(BaseModel):
    """
    User-submitted research query with search parameters.

    This schema validates the input request to the /research endpoint.
    """

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Research question or topic (3–500 characters)",
    )
    depth: str = Field(
        default="intermediate",
        pattern="^(basic|intermediate|deep)$",
        description="Search breadth: basic (5 sources), intermediate (10), deep (maximum per budget)",
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum sources to retrieve (1–50)",
    )
    time_range: str = Field(
        default="all",
        pattern="^(day|week|month|year|all)$",
        description="Recency filter: day/week/month/year/all",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What are the latest advances in quantum computing?",
                "depth": "intermediate",
                "max_sources": 10,
                "time_range": "month",
            }
        }
    }


# ============================================================================
# Source Record Schema
# ============================================================================


class SourceRecord(BaseModel):
    """
    A single source document used in research brief.

    Represents a source with metadata including relevance and credibility scores.
    """

    title: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Source title (5–500 chars)",
    )
    url: HttpUrl = Field(
        ...,
        description="Source URL (must be valid HTTP(S))",
    )
    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0=low, 1.0=highly relevant)",
    )
    credibility_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Credibility assessment: (0.50×domain_authority) + (0.30×recency) + (0.20×citation_count)",
    )
    snippet: str = Field(
        default="",
        max_length=5000,
        description="Optional excerpt from source (0–5000 chars, Tavily returns up to 4000)",
    )
    retrieved_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when source was retrieved",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "IBM Announces Condor — Quantum Processor",
                "url": "https://example.com/ibm-condor",
                "relevance": 0.95,
                "credibility_score": 0.88,
                "snippet": "IBM has revealed Condor, the most powerful quantum processor...",
                "retrieved_at": "2026-03-26T10:30:00Z",
            }
        }
    }


# ============================================================================
# Confidence Assessment Schema
# ============================================================================


class ConfidenceAssessment(BaseModel):
    """
    Breakdown of how confidence score is calculated.

    Optionally included in responses for observability and debugging.
    """

    source_agreement: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Fraction of sources agreeing (0=conflicting, 1=unanimous)",
    )
    source_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average credibility of sources",
    )
    recency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How recent sources are (1=<7 days, 0.5=7-30 days, 0.2=>30 days)",
    )
    freshness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Boolean boost: 1.0 if >50% sources <30 days, else 0.5",
    )
    contradiction_penalty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Penalty from contradictions (0.05 minor, 0.10 moderate, 0.20 major)",
    )
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Final confidence: 0.40×agreement + 0.30×quality + 0.20×recency + 0.10×freshness - 0.15×penalty",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "source_agreement": 0.9,
                "source_quality": 0.85,
                "recency": 0.9,
                "freshness": 1.0,
                "contradiction_penalty": 0.05,
                "final_score": 0.85,
            }
        }
    }


# ============================================================================
# Research Brief Schema (Main Response)
# ============================================================================


class ResearchBrief(BaseModel):
    """
    Structured research brief synthesized from retrieved sources.

    This is the main response object returned by the /research endpoint.
    """

    summary: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Concise narrative summary (50–2000 chars)",
    )
    key_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Bullet-point highlights (1–10 items)",
    )
    sources: list[SourceRecord] = Field(
        ...,
        min_length=1,
        description="Supporting sources used in synthesis",
    )
    contradictions: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Unresolved conflicts between sources (0–20 items)",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence (0.0=no evidence, 1.0=high agreement)",
    )
    confidence_breakdown: Optional[ConfidenceAssessment] = Field(
        default=None,
        description="Optional detailed breakdown of confidence calculation",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "Quantum computing has advanced significantly with new processor announcements",
                "key_points": [
                    "IBM released Condor with 1121 qubits",
                    "Google announced improved error correction",
                    "Industry shift toward practical quantum advantage",
                ],
                "sources": [
                    {
                        "title": "IBM Quantum Advances",
                        "url": "https://example.com/ibm",
                        "relevance": 0.95,
                        "credibility_score": 0.88,
                    }
                ],
                "contradictions": [
                    "Source A claims quantum advantage achieved; Source B claims still research phase"
                ],
                "confidence_score": 0.85,
            }
        }
    }


# ============================================================================
# Error Response Schema
# ============================================================================


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    Used for validation errors, API errors, and system failures.
    """

    error_code: str = Field(
        ...,
        description="Machine-readable error code (e.g., INVALID_INPUT, TAVILY_API_ERROR)",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    details: Optional[dict] = Field(
        default=None,
        description="Optional additional error details",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error_code": "INVALID_INPUT",
                "message": "Query must be between 3 and 500 characters",
                "details": {"field": "query", "provided_length": 2},
            }
        }
    }
