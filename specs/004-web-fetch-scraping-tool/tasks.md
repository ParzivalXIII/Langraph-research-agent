# Implementation Tasks: Web Fetch and Scraping Tool

**Feature**: 004-web-fetch-scraping-tool  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Branch**: `004-web-fetch-scraping-tool`  
**Date**: 2026-04-09

---

## Overview

This feature adds a `WebFetchTool` enrichment layer to enrich Tavily search results with full-page content.
Implementation spans 6 phases:

- **Phase 1**: Project setup & dependency management
- **Phase 2**: Core schemas & error types
- **Phase 3**: WebFetchTool base implementation (User Story 1 base)
- **Phase 4**: Rate limiting & retry logic (User Story 2)
- **Phase 5**: Headless browser support (User Story 3)
- **Phase 6**: RetrievalService integration & polish

**MVP Scope**: Phases 1–3 (US1 only — batch fetch with markdown/JSON output, no rate limiting, no headless).

---

## Phase 1: Setup & Dependencies

### Goal

Initialize project scaffolding, add all required dependencies, update configuration base.

### Independent Test Criteria

- All dependencies install successfully with `uv sync`
- No import errors when loading `app.tools`, `app.schemas`, `app.core`
- Environment variables can be read (no required secrets missing)

### Tasks

- [X] T001 Add `markdownify` to pyproject.toml dependencies via `uv add`
- [X] T002 Run `uv sync` and verify all dependencies resolve without conflict
- [X] T003 Create `app/schemas/web_fetch.py` stub module with package init
- [X] T004 Create `app/tools/web_fetch.py` stub module with minimal docstring
- [X] T005 Create `tests/unit/test_web_fetch_tool.py` stub with conftest imports
- [X] T006 Create `tests/unit/test_web_fetch_schemas.py` stub for Pydantic tests
- [X] T007 Create `tests/integration/test_web_fetch_pipeline.py` stub for end-to-end tests

---

## Phase 2: Core Schemas & Errors

### Goal

Define all Pydantic v2 schemas and error types. No business logic yet; pure data model.

### Independent Test Criteria

- All schemas validate/construct correctly with valid inputs
- All schemas reject invalid inputs with specific ValidationError messages
- Serialization to JSON and deserialization from JSON round-trips correctly
- JSON Schema contracts in `contracts/` match schema structure

### Tasks

- [X] T008 [P] Implement `WebFetchConfig` schema in `app/schemas/web_fetch.py` with fields: `output_format`, `use_headless`, `max_content_chars`, `timeout_seconds`, `include_links`
- [X] T009 [P] Implement `WebFetchRequest` schema with `urls` list validation (min 1, max 50) and nested `config`
- [X] T010 [P] Implement `FetchedPage` schema with fields: `url`, `title`, `content`, `content_type`, `fetched_at`, `http_status`, `processing_ms`, `content_length` (int ≥0), `content_truncated` (bool), `empty_extraction` (bool), `error`; add `succeeded` property
- [X] T011 [P] Implement `WebFetchResult` schema with fields: `requested_count`, `fetched_count`, `failed_count`, `total_ms`, `pages`; add count consistency validator
- [X] T012 Add `WebFetchError(ExternalServiceError)` to `app/core/errors.py` with `details["reason"]` field for error classifications
- [X] T013 Add 8 new optional settings fields to `Settings` in `app/core/config.py` (web_fetch_max_concurrency, etc.)
- [X] T014 [P] Write comprehensive Pydantic v2 unit tests in `tests/unit/test_web_fetch_schemas.py` covering happy path, validation errors, JSON round-trip, edge cases
- [X] T015 Validate JSON Schema contracts match Pydantic schemas: `contracts/web-fetch-request.json` vs `WebFetchRequest`, `contracts/web-fetch-result.json` vs `WebFetchResult`

---

## Phase 3: WebFetchTool Base Implementation — User Story 1 (P1)

### Story: Batch URL Enrichment for Research Briefs

**Goal**: Fetch a batch of 1–50 URLs, extract full-page content, return markdown or JSON.

### Independent Test Criteria

- Tool successfully fetches and transforms 5 real URLs to markdown with no HTML tags
- Tool successfully transforms 5 URLs to JSON with title, body, links fields
- Partial failures (2 of 5 fail) return 3 successes + 2 errors without aborting
- Processing time per URL is recorded and summed correctly
- All output conforms to `FetchedPage` schema before return

### Tasks

