# Tasks: Controlled Research Interface (Gradio 6)

**Input**: Design documents from `/specs/002-gradio-research-ui/`  
**Prerequisites**: ✅ spec.md, ✅ plan.md, ✅ research.md, ✅ data-model.md, ✅ contracts/, ✅ quickstart.md  
**Branch**: `002-gradio-research-ui`  
**Tests**: Included (unit + integration per user story)  

---

## Overview

This tasks list implements a thin, stateless Gradio 6 research client that collects user queries, submits them to the FastAPI backend, and renders structured results faithfully without inventing missing content. Implementation is organized by **user story** to enable independent development, testing, and delivery of each P1/P2 feature.

### Task Format

- **[P]**: Task can run in parallel (independent files, no blocking dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- **[Filepath]**: Exact location for implementation

### Dependency Graph

```
Phase 1: Setup (T001–T003, all [P])
    ↓
Phase 2: Foundational (T004–T006, blocking)
    ↓
Phase 3: US1 (T007–T011, [P] where noted)
    ↓
Phase 4: US2 (T012–T016, [P] where noted)
    ↓
Phase 5: US3/US4 (T017–T021, [P] where noted)
    ↓
Phase 6: Polish (T022–T025)
```

### User Story Mapping

- **US1 (P1)**: Submit Research Query — Accept query + controls, send to backend
- **US2 (P1)**: Review Structured Results — Render summary, key_points, sources, diagnostics
- **US3 (P2)**: Understand Result Quality — Display confidence score + contradictions
- **US4 (P2)**: Handle Loading/Failure States — Loading spinner, error messages

---

## Phase 1: Setup & Project Structure

**Purpose**: Initialize directory layout and stub core files

### Tasks

- [ ] T001 [P] Create `ui/` directory structure with `__init__.py`, `client/`, and `components/` subdirectories in `/home/parzival/projects/Langraph-research-agent/ui/`

- [ ] T002 [P] Create Pydantic validation models in `ui/models.py` with ResearchQuery, ResearchRequest, ResearchResponse, Source, and Diagnostics classes per data-model.md

- [ ] T003 [P] Create HTTP client module stub in `ui/client/__init__.py` and `ui/client/api_client.py` (empty class with docstring)

---

## Phase 2: Foundational Infrastructure (Blocking)

**Purpose**: Implement shared services and testing setup that all user stories depend on

### Tasks

- [ ] T004 Implement `ui/client/api_client.py` — ResearchClient class with:
  - `__init__(self, base_url: str, timeout: int)` with environment variable defaults
  - `async research(self, payload: dict) -> dict` method using httpx.AsyncClient
  - Try-catch for httpx.TimeoutException, httpx.HTTPError, httpx.ConnectError
  - Response validation with Pydantic ResearchResponse.model_validate()
  - Structured logging with structlog (request payload, response shape, error details)
  - Per-request AsyncClient pattern (Pattern B from research.md)

- [ ] T005 Create `tests/conftest.py` with pytest fixtures:
  - `mock_research_response()` — Returns sample ResearchResponse with summary, key_points, sources, contradictions, confidence_score
  - `mock_invalid_response()` — Returns incomplete/malformed response for error testing
  - `mock_client()` — AsyncMock of ResearchClient for unit tests
  - `research_client()` — Real ResearchClient instance pointing to test backend

- [ ] T006 Setup structured logging in `ui/client/api_client.py`:
  - Import structlog and configure for JSON output (or pretty-print for dev)
  - Log requests with: method, url, payload (sanitized), timestamp
  - Log responses with: status_code, response_shape, execution_time_ms
  - Log errors with: exception_type, message, retry_count (if applicable)
  - Ensure all logs are at module level (logger = structlog.get_logger())

---

## Phase 3: User Story 1 — Submit Research Query (P1)

**Goal**: User can enter a research question, select depth/sources/time_range, and submit.  
**Independent Test Criteria**:

- Query text input accepts user input and validates (non-empty, strips whitespace)
- Depth dropdown accepts "basic", "intermediate", "deep" selections
- Max sources slider enforces 3–10 range
- Time range dropdown accepts "day", "week", "month", "year", "all" selections
- Submit button sends payload to backend with all four fields
- Submission is blocked if query is empty

### Tasks

- [ ] T007 [P] [US1] Create `ui/components/controls.py` — Gradio dropdown/slider components:
  - `create_depth_dropdown()` → gr.Dropdown with choices ["basic", "intermediate", "deep"], value="intermediate"
  - `create_max_sources_slider()` → gr.Slider with minimum=3, maximum=10, value=5, step=1
  - `create_time_range_dropdown()` → gr.Dropdown with choices ["day", "week", "month", "year", "all"], value="all"
  - Return dict with all three components for reuse in app.py

- [ ] T008 [P] [US1] Create `ui/components/query_input.py` — Query text input component:
  - `create_query_input()` → gr.Textbox(label="Research Query", lines=2, placeholder="Enter your research question...", max_length=500)
  - Basic validation: non-empty, whitespace-only rejected by Pydantic ResearchQuery model (not in component, but documented)

- [ ] T009 [P] [US1] Create main `ui/app.py` layout with gr.Blocks():
  - Title: "Controlled Research Interface"
  - Input section: Query textbox (from T008), three control dropdowns/slider (from T007)
  - Submit button: "Run Research" with interactive=True
  - Output placeholders: summary, key_points, sources, contradictions, confidence (leave empty for now; will be wired in US2)
  - Tabs: Results, Diagnostics (structure only, content added in US2/US3)

- [ ] T010 [US1] Implement form validation in `ui/app.py`:
  - On form change: validate query using ResearchQuery.model_validate()
  - If validation fails (empty query): disable "Run Research" button, show inline error
  - If validation succeeds: enable button, clear error message
  - Ensure dropdown/slider values are always valid (no out-of-range selections possible in Gradio)

- [ ] T011 [US1] Implement submit button event in `ui/app.py` with async callback:
  - Bind submit_btn.click() to async function: `async run_research(query, depth, max_sources, time_range)`
  - Create ResearchRequest from inputs: `{"query": query, "depth": depth, "max_sources": max_sources, "time_range": time_range}`
  - Call client.research(request_payload) from T004
  - Return placeholder outputs (empty strings/lists for now; actual rendering in US2)
  - Catch ValidationError, HTTPError, TimeoutException and return error strings to UI

---

**Test Task for US1** *(optional, implement if TDD requested)*

- [ ] T011b [US1] Create `tests/unit/test_controls.py`:
  - Test depth dropdown options match spec
  - Test max_sources slider range enforces 3–10
  - Test time_range dropdown option values
  - Test query input accepts and rejects invalid inputs via ResearchQuery validation

---

## Phase 4: User Story 2 — Review Structured Results (P1)

**Goal**: User can see summary, key points, sources table, and confidence in separate tabs.  
**Independent Test Criteria**:

- Summary renders as markdown block
- Key points render as bullet list
- Sources render in table with title, URL (clickable), relevance score
- Contradictions show in warning section (if present)
- All sections update immediately after backend response

### Tasks

- [ ] T012 [P] [US2] Create `ui/components/results.py` with result rendering functions:
  - `create_summary_output()` → gr.Markdown(label="Summary")
  - `create_key_points_output()` → gr.Textbox(label="Key Points", lines=8, interactive=False) or gr.HTML
  - `create_sources_table()` → gr.Dataframe with columns ["Title", "URL", "Relevance"]
  - Each function returns the Gradio component for wiring in app.py

- [ ] T013 [P] [US2] Create summary rendering function in `ui/components/results.py`:
  - `format_summary(response: ResearchResponse) -> str` — Pass summary field through as-is (no modification)
  - Handle empty summary edge case: return "(No summary available)"

- [ ] T014 [P] [US2] Create key points rendering function in `ui/components/results.py`:
  - `format_key_points(response: ResearchResponse) -> str` — Join key_points array as markdown bullet list
  - Handle empty list edge case: return "(No key points available)"
  - Preserve order from backend (no re-sorting)

- [ ] T015 [P] [US2] Create sources table rendering function in `ui/components/results.py`:
  - `format_sources_table(response: ResearchResponse) -> list[list]` — Convert sources array to list-of-lists for Dataframe
  - Columns: title, url, relevance (formatted as percentage 0–100%)
  - Make URLs clickable: render as markdown link `[url](url)` or use gr.Dataframe's link handling
  - Handle empty sources: return empty dataframe or [(no sources)]
  - Sort by relevance descending (use backend order as-is per data-model assumption)

- [ ] T016 [US2] Wire result outputs in `ui/app.py` event handler:
  - Modify `run_research()` callback to unpack ResearchResponse and call format_summary(), format_key_points(), format_sources_table()
  - Return formatted values to output components
  - Render summary to Markdown, key_points to Textbox, sources to Dataframe
  - Handle ResearchResponse validation failure: return error messages to all outputs

- [ ] T016b [P] [US2] Create `ui/components/tabs.py` for organizing output sections:
  - Create Results Tab with summary, key_points, sources (stacked vertically or in sub-tabs)
  - Create Diagnostics Tab (placeholder for US3/US4)
  - Return Tabs component for wiring in app.py

---

**Test Task for US2** *(optional, implement if TDD requested)*

- [ ] T017b [US2] Create `tests/unit/test_components.py`:
  - Test format_summary() with valid/empty summary
  - Test format_key_points() with valid/empty list
  - Test format_sources_table() with valid/empty sources
  - Test Dataframe rendering with clickable URLs

---

## Phase 5: User Story 3 — Understand Result Quality (P2) & User Story 4 — Handle Loading/Failure States (P2)

**US3 Goal**: User can see confidence score as percentage + visual indicator, and contradictions as warning.  
**US4 Goal**: User sees loading spinner during request, error message if request fails.  
**Independent Test Criteria**:

- Confidence score displays as percentage (0–100%)
- Confidence visual indicator changes color (red ≤0.5, yellow 0.5–0.8, green >0.8)
- Contradictions warning appears only if contradictions array is non-empty
- Loading spinner shows during request; button is disabled
- Error message shows if request times out or returns invalid data

### Tasks

- [X] T017 [P] [US3] Create `ui/components/diagnostics.py` with quality visualization:
  - `create_confidence_display()` → gr.Number(label="Confidence Score", interactive=False) + gr.HTML for visual indicator
  - `create_contradictions_display()` → gr.Markdown(label="Contradictions & Warnings")

- [X] T018 [P] [US3] Implement confidence formatter in `ui/components/diagnostics.py`:
  - `format_confidence(confidence_score: float) -> tuple[str, str]` — Return (percentage_text, html_indicator)
  - Percentage text: "92.0% Confidence"
  - HTML indicator: color-coded bar (red if ≤0.5, yellow if 0.5–0.8, green if >0.8)
  - Handle invalid/missing score: default to 0.0 (red bar, 0% text)

- [X] T019 [P] [US3] Implement contradictions formatter in `ui/components/diagnostics.py`:
  - `format_contradictions(contradictions: list[str]) -> str` — Render as warning markdown block
  - If empty: return "(No contradictions detected)"
  - If present: return markdown block with warning emoji + each contradiction as bullet point
  - Example: "⚠️ **Contradictions Detected:** \n - Source A claims X\n - Source B claims Y"

- [X] T020 [P] [US4] Create loading state handler in `ui/app.py`:
  - Add `loading_state` Markdown component above submit button (hidden by default)
  - On submit button click: set loading_state to "⏳ Request in progress...", disable submit button, hide results
  - After response received (success or error): clear loading state, re-enable submit button

- [X] T021 [P] [US4] Create error state handler in `ui/app.py`:
  - Modify `run_research()` callback to catch all exceptions:
    - `httpx.TimeoutException`: return "❌ Request timed out after 60 seconds. Try a simpler query."
    - `httpx.HTTPError`: return f"❌ Backend error ({status_code}): {message}"
    - `ValidationError`: return "❌ Backend returned an invalid response. Please check the backend logs."
    - Generic Exception: return "❌ An unexpected error occurred. Please try again."
  - Display error message in a gr.Markdown(label="Error") component
  - Return empty values to result outputs if error occurs

- [X] T022 [US4] Implement error message display in `ui/app.py`:
  - Add error_display Markdown component (hidden by default)
  - On error response: set error_display to error message, clear result outputs
  - On successful response: clear error_display

---

**Test Tasks for US3/US4** *(optional, implement if TDD requested)*

- [X] T023b [P] [US3] Create `tests/unit/test_diagnostics.py`:
  - Test format_confidence() with scores 0.0, 0.5, 0.8, 1.0
  - Test format_contradictions() with empty/populated lists
  - Test HTML indicator color logic

- [X] T024b [P] [US4] Create `tests/unit/test_error_handling.py`:
  - Mock httpx.TimeoutException and verify error message is returned
  - Mock httpx.HTTPError(status_code=500) and verify error message is returned
  - Mock ValidationError and verify error message is returned
  - Verify loading state is cleared on error

---

## Phase 6: Integration Testing & Polish

**Purpose**: Verify end-to-end flow, documentation, and final cleanup

### Tasks

- [ ] T025 Create `tests/integration/test_research_flow.py`:
  - Test 1: Submit valid query → Verify client.research() is called with correct payload → Verify outputs are rendered
  - Test 2: Submit query with max_sources=3 → Verify payload includes max_sources=3
  - Test 3: Mock timeout exception → Verify error message is displayed
  - Test 4: Mock invalid response (missing field) → Verify ValidationError is caught and error message shown
  - Test 5: Full success flow — All outputs render correctly with mock backend response

- [X] T026 Add docstrings and type hints to `ui/app.py`, `ui/models.py`, `ui/client/api_client.py`:
  - Module-level docstring: "Gradio 6 research interface — thin client over FastAPI backend"
  - Function docstrings: Parameters, return type, raises (exceptions)
  - Inline comments for non-obvious async/callback logic

- [X] T027 Create `ui/README.md` documenting:
  - Module structure (app.py, client/, components/)
  - How to run locally (point to quickstart.md)
  - How to add new components (reference component pattern from controls.py, results.py)
  - Known limitations (e.g., no state persistence, no retry logic)

- [ ] T028 Verify all edge cases are handled:
  - Empty query submission → blocked by form validation
  - Backend returns empty key_points → displays "(No key points available)"
  - Backend returns no contradictions → contradictions section is hidden or empty
  - Backend timeout after 60s → error message displays, button re-enabled
  - Confidence score outside 0–1 range → formatted as 0 or 1 (clamp)

- [X] T029 Final integration check:
  - Run FastAPI backend on port 8000: `uv run fastapi dev app/main.py`
  - Run Gradio UI on port 7860: `uv run python ui/app.py`
  - Test full flow: enter query → adjust controls → submit → results render → verify sources are clickable
  - Capture screenshot for documentation

---

## Phase 7: Cross-Cutting Concerns & Validation

**Purpose**: Ensure specification compliance, observability, and deployment readiness

### Tasks

- [X] T030 Validate Pydantic models in `ui/models.py` against JSON Schema contracts:
  - ResearchRequest fields match research_request.schema.json (4 required fields)
  - ResearchResponse fields match research_response.schema.json (5 required fields)
  - Create custom validators for edge cases (e.g., max_sources must be int 3–10)

- [X] T031 Implement request/response logging in `ui/client/api_client.py`:
  - On every request: log query, depth, max_sources, time_range (payload summary)
  - On every response: log response_time_ms, source_count, confidence_score, has_contradictions
  - On every error: log error_type, error_message, full traceback
  - Log to stdout with structlog JSON format for integration with deployment logs

- [X] T032 Verify Constitution alignment in `ui/app.py` and `ui/client/api_client.py`:
  - ✅ Determinism: UI only renders backend output, never invents missing content (verified in T018, T019 — show "(No X)" instead of synthesizing)
  - ✅ Retrieval-first: Backend owns all research; UI is pure client (verified in T004 — client delegates to backend)
  - ✅ Bounded autonomy: Single query → single request → single response, no loops (verified in T011 — no retries, no refinement)
  - ✅ Structured outputs: All responses validated with Pydantic (verified in T004 — ResearchResponse.model_validate())
  - ✅ Observability: Logging at client layer with structlog (verified in T006 — all requests/responses logged)
  - ✅ Cost/latency: 60s timeout, no retries (verified in T004 — timeout=60)
  - ✅ Stateless core: No persistence, caching, or session state (verified in T009 — no state variables, fresh query each time)

---

## Summary

| Phase | Task Range | User Stories | Parallel Opportunity |
|-------|-----------|--------------|----------------------|
| 1: Setup | T001–T003 | — | All 3 tasks [P] |
| 2: Foundational | T004–T006 | — | Limited (T005 can start after T004 structure) |
| 3: US1 (P1) | T007–T011 | Submit Query | T007, T008 [P] after T004 |
| 4: US2 (P1) | T012–T016 | Review Results | T012, T013, T014, T015 [P] after T004 |
| 5: US3/US4 (P2) | T017–T024 | Quality + Loading | T017–T019 (US3) [P], T020–T024 (US4) [P] |
| 6: Integration | T025–T029 | Cross-cutting | T025 [P] with T026–T029 |
| 7: Final | T030–T032 | Validation | T030, T031, T032 [P] after T029 |

**Total Tasks**: 32 (including optional test tasks marked `*b`)  
**Estimated Effort**: 16–20 hours for full implementation + integration testing  
**MVP Scope** (Phase 1–3 + US2 basics): 8–10 hours (T001–T016 + T026 docstrings)  

---

## Dependency Notes

### Critical Path (Blocking)**

1. T004 (HTTP client) → T007–T011 (form submission)
2. T004 (HTTP client) → T012–T016 (result rendering)
3. T004 (HTTP client) → T017–T024 (quality/error handling)

### Parallelizable Opportunities

- **After T001–T003**: T005, T006 can start before T004 completes
- **After T004**: All US1/US2/US3/US4 tasks can overlap
- **Phase 6 onward**: T025–T029 can run independently

### Testing Strategy

- Unit tests (T011b, T017b, T023b, T024b) can be written in parallel with implementation
- Integration test (T025) unblocks only after T004, T007, T012–T016 are complete
- Final validation (T030–T032) runs after full implementation

---

## Acceptance Criteria per User Story

### US1: Submit Research Query ✅

- [ ] Form validation prevents empty query submission
- [ ] All control selections (depth, max_sources, time_range) are sent to backend
- [ ] Submit button sends correctly formatted ResearchRequest JSON

### US2: Review Structured Results ✅

- [ ] Summary renders as markdown block without modification
- [ ] Key points render as bullet list in order from backend
- [ ] Sources render in table with clickable URLs
- [ ] Dataframe shows title, URL, relevance (%)

### US3: Understand Result Quality ✅

- [ ] Confidence score displays as percentage (0–100%)
- [ ] Visual indicator color changes based on confidence level
- [ ] Contradictions warning shows only if contradictions present
- [ ] Users can distinguish high vs low confidence at a glance

### US4: Handle Loading/Failure States ✅

- [ ] Loading state shows spinner + disabled button during request
- [ ] Timeout exception displays "Request timed out after 60 seconds"
- [ ] HTTP error displays status code + message
- [ ] Validation error displays "Backend returned an invalid response"
- [ ] Button re-enables after response (success or error)

---

## File Checklist

By end of implementation, these files must exist:

```
ui/
├── __init__.py
├── app.py                ← Main Gradio app (T009, T010, T011, etc.)
├── models.py              ← Pydantic models (T002)
├── client/
│   ├── __init__.py
│   └── api_client.py      ← HTTP client (T004, T006)
└── components/
    ├── __init__.py
    ├── controls.py        ← Depth, max_sources, time_range (T007)
    ├── query_input.py     ← Query textbox (T008)
    ├── results.py         ← Summary, key_points, sources (T012–T015)
    ├── diagnostics.py     ← Confidence, contradictions (T017–T019)
    └── tabs.py            ← Results/Diagnostics tabs (T016b)

tests/
├── conftest.py            ← Fixtures (T005)
├── unit/
│   ├── test_controls.py   ← Controls unit tests (T011b)
│   ├── test_components.py ← Results unit tests (T017b)
│   ├── test_diagnostics.py ← Diagnostics unit tests (T023b)
│   └── test_error_handling.py ← Error handling tests (T024b)
└── integration/
    └── test_research_flow.py ← E2E integration test (T025)

ui/README.md               ← Module documentation (T027)
```
