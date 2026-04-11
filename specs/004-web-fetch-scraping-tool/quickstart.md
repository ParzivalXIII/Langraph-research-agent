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

---

## Phase 6: RetrievalService Integration & Enrichment

### Overview

Phase 6 integrates WebFetchTool into the retrieval pipeline, allowing automatic enrichment of source snippets with full-page content from Tavily search results.

### Key Features

- **Optional enrichment**: `retrieve_sources(..., enrich=True)` to enable
- **Graceful degradation**: Enrichment failures don't break the pipeline
- **Partial success handling**: Failed URLs return original Tavily snippet
- **Field mapping**: 
  - `FetchedPage.title` → `SourceRecord.title` (if not empty)
  - `FetchedPage.content` → `SourceRecord.snippet` (truncated to 5000 chars)
  - `FetchedPage.fetched_at` → `SourceRecord.retrieved_at` (ISO 8601)

### Usage

#### Disable enrichment (default)
```python
sources = await retrieval_service.retrieve_sources(
    query="AI trends 2024",
    depth="intermediate",
)
# Returns Tavily-only results (fast, no extra I/O)
```

#### Enable enrichment
```python
sources = await retrieval_service.retrieve_sources(
    query="AI trends 2024",
    depth="intermediate",
    enrich=True,  # Fetch full-page content for each source
)
# Returns enriched sources with full article content
# More details, but slower (~5-10 seconds for 10 URLs)
```

#### With ResearchAgent
```python
# ResearchAgent automatically uses enriched sources if available
agent = ResearchAgent()
brief = await agent.process_query(
    query="what is quantum computing?",
    enable_web_enrichment=True,  # Triggers enrich=True in RetrievalService
)
```

---

## Common Issues & Troubleshooting

### Issue: Enrichment is very slow

**Cause**: Fetching 10+ URLs sequentially. Phase 6 may fetch URLs one at a time.  
**Fix**: 
- Reduce `max_sources` (e.g., `max_sources=5`)
- Increase `web_fetch_max_concurrency` (default: 5, max safe: 10)
- Use `depth="basic"` (5 sources instead of 10)

```python
sources = await svc.retrieve_sources(
    query="...",
    max_sources=5,
    enrich=True,
)
```

### Issue: "headless_unavailable" errors

**Cause**: Playwright not installed or Chromium not found.  
**Fix**:
```bash
uv add playwright
uv run playwright install chromium
```

Then set global toggle:
```bash
WEB_FETCH_HEADLESS_ENABLED=true uv run pytest ...
```

### Issue: Enrichment returns empty snippets

**Cause**: Fetched pages had empty or unparseable content.  
**Fix**: Check `FetchedPage.error` in logs:
```python
result = await tool.fetch_batch(request)
for page in result.pages:
    if page.empty_extraction:
        print(f"Empty content: {page.url} (HTTP {page.http_status})")
```

### Issue: URL validation errors

**Cause**: Invalid URL format in batch.  
**Fix**: Ensure all URLs start with `http://` or `https://`:
```python
# WRONG
request = WebFetchRequest(urls=["example.com"])  # ❌ Missing scheme

# RIGHT
request = WebFetchRequest(urls=["https://example.com"])  # ✅
```

### Issue: Batch size limit exceeded

**Cause**: Requesting >50 URLs in a single batch.  
**Fix**: Split into multiple batches:
```python
# Process in chunks of 25
for chunk in batched(urls, 25):
    result = await tool.fetch_batch(
        WebFetchRequest(urls=chunk)
    )
```

---

## Monitoring & Logging

All operations are logged with structured fields for observability:

```python
# Watch for enrichment metrics
logger.info(
    "enrichment_complete",
    sources_count=10,
    fetched_count=9,
    failed_count=1,
)

# Check for partial failures
logger.debug(
    "enrichment_skipped_fetch_failed",
    url="https://...",
    error="timeout"
)
```

Log levels:
- **INFO**: Major pipeline events (retrieval_start, enrichment_complete)
- **WARNING**: Low-credibility sources, failed enrichment attempts
- **DEBUG**: Per-URL enrichment details, field mapping

---

## Architecture

```
RetrievalService.retrieve_sources(enrich=True)
    ↓
1. Fetch from Tavily (existing)
2. Apply credibility scoring (existing)
3. IF enrich=True:
    a. Collect URLs from sources
    b. Call WebFetchTool.fetch_batch()
    c. Map FetchedPage fields to SourceRecord
    d. Handle partial failures gracefully
4. Return enriched SourceRecord list
```

Key design decisions:
- **Enrichment is opt-in**: Default `enrich=False` for backward compatibility
- **Failures are graceful**: Failed URL fetches return original Tavily snippet
- **Rate limiting respected**: Per-domain rate limits apply during enrichment
- **No breaking changes**: All existing RetrievalService calls continue to work
