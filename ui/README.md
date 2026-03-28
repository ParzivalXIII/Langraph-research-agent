# Controlled Research Interface (UI)

A **thin, deterministic Gradio 6 client** for the FastAPI research backend.

- **Pure pass-through**: Renders backend output without synthesis or invention
- **Type-safe**: All input/output validated with Pydantic models
- **Async-native**: Leverages Gradio 6's native async without threading hacks
- **Structured logging**: JSON logs for observability and debugging
- **Deterministic**: Single query → single request → single response (no retries, no refinement)
- **Stateless**: No persistence, caching, or session state

**Location**: `ui/` directory  
**Framework**: Gradio 6 + Pydantic 2 + httpx + structlog  
**Purpose**: Bounded presentation layer; backend is single source of truth  
**Design**: Form input → Pydantic validation → HTTP request → Response → Formatters → UI render

---

## Module Structure

```
ui/
├── __init__.py             # Package initialization
├── README.md               # This file
├── app.py                  # Main Gradio Blocks app + event handlers
├── models.py               # Pydantic validation models
├── client/
│   ├── __init__.py
│   └── api_client.py       # ResearchClient: async HTTP with structlog
└── components/
    ├── __init__.py
    ├── controls.py         # Dropdown/slider components
    ├── query_input.py      # Query textbox component
    ├── results.py          # Result formatting functions
    ├── diagnostics.py      # Confidence score + contradictions formatters
    └── tabs.py             # Results/Diagnostics tab layout
```

## Core Modules

### `ui/app.py`
Main application layout and event handlers.

**Key Functions**:
- `build_app() -> gr.Blocks`
  - Constructs full Gradio UI with input section, submit button, tabbed outputs
  - Implements T009: Form structure with validation, loading states, error display
  
- `async run_research(query, depth, max_sources, time_range) -> tuple`
  - Main async callback for form submission
  - Step 1: Validate input with Pydantic ResearchQuery
  - Step 2: Call ResearchClient.research(payload)
  - Step 3: Format response using component formatters
  - Step 4: Handle all exceptions and return user-friendly errors
  - Returns: (summary, key_points, sources_table, contradictions, confidence, diagnostics_json)
  
- `validate_query(query) -> (bool, str)`
  - Real-time query validation (enables/disables submit button)
  - Checks: non-empty, whitespace-only rejection, minimum 3 characters

**Helper Functions**:
- `_get_user_friendly_error(error) -> str`: Maps exceptions to user messages
- `_get_error_status(error) -> str`: Maps exceptions to diagnostic status codes
- `_format_diagnostics(diagnostics) -> str`: Formats Diagnostics as JSON

### `ui/models.py`
Pydantic data validation models (strict, per JSON Schema contracts).

**ResearchQuery** (Form Input)
```python
query: str              # Non-empty, non-whitespace (validated)
depth: Literal[...]    # 'basic', 'intermediate', 'deep'
max_sources: int       # 3–10 inclusive
time_range: Literal... # 'day', 'week', 'month', 'year', 'all'
```

**ResearchResponse** (Backend Response)
```python
summary: str                    # Narrative answer (non-empty)
key_points: list[str]          # Bulleted highlights (empty list OK)
sources: list[Source]          # Ranked references (empty list OK)
contradictions: list[str]      # Conflicting statements (empty list OK)
confidence_score: float        # 0.0–1.0 stability score
```

**Source** (Reference Object)
```python
title: str              # Source headline (non-empty)
url: str               # Web URL (non-empty)
relevance: float       # 0.0–1.0 relevance score
```

**Diagnostics** (Metadata)
```python
request_payload: dict   # Original form submission
response_status: str    # 'success', 'timeout', 'http_error', 'validation_error', 'unknown_error'
error_message: str      # Empty if success, error description if failure
response_shape: dict    # Keys present in response (debugging)
execution_time_ms: int  # Wall-clock time from submission to render
```

### `ui/client/api_client.py`
Async HTTP client for backend communication with structured logging.

