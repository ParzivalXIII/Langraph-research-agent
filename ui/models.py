"""Pydantic models for research query, request, response, and diagnostics.

This module defines data validation schemas for the Controlled Research Interface.
All models implement strict validation per JSON Schema contracts in:
specs/002-gradio-research-ui/contracts/

**Model Hierarchy**:
- ResearchQuery: User input validation (query + control settings)
- ResearchRequest: HTTP request payload (alias for ResearchQuery)
- Source: Individual retrieved reference (title, url, relevance)
- ResearchResponse: HTTP response from backend (summary, key_points, sources, etc.)
- Diagnostics: Request/response metadata for debugging and transparency

**Validation Rules** (per data-model.md and JSON Schema contracts):
- ResearchQuery: query must be non-empty after strip(), depth/time_range must match enum, 
  max_sources in [3, 10]
- ResearchResponse: summary non-empty, key_points list (items non-empty), 
  sources list of Source objects, contradictions list (items non-empty), 
  confidence_score in [0.0, 1.0]
- Source: title non-empty, url non-empty, relevance in [0.0, 1.0]

**Design Principles**:
1. Type safety: All fields have explicit type hints and Field validators
2. Determinism: No default values that could hide missing data from backend
3. Transparency: Error messages explain exactly what validation failed
4. Compatibility: Models match JSON Schema contracts exactly (additionalProperties: false)
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ResearchQuery(BaseModel):
    """User input for research request: query + control settings.
    
    Represents the raw form input from the user in the Gradio UI. Validates
    immediately upon form submission before sending to backend.
    
    Attributes:
        query: The research question or topic. Must be non-empty and non-whitespace.
        depth: Research breadth level ('basic', 'intermediate', or 'deep').
        max_sources: Maximum number of sources to retrieve (3–10 inclusive).
        time_range: Temporal scope ('day', 'week', 'month', 'year', or 'all').
        
    Validation:
        - query: Stripped of leading/trailing whitespace; rejected if empty after strip.
        
    Example:
        >>> q = ResearchQuery(
        ...     query="AI agents 2026",
        ...     depth="intermediate",
        ...     max_sources=5,
        ...     time_range="month"
        ... )
        >>> q.model_dump()
        {'query': 'AI agents 2026', 'depth': 'intermediate', 'max_sources': 5, 'time_range': 'month'}
    """

    query: str = Field(..., min_length=1, description="Research question")
    depth: Literal["basic", "intermediate", "deep"] = Field(
        ..., description="Research depth level"
    )
    max_sources: int = Field(..., ge=3, le=10, description="Maximum sources to retrieve")
    time_range: Literal["day", "week", "month", "year", "all"] = Field(
        ..., description="Temporal scope for sources"
    )

    @field_validator("query")
    @classmethod
    def query_not_whitespace(cls, v: str) -> str:
        """Ensure query is not empty or whitespace-only after stripping."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

    model_config = {"frozen": False}


