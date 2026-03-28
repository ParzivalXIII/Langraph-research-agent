# Phase 1 Data Model: Controlled Research Interface

**Date**: 2026-03-28 | **Scope**: Data structures, validation, and transformation flow  
**Status**: Complete

## Design Principle

**Minimal transformation**: All data structures are designed for **transparent pass-through** from the backend to the UI. The UI is not responsible for synthesis, ranking, or re-ordering of results. Any transformation (e.g., sorting, filtering) remains solely in the backend.

---

## Domain Entities

### 1. Research Query (User Input)

**Definition**: The set of parameters provided by the user to request a research investigation.

**Fields**:

- `query` (string, required): The research question or topic. Must not be empty or whitespace-only.
- `depth` (string, required): Research breadth. Enum: `["basic", "intermediate", "deep"]`
- `max_sources` (integer, required): Maximum number of sources to retrieve. Range: 3–10.
- `time_range` (string, required): Temporal scope. Enum: `["day", "week", "month", "year", "all"]`

**Validation Rules**:

- `query` must be non-empty after `.strip()`
- `depth` must be one of the enumerated values
- `max_sources` must be an integer in [3, 10]
- `time_range` must be one of the enumerated values

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator

class ResearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="Research question")
    depth: Literal["basic", "intermediate", "deep"] = Field(...)
    max_sources: int = Field(..., ge=3, le=10)
    time_range: Literal["day", "week", "month", "year", "all"] = Field(...)
    
    @field_validator("query")
    @classmethod
    def query_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
```

---

### 2. Research Request (HTTP Request Payload)

**Definition**: The data sent to the backend `/research` endpoint. Maps 1:1 to `ResearchQuery`.

**Fields**: Same as `ResearchQuery` (no additional fields added by UI)

**JSON Representation**:

```json
{
  "query": "AI agents in 2026",
  "depth": "intermediate",
  "max_sources": 5,
  "time_range": "month"
}
```

**Transport**: HTTP POST to `${API_BASE_URL}/research` with `Content-Type: application/json`

---

### 3. Research Response (HTTP Response Payload)

**Definition**: The complete research result returned by the backend. The UI renders this faithfully without modification.

**Fields**:

- `summary` (string): A synthesized narrative answer to the query. May span multiple paragraphs.
- `key_points` (array of strings): Bulleted highlights extracted from retrieved sources. Order is as provided by backend.
- `sources` (array of Source objects): Ranked list of retrieved references. See `Source` entity below.
- `contradictions` (array of strings): Conflicting statements found across sources. May be empty.
- `confidence_score` (number, 0.0–1.0): Quantifies how stable/supported the answer is.

**Validation Rules**:

- `summary` must be non-empty string
- `key_points` must be a list; each element must be a non-empty string
- `sources` must be a list of valid `Source` objects
- `contradictions` must be a list; each element must be a non-empty string (may be empty list)
- `confidence_score` must be a float in [0.0, 1.0]

**Pydantic Model**:

```python
class Source(BaseModel):
    title: str = Field(..., min_length=1, description="Source title or headline")
    url: str = Field(..., description="Web URL or reference link")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score 0-1")

class ResearchResponse(BaseModel):
    summary: str = Field(..., min_length=1)
    key_points: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
```

**JSON Representation**:

```json
{
  "summary": "AI agents are increasingly autonomous decision-makers in 2026. Key trends include...",
  "key_points": [
    "Multi-agent frameworks enable complex task decomposition",
    "Tool-using agents show improved reasoning",
    "Safety constraints are still emerging"
  ],
  "sources": [
    {"title": "Agents in 2026 Survey", "url": "https://example.com/survey", "relevance": 0.95},
    {"title": "LLM Agents Review", "url": "https://example.com/review", "relevance": 0.87}
  ],
  "contradictions": [
    "Source A claims agents need more training data; Source B claims pretraining is sufficient"
  ],
  "confidence_score": 0.78
}
```

---

### 4. Source

**Definition**: A single retrieved reference cited in the research result.

**Fields**:

- `title` (string): Human-readable headline or source name.
- `url` (string): Web URL or document path. Must be clickable in the UI.
- `relevance` (number, 0.0–1.0): Normalized score indicating how relevant this source is to the query.

**Validation Rules**:

- `title` must be a non-empty string
- `url` must be a valid URL (basic format check; can be improved with `pydantic-extra-validators`)
- `relevance` must be a float in [0.0, 1.0]

**Pydantic Model**:

```python
from pydantic import HttpUrl

