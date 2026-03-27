"""Pytest fixtures for API-level testing with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.main import app


@pytest.fixture
def mock_tavily_response():
    """Mock response from Tavily API search.

    Returns:
        dict: Structured response with search results
    """
    return {
        "api_response": [
            {
                "title": "Understanding Quantum Computing",
                "url": "https://example.com/quantum",
                "content": "Quantum computers use superposition and entanglement...",
                "score": 0.92,
            },
            {
                "title": "Latest Quantum Breakthroughs",
                "url": "https://example.com/quantum-2024",
                "content": "Recent advances in quantum error correction...",
                "score": 0.87,
            },
        ]
    }


@pytest.fixture
def mock_tavily_client(mock_tavily_response):
    """Mock Tavily API client for search operations.

    Args:
        mock_tavily_response: Fixture providing mock search results

    Returns:
        AsyncMock: Mocked Tavily client with search method
    """
    mock_client = AsyncMock()
    mock_client.search = AsyncMock(return_value=mock_tavily_response)
    return mock_client


@pytest.fixture
def mock_llm_response():
    """Mock response from OpenRouter LLM.

    Returns:
        dict: Structured response from language model
    """
    return {
        "id": "chatcmpl-mock-abc123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "openai/gpt-4-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Quantum computing represents a fundamental shift in computational paradigms...",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 150, "total_tokens": 200},
    }


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Mock OpenRouter LLM client for synthesis operations.

    Args:
        mock_llm_response: Fixture providing mock LLM response

    Returns:
        AsyncMock: Mocked LLM client with chat completion method
    """
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content=mock_llm_response["choices"][0]["message"]["content"]
                    )
                )
            ]
        )
    )
    return mock_client


@pytest.fixture
def api_client(test_client, db_session):
    """FastAPI TestClient with dependency overrides for testing.

    Overrides database session dependency to use test session.
    All external API calls (Tavily, OpenRouter) must be mocked by tests.

    Args:
        test_client: FastAPI TestClient fixture from tests/conftest.py
        db_session: Test database session fixture

    Yields:
        TestClient: Configured test client with overridden dependencies
    """
    # Import here to avoid circular imports
    from app.core.database import get_db

    def override_get_db():
        """Override database dependency to use test session."""
        return db_session

    # Apply dependency overrides
    app.dependency_overrides[get_db] = override_get_db

    yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def api_client_with_mocked_services(api_client, mock_tavily_client, mock_llm_client):
    """API test client with both database and external services mocked.

    This fixture provides a fully mocked test environment where:
    - Database operations use in-memory SQLite
    - Tavily API calls are mocked
    - OpenRouter LLM calls are mocked

    Allows testing endpoint logic without external dependencies.

    Args:
        api_client: TestClient with database override
        mock_tavily_client: Mocked Tavily client
        mock_llm_client: Mocked LLM client

    Yields:
        tuple: (TestClient, mock_tavily_client, mock_llm_client)
    """
    return api_client, mock_tavily_client, mock_llm_client


@pytest.fixture
def mock_tavily_error():
    """Mock error response from Tavily API (rate limit).

    Returns:
        Exception: Simulated Tavily API error
    """
    error = Exception("Tavily API: Rate limit exceeded")
    error.status_code = 429
    return error


@pytest.fixture
def mock_llm_error():
    """Mock error response from OpenRouter LLM.

    Returns:
        Exception: Simulated LLM API error
    """
    error = Exception("OpenRouter API: Service temporarily unavailable")
    error.status_code = 503
    return error


@pytest.fixture
def mock_auth_header():
    """Mock authentication header for protected endpoints.

    Returns:
        dict: HTTP headers with Bearer token (placeholder token for testing)
    """
    # In a real scenario, this would be a valid JWT token
    return {"Authorization": "Bearer test-token-placeholder"}


@pytest.fixture
def invalid_auth_header():
    """Invalid authentication header for testing unauthorized access.

    Returns:
        dict: HTTP headers with invalid/expired token
    """
    return {"Authorization": "Bearer invalid-token"}
