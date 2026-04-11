# Feature Specification: Web Fetch and Scraping Tool

**Feature Branch**: `004-web-fetch-scraping-tool`  
**Created**: 2026-04-09  
**Status**: Draft  
**Input**: User description: "Integrate a web fetch and scraping tool into an existing pipeline, supporting batch operations and multiple output formats."

## Evidence & Retrieval Plan *(mandatory for research-driven features)*

- **Primary sources**: Live web pages fetched directly by URL (HTTP/HTTPS). Complements existing Tavily API results by providing full-page content where Tavily only yields short snippets.
- **Fallback behavior**: If a URL is unreachable or returns an error, the tool skips that entry and records an error status in the result set; the batch does not abort. Partial results with error context are returned to the caller.
- **Output schema**: `WebFetchResult` — a collection of `FetchedPage` objects, each containing the original URL, transformed content (markdown string or structured JSON object), extraction metadata (status, latency, content length, truncation flag), and an error record if applicable.
- **Traceability**: Every fetch attempt is logged with URL, HTTP status, content length, transform format, latency, and error reason. Batch-level logs capture total item count, success count, failure count, and aggregate latency.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Batch URL Enrichment for Research Briefs (Priority: P1)

A researcher submits a query. Tavily retrieves source URLs but only short snippets. The pipeline fetches the full content of each page and converts it into clean markdown. The synthesiser uses this richer content to produce a more accurate, evidence-dense research brief.

**Why this priority**: This is the core value delivery. Full-page content materially improves synthesis quality. Without it the tool has no purpose in the pipeline.

**Independent Test**: Call the tool with a batch of 5 real URLs and `output_format=markdown`. Assert that each `FetchedPage` has non-empty `content` in valid markdown with no raw HTML tags.

**Acceptance Scenarios**:

1. **Given** a batch of 5 valid HTTP/HTTPS URLs, **When** the tool is called with `output_format=markdown`, **Then** each page's content is returned as a clean markdown string with at least 50 characters and no raw HTML tags.
2. **Given** a batch of 5 valid URLs, **When** the tool is called with `output_format=json`, **Then** each page's content is returned as a structured JSON object containing at least `title`, `body`, and `links` fields.
3. **Given** a mixed batch where 2 of 5 URLs are unreachable, **When** the tool executes, **Then** 3 successful results are returned and the 2 failures each carry an `error` field with a human-readable reason; no exception propagates to the caller.

---

### User Story 2 — Rate-Limited, Respectful Crawling (Priority: P2)

An operator runs the tool in production without triggering server-side rate bans or causing undue load on target origins. The tool enforces per-domain request spacing and honours standard `Retry-After` headers.

**Why this priority**: Without rate limiting, production use at scale risks IP bans and ethical/legal issues. This is a non-negotiable operational requirement.

**Independent Test**: Configure a per-domain limit of 1 req/s and send 4 URLs from the same domain. Assert total elapsed time is ≥ 3 seconds.

**Acceptance Scenarios**:

1. **Given** 4 URLs from the same domain and a per-domain rate limit of 1 req/s, **When** the batch is processed, **Then** requests to that domain are spaced at least 1 second apart and total duration is ≥ 3 seconds.
2. **Given** a URL returns `429 Too Many Requests` with `Retry-After: 2`, **When** the tool processes it, **Then** it waits at least 2 seconds and retries automatically before marking it failed.
3. **Given** a URL that returns a transient `503` error, **When** the tool processes it, **Then** it retries up to 3 times with exponential backoff before recording a failure.

---

### User Story 3 — JavaScript-Rendered Page Support (Priority: P3)

A developer extracts content from pages that require client-side rendering (single-page applications). The tool supports an optional headless-browser mode per request.

**Why this priority**: Most public research pages are static HTML; JS-rendered support is desirable but not blocking for MVP.

**Independent Test**: Set `use_headless=true` for a known JS-rendered URL. Assert that returned content is richer than a plain HTTP GET of the same URL.

**Acceptance Scenarios**:

1. **Given** a URL known to require JavaScript and `use_headless=true`, **When** the tool fetches the page, **Then** the returned content includes dynamic content absent from a plain HTML GET.
2. **Given** headless mode is globally disabled, **When** a request sets `use_headless=true`, **Then** the fetch falls back to standard HTTP and logs a warning.
3. **Given** headless mode is enabled but the browser runtime is unavailable, **When** the tool fetches the page, **Then** it gracefully falls back to plain HTTP rather than raising an unhandled exception.

---

### Edge Cases

