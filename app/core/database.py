"""Database connection and session management."""

from typing import Generator

from sqlmodel import Session, create_engine, SQLModel

from app.core.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.database_url else {}
    ),
)


def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in SQLModel models. This should be called
    once during application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    """Provide database session as dependency.

    This is used as a FastAPI dependency to inject database sessions
    into route handlers and services. Sessions are automatically closed
    after use via the context manager.

    Yields:
        Session: Database session for a single request
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
