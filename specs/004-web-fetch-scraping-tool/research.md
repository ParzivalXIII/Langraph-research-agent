# Research: Web Fetch and Scraping Tool

**Feature**: 004-web-fetch-scraping-tool  
**Date**: 2026-04-09  
**Status**: Complete — all NEEDS CLARIFICATION items resolved

---

## Decision Log

### R-01: HTTP Fetch Engine — httpx (not Scrapy)

**Decision**: Use `httpx` (AsyncClient) for all HTTP fetching.

**Rationale**:
- `httpx` is already in `pyproject.toml` (`httpx>=0.28.1`) and is natively async.
- Scrapy uses a Twisted reactor that conflicts with FastAPI's uvicorn/asyncio event loop.
  Running Scrapy in-process would require isolating it in a subprocess or thread pool,
  adding complexity with no benefit for single-URL fetch operations.
- `httpx.AsyncClient` supports SSL, redirect following, timeouts, connection pooling, and
  `Retry-After` header parsing — all required by the spec.
- Scrapy's spider/pipeline model is designed for crawling site-graphs, not enriching a known
  list of discovered URLs. Over-engineered for this use case.

**Alternatives considered**:
- `aiohttp`: Comparable but httpx is already present; no reason to add another HTTP client.
- `Scrapy` (user suggestion): Technically feasible via subprocess but conflicts with asyncio
  event loop. Rejected per KISS principle and to avoid Twisted/asyncio interop complexity.
- `requests` + executor: Sync client wrapped in `run_in_executor`, same pattern as Tavily.
  Viable but httpx native async is cleaner and avoids thread pool saturation under concurrency.

---

### R-02: HTML Parsing and Content Extraction — BeautifulSoup4 + markdownify

**Decision**: Use `beautifulsoup4` for parsing; `markdownify` for HTML→markdown conversion;
`bs4`'s `find_all()` for structured JSON extraction (title, body, links).

**Rationale**:
- `beautifulsoup4>=4.14.3` is already in `pyproject.toml` (added by user before this session).
- BS4 with `html.parser` (stdlib, no C dep) handles malformed HTML gracefully.
- `markdownify` is a pure-Python library that converts BS4 tag trees to clean markdown.
  It strips navigation/header/footer noise when combined with targeted tag selection.
- For `output_format=json`: extract `<title>`, strip `<script>/<style>/<nav>/<header>/<footer>`,
  collect `<a href>` links from the main body — all achievable with BS4 selectors.

**Alternatives considered**:
- `lxml`: Faster but requires C extension; adds build complexity in Docker.
- `html2text`: CLI-first, less programmable than markdownify.
- `trafilatura`: Excellent article extraction but opinionated; doesn't expose structured JSON
  easily. Good future upgrade path if markdown quality needs improvement.
- `newspaper3k`: Article-only; doesn't support generic pages.

**`markdownify` addition to pyproject.toml required**: `markdownify>=0.13.0`

---

### R-03: JavaScript-Rendered Pages — Playwright async API

**Decision**: Use `playwright.async_api` (already in deps `playwright>=1.58.0`) directly
in the async fetch pipeline. Gate behind `use_headless=True` flag; fallback to httpx on
`PlaywrightError` or when headless is globally disabled.

**Rationale**:
- Playwright supports `async with async_playwright()` which is natively compatible with
  asyncio; no Twisted or subprocess isolation needed.
- `playwright` is already listed in `pyproject.toml`.
- Runtime guard: `playwright install chromium` must be run separately; if Chromium is absent,
  `playwright.async_api` raises `Error: Executable doesn't exist` which we catch and fall back
  to plain httpx.
- Scoped to P3 user story; default `use_headless=False` means zero overhead for the common path.

**Alternatives considered**:
- `selenium`: Heavier weight; not async-native.
- `pyppeteer`: Unmaintained.
- Subprocess isolation: Adds latency and complexity; not needed since Playwright is async.

---

### R-04: Per-Domain Rate Limiting — asyncio primitives (stdlib)

**Decision**: Implement with `asyncio.Semaphore` (global concurrency) and a
`dict[str, float]` of last-request timestamps (per-domain token bucket).
Use `asyncio.sleep` to enforce spacing. No external dependency.

