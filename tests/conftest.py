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
