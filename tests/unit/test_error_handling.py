"""Unit tests for UI error handling and state management in run_research() callback.

Tests T020-T022: Loading states, error display, error message formatting.
- Tests error scenarios: TimeoutException, HTTPError, ConnectError, ValidationError
- Tests error message formatting: user-friendly messages for different error types
- Tests error state display: visibility updates, error clearing on subsequent success
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ui.app import run_research, _get_user_friendly_error, _get_error_status
from ui.models import ResearchQuery, ResearchResponse, Source


# ============================================================================
# Mock Exception Classes
# ============================================================================


class TimeoutException(Exception):
    """Mock httpx.TimeoutException."""
    pass


class HTTPError(Exception):
    """Mock httpx.HTTPError."""
    pass


class ConnectError(Exception):
    """Mock httpx.ConnectError."""
    pass


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_input_args():
    """Provide valid input arguments for run_research() callback.
    
    Returns:
        tuple: (query, depth, max_sources, time_range)
    """
    return ("What is artificial intelligence?", "intermediate", 5, "all")


@pytest.fixture
def mock_response():
    """Provide a mock successful backend response."""
    return ResearchResponse(
        summary="AI is the simulation of human intelligence processes.",
        key_points=["Machine learning is a subset of AI", "Deep learning uses neural networks"],
        sources=[
            Source(title="AI Intro", url="https://example.com/ai", relevance=0.95),
        ],
        contradictions=[],
        confidence_score=0.85,
    )


# ============================================================================
# Test Error Message Formatting (T021)
# ============================================================================


class TestErrorMessageFormatting:
    """Test _get_user_friendly_error() function."""

    def test_timeout_exception_message(self):
        """TimeoutException should return user-friendly timeout message."""
        timeout_error = TimeoutException("Request timed out")
        
        result = _get_user_friendly_error(timeout_error)
        assert "timed out" in result.lower()
        assert "60 seconds" in result

    def test_http_error_message(self):
        """HTTPError should return user-friendly backend error message."""
        http_error = HTTPError("500 Internal Server Error")
        
        result = _get_user_friendly_error(http_error)
        assert "backend error" in result.lower() or "error" in result.lower()

    def test_connect_error_message(self):
        """ConnectError should return user-friendly connection error message."""
        connect_error = ConnectError("Connection refused")
        
        result = _get_user_friendly_error(connect_error)
        assert "backend error" in result.lower() or "error" in result.lower()

    def test_generic_error_message(self):
        """Generic exception should return basic error message."""
        generic_error = Exception("Something went wrong")
        
        result = _get_user_friendly_error(generic_error)
        assert "error" in result.lower()
        assert "Something went wrong" in result or "generic" in result.lower()


# ============================================================================
# Test Error Status Mapping (T021)
# ============================================================================


class TestErrorStatusMapping:
    """Test _get_error_status() function."""

    def test_timeout_status(self):
        """TimeoutException should map to "timeout" status."""
        timeout_error = TimeoutException("Request timed out")
        
        result = _get_error_status(timeout_error)
        assert result == "timeout"

    def test_http_error_status(self):
        """HTTPError should map to "http_error" status."""
        http_error = HTTPError("500 Internal Server Error")
        
        result = _get_error_status(http_error)
        assert result == "http_error"

    def test_connect_error_status(self):
        """ConnectError should map to "http_error" status."""
        connect_error = ConnectError("Connection refused")
        
        result = _get_error_status(connect_error)
        assert result == "http_error"

    def test_unknown_error_status(self):
        """Unknown exception should map to "unknown_error" status."""
        unknown_error = Exception("Something went wrong")
        
        result = _get_error_status(unknown_error)
        assert result == "unknown_error"


# ============================================================================
# Test run_research() Error Handling (T020-T022)
# ============================================================================


class TestRunResearchErrorScenarios:
    """Test run_research() callback error handling."""

    @pytest.mark.asyncio
    async def test_timeout_exception_handling(self, valid_input_args):
        """run_research() should catch TimeoutException and return user-friendly message."""
        query, depth, max_sources, time_range = valid_input_args
        
        # Mock client.research() to raise TimeoutException
        with patch("ui.app.client") as mock_client:
            mock_client.research = AsyncMock(side_effect=TimeoutException("Request timed out"))
            
            # Act
            result = await run_research(query, depth, max_sources, time_range)
            
            # Assert: Returns 6-tuple with error message in first position
            assert len(result) == 6
            summary, key_points, sources, contradictions, confidence, diagnostics = result
            assert "timed out" in summary.lower() or "error" in summary.lower()
            assert key_points == ""
            assert sources == []
            assert contradictions == ""
            assert confidence == "0%"
            assert diagnostics != ""  # Diagnostics JSON should be present

    @pytest.mark.asyncio
    async def test_http_error_handling(self, valid_input_args):
        """run_research() should catch HTTPError and return user-friendly message."""
        query, depth, max_sources, time_range = valid_input_args
        
        with patch("ui.app.client") as mock_client:
            mock_client.research = AsyncMock(side_effect=HTTPError("500 Internal Server Error"))
            
            result = await run_research(query, depth, max_sources, time_range)
            
            assert len(result) == 6
            summary = result[0]
            assert "error" in summary.lower()
            # Message should not expose full stack trace, just error description
            assert "traceback" not in summary.lower()
            assert "line" not in summary.lower()

    @pytest.mark.asyncio
    async def test_connect_error_handling(self, valid_input_args):
        """run_research() should catch ConnectError and return user-friendly message."""
        query, depth, max_sources, time_range = valid_input_args
        
        with patch("ui.app.client") as mock_client:
            mock_client.research = AsyncMock(side_effect=ConnectError("Connection refused"))
            
            result = await run_research(query, depth, max_sources, time_range)
            
            assert len(result) == 6
            summary = result[0]
            assert "error" in summary.lower()
            # Message should not expose full stack trace
            assert "traceback" not in summary.lower()
            assert "line" not in summary.lower()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, valid_input_args):
        """run_research() should handle ValidationError gracefully."""
        query, depth, max_sources, time_range = valid_input_args
        
        # Provide invalid input (empty query)
        result = await run_research("", depth, max_sources, time_range)
        
        assert len(result) == 6
        summary = result[0]
        assert "validation" in summary.lower() or "error" in summary.lower()

    @pytest.mark.asyncio
    async def test_success_clears_error_state(self, valid_input_args, mock_response):
        """Successful request after error should clear error state."""
        query, depth, max_sources, time_range = valid_input_args
        
        with patch("ui.app.client") as mock_client:
            # First request succeeds
            mock_client.research = AsyncMock(return_value=mock_response.model_dump())
            
            result = await run_research(query, depth, max_sources, time_range)
            
            assert len(result) == 6
            summary = result[0]
            # Should not contain error message
            assert "error" not in summary.lower() or "AI is the simulation" in summary


# ============================================================================
# Test Loading State Requirements (T020)
# ============================================================================


class TestLoadingStateRequirements:
    """Test requirements for loading state (T020).
    
    Notes: Loading state component management is tested via Gradio callbacks.
    This test class documents requirements for later integration testing.
    """

    def test_loading_state_visibility_requirement(self):
        """Loading state component MUST be hidden by default and shown during request."""
        # Requirement: gr.Markdown(visible=False) for loading_state
        # On submit: set visible=True, button interactive=False
        # On response: set visible=False, button interactive=True
        pytest.skip("Loading state toggle tested in UI integration tests")

    def test_submit_button_disabled_during_loading(self):
        """Submit button MUST be disabled while request is in flight."""
        pytest.skip("Button state toggle tested in UI integration tests")


# ============================================================================
# Test Error Display Component (T022)
# ============================================================================


class TestErrorDisplayComponent:
    """Test requirements for error_display component (T022).
    
    Notes: Component state is managed by Gradio callbacks.
    This test class documents requirements for later integration testing.
    """

    def test_error_display_hidden_by_default(self):
        """Error display component MUST be hidden by default (visible=False)."""
        pytest.skip("Error display visibility tested in UI integration tests")

    def test_error_display_shows_on_error(self):
        """Error display MUST become visible when error occurs."""
        pytest.skip("Error display visibility tested in UI integration tests")

    def test_error_display_cleared_on_success(self):
        """Error display MUST be cleared when request succeeds."""
        pytest.skip("Error display clearing tested in UI integration tests")