**ResearchClient Class**
- **Configuration**:
  - `base_url`: Backend URL (env: `API_BASE_URL`, default: `http://localhost:8000`)
  - `timeout`: Request timeout in seconds (env: `API_TIMEOUT`, default: `60`)
  - Precedence: Constructor arg → env var → hardcoded default

- **`__init__(base_url: str | None, timeout: int | None)`**
  - Initialize client with optional overrides
  - Log initialization with structlog

- **`async research(payload: dict) -> dict`**
  - Submit POST request to `/research` endpoint
  - Per-request AsyncClient pattern (efficient for 10-60s latency)
  - Response validation with Pydantic ResearchResponse.model_validate()
  - Structured logging:
    - **Request**: endpoint, payload_keys, timeout
    - **Success**: status_code, response_keys, execution_time_ms, result counts
    - **Error**: error_type, status_code, execution_time_ms
  - Raises: httpx.TimeoutException, httpx.HTTPStatusError, httpx.ConnectError, ValueError

## Component Modules

### `ui/components/controls.py`
Form control components (dropdowns and slider).

```python
create_depth_dropdown() -> gr.Dropdown
  # Choices: ['basic', 'intermediate', 'deep']
  # Default: 'intermediate'

create_max_sources_slider() -> gr.Slider
  # Range: [3, 10], Default: 5

create_time_range_dropdown() -> gr.Dropdown
  # Choices: ['day', 'week', 'month', 'year', 'all']
  # Default: 'all'
```

### `ui/components/query_input.py`
Query textbox component.

```python
create_query_input() -> gr.Textbox
  # Placeholder: "Enter your research question..."
  # Max length: 500 characters
  # Lines: 2
  # Validation: Pydantic ResearchQuery checks non-empty at submission
```

### `ui/components/results.py`
Result rendering functions (transform ResearchResponse to UI-ready formats).

**Component Builders**:
```python
create_summary_output() -> gr.Markdown
create_key_points_output() -> gr.Textbox
create_sources_table() -> gr.Dataframe
create_contradictions_output() -> gr.Markdown
create_confidence_output() -> gr.Textbox
```

**Formatting Functions**:
```python
format_summary(response) -> str
  # Passes summary as-is
  # Edge case: "(No summary available)" if empty

format_key_points(response) -> str
  # Joins as bullet list: "• Point 1\n• Point 2"
  # Edge case: "(No key points available)" if empty

format_sources_table(response) -> list[list]
  # Converts to: [[title, url, relevance_pct], ...]
  # Edge case: [] if no sources

format_contradictions(response) -> str
  # Delegates to diagnostics.format_contradictions()

format_confidence(response) -> str
  # Delegates to diagnostics.format_confidence()
  # Returns: percentage string like "78%"
```

### `ui/components/diagnostics.py`
Quality visualization helpers (confidence score and contradictions).

**Component Builders**:
```python
create_confidence_display() -> (gr.Number, gr.HTML)
  # Returns: (percentage_number, colored_bar_html)

create_contradictions_display() -> gr.Markdown
  # Markdown component for contradictions warning
```

**Formatting Functions**:
```python
format_confidence(score: float) -> (str, str)
  # Returns: (percentage_text, html_indicator)
  # Colors: Red (≤0.5), Yellow (0.5–0.8), Green (>0.8)
  # Handles invalid/missing: defaults to 0.0 (red, 0%)

format_contradictions(contradictions: list[str]) -> str
  # If empty: "(No contradictions detected)"
  # If present: "⚠️ **Contradictions Detected:**\n - bullet points"
```

### `ui/components/tabs.py`
Tabbed layout for Results and Diagnostics.

```python
create_results_tabs() -> tuple[gr.Tabs, gr.Markdown, gr.Textbox, gr.Dataframe, gr.Markdown, gr.Textbox, gr.Textbox]
  # Returns: (tabs, summary, key_points, sources, contradictions, confidence, diagnostics)
  # Results Tab: Summary, Key Points, Sources, Contradictions, Confidence
  # Diagnostics Tab: Request/Response metadata (JSON)
```