- [X] T016 [US1] Implement `WebFetchTool.__init__()` with logger, settings injection, httpx client initialization
- [X] T017 [US1] Implement `WebFetchTool.fetch_batch(request: WebFetchRequest) -> WebFetchResult` public method signature
- [X] T018 [P] [US1] Implement `_fetch_single(url, config) -> FetchedPage` for a single URL with httpx.AsyncClient.get()
- [X] T019 [P] [US1] Implement HTML parsing and markdown extraction via BeautifulSoup4 + markdownify in `_extract_markdown(html_bytes, max_chars) -> str`
- [X] T020 [P] [US1] Implement HTML parsing and JSON extraction in `_extract_json(html_bytes, max_chars, include_links) -> dict` returning {title, body, links}
- [X] T021 [US1] Implement `_fetch_single()` error handling: catch httpx exceptions, record error reason (timeout, http_error, empty_extraction, unsupported_content_type), return FetchedPage with error field
- [X] T022 [US1] Implement HTTP redirect following with 5-hop limit; if exceeded, set error reason to `too_many_redirects`
- [X] T023 [US1] Implement max-response-size check; truncate to `max_content_chars` and set `content_truncated` flag if needed
- [X] T024 [US1] Implement `_feed_batch(urls, config)` to orchestrate batch fetch using `asyncio.gather()` on list of `_fetch_single` coroutines
- [X] T025 [US1] Implement `fetch_batch()` to: (1) validate request, (2) call `_feed_batch()`, (3) aggregate results into `WebFetchResult` with counts and total_ms, (4) return result
- [X] T026 [US1] Add per-URL logging (start, http_status, extraction_format, latency_ms, error_reason) via structlog
- [X] T027 [US1] Add batch-level logging (requested_count, fetched_count, failed_count, total_ms)
- [X] T028 [P] [US1] Write integration test: fetch 5 real URLs with markdown format, assert no HTML tags, assert content ≥50 chars, assert FetchedPage schema compliance
- [X] T029 [P] [US1] Write integration test: fetch 5 URLs with JSON format, assert title/body/links present, verify output ≥3 links for typical page
- [X] T030 [US1] Write integration test: mixed batch (2 bad URLs, 3 good), assert 3 successes return content + 2 failures return error reason without exception
- [ ] T031 [P] Write unit test: Create fixture of 20 real URLs (news, docs, blogs); run batch with output_format=markdown; assert ≥95% of pages produce non-empty, valid markdown (no raw HTML tags, parseable structure). This validates SC-002.
- [ ] T074 [P] Write integration test: Fetch a controlled batch of 10 URLs from distinct domains; use mocked httpx to eliminate network variance; assert `total_ms` is ≤ 10,000 and latency budget is honoured. This validates SC-001 timing SLA.
- [ ] T075 [P] Implement `asyncio.Semaphore(settings.web_fetch_max_concurrency)` inside `_feed_batch()` to enforce the global concurrency cap; ensure all `_fetch_single()` calls acquire the semaphore before making any network request. This validates FR-002 concurrency limit.

---

## Phase 4: Rate Limiting & Retry Logic — User Story 2 (P2)

### Story: Rate-Limited, Respectful Crawling

**Goal**: Enforce per-domain rate limiting (1 req/s default), retry on transient errors with backoff, respect `Retry-After`.

### Independent Test Criteria

- 4 URLs from same domain with 1 req/s limit → total time ≥ 3 seconds
- 429 response with `Retry-After: 2s` → tool waits ≥ 2s and retries
- 503 error → retried up to 3 times with exponential backoff
- `Retry-After` header takes precedence over computed backoff

### Tasks

- [ ] T031 [P] [US2] Add `_last_request_time: dict[str, float]` instance variable (domain → timestamp) to WebFetchTool
- [ ] T032 [P] [US2] Implement `_parse_domain(url: str) -> str` to extract domain from HttpUrl for rate-limit bucketing
- [ ] T033 [US2] Implement `_wait_for_domain_rate_limit(domain, per_domain_limit)` to enforce 1/rate_limit spacing using `time.monotonic` and `asyncio.sleep`
- [ ] T034 [P] [US2] Integrate rate limit wait into `_fetch_single()`: call wait BEFORE httpx.get() each attempt
- [ ] T035 [P] [US2] Implement `_should_retry(http_status, error, retries_left) -> bool` to check for 429/5xx and retries_left > 0
- [ ] T036 [US2] Implement retry loop inside `_fetch_single()` with exponential backoff: `delay = base_delay * (2 ** attempt) + jitter`
- [ ] T037 [US2] Parse `Retry-After` header from response; if present, use as override to computed backoff in retry loop
- [ ] T038 [US2] Cap total retries per URL at `web_fetch_max_retries` setting (default 3); after exhaustion, record error and move to next
- [ ] T039 [US2] Add retry logging: per-attempt events (attempt N, wait_ms, retry_reason)
- [ ] T040 [P] [US2] Write unit test: mock httpx with 429 response + `Retry-After: 2s`, assert tool waits ≥ 2s before retry
- [ ] T041 [P] [US2] Write unit test: mock httpx with two 503s then 200, assert succeeds after 2 retries with backoff
- [ ] T042 [US2] Write integration test: 4 URLs same domain, 1 req/s limit, assert total_ms ≥ 3000
- [ ] T043 [US2] Write integration test: URL that 429s once then succeeds, assert final result is success with `error=None`