class Source(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(...)  # Can be enhanced with HttpUrl validation
    relevance: float = Field(..., ge=0.0, le=1.0)
```

---

### 5. Diagnostics (Rendered Metadata)

**Definition**: Metadata about request/response status, not a separate backend entity. Computed by UI.

**Fields** (UI-side only):

- `request_time_ms` (integer): Time elapsed from click to result. For transparency.
- `response_status` (string): "success" | "timeout" | "validation_error" | "http_error"
- `error_message` (string, optional): Human-readable error if response failed.
- `source_count` (integer): Count of returned sources (may be < `max_sources`).
- `has_contradictions` (boolean): True if contradictions array is non-empty.

**Purpose**: Help users understand completeness and reliability of the result. UI-side computation only.

**Implementation Note**: Diagnostics is a logical grouping rendered across multiple UI components (confidence display in T018, contradictions warning in T019, error messages in T020–T022) rather than a single unified module. Each field maps to a specific UI element: `confidence_score` → confidence visual, `contradictions` → warning section, `error_message` → error display, `source_count` → metadata, `has_contradictions` → conditional warning visibility.

---

## Data Transformation Flow

```
User Input (Gradio components)
    ↓
ResearchQuery (validated)
    ↓
ResearchRequest (JSON serialization)
    ↓
POST /research → Backend
    ↓
HTTP 200 + JSON
    ↓
ResearchResponse (Pydantic validation)
    ↓
UI Rendering (breakdown by tab/component)
    - Summary tab ← summary field
    - Key Points tab ← key_points array
    - Sources tab ← sources array (as dataframe)
    - Diagnostics tab ← confidence_score + contradictions
    - Raw (optional) ← entire ResearchResponse as JSON
```

---

## Error Handling & Edge Cases

### Invalid Request (Client-Side)

If user submits with empty query or invalid controls:

- **Action**: Block submission button; show inline error message.
- **No request sent**.

### Valid Request, Invalid Response

If backend returns:

- **Missing fields**: ValidationError caught; show "Invalid backend response" error.
- **Partial fields** (e.g., empty `key_points`): Still render; show empty section, not error.
- **Malformed JSON**: httpx parsing fails; show "Backend error" message.

### HTTP / Timeout Errors

- **httpx.TimeoutException**: Show "Request timed out after 60 seconds."
- **httpx.HTTPError (4xx/5xx)**: Show "Backend error: [status code]".
- **httpx.ConnectError**: Show "Unable to connect to backend."

### Schema Validation Failure

```python
try:
    result = ResearchResponse.model_validate(response_data)
except ValidationError as e:
    logger.error("response_validation_error", errors=e.errors())
    return "Error: Backend returned invalid response", "", [], "", 0
```

---

## Assumptions & Constraints

1. **Backend schema is stable**: No need for versioning in v1.
2. **Sources are pre-ranked**: Backend provides correct ordering; UI doesn't re-sort.
3. **Summary is synthesized by backend**: UI doesn't need to generate or condense.
4. **Contradictions are pre-identified**: UI doesn't perform logical analysis.
5. **No multi-request workflows**: One query → one response. No iterative refinement.
6. **No state persistence**: UI doesn't cache, store, or recall past results in v1.

---

## Summary Table

| Entity | Source | Ownership | Validation |
|---|---|---|---|
| ResearchQuery | User input (Gradio) | Client (UI) | Pydantic model |
| ResearchRequest | ResearchQuery | Client (UI) | Pydantic model |
| ResearchResponse | Backend HTTP | Shared | Pydantic model (client-side validation) |
| Source | ResearchResponse | Backend | Pydantic model (nested in ResearchResponse) |
| Diagnostics | Computed by UI | Client (UI) | None (metadata only) |

All models are defined in `ui/models.py` for reusability across components.