---

## How to Run Locally

### Prerequisites
- Python 3.10+ (tested on 3.12)
- Dependencies: Gradio 6, Pydantic 2, httpx, structlog
- FastAPI backend running on http://localhost:8000 (or set `API_BASE_URL`)

### Installation

```bash
# From project root
cd /home/parzival/projects/Langraph-research-agent

# Using uv (recommended)
uv sync

# Or using Poetry
poetry install

# Verify installation
python -c "import gradio; import pydantic; print('✓ Dependencies OK')"
```

### Running the UI

```bash
# Start Gradio UI on port 7860 (opens in browser)
uv run python ui/app.py

# Or with custom backend URL
API_BASE_URL=http://api.example.com:8000 uv run python ui/app.py

# Or with custom timeout
API_TIMEOUT=120 uv run python ui/app.py
```

### Running Full Stack (UI + Backend)

**Terminal 1: FastAPI Backend**
```bash
cd /home/parzival/projects/Langraph-research-agent
uv run fastapi dev app/main.py
# Backend runs on http://localhost:8000
# /research endpoint: POST /research with {query, depth, max_sources, time_range}
```

**Terminal 2: Gradio UI**
```bash
cd /home/parzival/projects/Langraph-research-agent
uv run python ui/app.py
# UI runs on http://localhost:7860
# Auto-opens browser
```

---

## How to Add New Components

### Step 1: Create Component Module
Create `ui/components/my_feature.py`:

```python
"""Custom UI component for my feature.

Implements new functionality as reusable Gradio components.
"""

import gradio as gr
from typing import Optional


def create_my_component() -> gr.Textbox:
    """Create my custom component.
    
    Returns:
        gr.Textbox: Custom textbox configured for my feature
        
    Example:
        component = create_my_component()
        # Wire to event handler in app.py
    """
    return gr.Textbox(label="My Feature", interactive=False)
```

### Step 2: Wire into app.py
Import and add to `build_app()`:

```python
from ui.components.my_feature import create_my_component

def build_app() -> gr.Blocks:
    with gr.Blocks() as app:
        # ... existing code ...
        my_component = create_my_component()
        # Wire to event handler if needed
        submit_btn.click(fn=my_callback, inputs=[query], outputs=[my_component])
    return app
```

### Step 3: Add Tests
Create `tests/unit/test_my_feature.py`:

```python
import pytest
import gradio as gr
from ui.components.my_feature import create_my_component


def test_create_my_component():
    """Verify component is properly configured."""
    component = create_my_component()
    assert isinstance(component, gr.Textbox)
    assert component.interactive is False
```

### Step 4: Follow Design Principles
- **Single Responsibility**: Each component does one thing
- **Type Safety**: Use Pydantic for validation
- **Error Handling**: Catch exceptions, return user-friendly messages
- **Logging**: Use structlog for observability
- **Testing**: 80%+ code coverage for new code

---

## Known Limitations

### V1 Constraints
1. **No Result Caching**: Each query generates fresh backend request (no persistence)
2. **No Pagination**: Backend controls source count via `max_sources` (3–10)
3. **No Refinement Loops**: Single query → single response (manual submission for refinement)
4. **No Conversation History**: Each submission is independent
5. **No Result Filtering**: UI renders in backend order (no client-side ranking)

### Future Enhancements (Out of Scope)
- Redis caching for repeated queries
- Advanced filtering/sorting UI
- Export results (PDF, JSON, Markdown)
- Multi-language support
- User annotations on sources
- Result comparison view

---

## Architecture Decisions

### Why Gradio?
- Fast prototyping with minimal boilerplate
- Python-native (no JavaScript needed)
- Async support for I/O-bound operations
- Live updates and real-time validation