---

## Phase 5: Headless Browser Support — User Story 3 (P3)

### Story: JavaScript-Rendered Page Support

**Goal**: Optional Playwright-based fetching for JS-rendered pages; graceful fallback to httpx if unavailable.

### Independent Test Criteria

- `use_headless=true` for known JS page → content includes dynamic elements absent from plain GET
- Globally disabled headless (env var false) + request `use_headless=true` → falls back to httpx + logs warning
- Headless unavailable (Chromium not installed) → fallback to httpx + logs warning, no exception

### Tasks

- [ ] T044 [P] [US3] Implement `_fetch_with_playwright(url, timeout) -> bytes` using `async_playwright().chromium.launch(headless=True)`
- [ ] T045 [US3] Add import guard for playwright in `_fetch_with_playwright()`: catch ImportError and raise `WebFetchError(reason="headless_unavailable")`
- [ ] T046 [US3] Add try/except around browser.newPage().goto(url) to catch `playwright.Error` (e.g., Chromium not found)
- [ ] T047 [P] [US3] Implement `_should_use_headless(config, global_enabled) -> bool` respecting both global setting and per-request config
- [ ] T048 [US3] Modify `_fetch_single()` to check `_should_use_headless()` after rate-limit wait; if true, try Playwright path; on failure, fallback to httpx
- [ ] T049 [US3] Add logging: "using_playwright=true|false" per fetch; "headless_fallback_reason=..." on fallback
- [ ] T050 [P] [US3] Write unit test: mock playwright browser.page.goto() to return HTML with dynamic content, assert content matches extracted markdown
- [ ] T051 [US3] Write unit test: mock playwright ImportError, assert tool falls back to httpx without exception, logs warning
- [ ] T052 [P] [US3] Write unit test: global headless disabled, per-request `use_headless=true`, assert httpx used + warning logged
- [ ] T053 [US3] Write integration test (optional, may skip if no public JS page available): real JS-rendered URL with `use_headless=true`, assert content ≠ plain httpx result

---

## Phase 6: RetrievalService Integration & Polish

### Goal

Integrate WebFetchTool into existing pipeline; add comprehensive observability; finalize tests and documentation.

### Independent Test Criteria

- `retrieve_sources(enrich=False)` unchanged; all existing tests pass
- `retrieve_sources(enrich=True)` enriches snippets without breaking SourceRecord schema
- All code follows PEP 8, passes ruff + black formatting
- Test coverage ≥ 85% for core paths
- Observability: per-URL and batch-level logs captured in all scenarios
- End-to-end test: call research agent with enrichment enabled; brief uses enriched content

### Tasks

