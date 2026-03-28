# Langraph-research-agent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-26

## Active Technologies

- Python 3.11+ + FastAPI, LangChain, Tavily API client, OpenRouter API client, Pydantic, SQLModel (optional: SQLAlchemy for ORM), Redis (optional) (001-research-agent)
- Python 3.12+ + Gradio 6.x (Blocks API), httpx (async), Pydantic (request/response validation) (002-gradio-research-ui)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-research-agent: Added Python 3.11+ + FastAPI, LangChain, Tavily API client, OpenRouter API client, Pydantic, SQLModel (optional: SQLAlchemy for ORM), Redis (optional)
- 002-gradio-research-ui: Added Python 3.12+ + Gradio 6.x (Blocks API, native async), httpx (async HTTP client with connection pooling), Pydantic (strict request/response validation, no logic drift), structured logging for observability

<!-- MANUAL ADDITIONS START -->

### Gradio 6 + httpx Patterns (002-gradio-research-ui)

**Async Callbacks**: Use `async def` natively in Gradio event handlers; Gradio 6 fully supports async/await without thread pools.

```python
async def run_research(query, depth, max_sources, time_range):
    result = await client.research(payload)
    return render_results(result)
```

**HTTP Client**: Instantiate `httpx.AsyncClient` either per-request (simpler) or as a singleton (more efficient). Per-request pattern recommended for simplicity:

```python
async def research(self, payload: dict):
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(...)
        return response.json()
```

**Pydantic Validation**: Always validate requests and responses to prevent schema drift:

```python
class ResearchRequest(BaseModel):
    query: str
    depth: Literal["basic", "intermediate", "deep"]
    max_sources: int  # 3-10
    time_range: Literal["day", "week", "month", "year", "all"]

class ResearchResponse(BaseModel):
    summary: str
    key_points: list[str]
    sources: list[Source]
    contradictions: list[str]
    confidence_score: float

# Validate
request = ResearchRequest(**user_input)
response = ResearchResponse.model_validate(backend_data)
```

**Error Handling**: Catch httpx and validation errors gracefully:

```python
try:
    result = await client.research(payload)
    response = ResearchResponse.model_validate(result)
except httpx.TimeoutException:
    return "Timeout after 60s", "", [], "", 0
except httpx.HTTPError as e:
    logger.error("http_error", error=str(e))
    return f"Backend error: {str(e)}", "", [], "", 0
except ValidationError as e:
    logger.error("schema_error", errors=e.errors())
    return "Invalid response from backend", "", [], "", 0
```

**Logging**: Log requests, responses, and errors at the client layer:

```python
import structlog
logger = structlog.get_logger()

logger.info("research_request", payload=payload)
logger.info("research_success", status_code=response.status_code)
logger.error("research_timeout", payload=payload)
```

<!-- MANUAL ADDITIONS END -->