### Why Per-Request AsyncClient?
- More efficient for typical 10-60s latency than connection pooling
- Automatic resource cleanup via context manager
- Simpler testing and debugging (isolated instances)

### Why Pydantic Everywhere?
- Type safety with Python type hints
- Auto-generates JSON Schema for API contracts
- Custom validators for complex business logic
- Consistent validation layer (forms, requests, responses)

### Why Stateless?
- No synchronization issues between frontend/backend
- Full auditability: every request/response logged
- Alignment with project constitution (Stateless Core principle)
- Simplicity: single callback per form submission

---

## Observability & Debugging

### Structured Logging
All requests/responses logged via structlog with JSON output.

**Request Log Example**:
```json
{
  "event": "research_request",
  "endpoint": "http://localhost:8000/research",
  "payload_keys": ["query", "depth", "max_sources", "time_range"],
  "timeout": 60
}
```

**Success Response Log**:
```json
{
  "event": "research_success",
  "status_code": 200,
  "response_keys": ["summary", "key_points", "sources", "contradictions", "confidence_score"],
  "execution_time_ms": 2345,
  "sources_count": 3,
  "confidence_score": 0.78
}
```

**Error Log**:
```json
{
  "event": "research_timeout",
  "timeout": 60,
  "execution_time_ms": 60234,
  "error": "Request exceeded timeout threshold"
}
```

View logs in terminal where UI is running, or pipe to log aggregation service.

---

## Testing

```bash
# All unit tests
uv run pytest tests/unit/ -v

# UI-specific tests
uv run pytest tests/unit/test_ui_* tests/unit/test_constitution_compliance.py -v

# With coverage report
uv run pytest tests/unit/ --cov=ui --cov-report=html
# Open: htmlcov/index.html
```

**Key Test Modules**:
- `tests/unit/test_ui_models.py`: Pydantic model validation
- `tests/unit/test_ui_components.py`: Component rendering
- `tests/unit/test_error_handling.py`: Exception handling
- `tests/unit/test_constitution_compliance.py`: Constitution principles
- `tests/integration/test_research_pipeline.py`: End-to-end flow

---

## API Contract

### Backend Endpoint: POST /research

**Request Body**:
```json
{
  "query": "AI agents 2026",
  "depth": "intermediate",
  "max_sources": 5,
  "time_range": "month"
}
```

**Response Body** (200 OK):
```json
{
  "summary": "AI agents in 2026 represent...",
  "key_points": ["Agents enable decomposition...", "Safety remains active..."],
  "sources": [
    {"title": "AI Agents Survey", "url": "https://...", "relevance": 0.95},
    {"title": "Tool Use in LLMs", "url": "https://...", "relevance": 0.87}
  ],
  "contradictions": [],
  "confidence_score": 0.78
}
```

**Full Contracts**: See `specs/002-gradio-research-ui/contracts/`

---

## Constitution Compliance

The UI satisfies all seven core principles:

1. **Determinism**: Backend is single source of truth; no client-side synthesis
2. **Retrieval-First**: Backend owns all research; UI is pure client
3. **Bounded Autonomy**: Single query → single response, no loops
4. **Structured Outputs**: All responses validate against Pydantic schemas
5. **Observability**: Structured logging with request/response details
6. **Cost/Latency**: 60s timeout, no retries, single request
7. **Stateless Core**: No persistence, caching, or session state

**Verification**: See `specs/002-gradio-research-ui/constitution-check.md`

---

## Related Documentation

- **Specification**: `specs/002-gradio-research-ui/spec.md`
- **Data Model**: `specs/002-gradio-research-ui/data-model.md`
- **Technical Plan**: `specs/002-gradio-research-ui/plan.md`
- **API Contracts**: `specs/002-gradio-research-ui/contracts/`
- **Quick Start**: `specs/002-gradio-research-ui/quickstart.md`
- **Constitution Check**: `specs/002-gradio-research-ui/constitution-check.md`
- **Project Instructions**: `/home/parzival/.claude/rules/python-dev-standards.instructions.md`

