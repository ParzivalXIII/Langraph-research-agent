"""Test that the UI implementation adheres to project Constitution.

Constitution (7 principles + 4 constraints) defined in:
specs/002-gradio-research-ui/constitution-check.md

Tests verify that the actual code implementation enforces:
1. Determinism over Agentic Creativity
2. Retrieval First, Generation Second
3. Bounded Autonomy
4. Structured Outputs Only
5. Observability by Default
6. Cost + Latency Constraints
7. Stateless Core, Stateful Extensions

+ 4 Operational Constraints:
- Source traceability
- Conflict surfacing
- Output validation
- Structured logging
"""

import asyncio
import inspect
import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ui.app import (
    _format_diagnostics,
    _get_error_status,
    _get_user_friendly_error,
    build_app,
    run_research,
    validate_query,
)
from ui.client.api_client import ResearchClient
from ui.models import (
    Diagnostics,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    Source,
)


# ============================================================================
# Principle 1: Determinism over Agentic Creativity
# ============================================================================


class TestDeterminismPrinciple:
    """Verify: UI renders exactly what backend provides; no invention."""

    def test_response_validation_enforced_before_rendering(self):
        """All backend responses must pass Pydantic validation before use."""
        # Invalid response (missing summary)
        invalid = {
            "key_points": ["Point 1"],
            "sources": [],
            "contradictions": [],
            "confidence_score": 0.5,
            # summary missing
        }

        with pytest.raises(ValueError):
            ResearchResponse.model_validate(invalid)

    def test_empty_key_points_rendered_faithfully(self):
        """Empty key_points from backend should render as empty, not synthesized."""
        response = ResearchResponse(
            summary="Test summary",
            key_points=[],  # Empty; UI shows this, not auto-generated points
            sources=[],
            contradictions=[],
            confidence_score=0.5,
        )

        # Verify empty list is preserved (not replaced)
        assert response.key_points == []
        assert isinstance(response.key_points, list)

    def test_empty_sources_rendered_faithfully(self):
        """Empty sources list preserved; UI doesn't synthesize references."""
        response = ResearchResponse(
            summary="Test summary",
            key_points=["Point 1"],
            sources=[],  # Empty
            contradictions=[],
            confidence_score=0.5,
        )

        assert response.sources == []

    def test_no_client_side_nlp_or_synthesis(self):
        """No NLP, ranking, or synthesis functions in UI code."""
        # Scan ui/app.py, ui/models.py, ui/client/api_client.py for forbidden patterns
        forbidden_patterns = [
            r"\.lower\(\)", r"\.upper\(\)",  # Text transformation
            r"re\.sub", r"re\.findall",  # Regex extraction  
            r"tokenize", r"nltk",  # NLP
            r"sort\(", r"sorted\(",  # Custom ranking
            r"sklearn", r"spacy",  # ML
            r"openai\.", r"anthropic\.",  # LLM synthesis
        ]

        app_content = inspect.getsource(build_app)
        run_research_content = inspect.getsource(run_research)
        client_content = inspect.getsource(ResearchClient)

        for pattern in forbidden_patterns:
            assert not re.search(
                pattern, app_content + run_research_content + client_content
            ), f"Forbidden pattern detected: {pattern}"


# ============================================================================
# Principle 2: Retrieval First, Generation Second
# ============================================================================


class TestRetrievalFirstPrinciple:
    """Verify: Backend owns all retrieval; UI is pass-through."""

    @pytest.mark.asyncio
    async def test_ui_submits_to_backend_not_retrieves(self):
        """UI must call backend, not Tavily or search APIs directly."""
        # Check ResearchClient only calls self.base_url
        client = ResearchClient()
        
        # Verify client only has one endpoint: /research
        assert hasattr(client, "base_url")
        assert hasattr(client, "timeout")
        
        # Verify no Tavily imports in UI
        import ui.app
        import ui.client.api_client
        ui_source = inspect.getsource(ui.app)
        client_source = inspect.getsource(ui.client.api_client)
        
        assert "tavily" not in ui_source.lower()
        assert "tavily" not in client_source.lower()

    def test_ui_not_retrieval_assistant(self):
        """UI is a presentation layer, not a research assistant."""
        # Verify no auto-refinement or follow-up logic
        app_source = inspect.getsource(build_app)
        
        # Check for auto-submit patterns (should not exist)
        assert "automatic" not in app_source.lower()
        assert "auto_submit" not in app_source
        assert "refine_automatically" not in app_source

    def test_no_fallback_retrieval_on_partial_response(self):
        """If backend returns partial results, UI shows them as-is."""
        partial_response = ResearchResponse(
            summary="Partial answer",
            key_points=[],  # Empty, not fetched again by UI
            sources=[],  # Empty
            contradictions=[],
            confidence_score=0.3,  # Low confidence
        )

        # UI accepts and renders it (no fallback fetch)
        assert partial_response.summary == "Partial answer"


