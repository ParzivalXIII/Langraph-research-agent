# Data Model: Web Fetch and Scraping Tool

**Feature**: 004-web-fetch-scraping-tool  
**Date**: 2026-04-09  
**Status**: Final

---

## 1. Entity Map

```
WebFetchConfig (config object)
   └── used by WebFetchTool.fetch_batch()

WebFetchRequest (input to batch)
   └── List[str] urls  (max 50)
   └── Optional WebFetchConfig config

FetchedPage (single-URL result)
   ├── url: HttpUrl
   ├── title: Optional[str]
   ├── content: str          (markdown or JSON str, max 5000)
   ├── content_type: str     ("markdown" | "json")
   ├── fetched_at: str       (ISO 8601)
   ├── http_status: int
   ├── processing_ms: int
   ├── content_length: int   (≥ 0)
   ├── content_truncated: bool
   ├── empty_extraction: bool
   └── error: Optional[str]

WebFetchResult (batch result)
   ├── requested_count: int
   ├── fetched_count: int
   ├── failed_count: int
   ├── total_ms: int
   └── pages: List[FetchedPage]
```

**SourceRecord** (existing, from `app/schemas/research.py`) — no changes:
```
SourceRecord
   ├── title: str (5–500)
   ├── url: HttpUrl
   ├── relevance: float (0.0–1.0)
   ├── credibility_score: Optional[float]
   ├── snippet: str (max 5000)          ← enrichment writes here
   └── retrieved_at: Optional[str]      ← enrichment writes here
```

`FetchedPage` → `SourceRecord` mapping:
- `page.title` → `source.title` (if not empty)
- `page.content` → `source.snippet` (truncate at 5000)
- `page.fetched_at` → `source.retrieved_at`

---

## 2. Pydantic v2 Schemas

### `app/schemas/web_fetch.py`

```python
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

# Precompiled for performance
_ALLOWED_SCHEME_RE = re.compile(r'^https?://', re.IGNORECASE)


class WebFetchConfig(BaseModel):
    """Per-batch configuration for WebFetchTool."""

    output_format: Literal["markdown", "json"] = Field(
        default="markdown",
        description="Output format for extracted page content.",
    )
    use_headless: bool = Field(
        default=False,
        description="Use Playwright Chromium for JS-rendered pages.",
    )
    max_content_chars: int = Field(
        default=5_000,
        ge=100,
        le=50_000,
        description="Maximum characters to include in content field.",
    )
    timeout_seconds: float = Field(
        default=15.0,
        ge=1.0,
        le=120.0,
        description="Per-request HTTP timeout.",
    )
    include_links: bool = Field(
        default=False,
        description="Include extracted hyperlinks in JSON output.",
    )


class WebFetchRequest(BaseModel):
    """Input to WebFetchTool.fetch_batch()."""

    urls: list[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="URLs to fetch. Must be http or https.",
    )
    config: WebFetchConfig = Field(default_factory=WebFetchConfig)

    @field_validator("urls", mode="before")
    @classmethod
    def validate_url_schemes(cls, v: list) -> list:
        for url in v:
            if not _ALLOWED_SCHEME_RE.match(str(url)):
                raise ValueError(
                    f"Only http/https URLs are allowed. Got: {url}"
                )
        return v


class FetchedPage(BaseModel):
    """Result for a single fetched URL."""

    url: str = Field(..., description="The URL that was fetched.")
    title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Extracted <title> text.",
    )
    content: str = Field(
        default="",
        description="Extracted page content as markdown or JSON string.",
    )
    content_type: Literal["markdown", "json"] = Field(
        default="markdown",
        description="Format of the content field.",
    )
    fetched_at: str = Field(
        ...,
        description="ISO 8601 timestamp when fetch completed.",
    )
    http_status: int = Field(
        ...,
        ge=0,
        le=999,
        description="HTTP status code (0 if connection error).",
    )
    processing_ms: int = Field(
        default=0,
        ge=0,
        description="Wall-clock ms for fetch + extraction.",
    )
    content_length: int = Field(
        default=0,
        ge=0,
        description="Byte length of extracted content after truncation.",
    )
    content_truncated: bool = Field(
        default=False,
        description="True if content was truncated to max_content_chars limit.",
    )
    empty_extraction: bool = Field(
        default=False,
        description="True if HTML parsed but yielded empty content (warning flag, not error).",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error description if fetch failed.",
    )

    @property
    def succeeded(self) -> bool:
        """True if fetch produced usable content."""
        return self.error is None and bool(self.content)


class WebFetchResult(BaseModel):
    """Batch result from WebFetchTool.fetch_batch()."""

    requested_count: int = Field(..., ge=1)
    fetched_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    total_ms: int = Field(..., ge=0)
    pages: list[FetchedPage] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_counts_consistent(self) -> "WebFetchResult":
        if self.fetched_count + self.failed_count > self.requested_count:
            raise ValueError(
                "fetched_count + failed_count must not exceed requested_count"
            )
        return self
```