---

## License

Part of the Langraph Research Agent project. See `LICENSE` for details.

**Pattern**: Factory function returns Gradio component with fixed configuration.

```python
# ui/components/query_input.py
def create_query_input() -> gr.Textbox:
    return gr.Textbox(
        label="Research Query",
        lines=2,
        placeholder="Enter your research question...",
        max_length=500
    )

# Usage in app.py
query_input = create_query_input()
```

**Why this pattern?**
- Encapsulates component configuration (no magic strings in app.py)
- Reusable across tests and different app instances
- Easy to modify styling, validation, etc. in one place

### 2. Response Formatting Components

**Pattern**: Transform ResearchResponse field → UI-ready string/table.

```python
# ui/components/results.py
def format_confidence(response: ResearchResponse) -> tuple[str, str]:
    """Return (percentage_text, colored_html_bar)"""
    score = response.confidence_score
    percentage = f"{score * 100:.0f}%"
    
    if score > 0.8:
        color = "green"
    elif score > 0.5:
        color = "yellow"
    else:
        color = "red"
    
    html_bar = f'<div style="background: {color}; width: {percentage}; height: 20px;"></div>'
    return percentage, html_bar

# Usage in app.py
confidence_str = format_confidence(result)
```

**Why this pattern?**
- Separates business logic (formatting) from Gradio UI code
- Easy to test formatters independently
- Reusable across components

### 3. Async Event Handlers

**Pattern**: Gradio button.click() → async function → multiple output updates.

```python
# ui/app.py
async def run_research(query: str, depth: str, max_sources: int, time_range: str) -> tuple:
    """Validate → submit → render → log"""
    # Step 1: Validate with Pydantic
    try:
        ResearchQuery.model_validate({...})
    except ValueError:
        return ("Validation error", ...)
    
    # Step 2: Submit to backend
    try:
        response_data = await client.research(payload)
    except Exception as e:
        return (_get_user_friendly_error(e), ...)
    
    # Step 3: Validate response
    try:
        result = ResearchResponse.model_validate(response_data)
    except ValueError:
        return ("Invalid response", ...)
    
    # Step 4: Format outputs
    return (
        format_summary(result),
        format_key_points(result),
        format_sources_table(result),
        format_contradictions(result),
        format_confidence(result),
        _format_diagnostics(diagnostics)
    )

submit_btn.click(
    fn=run_research,
    inputs=[query_input, depth_dropdown, max_sources_slider, time_range_dropdown],
    outputs=[summary_output, key_points_output, sources_table, ...]
)
```

**Why this pattern?**
- Clear separation of concerns: validate → query → render
- Structured error handling at each stage
- Type-safe with Pydantic
- Logged with structlog

### 4. Error Handling

**Pattern**: Try-catch at each stage → map to user-friendly message → log details.

```python
# ui/app.py
def _get_user_friendly_error(error: Exception) -> str:
    """Technical → user-friendly message mapping"""
    if type(error).__name__ == "TimeoutException":
        return "Request timed out after 60 seconds..."
    elif type(error).__name__ == "HTTPError":
        return "Backend error. Please try again later."
    else:
        return f"Error: {str(error)}"

# In run_research()
try:
    response_data = await client.research(payload)
except Exception as e:
    error_msg = _get_user_friendly_error(e)
    logger.error("run_research_backend_error", error=str(e))
    return (error_msg, "", [], "", "", diagnostics_json)
```

**Why this pattern?**
- Users see helpful, non-technical messages
- Developers see detailed logs for troubleshooting
- Consistent error mapping across the app

---

## Design Principles

### 1. **Determinism over Invention**
- The UI renders exactly what the backend provides
- If backend returns empty `key_points`, UI shows "No key points found", NOT synthesized bullets
- No client-side NLP, ranking, or content generation
- **Design enforcement**: Response formatting functions check for empty lists and render appropriately