- What happens when a URL redirects more than 5 times? — The tool follows up to 5 redirects then records a `too_many_redirects` error for that entry.
- What happens when the response body exceeds the configured maximum (e.g., 5 MB)? — The tool truncates content to the configured limit and sets a `content_truncated` flag in the result metadata.
- What happens when the HTML parser produces an empty string for a valid page? — The result is included with empty `content`, an `empty_extraction` warning flag set, and the original URL preserved.
- What happens when `output_format` is not one of the supported values? — Input validation rejects the request with a descriptive error before any network calls are made.
- What happens with non-text content types (PDF, images, binary)? — The tool skips content transformation and records an `unsupported_content_type` error with the detected MIME type.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST accept a batch of 1–50 HTTP/HTTPS URLs in a single call.
- **FR-002**: The tool MUST fetch all URLs in the batch concurrently, governed by a configurable global concurrency limit.
- **FR-003**: The tool MUST enforce per-domain request rate limiting to prevent overloading any single origin.
- **FR-004**: The tool MUST transform raw HTML into clean markdown when `output_format=markdown` is specified.
- **FR-005**: The tool MUST transform raw HTML into a structured JSON representation (title, body text, links) when `output_format=json` is specified.
- **FR-006**: The tool MUST retry failed requests on transient HTTP 429/5xx errors up to a configurable maximum using exponential backoff, respecting `Retry-After` headers where present.
- **FR-007**: The tool MUST return a partial result set for the batch when individual URLs fail, without aborting the entire batch.
- **FR-008**: The tool MUST provide a headless-browser fetch mode, configurable per request, for JavaScript-rendered pages.
- **FR-009**: The tool MUST be callable as a standalone agent tool AND integrable directly within `RetrievalService` as an optional content-enrichment step.
- **FR-010**: The tool MUST validate all inputs at the boundary using defined schemas before initiating any network activity.
- **FR-011**: The tool MUST produce output objects structurally compatible with `SourceRecord` fields (url, snippet/content, retrieved_at) so results flow into the existing synthesis pipeline without schema changes.
- **FR-012**: The tool MUST truncate oversized responses to a configurable byte limit and mark results with a `content_truncated` flag.
- **FR-013**: The tool MUST log per-URL fetch events (URL, status, latency, format, error) and batch-level summary events.

### Key Entities

- **`WebFetchRequest`**: Represents a single batch invocation. Attributes: list of URLs (1–50), output format (markdown | json), optional per-request headless flag, optional concurrency and timeout overrides.
- **`FetchedPage`**: Result of fetching and transforming one URL. Attributes: source URL, HTTP status code, output format used, transformed content (string or dict), content length, latency ms, truncated flag, empty_extraction flag, error reason (nullable), retrieved_at timestamp.
- **`WebFetchResult`**: Top-level batch result container. Attributes: list of `FetchedPage` items, total count, success count, failure count, total batch latency ms.
- **`WebFetchConfig`**: Tool-level runtime configuration. Attributes: max global concurrency, per-domain rate limit (req/s), max retries, retry base delay, max response size bytes, headless browser available flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A batch of 10 URLs from distinct domains completes within 10 seconds under normal network conditions, with responses under 1 MB each.
- **SC-002**: Content transformation produces non-empty, valid markdown for ≥ 95% of standard public news and documentation pages, measured against a reproducible benchmark set of 20 known-good URLs.
- **SC-003**: Per-domain rate limiting holds to within ±100 ms of the configured spacing when tested with 5 consecutive URLs from the same domain.
- **SC-004**: Transient 429/503 responses are retried correctly and succeed within the retry budget for URLs that fail only on the first attempt; no transient error propagates to the caller when retries succeed.
- **SC-005**: Input validation rejects malformed URLs, unsupported format strings, and batch sizes exceeding 50 — returning a descriptive validation error before any network call is initiated.
- **SC-006**: Integrating the tool into the existing pipeline requires no changes to `RetrievalService`'s public interface or `ResearchBrief`'s schema; all existing end-to-end tests pass without modification.

## Assumptions

- Headless browser support is optional and disabled by default. If the headless runtime is not installed, the tool falls back to plain HTTP fetching and logs a warning rather than failing hard.
- The tool operates on public HTTP/HTTPS URLs only. Non-HTTP protocols (FTP, file://, data: URIs) are out of scope.
- Full-page content extracted by this tool supplements Tavily snippets; it does not replace the Tavily retrieval step. The Tavily search remains the source-discovery step; this tool handles content-enrichment.
- The integration point in `RetrievalService` is an opt-in enrichment pass applied after Tavily returns source URLs, operating on the already-filtered, credibility-scored list.
- Output format defaults to `markdown` when not specified by the caller, as markdown is the most useful format for downstream LLM synthesis prompts.
- The tool is executed within the synchronous request lifecycle (in-process, async). Redis/ARQ background job queuing is out of scope for this feature; latency budgets follow existing depth-based SLAs (basic <30s, intermediate <60s, deep <120s).
- `robots.txt` compliance is configurable (default: off for research use; operators may enable for compliance contexts).
- Pydantic v2 model conventions are used, consistent with the existing codebase (`model_config`, `Field`, validators).
