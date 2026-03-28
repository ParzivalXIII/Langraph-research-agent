"""LLM client initialization and configuration using LangChain + OpenRouter."""

from functools import lru_cache
from typing import Any

from langchain_openrouter import ChatOpenRouter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_llm_client() -> ChatOpenRouter:
    """Get or initialize the LLM client (cached singleton).

    Uses LangChain's ChatOpenRouter integration to communicate with
    OpenRouter-hosted models (e.g., OpenAI GPT-4, Anthropic Claude, etc.).

    Environment configuration:
    - OPENROUTER_API_KEY: API key for OpenRouter
    - OPENROUTER_BASE_URL: OpenRouter API base URL
    - OPENROUTER_MODEL_ID: Model identifier (e.g., "openai/gpt-4-turbo")

    Returns:
        ChatOpenRouter: Initialized LLM client

    Raises:
        ValueError: If OPENROUTER_API_KEY is not configured
    """
    if not settings.openrouter_api_key:
        logger.warning(
            "openrouter_api_key_not_configured",
            message="OPENROUTER_API_KEY not set in environment. LLM synthesis disabled.",
        )
        raise ValueError(
            "OPENROUTER_API_KEY environment variable not configured. "
            "Set it in .env file or environment before using LLM features."
        )

    logger.info(
        "llm_client_initialized",
        model=settings.openrouter_model_id,
        base_url=settings.openrouter_base_url,
    )

    # Initialize ChatOpenRouter with proper configuration
    kwargs: dict[str, Any] = {
        "model": settings.openrouter_model_id,
        "api_key": settings.openrouter_api_key,
        "temperature": 0.2,  # Low temperature for deterministic research synthesis
    }

    # Add custom base URL if not using the default OpenRouter endpoint
    if settings.openrouter_base_url != "https://openrouter.ai/api/v1":
        kwargs["base_url"] = settings.openrouter_base_url

    return ChatOpenRouter(**kwargs)