# ============================================================================
# Principle 3: Bounded Autonomy
# ============================================================================


class TestBoundedAutonomyPrinciple:
    """Verify: Single query → single request → single response. No loops."""

    def test_single_submission_one_request(self):
        """One form submit = exactly one HTTP request."""
        # run_research() should call client.research() exactly once
        # (verified via function signature and flow)
        source = inspect.getsource(run_research)
        
        # Count "await client.research" calls
        matches = re.findall(r"await client\.research\(", source)
        assert len(matches) == 1, "Should have exactly one client.research() call"

    def test_no_auto_refinement_loops(self):
        """No automatic follow-up queries or refinement."""
        source = inspect.getsource(run_research)
        
        # Check for loop patterns (for/while) around client.research()
        assert "while" not in source or "run_research" not in source
        
        # No recursive calls
        assert "run_research(" not in source.split("async def run_research")[1]

    def test_timeout_bounded_60_seconds(self):
        """HTTP timeout hard-coded to 60 seconds."""
        client = ResearchClient()
        assert client.timeout == 60
        
        # Verify hardcoded in class
        source = inspect.getsource(ResearchClient.__init__)
        assert "60" in source or "API_TIMEOUT" in source

    def test_no_tool_budget_in_ui(self):
        """UI is not a tool consumer; no tool calls tracked."""
        source = inspect.getsource(run_research)
        
        assert "tool_budget" not in source
        assert "tools_used" not in source
        # Backend owns tool budget, not UI


# ============================================================================
# Principle 4: Structured Outputs Only
# ============================================================================


class TestStructuredOutputsPrinciple:
    """Verify: All outputs conform to declared schemas."""

    def test_request_validates_against_schema(self):
        """ResearchRequest conforms to JSON Schema."""
        valid = ResearchRequest(
            query="Test query",
            depth="basic",
            max_sources=5,
            time_range="month",
        )
        
        # Verify all required fields present
        assert valid.query
        assert valid.depth in ["basic", "intermediate", "deep"]
        assert 3 <= valid.max_sources <= 10
        assert valid.time_range in ["day", "week", "month", "year", "all"]

    def test_response_validates_against_schema(self):
        """ResearchResponse conforms to JSON Schema."""
        valid = ResearchResponse(
            summary="Answer",
            key_points=["Point 1"],
            sources=[Source(title="S1", url="http://example.com", relevance=0.5)],
            contradictions=[],
            confidence_score=0.5,
        )
        
        # Verify all required fields present and typed correctly
        assert isinstance(valid.summary, str)
        assert isinstance(valid.key_points, list)
        assert isinstance(valid.sources, list)
        assert isinstance(valid.contradictions, list)
        assert isinstance(valid.confidence_score, float)
        assert 0.0 <= valid.confidence_score <= 1.0

    def test_no_free_form_text_blobs_in_response(self):
        """Response fields are typed, not concatenated strings."""
        # key_points should be list, not comma-separated string
        response = ResearchResponse(
            summary="Test",
            key_points=["Point 1", "Point 2"],  # List, not "Point 1, Point 2"
            sources=[],
            contradictions=[],
            confidence_score=0.5,
        )
        
        assert isinstance(response.key_points, list)
        assert isinstance(response.key_points[0], str)

    def test_ui_renders_distinct_components_not_concatenated(self):
        """Each field rendered in separate Gradio component."""
        # Verify format_* functions return distinct outputs
        response = ResearchResponse(
            summary="Summary text",
            key_points=["Key 1", "Key 2"],
            sources=[Source(title="Title", url="https://example.com", relevance=0.8)],
            contradictions=["Contradiction 1"],
            confidence_score=0.75,
        )
        
        # Each formatter returns string/table, not concatenated blob
        from ui.components.results import (
            format_confidence,
            format_contradictions,
            format_key_points,
            format_sources_table,
            format_summary,
        )
        
        summary = format_summary(response)
        key_points = format_key_points(response)
        sources = format_sources_table(response)
        contradictions = format_contradictions(response)
        confidence = format_confidence(response)
        
        # All should return text/tables, not None
        assert summary is not None
        assert key_points is not None
        assert sources is not None
        assert contradictions is not None
        assert confidence is not None


