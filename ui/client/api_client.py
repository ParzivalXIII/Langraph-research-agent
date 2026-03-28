"""HTTP client for research backend API.

Module: ui.client.api_client
Responsibility: Async HTTP communication with the FastAPI research backend

**Design Pattern**: Per-request AsyncClient (Pattern B from research.md)
- Creates a new httpx.AsyncClient() for each research() call
- More efficient than singleton for typical research latency (~10-60s)
- Integrates seamlessly with async Gradio event loop
- Automatic resource cleanup via async context manager

**Architecture Components**:
- ResearchClient: Main class with async research() method
- Error handling: Catches and re-raises httpx exceptions (TimeoutException, HTTPError, ConnectError)
- Response validation: Uses Pydantic ResearchResponse.model_validate()
- Logging: Structured JSON logging with structlog for request/response/error traces
  - Request logs: endpoint, payload keys, timeout, timing
  - Response logs: status code, keys present, execution time
  - Error logs: exception type, endpoint, elapsed time

**Configuration** (environment variables):
- API_BASE_URL: Backend base URL (default: http://localhost:8000)
- API_TIMEOUT: Request timeout in seconds (default: 60)

**Integration**:
- Imported in ui/app.py as a module-level singleton: `client = ResearchClient()`
- Called from async run_research() callback with form payload
- Exceptions are caught and mapped to user-friendly error messages
"""

import os
import time

import httpx
import structlog

from ui.models import ResearchResponse

logger = structlog.get_logger(__name__)