- [ ] T054 [P] Add `enrich: bool = False` keyword-only argument to `RetrievalService.retrieve_sources()` method signature (no breaking change)
- [ ] T055 Implement `RetrievalService._enrich_sources(sources: list[SourceRecord]) -> list[SourceRecord]` private method
- [ ] T056 In `_enrich_sources()`, instantiate `WebFetchTool()`, call `fetch_batch()` with URLs from sources, map successful fetches back to SourceRecord fields
- [ ] T057 Update SourceRecord field writes in enrichment: map `FetchedPage.title` → `SourceRecord.title` (if not empty), `FetchedPage.content` → `SourceRecord.snippet`, `FetchedPage.fetched_at` → `SourceRecord.retrieved_at`
- [ ] T058 In `_enrich_sources()`, handle partial failures: only update SourceRecord if `FetchedPage.succeeded=True`; skip failed pages gracefully
- [ ] T059 In `retrieve_sources()`, call `await self._enrich_sources(sources)` conditionally when `enrich=True` and `sources` is non-empty
- [ ] T060 [P] Write integration test: call `retrieve_sources(..., enrich=False)`, assert SourceRecord fields unchanged from Tavily-only output
- [ ] T061 [P] Write integration test: call `retrieve_sources(..., enrich=True)`, assert snippet field updated with fetched content, retrieved_at populated
- [ ] T062 [P] Write end-to-end test: call `ResearchAgent.process_query()` internally using enriched sources, assert brief content uses enriched snippets
- [ ] T063 Add comprehensive inline docstrings to all public methods: WebFetchTool, WebFetchRequest, FetchedPage, WebFetchResult, WebFetchConfig
- [ ] T064 Run `ruff check app/tools/web_fetch.py app/schemas/web_fetch.py` and fix all lint errors
- [ ] T065 Run `black --line-length 100 app/tools/web_fetch.py app/schemas/web_fetch.py` and verify formatting
- [ ] T066 Run full test suite: `pytest tests/unit/test_web_fetch_*.py tests/integration/test_web_fetch_pipeline.py -v --cov`
- [ ] T067 Verify test coverage ≥ 85% for core modules; generate coverage report
- [ ] T068 Validate no new `# type: ignore` comments added; run `pyright` in strict mode on new code
- [ ] T069 Update Copilot context file (already done by setup-plan.sh) and confirm agent context includes new tech stack
- [ ] T070 Create/update README in `specs/004-web-fetch-scraping-tool/` with quick-start and common issues
- [ ] T071 Smoke test: import all new modules, instantiate WebFetchTool, call with 1 real URL, verify no runtime errors
- [ ] T072 Final edge-case test: empty batch (0 URLs) → rejected by validation; malformed URL → rejected by validation; batch size > 50 → rejected by validation

---

## Appendix: Dependencies & Complexity

### New External Dependencies

- `markdownify>=0.13.0` — HTML to markdown converter (pure Python, ~5 KB)

### Existing Dependencies Leveraged

- `httpx>=0.28.1` — async HTTP client (already installed)
- `beautifulsoup4>=4.14.3` — HTML parser (already installed)
- `playwright>=1.58.0` — headless browser (already installed, optional at runtime)
- `pydantic>=2.12.5` — schema validation (already installed)
- `structlog>=24.1.0` — structured logging (already installed)

### Concurrency Model

- Single `WebFetchTool` instance per `retrieve_sources()` call
- `asyncio.gather(*coroutines)` orchestrates parallel fetches within global `max_concurrency` limit
- Per-domain rate-limit state (dict) lives only within that instance lifetime
- No background jobs (ARQ/Celery); all processing in-process, in-request

### Performance Budget

- **SC-001**: 10 URLs from distinct domains → ≤ 10 seconds total
- **SC-003**: 5 URLs same domain (1 req/s) → ±100 ms spacing accuracy
- Typical: 2–5 MB transfer, <1 MB per page after truncation

### Backward Compatibility

- ✅ `retrieve_sources()` — new kwarg `enrich=False` (opt-in)
- ✅ `SourceRecord` — no schema changes
- ✅ `ResearchBrief` — no schema changes
- ✅ All existing tests pass unmodified

---

## Execution Strategy

### MVP (Minimal Viable Product)

**Phases 1–3** — Foundational batch fetch with markdown/JSON output, no rate limiting or JS support.
**Deliverable**: `WebFetchTool` can enrich a batch of URLs to markdown in <10s per batch.

### Phase 2 (Robustness)

**Phase 4** — Production-grade rate limiting and retry logic.
**Deliverable**: Tool can be safely deployed to high-traffic scenarios without IP bans or service disruption.

### Phase 3 (Full Feature)

**Phase 5** — JS-rendered page support.
**Deliverable**: Tool handles dynamic content; fallback ensures robustness when Chromium unavailable.

### Polish

**Phase 6** — RetrievalService integration, comprehensive tests, documentation.
**Deliverable**: End-to-end pipeline integration; research briefs use enriched content.

---

## Story Completion Order (Dependency Graph)

```
Phase 1 (Setup)
    ↓
Phase 2 (Schemas & Errors)
    ├─→ Phase 3 [US1: Batch Fetch] ← MVP complete here
    │       ├─→ Phase 4 [US2: Rate Limiting]
    │       │       ├─→ Phase 6 [Integration & Polish]
    │       └─→ Phase 5 [US3: Headless]
    │               ├─→ Phase 6 [Integration & Polish]
    └─→ Phase 6 [Documentation]
```

**Parallel opportunities**:

- Phases 3, 4, 5 can proceed in parallel after Phase 2 (if team size > 1)
- Unit tests (within each phase) can run as implementation proceeds
- Phase 6 tasks can begin once Phase 2 completes
