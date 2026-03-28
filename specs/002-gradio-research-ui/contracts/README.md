# API Contracts

This directory contains JSON Schema definitions for the HTTP API contracts between the Gradio UI and the FastAPI research backend.

## Files

- **research_request.schema.json**: The request payload structure for `POST /research`
- **research_response.schema.json**: The response payload structure from `POST /research`
- **health_metrics.schema.json**: (Reference) The research backend health/metrics schema

## Purpose

These schemas serve as the **source of truth** for request/response validation. The Gradio UI client MUST validate all requests and responses against these schemas to catch mismatches early and prevent logic drift.

## Usage

In the Gradio UI:

```python
import json
from pydantic import ValidationError, BaseModel

# Load schema and create Pydantic model
with open('contracts/research_request.schema.json') as f:
    request_schema = json.load(f)

# Alternatively, manually define Pydantic models (preferred for clarity)
class ResearchRequest(BaseModel):
    query: str
    depth: Literal["basic", "intermediate", "deep"]
    max_sources: int
    time_range: Literal["day", "week", "month", "year", "all"]

# Use model for validation
try:
    payload = ResearchRequest(**user_input)
except ValidationError as e:
    show_error(f"Invalid input: {e}")
```

## Contract Enforcement

1. **Pre-submission validation**: Use Pydantic to validate user input before sending to backend
2. **Post-response validation**: Use Pydantic to validate backend response before rendering
3. **Error handling**: Catch ValidationError and show user-friendly messages
4. **Logging**: Log schema violations for debugging and monitoring

## Evolution

When the backend schema changes:

1. Update the relevant `.schema.json` file
2. Update the corresponding Pydantic model in `ui/models.py`
3. Add a changelog entry documenting the breaking change
4. Test the UI with the new schema

## Notes

- Schemas follow **JSON Schema Draft 7** standard for maximum portability
- All schemas include examples for clarity and testing
- Required fields are explicitly marked; optional fields have defaults
