"""Unit tests for HTTP client ResearchClient.

Tests async research() method with mocked httpx responses,
error handling (timeout, HTTP errors, validation), and logging.
"""

import asyncio

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ui.client.api_client import ResearchClient
from ui.models import ResearchResponse


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Provide ResearchClient instance for testing."""
    return ResearchClient(base_url="http://localhost:8000", timeout=60)


@pytest.fixture
def valid_request_payload():
    """Provide a valid research request payload."""
    return {
        "query": "What are AI agents?",
        "depth": "intermediate",
        "max_sources": 5,
        "time_range": "month",
    }


@pytest.fixture
def valid_response_data():
    """Provide a valid research response data."""
    return {
        "summary": "AI agents are autonomous systems...",
        "key_points": ["Point 1", "Point 2"],
        "sources": [
            {"title": "Source 1", "url": "https://example.com/1", "relevance": 0.9}
        ],
        "contradictions": [],
        "confidence_score": 0.78,
    }


# ============================================================================
# Test Successful Request
# ============================================================================


@pytest.mark.asyncio
async def test_research_successful_response(client, valid_request_payload, valid_response_data):
    """Test successful research request and response."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = valid_response_data
        mock_response.raise_for_status = MagicMock()

        # Setup mock AsyncClient context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute
        result = await client.research(valid_request_payload)

        # Assert
        assert result["summary"] == valid_response_data["summary"]
        assert result["confidence_score"] == valid_response_data["confidence_score"]
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_research_timeout_exception(client, valid_request_payload):
    """Test handling of httpx.TimeoutException."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        # Setup mock to raise TimeoutException
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute and assert
        with pytest.raises(httpx.TimeoutException):
            await client.research(valid_request_payload)


@pytest.mark.asyncio
async def test_research_http_error(client, valid_request_payload):
    """Test handling of httpx.HTTPError (500, 404, etc.)."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        # Setup mock to raise HTTPError
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        )

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute and assert
        with pytest.raises(httpx.HTTPError):
            await client.research(valid_request_payload)


@pytest.mark.asyncio
async def test_research_connect_error(client, valid_request_payload):
    """Test handling of httpx.ConnectError (unreachable backend)."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        # Setup mock to raise ConnectError
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.ConnectError("Cannot connect to backend")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute and assert
        with pytest.raises(httpx.ConnectError):
            await client.research(valid_request_payload)


@pytest.mark.asyncio
async def test_research_validation_error_invalid_response(client, valid_request_payload):
    """Test handling of response validation failure (missing required fields)."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        # Setup mock response with missing required field
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "summary": "Valid summary",
            # Missing: key_points, sources, contradictions, confidence_score
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute and assert
        with pytest.raises(ValueError):  # Pydantic raises ValueError for validation errors
            await client.research(valid_request_payload)


# ============================================================================
# Test Configuration
# ============================================================================


def test_client_initialization_defaults():
    """Test ResearchClient initialization with default values."""
    with patch.dict("os.environ", {"API_BASE_URL": "", "API_TIMEOUT": ""}):
        client = ResearchClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 90


def test_client_initialization_from_env():
    """Test ResearchClient initialization from environment variables."""
    with patch.dict(
        "os.environ",
        {"API_BASE_URL": "http://backend.example.com:8000", "API_TIMEOUT": "30"},
    ):
        client = ResearchClient()
        assert client.base_url == "http://backend.example.com:8000"
        assert client.timeout == 30


def test_client_initialization_with_args():
    """Test ResearchClient initialization with explicit arguments."""
    client = ResearchClient(base_url="http://custom.com", timeout=45)
    assert client.base_url == "http://custom.com"
    assert client.timeout == 45


# ============================================================================
# Test Request/Response Payload Structure
# ============================================================================


@pytest.mark.asyncio
async def test_research_request_structure(client, valid_request_payload):
    """Test that research request is structured correctly."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "summary": "Test",
            "key_points": [],
            "sources": [],
            "contradictions": [],
            "confidence_score": 0.5,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute
        await client.research(valid_request_payload)

        # Assert POST was called with correct URL and payload
        call_args = mock_client_instance.post.call_args
        assert "http://localhost:8000/research" in str(call_args)
        assert call_args.kwargs["json"] == valid_request_payload


@pytest.mark.asyncio
async def test_research_response_validation_pydantic(client, valid_request_payload, valid_response_data):
    """Test that response is validated with Pydantic ResearchResponse model."""
    with patch("ui.client.api_client.httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = valid_response_data
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client_class.return_value = mock_client_instance

        # Execute
        result = await client.research(valid_request_payload)

        # Assert result is a dict (from model_dump())
        assert isinstance(result, dict)
        assert "summary" in result
        assert "confidence_score" in result
