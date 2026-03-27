# API Contracts

This directory contains JSON Schema definitions for the research agent API contracts.

## Files

### research_request.schema.json

**Endpoint**: `POST /research`  
**Purpose**: User-submitted research query with search parameters  
**Required Fields**: `query`  
**Optional Fields**: `depth`, `max_sources`, `time_range`

**Example Request**:

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest quantum computing advances",
    "depth": "intermediate",
    "max_sources": 10,
    "time_range": "month"
  }'
```

---

### research_brief.schema.json

**Endpoint**: `POST /research` (response)  
**Purpose**: Structured research brief synthesized from retrieved sources  
**Required Fields**: `summary`, `key_points`, `sources`, `confidence_score`  
**Optional Fields**: `contradictions`

**Example Response**:

```json
{
  "summary": "Recent advances in quantum computing...",
  "key_points": [
    "IBM released Condor processor with 1121 qubits",
    "Google announced Willow with improved error correction"
  ],
  "sources": [
    {
      "title": "IBM Announces Condor",
      "url": "https://example.com/ibm-condor",
      "relevance": 0.95
    }
  ],
  "contradictions": [],
  "confidence_score": 0.88
}
```

---

### health_metrics.schema.json

**Endpoint**: `GET /health`  
**Purpose**: Service health status and operational metrics  
**HTTP Status**: 200 (healthy) or 503 (unhealthy)

**Example Response**:

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2026-03-26T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "api": "healthy",
    "tavily": "healthy",
    "database": "healthy",
    "cache": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "requests_total": 1500,
    "requests_failed": 2,
    "average_latency_ms": 1200,
    "tavily_calls_total": 450,
    "cache_hit_rate": 0.65,
    "memory_usage_mb": 125.4
  }
}
```

---

## HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Successful research brief returned; health check passed |
| 400 | Invalid request (e.g., query too short, invalid depth parameter) |
| 422 | Validation error (e.g., URL field not valid HTTP(S)) |
| 500 | Internal server error (unexpected error during synthesis) |
| 503 | Service unavailable (Tavily API unreachable; Tavily returned confidence=0.0) |

---

## Error Response Format (400, 422, 500)

```json
{
  "detail": "Human-readable error message",
  "error_code": "TAVILY_UNAVAILABLE | SYNTHESIS_FAILED | VALIDATION_ERROR",
  "status_code": 500
}
```

---

## Rate Limiting (Phase 2+)

Not implemented in Phase 1 MVP. Phase 2 will add per-IP rate limiting (e.g., 10 requests/minute).

---

## Authentication (Future)

Not implemented in Phase 1 MVP. Phase 2+ may add API key validation.

---

## Versioning

Current API version: **v1** (implicit in routes; `/research`, not `/v1/research`)

Future: If major breaking changes occur, may introduce `/v2/research` alongside `/v1/research` for backward compatibility.

---

## Validation Notes

All schemas are validated against JSON Schema Draft 7. Pydantic models in `app/schemas/research.py` enforce these constraints at runtime.

**Validation happens at two levels**:

1. **Request**: Pydantic validates incoming POST /research body
2. **Response**: Pydantic validates outgoing ResearchBrief before serialization

---

## Extending the API (Future)

When adding new endpoints (Phase 2+):

1. Create a new schema file in `contracts/` (e.g., `search_history.schema.json`)
2. Add corresponding Pydantic model in `app/schemas/`
3. Implement FastAPI route in `app/api/routes.py`
4. Update this README with endpoint details