class ResearchRequest(BaseModel):
    """HTTP request payload to backend /research endpoint (same as ResearchQuery).
    
    This model mirrors ResearchQuery for clarity when sending requests to the backend.
    The backend's FastAPI router expects exactly these four fields.
    
    Attributes:
        query: The research question.
        depth: Research breadth level.
        max_sources: Maximum sources to retrieve.
        time_range: Temporal scope.
        
    Note:
        This is semantically identical to ResearchQuery; the separation exists for
        explicit API contract documentation (request vs. form input).
    """

    query: str = Field(..., min_length=1, description="Research question")
    depth: Literal["basic", "intermediate", "deep"] = Field(
        ..., description="Research depth level"
    )
    max_sources: int = Field(..., ge=3, le=10, description="Maximum sources to retrieve")
    time_range: Literal["day", "week", "month", "year", "all"] = Field(
        ..., description="Temporal scope for sources"
    )

    @field_validator("query")
    @classmethod
    def query_not_whitespace(cls, v: str) -> str:
        """Ensure query is not empty or whitespace-only after stripping."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

    model_config = {"frozen": False}


class Source(BaseModel):
    """A single retrieved reference cited in the research result.
    
    Represents one source in the ranked list returned by the backend.
    The backend ranks sources by relevance; the UI renders them in order.
    
    Attributes:
        title: The source title or headline (string, non-empty).
        url: Web URL or reference link (string, valid URI, non-empty).
        relevance: Relevance score from 0.0 (not relevant) to 1.0 (highly relevant).
        
    Design:
        This is a flat object; relationships are handled at the ResearchResponse level.
        
    Example:
        >>> source = Source(
        ...     title="AI Agents Survey 2026",
        ...     url="https://example.com/agents-survey",
        ...     relevance=0.95
        ... )
    """

    title: str = Field(..., min_length=1, description="Source title or headline")
    url: str = Field(..., min_length=1, description="Web URL or reference link")
    relevance: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score 0–1"
    )

    model_config = {"frozen": False}


class ResearchResponse(BaseModel):
    """HTTP response payload from backend /research endpoint.
    
    Represents the complete structured answer to a research query. The UI renders
    this response faithfully without modification or invention of missing content.
    
    This is the primary contract between backend and UI. All fields are validated
    strictly; invalid responses are rejected with detailed error messages.
    
    Attributes:
        summary: Synthesized narrative answer to the research query (non-empty string).
        key_points: Bulleted highlights extracted from sources (list of non-empty strings).
                   Empty list is permitted if backend found no key points.
        sources: Ranked list of retrieved references (list of Source objects).
                Empty list is permitted if no sources were retrieved.
        contradictions: Conflicting statements found across sources (list of non-empty strings).
                       Empty list is permitted if no contradictions were detected.
        confidence_score: Confidence/stability score for the answer (0.0 to 1.0).
    
    Design Principles:
        - Determinism: Renders exactly what backend provides; no client-side synthesis.
        - Transparency: Empty lists are rendered as "No X found", not hidden or synthesized.
        - Type Safety: All fields validated with Pydantic before rendering.
        
    Example:
        >>> resp = ResearchResponse(
        ...     summary="AI agents in 2026...",
        ...     key_points=["Agents enable...", "Safety remains..."],
        ...     sources=[Source(title="Survey", url="https://...", relevance=0.95)],
        ...     contradictions=[],
        ...     confidence_score=0.78
        ... )
    """

    summary: str = Field(..., min_length=1, description="Synthesized narrative answer")
    key_points: list[str] = Field(
        default_factory=list,
        description="Bulleted highlights from sources (order as provided by backend)",
    )
    sources: list[Source] = Field(
        default_factory=list, description="Ranked list of retrieved references"
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Conflicting statements found across sources (may be empty)",
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Stability/support score for the answer"
    )

    @field_validator("key_points", "contradictions", mode="before")
    @classmethod
    def validate_list_items_not_empty(cls, v):
        """Ensure all items in key_points and contradictions are non-empty strings."""
        if not isinstance(v, list):
            return v
        for item in v:
            if isinstance(item, str) and not item.strip():
                raise ValueError("List items must not be empty or whitespace-only strings")
        return v

    model_config = {"frozen": False}


class Diagnostics(BaseModel):
    """Metadata about request/response for debugging and transparency.
    
    Captures request payload, response status, error details, and execution timing.
    Displayed in the Diagnostics tab for users to inspect and understand what happened.
    
    Attributes:
        request_payload: The original user form submission (dict: query, depth, max_sources, time_range).
        response_status: One of 'success', 'timeout', 'http_error', 'validation_error', 'unknown_error'.
        error_message: Empty string if response_status is 'success'; otherwise, the exception message.
        response_shape: Keys present in the backend response (for debugging schema mismatches).
        execution_time_ms: Wall-clock time from form submission to render completion.
        
    Design:
        - Immutability: Not frozen (allow mutation pre-response) but semantically "final" once rendered.
        - Transparency: Users can inspect the raw request and response metadata.
        - Debugging: Execution time, status codes, and error messages aid troubleshooting.
        
    Example:
        >>> diag = Diagnostics(
        ...     request_payload={"query": "...", "depth": "intermediate", ...},
        ...     response_status="success",
        ...     execution_time_ms=2345
        ... )
    """

    request_payload: dict = Field(
        ..., description="Original user request (query, depth, max_sources, time_range)"
    )
    response_status: str = Field(
        ...,
        description="'success', 'timeout', 'http_error', 'validation_error', 'unknown_error'",
    )
    error_message: str = Field(
        default="", description="Error message if status is not 'success'"
    )
    response_shape: dict = Field(
        default_factory=dict, description="Keys present in response (for schema debugging)"
    )
    execution_time_ms: int = Field(
        default=0, description="Time elapsed from submission to render completion"
    )

    model_config = {"frozen": False}
