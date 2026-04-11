"""Custom exception hierarchy and error handling utilities for Research Agent.

Provides structured error types with error codes, retry logic with exponential
backoff, and graceful degradation patterns for external service failures.

From spec.md (A2 — Error Handling):
- Tavily API failures (rate limits, timeouts) handled with exponential backoff
- LLM synthesis failures fall back to summary without analysis
- Network errors trigger graceful degradation (cached sources or partial results)
"""

import asyncio
import random
from typing import Callable, TypeVar, Optional, Any, Coroutine

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class AppError(Exception):
    """Base application exception with error code and context support.

    All custom exceptions inherit from this to enable structured error handling,
    logging, and API response serialization.
    """

    def __init__(self, message: str, error_code: str, details: Optional[dict] = None):
        """Initialize AppError.

        Args:
            message: Human-readable error message
            error_code: Standardized error code (e.g., "TAVILY_API_ERROR")
            details: Optional context dict for debugging/API responses
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(AppError):
    """Data validation failed (user input or schema mismatch)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(AppError):
    """Requested resource not found (e.g., query ID in database)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "NOT_FOUND", details)


class ExternalServiceError(AppError):
    """External API or service call failed (Tavily, OpenRouter, etc.)."""

    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        """Initialize ExternalServiceError.

        Args:
            message: Error message
            service_name: Name of the failed service (e.g., "Tavily API")
            status_code: HTTP status code if applicable
            details: Additional context
        """
        if details is None:
            details = {}
        details["service"] = service_name
        if status_code:
            details["status_code"] = status_code

        error_code = f"{service_name.upper().replace(' ', '_')}_ERROR"
        super().__init__(message, error_code, details)
        self.service_name = service_name
        self.status_code = status_code
        self.retryable = (
            status_code in (429, 500, 502, 503, 504) if status_code else True
        )


class TavilyError(ExternalServiceError):
    """Tavily API call failed."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, "Tavily API", status_code, details)


class LLMError(ExternalServiceError):
    """LLM (OpenRouter) call failed."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, "OpenRouter LLM", status_code, details)


class WebFetchError(ExternalServiceError):
    """Web fetch operation failed."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        """Initialize WebFetchError.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            details: Additional context including 'reason' field for error classifications
                    (e.g., 'timeout', 'http_error', 'empty_extraction', 'unsupported_content_type')
        """
        if details is None:
            details = {}
        super().__init__(message, "Web Fetch", status_code, details)


class SynthesisError(AppError):
    """Synthesis service internal error (used for fallback chain)."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "SYNTHESIS_ERROR", details)


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================


async def retry_with_backoff(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    jitter: bool = True,
    **kwargs,
) -> T:
    """Retry an async function with exponential backoff and jitter.

    From data-model.md (T020a Error Handling):
    - Exponential backoff: delay = base_delay * (2 ^ attempt_number)
    - Jitter: random 0-50% variance to prevent thundering herd
    - Max retries: 3 (default, configurable)

    Args:
        func: Async function to retry
        *args: Positional arguments to pass to func
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        jitter: Whether to add random variance (default True)
        **kwargs: Keyword arguments to pass to func

    Returns:
        Return value from successful function call

    Raises:
        Last exception encountered if all retries exhausted
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    function=func.__name__,
                    attempt=attempt,
                    total_attempts=max_retries + 1,
                )
            return result
        except Exception as exc:
            last_exception = exc

            if attempt < max_retries:
                # Calculate delay: base_delay * 2^attempt
                delay = base_delay * (2**attempt)

                # Add jitter: random 0-50% variance
                if jitter:
                    delay *= 1.0 + random.uniform(0, 0.5)

                logger.warning(
                    "retry_backoff",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    max_retries=max_retries,
                    error=str(exc),
                )

    if last_exception is not None:
        raise last_exception
    raise RuntimeError(f"Function {func.__name__} failed unexpectedly")


async def retry_with_backoff_sync(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    jitter: bool = True,
    **kwargs,
) -> T:
    """Retry a sync function with exponential backoff (runs in executor).

    For blocking operations that must run in thread pool.

    Args:
        func: Sync function to retry
        *args: Positional arguments to pass to func
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        jitter: Whether to add random variance (default True)
        **kwargs: Keyword arguments to pass to func

    Returns:
        Return value from successful function call

    Raises:
        Last exception encountered if all retries exhausted
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(
                    "retry_succeeded_sync",
                    function=func.__name__,
                    attempt=attempt,
                )
            return result
        except Exception as exc:
            last_exception = exc

            if attempt < max_retries:
                delay = base_delay * (2**attempt)
                if jitter:
                    delay *= 1.0 + random.uniform(0, 0.5)

                logger.warning(
                    "retry_backoff_sync",
                    function=func.__name__,
                    attempt=attempt + 1,
                    delay_seconds=delay,
                    error=str(exc),
                )
                await asyncio.sleep(delay)

    if last_exception is not None:
        raise last_exception
    raise RuntimeError(f"Function {func.__name__} failed unexpectedly")