---

## 3. Settings Extension (existing `app/core/config.py`)

```python
# New fields to add to Settings class — no breaking changes
web_fetch_max_concurrency: int = Field(default=5, ge=1, le=50)
web_fetch_per_domain_rate_limit: float = Field(default=1.0, ge=0.1)
web_fetch_max_retries: int = Field(default=3, ge=0, le=10)
web_fetch_retry_base_delay: float = Field(default=1.0, ge=0.1)
web_fetch_max_response_size: int = Field(default=5_242_880)  # 5 MB
web_fetch_headless_enabled: bool = Field(default=False)
web_fetch_timeout: float = Field(default=15.0, ge=1.0)
```

---

## 4. Error Extension (existing `app/core/errors.py`)

```python
class WebFetchError(ExternalServiceError):
    """Raised when web fetch or content extraction fails.
    
    Reason codes (via details["reason"]):
      - too_many_redirects
      - unsupported_content_type
      - empty_extraction
      - timeout
      - http_error
      - headless_unavailable
    """

    def __init__(
        self,
        message: str,
        url: str,
        reason: str,
        status_code: int = 0,
    ) -> None:
        super().__init__(
            message=message,
            service_name="web_fetch",
            status_code=status_code,
        )
        self.details["url"] = url
        self.details["reason"] = reason
```

---

## 5. Integration Extension (existing `app/services/retrieval_service.py`)

```python
# Add optional enrich parameter — keyword-only, defaults to False
async def retrieve_sources(
    self,
    query: str,
    depth: str = "standard",
    max_sources: int = 10,
    time_range: Optional[str] = None,
    *,
    enrich: bool = False,          # NEW — no breaking change
) -> list[SourceRecord]:
    ...
    # Existing scored_sources list is built here
    # [NEW] optional enrichment hook:
    if enrich and scored_sources:
        scored_sources = await self._enrich_sources(scored_sources)

    return scored_sources

async def _enrich_sources(
    self, sources: list[SourceRecord]
) -> list[SourceRecord]:
    """Enrich SourceRecord snippets with full-page content via WebFetchTool."""
    from app.tools.web_fetch import WebFetchTool
    from app.schemas.web_fetch import WebFetchConfig, WebFetchRequest
    tool = WebFetchTool()
    request = WebFetchRequest(
        urls=[s.url for s in sources],
        config=WebFetchConfig(output_format="markdown"),
    )
    result = await tool.fetch_batch(request)
    page_map = {p.url: p for p in result.pages if p.succeeded}
    for source in sources:
        page = page_map.get(str(source.url))
        if page:
            if page.title:
                source.title = page.title
            source.snippet = page.content
            source.retrieved_at = page.fetched_at
    return sources
```

---

## 6. State Transitions

`FetchedPage.error` is the failure discriminant — no explicit state machine is needed.

```
URL submitted
  → httpx.AsyncClient.get()
     → [timeout]       → error="timeout"          http_status=0
     → [redirect > 10] → error="too_many_redirects" http_status=last
     → [4xx/5xx]       → error="http_error"        http_status=N
     → [200, binary]   → error="unsupported_content_type"
     → [200, html]     → BS4 extraction
        → [empty body] → error="empty_extraction"
        → [ok]         → content=<markdown or json>  error=None
     → [use_headless=True, playwright unavailable] → fallback to httpx path
```

---

## 7. File Layout

```
app/
  tools/
    web_fetch.py          # WebFetchTool class (new)
  schemas/
    web_fetch.py          # WebFetchRequest, FetchedPage, WebFetchResult, WebFetchConfig (new)
  core/
    config.py             # add web_fetch_* fields (modify)
    errors.py             # add WebFetchError (modify)
  services/
    retrieval_service.py  # add enrich param + _enrich_sources() (modify)

tests/
  unit/
    test_web_fetch_tool.py         # new
    test_web_fetch_schemas.py      # new
  integration/
    test_web_fetch_pipeline.py     # new
```

---

## 5. Semantic Clarification: `empty_extraction` Flag

**Question**: Is `empty_extraction` a **partial success** (page fetched, HTML valid, but no extractable content → flag set, error=None) 
or a **failure** (page fetched but extraction produced nothing → error field set)?

**Decision**: `empty_extraction` is a **warning flag on a partial success** path.

**Semantics**:
- `FetchedPage.error = None` (no network/parsing failure)
- `FetchedPage.content = ""` (empty string after extraction)
- `FetchedPage.empty_extraction = True` (warning flag set)
- `FetchedPage.succeeded = False` (because `succeeded` requires non-empty `content`)

**Implementation implication**: When HTML is valid and parseable but yields no body text/title, 
the page is included in the result with no error reason but with the flag set. This allows 
the caller to distinguish between "network/parse failed" (in `error` field) and "content empty but valid" 
(flag set). Downstream logic (e.g., `_enrich_sources()`) can choose to skip enrichment for this page.
