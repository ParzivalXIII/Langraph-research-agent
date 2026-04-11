# Quickstart: Web Fetch and Scraping Tool

**Feature**: 004-web-fetch-scraping-tool  
**Branch**: `004-web-fetch-scraping-tool`

---

## Prerequisites

1. Python 3.11+ with uv installed
2. Dependencies synced (`uv sync`)
3. Playwright Chromium browser (optional — only needed for headless mode):
   ```bash
   uv run playwright install chromium
   ```
4. For the enrichment path, ensure `TAVILY_API_KEY` is set (needed by `RetrievalService`)

---

## Add the only new dependency

```bash
uv add markdownify
```

---

## New Files to Create

```
app/tools/web_fetch.py        # WebFetchTool
app/schemas/web_fetch.py      # WebFetchRequest, FetchedPage, WebFetchResult, WebFetchConfig
```

Modify existing files:
- `app/core/config.py` — add `web_fetch_*` settings
- `app/core/errors.py` — add `WebFetchError`
- `app/services/retrieval_service.py` — add `enrich` kwarg + `_enrich_sources()`

---

## Usage

### Standalone fetch (ad-hoc)

```python
import asyncio
from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest
from app.tools.web_fetch import WebFetchTool

async def main():
    tool = WebFetchTool()
    req = WebFetchRequest(
        urls=["https://example.com"],
        config=WebFetchConfig(output_format="markdown"),
    )
    result = await tool.fetch_batch(req)
    for page in result.pages:
        if page.succeeded:
            print(page.title)
            print(page.content[:500])
        else:
            print(f"FAILED: {page.url} — {page.error}")

asyncio.run(main())
```

### With pipeline enrichment

```python
from app.services.retrieval_service import RetrievalService

svc = RetrievalService()
sources = await svc.retrieve_sources(
    query="quantum computing applications",
    depth="standard",
    max_sources=10,
    enrich=True,   # ← opt-in: fetches full page content
)
# sources[i].snippet now contains full page markdown (max 5000 chars)
```

### Headless / JS-rendered pages

Either set globally via env var:
```bash
WEB_FETCH_HEADLESS_ENABLED=true uv run uvicorn app.main:app
```

Or per-request:
```python
from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest

req = WebFetchRequest(
    urls=["https://react-spa-example.com"],
    config=WebFetchConfig(use_headless=True),
)
```

---

## Running Tests

```bash
# All unit tests for this feature
uv run pytest tests/unit/test_web_fetch_tool.py tests/unit/test_web_fetch_schemas.py -v

# Integration pipeline test
uv run pytest tests/integration/test_web_fetch_pipeline.py -v

# Full suite
uv run pytest -v
```

---

## Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_FETCH_MAX_CONCURRENCY` | `5` | Max parallel URL fetches |
| `WEB_FETCH_PER_DOMAIN_RATE_LIMIT` | `1.0` | Requests per second per domain |
| `WEB_FETCH_MAX_RETRIES` | `3` | Retry limit per URL |
| `WEB_FETCH_RETRY_BASE_DELAY` | `1.0` | Seconds for first retry backoff |
| `WEB_FETCH_MAX_RESPONSE_SIZE` | `5242880` | Max bytes per response (5 MB) |
| `WEB_FETCH_HEADLESS_ENABLED` | `false` | Enable Playwright globally |
| `WEB_FETCH_TIMEOUT` | `15.0` | Per-request timeout in seconds |
