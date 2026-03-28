"""LLM client initialization and configuration using LangChain + OpenRouter."""

from functools import lru_cache
from typing import Any
import uuid

from langchain_openrouter import ChatOpenRouter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Track LLM invocations for debugging excessive API calls
_llm_call_counter = 0
_llm_call_session_id = str(uuid.uuid4())[:8]


class TrackedChatOpenRouter:
    """Wrapper around ChatOpenRouter to track API calls."""

    def __init__(self, llm_client: ChatOpenRouter):
        """Initialize wrapper with the underlying LLM client."""
        self._llm_client = llm_client

    async def ainvoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        """Track and invoke the LLM asynchronously."""
        global _llm_call_counter
        _llm_call_counter += 1

        logger.warning(
            "llm_api_call_made",
            call_number=_llm_call_counter,
            session_id=_llm_call_session_id,
            model=settings.openrouter_model_id,
            input_length=len(str(input_data)) if input_data else 0,
        )

        try:
            result = await self._llm_client.ainvoke(input_data, *args, **kwargs)
            logger.warning(
                "llm_api_call_succeeded",
                call_number=_llm_call_counter,
                session_id=_llm_call_session_id,
            )
            return result
        except Exception as e:
            logger.error(
                "llm_api_call_failed",
                call_number=_llm_call_counter,
                session_id=_llm_call_session_id,
                error=str(e),
            )
            raise

    def invoke(self, input_data: Any, *args: Any, **kwargs: Any) -> Any:
        """Track and invoke the LLM synchronously."""
        global _llm_call_counter
        _llm_call_counter += 1

        logger.warning(
            "llm_api_call_made",
            call_number=_llm_call_counter,
            session_id=_llm_call_session_id,
            model=settings.openrouter_model_id,
            input_length=len(str(input_data)) if input_data else 0,
        )

        try:
            result = self._llm_client.invoke(input_data, *args, **kwargs)
            logger.warning(
                "llm_api_call_succeeded",
                call_number=_llm_call_counter,
                session_id=_llm_call_session_id,
            )
            return result
        except Exception as e:
            logger.error(
                "llm_api_call_failed",
                call_number=_llm_call_counter,
                session_id=_llm_call_session_id,
                error=str(e),
            )
            raise

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying LLM client."""
        return getattr(self._llm_client, name)


@lru_cache(maxsize=1)
def get_llm_client() -> TrackedChatOpenRouter:
    """Get or initialize the LLM client (cached singleton).

    Uses LangChain's ChatOpenRouter integration to communicate with
    OpenRouter-hosted models (e.g., OpenAI GPT-4, Anthropic Claude, etc.).

    Environment configuration:
    - OPENROUTER_API_KEY: API key for OpenRouter
    - OPENROUTER_BASE_URL: OpenRouter API base URL
    - OPENROUTER_MODEL_ID: Model identifier (e.g., "openai/gpt-4-turbo")

    Returns:
        TrackedChatOpenRouter: Wrapped LLM client with request tracking

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
    # Disable retries to prevent duplicate API calls
    kwargs: dict[str, Any] = {
        "model": settings.openrouter_model_id,
        "api_key": settings.openrouter_api_key,
        "temperature": 0.2,  # Low temperature for deterministic research synthesis
        "max_retries": 0,  # Disable retries - we handle errors at application level
    }

    # Add custom base URL if not using the default OpenRouter endpoint
    if settings.openrouter_base_url != "https://openrouter.ai/api/v1":
        kwargs["base_url"] = settings.openrouter_base_url

    llm_client = ChatOpenRouter(**kwargs)

    # Return wrapped client with tracking
    return TrackedChatOpenRouter(llm_client)
