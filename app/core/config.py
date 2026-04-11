"""Application configuration and settings management."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Configuration
    api_title: str = "Research Agent"
    api_description: str = (
        "A bounded research agent that synthesizes web evidence into structured briefs"
    )
    api_version: str = "0.1.0"
    debug: bool = False

    # Tavily API Configuration
    tavily_api_key: str = ""  # Optional for testing, required in production
    tavily_max_retries: int = 3
    tavily_retry_backoff: float = 1.0

    # OpenRouter LLM Configuration
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_model_id: str = "z-ai/glm-4.5-air:free"

    # Database Configuration
    database_url: str = "sqlite:///./research_agent.db"

    # Redis Configuration (optional, Phase 3+)
    redis_url: Optional[str] = None

    # Logging Configuration
    log_level: str = "INFO"

    # Feature Flags (Phase 4+)
    enable_persistence: bool = False
    enable_caching: bool = False

    # Web Fetch Tool Configuration (Phase 2+)
    web_fetch_enabled: bool = True
    web_fetch_max_concurrency: int = 5
    web_fetch_max_retries: int = 3
    web_fetch_retry_backoff: float = 1.0
    web_fetch_timeout_seconds: int = 15
    web_fetch_max_content_chars: int = 50000
    web_fetch_headless_enabled: bool = False
    web_fetch_per_domain_rate_limit: float = 1.0  # requests per second

    # RetrievalService Configuration (Phase 6+)
    enrich_sources_by_default: bool = True  # Enable source enrichment by default

    # Operational Constraints
    max_sources_default: int = 10
    max_sources_limit: int = 50
    max_iterations: int = 3
    confidence_threshold_warning: float = 0.6


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    This function is cached to avoid reloading settings multiple times
    during the application lifecycle.

    Returns:
        Settings: Application configuration object
    """
    return Settings()


# Export singleton settings instance
settings = get_settings()