### 2. **Type Safety**
- All form inputs validated with Pydantic ResearchQuery
- All backend responses validated with Pydantic ResearchResponse
- Invalid data is rejected with descriptive error messages
- **Design enforcement**: `model_validate()` called before rendering; exceptions trigger error display

### 3. **Stateless Operation**
- No session state, cookies, or persistent local storage
- Each form submission is independent
- Results are not cached on the client
- **Design enforcement**: form.submit() → run_research() → render → discard. No variables persist.

### 4. **Structured Logging**
- All requests, responses, and errors logged with structlog
- JSON format for easy parsing and aggregation
- Includes: endpoint, payload, status, timing, error details
- **Design enforcement**: `logger = structlog.get_logger()` at module level

### 5. **Bounded Latency**
- Default timeout: 60 seconds  
- User is notified if request exceeds timeout
- **Design enforcement**: `timeout=60` in ResearchClient.__init__; caught and displayed as error

---

## Testing

### Unit Tests

Location: `tests/unit/`

```bash
# Run all UI unit tests
pytest tests/unit/test_ui_*.py -v

# Key test files:
# - test_ui_models.py: Pydantic validation (ResearchQuery, ResearchResponse)
# - test_ui_components.py: Component factory functions (formatting functions)
# - test_error_handling.py: Error mapping and user-friendly messages
# - test_diagnostics.py: Diagnostics data capture
```

### Integration Tests

Location: `tests/integration/`

```bash
# Run UI integration tests
pytest tests/integration/test_*.py -v

# Requires backend running on http://localhost:8000
```

### Manual Testing

1. Start backend: `uv run main.py` (port 8000)
2. Start UI: `uv run ui/app.py` (port 7860)
3. Test flow:
   - Enter query: "AI agents 2026"
   - Select depth: "intermediate"
   - Select max sources: 5
   - Select time range: "month"
   - Click "Run Research"
   - Verify results rendered (summary, key points, sources, etc.)
   - Check Diagnostics tab for request/response metadata

---

## Limitations

### Scope Limitations

1. **No multi-turn conversation**
   - Each form submission is a single, independent query
   - No conversation history or context carried between requests
   - User must manually refine and resubmit queries

2. **No caching on client**
   - Every query triggers a new backend request
   - Results are not cached locally after rendering
   - To view previous results, resubmit the query

3. **No search/filtering of results**
   - UI renders backend response as-is
   - No client-side reranking, filtering, or sorting of sources
   - No full-text search within results

4. **No chat/refinement interface**
   - Pure form-based query submission
   - No follow-up questions or clarifications
   - No "explain this source" or "dig deeper" buttons

### Technical Limitations

1. **Single-browser instance**
   - Gradio is designed for single-user local development
   - No multi-user session management
   - No authentication or authorization (relies on backend)

2. **Browser file size**
   - Gradio compiles JavaScript in the browser
   - No large file uploads/downloads
   - Results JSON must fit in a single HTTP response

3. **No offline mode**
   - Requires active connection to backend
   - Cannot work with stale/cached backend responses

4. **No partial rendering**
   - Results wait for entire backend response before rendering
   - No streaming of results as they become available
   - No "show partial results while waiting for more"

### Dependency Limitations

1. **Gradio version pinning**
   - Code depends on Gradio 6.x API
   - Breaking changes in Gradio 7+ may require significant refactoring
   - Limited access to bleeding-edge Gradio features

2. **Pydantic 2.x only**
   - Models use Pydantic v2 syntax (field_validator, model_dump, etc.)
   - Not backward-compatible with Pydantic 1.x

3. **httpx async only**
   - No synchronous HTTP client version
   - Requires async/await throughout the app

---

## Troubleshooting

### "Backend is unreachable" Error

**Symptom**: Every query returns "Backend error: Unable to connect"

**Diagnosis**:
- Check backend is running: `curl http://localhost:8000/health`
- Check backend port with: `lsof -i :8000` (macOS/Linux)
- Verify `API_BASE_URL` env var: `echo $API_BASE_URL`