**Rationale**:
- No external rate-limiting library needed; the logic is 10–15 lines.
- `asyncio.Semaphore(max_concurrency)` caps parallel fetches globally.
- Per-domain: store `last_request_time[domain]`, compute `wait = (1/rate_limit) - elapsed`,
  sleep if `wait > 0`. Shared state lives in `WebFetchTool` instance (in-process, per-request
  lifecycle means one short-lived instance per batch call).

**Alternatives considered**:
- `aiolimiter`: Clean library but adds a dep for what is ~15 lines of stdlib code.
- `asyncio-throttle`: Same reasoning.

---

### R-05: Retry Logic — Extend existing `retry_with_backoff`

**Decision**: Reuse `retry_with_backoff` from `app/core/errors.py`. Add `Retry-After` header
inspection in the WebFetchTool fetch loop (outside the generic utility), as it requires
per-response header access that doesn't fit the generic retry abstraction.

**Rationale**:
- `retry_with_backoff` already handles exponential backoff + jitter (data-model.md T020a).
- `Retry-After` is a per-response concern; implement as a check inside `_fetch_single` before
  re-raising so the caller's retry loop respects it.
- Keeps the retry utility generic and avoids coupling it to HTTP-layer concerns.

---

### R-06: Integration Point in RetrievalService

**Decision**: Add optional `enrich: bool = False` keyword argument to
`RetrievalService.retrieve_sources()`. When `True`, pass the scored source list through
`WebFetchTool.fetch_batch()` to populate/replace the `snippet` field with full-page content.
Return type is unchanged (`list[SourceRecord]`). No breaking change.

**Rationale**:
- SC-006 mandates no changes to public interface or downstream schemas.
- `SourceRecord.snippet` is already `max_length=5000` — sufficient for enriched content.
- Enrichment runs after scoring/filtering so we only fetch pages we're actually going to use.
- The enrichment step is opt-in; calling code that does not pass `enrich=True` is unaffected.

---

### R-07: Error Hierarchy Extension

**Decision**: Add `WebFetchError(ExternalServiceError)` in `app/core/errors.py` with
sub-reasons surfaced via the `details` dict (`reason` key: `too_many_redirects`,
`unsupported_content_type`, `empty_extraction`, `timeout`, `http_error`).

**Rationale**: Consistent with `TavilyError` and `LLMError` patterns. Error code auto-generated
as `WEB_FETCH_TOOL_ERROR` by the parent `ExternalServiceError.__init__`.

---

### R-08: Configuration Extension

**Decision**: Add to `Settings` (all optional with sensible defaults, no breaking change):

```
web_fetch_max_concurrency: int = 5
web_fetch_per_domain_rate_limit: float = 1.0  # req/s
web_fetch_max_retries: int = 3
web_fetch_retry_base_delay: float = 1.0
web_fetch_max_response_size: int = 5_242_880  # 5 MB
web_fetch_headless_enabled: bool = False
web_fetch_timeout: float = 15.0  # seconds per request
```

---

## Constitution Check — Phase 0

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Determinism over Agentic Creativity | ✅ PASS | Tool fetches deterministically from known URLs; no LLM in fetch path |
| II. Retrieval First, Generation Second | ✅ PASS | Tool is part of retrieval; enriches *before* synthesis. No generation in this module. |
| III. Bounded Autonomy | ✅ PASS | Batch capped at 50 URLs (FR-001); max_retries configurable with hard cap; no unbounded loops |
| IV. Structured Outputs Only | ✅ PASS | All outputs conform to `WebFetchResult` / `FetchedPage` schemas, validated by Pydantic v2 |
| V. Observability by Default | ✅ PASS | Per-URL log events + batch summary (FR-013); structlog used |
| VI. Cost + Latency Constraints | ✅ PASS | SC-001: 10s budget for 10 URLs; timeout per-request (15s default); depth SLAs preserved |
| VII. Stateless Core, Stateful Extensions | ✅ PASS | No state persisted; rate-limit state lives only within single batch call lifetime |