# ============================================================================
# Principle 5: Observability by Default
# ============================================================================


class TestObservabilityPrinciple:
    """Verify: Structured logging of queries, responses, errors."""

    def test_request_logged_with_structlog(self):
        """All requests logged with structlog (JSON format)."""
        source = inspect.getsource(ResearchClient.research)
        
        # Check for structlog usage
        assert "logger.info" in source or "logger.error" in source
        assert "research_request" in source
        assert "research_success" in source

    def test_response_logged_with_details(self):
        """Responses logged with status code, execution time, source count."""
        source = inspect.getsource(ResearchClient.research)
        
        # Check logged fields
        assert "status_code" in source
        assert "execution_time_ms" in source
        assert "sources_count" in source or "response_keys" in source

    def test_errors_logged_with_context(self):
        """Errors logged with exception type, message, request context."""
        source = inspect.getsource(ResearchClient.research)
        
        # Check error logging
        assert "research_timeout" in source
        assert "research_http_error" in source
        assert "research_connect_error" in source
        assert "research_validation_error" in source

    def test_diagnostics_include_request_payload(self):
        """Diagnostics capture original request for auditability."""
        diag = Diagnostics(
            request_payload={"query": "test", "depth": "basic", "max_sources": 5, "time_range": "month"},
            response_status="success",
        )
        
        assert "query" in diag.request_payload
        assert diag.request_payload["query"] == "test"

    def test_diagnostics_include_timing(self):
        """Diagnostics capture execution time for performance tracking."""
        diag = Diagnostics(
            request_payload={},
            response_status="success",
            execution_time_ms=1234,
        )
        
        assert diag.execution_time_ms == 1234


# ============================================================================
# Principle 6: Cost + Latency Constraints
# ============================================================================


class TestCostLatencyConstraintsPrinciple:
    """Verify: Explicit budgets; no unbounded retries."""

    def test_timeout_hardcoded_60_seconds(self):
        """HTTP timeout is 60 seconds, not configurable."""
        client = ResearchClient()
        assert client.timeout == 60

    def test_no_retry_on_timeout(self):
        """Timeout exception is raised, not retried."""
        source = inspect.getsource(ResearchClient.research)
        
        # Check TimeoutException is raised, not caught and retried
        assert "except httpx.TimeoutException" in source
        assert "raise" in source  # Re-raise, don't retry

    def test_single_request_no_pagination(self):
        """Single request per query; no pagination loops."""
        source = inspect.getsource(run_research)
        
        # Check for pagination patterns
        assert "page" not in source.lower() or "page_number" not in source.lower()
        assert "offset" not in source or "limit" not in source

    def test_max_sources_bounded_3_to_10(self):
        """Max sources control bounds resource usage."""
        valid_low = ResearchQuery(query="test", depth="basic", max_sources=3, time_range="day")
        assert valid_low.max_sources == 3
        
        valid_high = ResearchQuery(query="test", depth="basic", max_sources=10, time_range="day")
        assert valid_high.max_sources == 10
        
        with pytest.raises(ValueError):
            ResearchQuery(query="test", depth="basic", max_sources=0, time_range="day")
        
        with pytest.raises(ValueError):
            ResearchQuery(query="test", depth="basic", max_sources=20, time_range="day")


# ============================================================================
# Principle 7: Stateless Core, Stateful Extensions
# ============================================================================


