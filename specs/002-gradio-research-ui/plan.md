# Implementation Plan: Controlled Research Interface

**Branch**: `002-gradio-research-ui` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-gradio-research-ui/spec.md`

## Summary

Build a thin, deterministic Gradio 6 interface that serves as a pure client-side wrapper over the research backend. The UI is responsible for:

1. Collecting user queries and control settings (depth, source limit, time range)
2. Sending a single structured request to the FastAPI backend
3. Rendering the backend's structured response faithfully without inventing missing content
4. Providing transparency (sources, contradictions, confidence) and clear error states

The UI enforces no logic drift by treating the backend as the single source of truth and never mutating or reinterpreting the research result.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: Gradio 6.x (Blocks API), httpx (async), FastAPI (backend)  
**Storage**: N/A (stateless client only)  
**Testing**: pytest with fixtures for mocked backend responses  
**Target Platform**: Web browser (desktop + tablet, mobile out of scope v1)  
**Project Type**: Web application frontend (SPA)  
**Performance Goals**: <500ms p95 response time from user click to result render; 60 FPS on interaction  
**Constraints**: 60-second HTTP timeout; no client-side synthesis or completion; no state persistence v1  
**Scale/Scope**: Single-page Gradio app, ~200 LOC core layout, ~100 LOC HTTP client

## Constitution Check

✅ **GATE PASS**

- **Determinism**: Backend is determinist; UI only renders what backend returns without invention. ✓
- **Retrieval First**: UI is not a retrieval system; it delegates all research to backend. ✓
- **Bounded Autonomy**: Single query → single request → single response. No iterative loops. ✓
- **Structured Outputs**: Backend response uses strict schema; UI renders each field distinctly. ✓
- **Observability**: All UI requests log query params, response shape, and render status to stderr. ✓
- **Cost + Latency**: HTTP timeout set to 60s per spec. No repeated calls or fallback synthesis. ✓
- **Stateless Core**: Stateless client; no persistence, no caching, no session state in v1. ✓

## Project Structure

### Documentation (this feature)

```text
specs/002-gradio-research-ui/
├── plan.md              # This file
├── research.md          # Phase 0 research artifact
├── data-model.md        # Phase 1 data structures
├── quickstart.md        # Phase 1 quick start guide
├── contracts/           # Phase 1 API contracts
│   ├── README.md
│   ├── research_request.schema.json
│   ├── research_response.schema.json
│   └── health_metrics.schema.json
├── checklists/
│   └── requirements.md
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
ui/
├── __init__.py
├── app.py               # Gradio Blocks app entry point
├── client/
│   ├── __init__.py
│   └── api_client.py    # HTTP client abstraction
└── components/
    ├── __init__.py
    ├── controls.py      # Depth, max_sources, time_range UI
    ├── results.py       # Summary, key_points, sources tabs
    └── diagnostics.py   # Contradictions, confidence, raw JSON

tests/
├── unit/
│   ├── test_api_client.py     # Mocked httpx responses
│   └── test_components.py     # Gradio component logic
├── integration/
│   └── test_research_flow.py  # End-to-end with mock backend
└── conftest.py                # Fixtures for research results
```

**Structure Decision**: Standalone `ui/` module within the monorepo. API client is isolated to facilitate mocking and future backend swaps. Component UI logic is separate for testability.

## Complexity Tracking

No Constitution violations requiring justification. The stateless design is appropriate for a client-side wrapper.

---

## Phase 0: Research & Validation

### Tasks

1. **Confirm Gradio 6 async support** — Verify native async callbacks work without workarounds
2. **Validate httpx session lifecycle** — Ensure connection pooling is correct per Gradio request cycle
3. **Inspect backend `/research` contract** — Ensure response schema is stable and complete
4. **Test timeout behavior** — Confirm 60s timeout doesn't cut requests mid-stream

**Deliverable**: [research.md](research.md)

---

## Phase 1: Design & Contracts

### 1.1 Data Model & Domain

**Research Query** (user input) → **Research Request** (JSON) → **Research Response** (JSON) → **UI State** (Gradio components)

```
User Input:
  query (str) + depth (str) + max_sources (int) + time_range (str)
    ↓
Request Payload:
  {
    "query": string,
    "depth": "basic" | "intermediate" | "deep",
    "max_sources": 3–10,
    "time_range": "day" | "week" | "month" | "year" | "all"
  }
    ↓
Response Payload:
  {
    "summary": string,
    "key_points": [string, ...],
    "sources": [
      { "title": string, "url": string, "relevance": 0.0–1.0 },
      ...
    ],
    "contradictions": [string, ...],
    "confidence_score": 0.0–1.0
  }
    ↓
UI Rendering:
  - Summary tab (markdown)
  - Key Points tab (bullet list)
  - Sources tab (dataframe: title, url, relevance)
  - Diagnostics tab (contradictions warning + confidence slider)
```

**Deliverable**: [data-model.md](data-model.md)

### 1.2 API Contracts

Document strict JSON schemas for request and response to ensure UI doesn't drift from backend expectations.

**Deliverable**: [contracts/](contracts/)

### 1.3 Quickstart

Setup instructions, environment variables, and how to run locally.

**Deliverable**: [quickstart.md](quickstart.md)

### 1.4 Agent Context Update

Update `copilot-instructions.md` or equivalent to record Gradio 6 + httpx patterns for this project.

**Deliverable**: Updated `.github/copilot-instructions.md` or similar

---

## Phase 2: Tasks & Implementation

Will be generated by `/speckit.tasks` after Phase 1 completion.

**Deliverable**: [tasks.md](tasks.md) (not created by `/speckit.plan`)

---

## Implementation Flow Summary

1. **HTTP Client** ([Phase 2 Task 1](tasks.md)): Async wrapper around httpx, error handling, logging
2. **Layout & Controls** ([Phase 2 Task 2](tasks.md)): Gradio Blocks with query input, depth/sources/time range dropdowns/sliders
3. **Result Components** ([Phase 2 Task 3](tasks.md)): Summary markdown, Key Points list, Sources dataframe, Diagnostics section
4. **Event Binding** ([Phase 2 Task 4](tasks.md)): Connect "Run Research" button to HTTP client and output components
5. **Error Handling** ([Phase 2 Task 5](tasks.md)): Try-catch around HTTP call with user-facing error messages
6. **Loading State** ([Phase 2 Task 6](tasks.md)): Disable button, show spinner during request
7. **Testing** ([Phase 2 Task 7](tasks.md)): Unit tests for client, integration tests with mock backend
8. **Observability** ([Phase 2 Task 8](tasks.md)): Structured logging of requests, timeouts, validation failures
