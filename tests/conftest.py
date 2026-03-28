"""Pytest configuration and shared fixtures for all tests."""

import json
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from app.main import app
from app.core.config import get_settings

# ============================================================================
# Fixtures: Test Settings and Configuration
# ============================================================================


@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings with overridden configuration."""
    settings = get_settings()
    # Override for testing
    settings.debug = True
    settings.database_url = "sqlite:///:memory:"
    return settings


# ============================================================================
# Fixtures: Database Setup
# ============================================================================


@pytest.fixture(scope="session")
def test_db_engine():
    """Create an in-memory SQLite database for testing.

    Uses an in-memory database for speed and isolation.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup: drop all tables
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Provide a clean database session for each test.

    Rolls back changes after test completion for isolation.
    """
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


# ============================================================================
# Fixtures: Test Client
# ============================================================================


@pytest.fixture(scope="session")
def test_client():
    """Provide a FastAPI test client."""
    return TestClient(app)


# ============================================================================
# Fixtures: Sample Data
# ============================================================================


@pytest.fixture(scope="session")
def sample_queries_data() -> list[dict]:
    """Load sample queries from fixtures for testing."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_queries.json"

    if not fixture_path.exists():
        # Return default sample queries if fixture doesn't exist
        return [
            {
                "query": "recent AI breakthroughs",
                "depth": "basic",
                "expected_source_count_min": 1,
                "expected_contradictions_count": 0,
                "description": "Broad topic - quick facts",
                "sla_seconds": 30,
            }
        ]

    with open(fixture_path, "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def mock_tavily_response() -> dict[str, Any]:
    """Provide a mock Tavily API response for testing."""
    return {
        "results": [
            {
                "title": "AI Breakthroughs in 2026",
                "url": "https://example.com/ai-breakthroughs",
                "content": "Recent advances in AI include improved transformers and multimodal models",
                "score": 0.95,
            },
            {
                "title": "Machine Learning Trends",
                "url": "https://example.com/ml-trends",
                "content": "Latest ML trends point toward smaller, more efficient models",
                "score": 0.87,
            },
        ],
        "query": "AI breakthroughs 2026",
        "response_time": 0.45,
    }


@pytest.fixture(scope="session")
def sample_research_query_data() -> dict[str, Any]:
    """Provide sample ResearchQuery data for testing."""
    return {
        "query": "What are the latest advances in quantum computing?",
        "depth": "intermediate",
        "max_sources": 10,
        "time_range": "month",
    }


@pytest.fixture(scope="session")
def sample_source_record_data() -> dict[str, Any]:
    """Provide sample SourceRecord data for testing."""
    return {
        "title": "IBM Quantum Computing Advances",
        "url": "https://example.com/ibm-quantum",
        "relevance": 0.92,
        "credibility_score": 0.85,
        "snippet": "IBM has announced new quantum computing breakthroughs",
        "retrieved_at": "2026-03-26T10:30:00Z",
    }


# ============================================================================
# Fixtures: LLM Mocking
# ============================================================================


@pytest.fixture
def mock_llm_client(monkeypatch):
    """Mock the LLM client to avoid needing real API keys in tests.

    This fixture can be used in tests that need LLM mocking.
    Usage: def test_something(mock_llm_client): ...
    """
    from unittest.mock import AsyncMock, MagicMock

    # Create a mock LLM response object with a content attribute
    mock_response = MagicMock()
    mock_response.content = (
        "This is a synthesized research summary based on the provided sources. "
        "Key findings include important information gleaned from the source materials."
    )

    # Create a mock LLM client with an ainvoke method
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)

    # Mock the get_llm_client function throughout the tests
    def mock_get_llm_client():
        return mock_llm

    monkeypatch.setattr("app.core.llm.get_llm_client", mock_get_llm_client)

    return mock_llm


# ============================================================================
# Fixtures: UI Client (Gradio Research Interface)
# ============================================================================


@pytest.fixture(scope="function")
def mock_research_response() -> dict[str, Any]:
    """Provide a mock research response for testing UI rendering.
    
    Returns a complete, valid ResearchResponse with all fields populated.
    """
    return {
        "summary": (
            "AI agents are increasingly autonomous decision-makers in 2026. "
            "Key trends include multi-agent frameworks for task decomposition "
            "and tool-using agents showing improved reasoning capabilities."
        ),
        "key_points": [
            "Multi-agent frameworks enable complex task decomposition",
            "Tool-using agents show improved reasoning",
            "Safety constraints are still emerging",
            "Fine-tuning on specialized tasks improves performance",
        ],
        "sources": [
            {
                "title": "Agents in 2026 Survey",
                "url": "https://example.com/agents-survey-2026",
                "relevance": 0.95,
            },
            {
                "title": "LLM Agents Review",
                "url": "https://example.com/llm-agents-review",
                "relevance": 0.87,
            },
            {
                "title": "Multi-Agent Systems Design",
                "url": "https://example.com/multi-agent-systems",
                "relevance": 0.82,
            },
        ],
        "contradictions": [
            "Source A claims agents need more training data; Source B claims pretraining is sufficient"
        ],
        "confidence_score": 0.78,
    }


@pytest.fixture(scope="function")
def mock_invalid_response() -> dict[str, Any]:
    """Provide a malformed response for error handling tests.
    
    Missing required fields to trigger ValidationError.
    """
    return {
        "summary": "This response is incomplete",
        # Missing: key_points, sources, contradictions, confidence_score
    }


@pytest.fixture(scope="function")
def mock_client(monkeypatch):
    """Provide an AsyncMock of ResearchClient for unit tests.
    
    Usage: def test_something(mock_client): ...
    """
    from unittest.mock import AsyncMock

    mock_client_instance = AsyncMock()
    mock_client_instance.research = AsyncMock()
    return mock_client_instance


@pytest.fixture(scope="function")
def research_client():
    """Provide a real ResearchClient instance pointing to test backend.
    
    Uses environment variable API_BASE_URL (default: http://localhost:8000)
    and API_TIMEOUT (default: 60).
    
    Usage: def test_something(research_client): ...
    """
    from ui.client.api_client import ResearchClient

    return ResearchClient()