class ResearchClient:
    """Async HTTP client for research backend.
    
    Handles all communication with the FastAPI research backend via the /research endpoint.
    Validates responses strictly using Pydantic and logs all requests/responses.
    
    **Configuration**:
        Backend URL and timeout are configurable via environment variables or constructor arguments.
        Environment variables take precedence if not overridden in constructor.
    
    **Attributes**:
        base_url (str): Base URL for research backend.
                       Source: API_BASE_URL env var → constructor arg → default http://localhost:8000
        timeout (int): Request timeout in seconds.
                      Source: API_TIMEOUT env var → constructor arg → default 60
                      
    **Error Handling**:
        The research() method may raise:
        - httpx.TimeoutException: if request exceeds self.timeout seconds
        - httpx.HTTPStatusError: if response status >= 400
        - httpx.ConnectError: if backend is unreachable
        - ValueError: if response validation fails
        
        All exceptions are logged with context (endpoint, elapsed time) before re-raising.
        Caller (ui.app.run_research) is responsible for catching and converting to user messages.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        """Initialize research client with optional base_url and timeout overrides.
        
        **Precedence** (first match wins):
        1. Constructor argument (if provided)
        2. Environment variable (if set)
        3. Hardcoded default
        
        Args:
            base_url: Backend API base URL (e.g., http://localhost:8000).
                     If None, uses API_BASE_URL env var or default http://localhost:8000
            timeout: Request timeout in seconds (e.g., 90).
                    If None, uses API_TIMEOUT env var or default 90
                    
        Examples:
            >>> # Use environment variables
            >>> client = ResearchClient()
            
            >>> # Override environment variables
            >>> client = ResearchClient(base_url="http://api.example.com", timeout=120)
            
            >>> # Mix: use env var for base_url, override timeout
            >>> client = ResearchClient(timeout=30)
        """
        self.base_url = base_url or os.getenv(
            "API_BASE_URL", "http://localhost:8000"
        ) or "http://localhost:8000"
        
        timeout_str = os.getenv("API_TIMEOUT", "90")
        self.timeout = timeout or (int(timeout_str) if timeout_str else 90)

        logger.info(
            "research_client_init",
            base_url=self.base_url,
            timeout=self.timeout,
        )

    async def research(self, payload: dict) -> dict:
        """Submit research request to backend and return structured response.
        
        Implements the core request/response cycle:
        1. Log request details (endpoint, payload keys, timeout)
        2. Create AsyncClient with configured timeout
        3. POST to /research endpoint with JSON payload
        4. Validate response using Pydantic ResearchResponse model
        5. Log response details (status, keys, execution time) or error
        6. Return validated response as dict or re-raise exception
        
        **Request Validation**:
            Payload is validated by the backend; this client does not pre-validate.
            Invalid payloads receive HTTP 422 (validation error) from backend.
        
        **Response Validation**:
            Backend response is strictly validated against ResearchResponse schema.
            If validation fails, ValueError is raised with detail message.
            
        **Timeout Behavior**:
            If request exceeds self.timeout seconds, httpx.TimeoutException is raised.
            Default timeout is 90 seconds; typical research takes 10-90 seconds.
            
        Args:
            payload: Research request dict with four required keys:
                - query (str): Research question
                - depth (str): 'basic', 'intermediate', or 'deep'
                - max_sources (int): 3–10
                - time_range (str): 'day', 'week', 'month', 'year', or 'all'
            
        Returns:
            dict: ResearchResponse fields:
                - summary (str): Synthesized narrative answer
                - key_points (list[str]): Bulleted highlights
                - sources (list[dict]): Ranked references (title, url, relevance)
                - contradictions (list[str]): Conflicting statements (empty list if none)
                - confidence_score (float): 0.0–1.0
            
        Raises:
            httpx.TimeoutException: Request exceeded timeout threshold.
                                    User-friendly message: "Request timed out after 90 seconds."
            httpx.HTTPStatusError: Backend returned HTTP error status (>= 400).
                                   User-friendly message: "Backend error: {status_code}. Try again."
            httpx.ConnectError: Unable to connect to backend (network issue).
                               User-friendly message: "Unable to connect to backend."
            ValueError: Response validation failed (response doesn't match schema).
                       User-friendly message: "Backend returned invalid response."
            
        Examples:
            >>> client = ResearchClient()
            >>> payload = {
            ...     "query": "AI agents",
            ...     "depth": "intermediate",
            ...     "max_sources": 5,
            ...     "time_range": "month"
            ... }
            >>> response = await client.research(payload)
            >>> response.keys()
            dict_keys(['summary', 'key_points', 'sources', 'contradictions', 'confidence_score'])
            
        See Also:
            - ui.app.run_research() for error handling and user messaging
            - ui.models.ResearchResponse for response schema
        """
        endpoint = f"{self.base_url}/research/"
        start_time = time.time()

        logger.info(
            "research_request",
            endpoint=endpoint,
            payload_keys=list(payload.keys()) if payload else [],
            timeout=self.timeout,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

            # Validate response shape with Pydantic
            result = ResearchResponse.model_validate(data)
            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "research_success",
                status_code=response.status_code,
                response_keys=list(data.keys()),
                execution_time_ms=elapsed_ms,
                summary_length=len(result.summary),
                sources_count=len(result.sources),
                key_points_count=len(result.key_points),
                contradictions_count=len(result.contradictions),
                confidence_score=result.confidence_score,
            )

            return result.model_dump()

        except httpx.TimeoutException as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "research_timeout",
                timeout=self.timeout,
                execution_time_ms=elapsed_ms,
                error=str(e),
            )
            raise

        except httpx.HTTPStatusError as e:
            # HTTPStatusError provides a response attribute with the status code
            elapsed_ms = int((time.time() - start_time) * 1000)
            status_code = e.response.status_code if e.response is not None else None
            logger.error(
                "research_http_error",
                status_code=status_code,
                execution_time_ms=elapsed_ms,
                error=str(e),
            )
            raise

        except httpx.ConnectError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "research_connect_error",
                endpoint=endpoint,
                execution_time_ms=elapsed_ms,
                error=str(e),
            )
            raise

        except httpx.HTTPError as e:
            # Fallback for other HTTP-related errors
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "research_http_generic_error",
                execution_time_ms=elapsed_ms,
                error=str(e),
            )
            raise

        except ValueError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "research_validation_error",
                execution_time_ms=elapsed_ms,
                error=str(e),
            )
            raise