**Solution**:
```bash
# Terminal 1: Start backend
uv run main.py

# Terminal 2: Check health
curl http://localhost:8000/health

# Terminal 3: Start UI
API_BASE_URL=http://localhost:8000 uv run ui/app.py
```

### "Request timed out" Error

**Symptom**: Queries consistently timeout after 60 seconds

**Diagnosis**:
- Backend is slow (>60s response time)
- Network latency is high
- Large payload or complex research task

**Solution**:
```bash
# Increase timeout to 120 seconds
API_TIMEOUT=120 uv run ui/app.py

# Or check backend performance
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query":"test","depth":"basic","max_sources":3,"time_range":"day"}'
```

### "Invalid response" Error

**Symptom**: "Backend returned invalid response" appears after submission

**Diagnosis**:
- Backend returned data missing required fields
- Backend response doesn't match ResearchResponse schema
- Check Diagnostics tab for response_shape key

**Solution**:
- View Diagnostics tab → response_shape
- Compare with ResearchResponse schema (ui/models.py)
- Report issue with backend response structure

### Components Not Appearing

**Symptom**: Gradio UI loads but form/outputs not visible

**Diagnosis**:
- Gradio not fully loaded in browser
- JavaScript error in browser console
- CSS/styling issue

**Solution**:
```bash
# Hard refresh browser
# macOS: Cmd+Shift+R
# Windows/Linux: Ctrl+Shift+R

# Or restart UI
pkill -f "uv run ui/app.py"
uv run ui/app.py
```

---

## Architecture Diagrams

### Request/Response Flow

```
User Input (Form)
    ↓
validate_query() + Pydantic ResearchQuery validation
    ↓ (if invalid → error display)
    ↓ (if valid → enable submit)
Submit Button Click
    ↓
run_research() async callback
    ├─ Step 1: ResearchQuery.model_validate(form_data)
    │   └─ if failed → user-friendly error message
    ├─ Step 2: client.research(payload)
    │   └─ if error → catch & map to user message
    └─ Step 3: ResearchResponse.model_validate(backend_data)
        └─ if failed → validation error message
    ↓
format_* functions (summary, key_points, sources, confidence, contradictions)
    ↓
Gradio output components update (Markdown, Textbox, Dataframe)
    ↓
User sees results
```

### Module Dependency Graph

```
ui/app.py (main)
├── ui/client/api_client.py (ResearchClient)
├── ui/models.py (Pydantic models)
├── ui/components/query_input.py
├── ui/components/controls.py
├── ui/components/results.py
├── ui/components/diagnostics.py
└── ui/components/tabs.py

Back-end:
└── http://localhost:8000/research (FastAPI)
```

---

## Related Files

- **Specs**: `/specs/002-gradio-research-ui/` (design documents, contracts)
- **Tests**: `/tests/unit/test_ui_*.py`, `/tests/integration/`
- **Backend**: `/app/api/routes/research.py`, `/app/services/research_service.py`
- **Config**: `.env` (optional), `pyproject.toml`

---

## Contributing

### Adding a New Component

1. Create `ui/components/new_feature.py` with factory function
2. Import and use in `ui/app.py`
3. Write unit tests in `tests/unit/test_ui_new_feature.py`
4. Document in this README under "Component Patterns"

### Modifying Error Handling

1. Update `_get_user_friendly_error()` for new exception types
2. Update `_get_error_status()` for diagnostics
3. Add test case in `tests/unit/test_error_handling.py`

### Updating Models

1. Modify Pydantic model in `ui/models.py`
2. Update JSON Schema contract in `specs/002-gradio-research-ui/contracts/`
3. Run `pytest tests/unit/test_ui_models.py` to validate

---

## Version History

- **v2.0** (Phase 5, 2026-03-28): Added loading states, error handling, confidence visualization
- **v1.0** (Phase 3–4, 2026-03): Initial UI with form input, results rendering

---

## License

See `/LICENSE`