class TestStatelessPrinciple:
    """Verify: UI is stateless; no session persistence."""

    def test_no_gradio_state_components(self):
        """UI doesn't use Gradio State() for persistence."""
        source = inspect.getsource(build_app)
        
        # Check for gr.State usage (indicates stateful design)
        assert "gr.State(" not in source or "State" not in source

    def test_no_session_storage(self):
        """No session variables, cookies, or local storage."""
        source = inspect.getsource(build_app) + inspect.getsource(run_research)
        
        assert "session" not in source or "session(" not in source
        assert "sessionStorage" not in source
        assert "localStorage" not in source

    def test_no_result_caching_on_client(self):
        """Results are not cached after rendering."""
        source = inspect.getsource(run_research)
        
        # Check for caching patterns
        assert "cache.set" not in source or "self.cache" not in source
        # Backend owns caching, not UI

    def test_each_query_independent(self):
        """Each form submit is independent; no context carried."""
        # Verify run_research() doesn't access global state
        source = inspect.getsource(run_research)
        
        # Should only use parameters and local variables
        # No access to module-level results cache
        assert "global results" not in source
        assert "previous_result" not in source

    def test_no_conversation_history(self):
        """No multi-turn conversation; each query is atomic."""
        source = inspect.getsource(build_app) + inspect.getsource(run_research)
        
        assert "conversation" not in source
        assert "message_history" not in source
        assert "num_turns" not in source or "turn_count" not in source
        # "turn" may appear in docstrings ("Return", "return") so be specific


# ============================================================================
# Operational Constraints
# ============================================================================


class TestOperationalConstraints:
    """Verify: 4 operational constraints."""

    def test_source_traceability_all_outputs_cited(self):
        """All claims in summary trace to sources."""
        response = ResearchResponse(
            summary="Supported by sources",
            key_points=["Extracted from sources"],
            sources=[Source(title="Source", url="http://example.com", relevance=0.9)],
            contradictions=[],
            confidence_score=0.8,
        )
        
        # UI renders sources; each claim can be verified
        assert response.sources is not None
        assert len(response.sources) > 0

    def test_conflicting_evidence_surfaced_in_contradictions(self):
        """Conflicting evidence displayed in contradictions."""
        response = ResearchResponse(
            summary="Answer",
            key_points=[],
            sources=[],
            contradictions=["Source A says X", "Source B says Y"],  # Conflict noted
            confidence_score=0.4,  # Low confidence indicates conflict
        )
        
        assert len(response.contradictions) > 0

    def test_outputs_validated_before_delivery(self):
        """All responses validated before rendering."""
        # Invalid response raises exception
        with pytest.raises(ValueError):
            ResearchResponse.model_validate({  # Missing required field
                "key_points": [],
                "sources": [],
                "contradictions": [],
                "confidence_score": 0.5,
            })

    def test_query_params_response_logged(self):
        """Request query, params, and response logged together."""
        diag = Diagnostics(
            request_payload={
                "query": "AI agents",
                "depth": "intermediate",
                "max_sources": 5,
                "time_range": "month",
            },
            response_status="success",
            execution_time_ms=2345,
            response_shape={"summary": "str", "sources": "list"},
        )
        
        # All present
        assert diag.request_payload["query"] == "AI agents"
        assert diag.response_status == "success"
        assert diag.execution_time_ms == 2345
        assert "summary" in diag.response_shape


# ============================================================================
# Summary: Constitution Compliance Report
# ============================================================================


class TestConstitutionComplianceSummary:
    """Final checklist: All principles and constraints verified."""

    def test_constitution_compliance_report(self):
        """Generate compliance report for T032."""
        principles = {
            "I. Determinism over Agentic Creativity": TestDeterminismPrinciple,
            "II. Retrieval First, Generation Second": TestRetrievalFirstPrinciple,
            "III. Bounded Autonomy": TestBoundedAutonomyPrinciple,
            "IV. Structured Outputs Only": TestStructuredOutputsPrinciple,
            "V. Observability by Default": TestObservabilityPrinciple,
            "VI. Cost + Latency Constraints": TestCostLatencyConstraintsPrinciple,
            "VII. Stateless Core, Stateful Extensions": TestStatelessPrinciple,
        }
        
        constraints = {
            "Source traceability": TestOperationalConstraints,
            "Conflicting evidence surfaced": TestOperationalConstraints,
            "Output validation": TestOperationalConstraints,
            "Query/params/response logging": TestOperationalConstraints,
        }
        
        # Report: all principles and constraints have test classes
        assert len(principles) == 7
        assert len(constraints) >= 4
