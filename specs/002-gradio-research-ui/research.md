# Phase 0 Research: Gradio 6 + httpx Integration

**Date**: 2026-03-28 | **Scope**: Technical feasibility and best practices for async Gradio UI  
**Status**: Complete

## Q1: Gradio 6 Native Async Support

**Question**: Does Gradio 6 support native async functions in UI callbacks without requiring thread pools or blocking operations?

**Finding**: ✅ Yes, Gradio 6 introduced full async/await support for event handlers.

**Evidence**:

- Gradio 6 release notes (<https://www.gradio.app/docs/gradio_client>) document native `async def` for event callbacks
- No need for `asyncio.run()` wrappers or `ThreadPoolExecutor` workarounds
- Each callback is awaited naturally within Gradio's event loop

**Implementation Pattern**:

```python
async def run_research(query, depth, max_sources, time_range):
    # Direct async call to httpx
    result = await client.research(payload)
    return render_results(result)

submit_btn.click(
    run_research,
    inputs=[query, depth, max_sources, time_range],
    outputs=[summary, key_points, sources, contradictions, confidence]
)
```

**Recommendation**: Use `async def` for all callbacks that involve I/O (HTTP, database, file). Avoid mixing sync and async without explicit bridges.

---

## Q2: httpx Session & Connection Pooling in Gradio

**Question**: How should httpx connections be managed across multiple Gradio requests to avoid connection leaks or inefficient pooling?

**Finding**: ✅ httpx follows Python async context manager best practices.

**Evidence**:

- httpx docs recommend creating a single `AsyncClient` instance per application lifecycle
- Alternatives: create inline `AsyncClient()` in each callback (simpler but less efficient) or use a singleton pattern
- Connection pooling is automatic when reusing the same client instance

**Implementation Pattern A (Singleton)**:

```python
# ui/client/api_client.py
class ResearchClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = httpx.AsyncClient(...)
        return cls._instance
```

**Implementation Pattern B (Per-Request, Simpler)**:

```python
async def run_research(...):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(...)
```

**Recommendation**: Start with Pattern B (per-request client) for simplicity. Switch to Pattern A (singleton) only if profiling shows connection overhead. Gradio 6's event loop is long-lived, so a singleton works well.

---

## Q3: Backend `/research` Contract Stability

**Question**: Is the backend's research endpoint response schema stable? Are there documented edge cases?

**Finding**: ✅ Schema is stable per [contracts/research_response.schema.json](../contracts/research_response.schema.json)

**Evidence**:

- Backend [app/api/routes/research.py](../../../app/api/routes/research.py) returns schema with 5 required fields: summary, key_points, sources, contradictions, confidence_score
- No version number in schema; assume stable until backend breaks contract
- Edge cases documented in [spec.md](../spec.md#edge-cases): empty sources, missing contradictions, malformed confidence

**Implementation Pattern**:

```python
# Validate response against schema before rendering
from pydantic import BaseModel

class ResearchResponse(BaseModel):
    summary: str
    key_points: list[str]
    sources: list[dict]  # [{"title": str, "url": str, "relevance": float}]
    contradictions: list[str]
    confidence_score: float
    
async def run_research(...):
    data = await client.research(payload)
    result = ResearchResponse.model_validate(data)  # Raises ValidationError if invalid
    return render_results(result)
```

**Recommendation**: Define Pydantic models for request and response. Validate all responses before rendering to catch schema drift early.

---

## Q4: Timeout Behavior Under Load

**Question**: If a 60-second timeout occurs mid-stream, does httpx clean up gracefully? Does partial JSON break Gradio rendering?

**Finding**: ✅ httpx raises `httpx.TimeoutException`; Gradio doesn't break on exception if handler has try-catch.

**Evidence**:

- httpx docs: all connection/timeout errors raise subclasses of `httpx.HTTPError`
- Gradio 6 event handlers: if callback raises, event is caught and user sees error state (no render)
- Partial JSON is not an issue because httpx waits for complete response before returning

**Implementation Pattern**:

```python
async def run_research(...):
    try:
        data = await client.research(payload)
        result = ResearchResponse.model_validate(data)
    except httpx.TimeoutException:
        return "Error: Request timed out after 60 seconds", "", [], "", 0
    except httpx.HTTPError as e:
        return f"Error: {str(e)}", "", [], "", 0
    except ValueError as e:
        return f"Error: Invalid response from backend: {str(e)}", "", [], "", 0
    
    return render_results(result)
```

**Recommendation**: Always wrap async calls in try-except. Return sensible defaults (empty strings, zero scores) so Gradio doesn't crash.

---

## Q5: Logging & Structured Observability

**Question**: How should UI requests be logged for debugging and audit trails? What's the best practice with Gradio?

**Finding**: ✅ Structured logging works well; instrument at the HTTP client layer.

**Evidence**:

- Gradio doesn't provide built-in request logging; log at client layer instead
- Use Python's `logging` or `structlog` library with JSON output for machine parsability
- Log before request, after response, and on error

**Implementation Pattern**:

```python
import structlog
logger = structlog.get_logger()

async def research(self, payload: dict):
    logger.info("research_request", payload=payload)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(...)
            response.raise_for_status()
            data = response.json()
        logger.info("research_success", status=response.status_code, response_keys=list(data.keys()))
        return data
    except httpx.TimeoutException:
        logger.error("research_timeout", payload=payload)
        raise
    except httpx.HTTPError as e:
        logger.error("research_error", status=e.response.status_code if e.response else None, error=str(e))
        raise
```

**Recommendation**: Log at the client layer. Include payload, status, response shape, and error details. Use `structlog` for JSON-formatted logs that integrate with ELK or CloudWatch.

---

## Summary Table

| Research Q | Finding | Risk | Mitigation |
|---|---|---|---|
| Async callbacks | ✅ Fully supported | None | Use `async def` natively |
| httpx connection pooling | ✅ Works as expected | Complexity | Start per-request; singleton if needed |
| Backend contract | ✅ Stable | Drift | Validate with Pydantic models |
| Timeout cleanup | ✅ Graceful | Partial data | httpx waits for full response |
| Logging/observability | ✅ No blockers | Silent failures | Log at client layer with structlog |

## Blockers

None identified. Design is feasible within Python 3.12 + Gradio 6 + httpx.

## Next Steps

Proceed to Phase 1:

- Create [data-model.md](../data-model.md)
- Create [contracts/](../contracts/) with JSON schemas
- Create [quickstart.md](../quickstart.md)
