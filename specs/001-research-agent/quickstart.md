# Quickstart: Research Agent Integration Guide

**Last Updated**: 2026-03-26  
**Feature**: Research Agent (001-research-agent)  
**Stage**: Phase 1 MVP

---

## Table of Contents

1. [Setup](#setup)
2. [Local Development](#local-development)
3. [Making Requests](#making-requests)
4. [Understanding Responses](#understanding-responses)
5. [Health Checks](#health-checks)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Setup

### Prerequisites

- Python 3.11+
- `uv` package manager (see [uv-guidelines.md](/home/parzival/.claude/rules/uv-guidelines.md))
- Tavily API key (free tier available at <https://tavily.com>)
- OpenRouter API key (free credits at <https://openrouter.ai>)

### Environment Configuration

Create a `.env` file in the repository root:

```bash
# .env
# Tavily API key for web search
TAVILY_API_KEY=your_tavily_key_here

# OpenRouter API configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_ID=anthropic/claude-3.5-sonnet

# Optional: Database (Phase 4+)
DATABASE_URL=sqlite:///./research-agent.db
# DATABASE_URL=postgresql://user:password@localhost:5432/research_agent

# Optional: Cache (Phase 3+)
# REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
```

---

## Local Development

### 1. Install Dependencies

```bash
cd /home/parzival/projects/Langraph-research-agent

# Sync Python environment
uv sync

# Verify installation
uv run python --version
```

### 2. Run the Development Server

```bash
# Start FastAPI app with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3. Access the API Documentation

Open your browser:

- **OpenAPI (Swagger UI)**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

You can test endpoints directly from the Swagger UI.

---

## Making Requests

### Example 1: Basic Query

**Request**:

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest advances in quantum computing?",
    "depth": "basic"
  }'
```

**Expected Response** (200 OK):

```json
{
  "summary": "Recent developments in quantum computing show significant progress...",
  "key_points": [
    "IBM released Condor processor with 1121 qubits",
    "Google announced Willow with improved error correction",
    "Error rates improving exponentially"
  ],
  "sources": [
    {
      "title": "IBM Announces Condor",
      "url": "https://example.com/ibm-condor",
      "relevance": 0.95
    },
    {
      "title": "Google Willow Chip Breakthrough",
      "url": "https://example.com/google-willow",
      "relevance": 0.92
    }
  ],
  "contradictions": [],
  "confidence_score": 0.88
}
```

---

### Example 2: Deep Research with Time Filter

**Request**:

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "climate change mitigation strategies 2026",
    "depth": "deep",
    "max_sources": 15,
    "time_range": "month"
  }'
```

**Parameters Explained**:

- `depth: "deep"` → More comprehensive search (up to 10+ Tavily calls)
- `max_sources: 15` → Return up to 15 sources (max 50)
- `time_range: "month"` → Only sources from the last month

---

### Example 3: Quick Check (Basic Depth)

**Request**:

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{"query": "Is Python 3.12 released?"}'
```

**Parameters Explained**:

- `depth` defaults to `"intermediate"` (5–10 sources)
- `max_sources` defaults to `10`
- `time_range` defaults to `"all"`

---

## Understanding Responses

### Response Structure

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | Narrative summary (50–2000 chars) |
| `key_points` | array | 1–10 bullet points highlighting findings |
| `sources` | array | Sources cited (min 1) with title, URL, relevance |
| `contradictions` | array | Any conflicting claims between sources (optional) |
| `confidence_score` | float | 0.0–1.0 indicating certainty of synthesis |

### Interpreting Confidence Score

| Score | Interpretation | Action |
|-------|-----------------|--------|
| 0.9–1.0 | Very High | All sources agree; strong consensus |
| 0.7–0.9 | High | Most sources agree; minor ambiguities |
| 0.5–0.7 | Moderate | Mixed signals; contradictions present |
| 0.3–0.5 | Low | Scarce evidence; high uncertainty |
| 0.0–0.3 | Very Low | Insufficient evidence; retrieval failed |

### Handling Contradictions

If the `contradictions` array is non-empty:

1. Review the claims carefully
2. Check timestamps of sources (older sources may be outdated)
3. Consider domain authority: academic papers > news > blogs
4. Request a re-search with updated time range if needed

---

## Health Checks

### Check Service Status

```bash
curl http://localhost:8000/health
```

**Expected Response** (200 OK):

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
    "uptime_seconds": 3600,
    "requests_total": 42,
    "requests_failed": 1,
    "average_latency_ms": 1245,
    "tavily_calls_total": 120,
    "cache_hit_rate": 0.0,
    "memory_usage_mb": 95.2
  }
}
```

**Status Legend**:

- `healthy`: Dependency is operational
- `degraded`: Dependency is slow or having intermittent issues
- `unhealthy`: Dependency is unavailable
- `not_configured`: Feature (e.g., cache) is not enabled

---

## Troubleshooting

### Problem: "Tavily API unavailable"

**Response**: HTTP 503 with `confidence_score: 0.0`

**Causes**:

- Tavily API is down
- API key is invalid or expired
- Network connectivity issue

**Solution**:

1. Verify `TAVILY_API_KEY` is set and valid
2. Check Tavily status: <https://tavily.com/status>
3. Retry after a few seconds (temporary outage)

---

### Problem: "Invalid request" (HTTP 400)

**Common Causes**:

- `query` is too short (<3 chars)
- `query` is too long (>500 chars)
- `depth` is not one of: basic, intermediate, deep
- `time_range` is not one of: day, week, month, year, all

**Solution**:

```bash
# Verify your request against the schema
# See: specs/001-research-agent/contracts/research_request.schema.json
```

---

### Problem: "Validation error" (HTTP 422)

**Cause**: Request body doesn't match schema

**Example Error Response**:

```json
{
  "detail": [
    {
      "loc": ["body", "max_sources"],
      "msg": "ensure this value is less than or equal to 50",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Solution**: Check your JSON structure and data types against the schema.

---

### Problem: "Slow responses (>2 minutes)"

**Causes**:

- `depth: "deep"` with large `max_sources` (too many Tavily calls)
- Network latency to Tavily or OpenRouter
- System CPU/memory constraints

**Solutions**:

1. Use `depth: "basic"` for faster results
2. Reduce `max_sources` (e.g., from 20 to 10)
3. Narrow `time_range` (e.g., `"week"` instead of `"all"`)
4. Check Phase 3 (caching) for repeated queries

---

## Testing the API Locally

### Using Swagger UI (Recommended)

1. Open <http://localhost:8000/docs>
2. Click "Try it out" on the `/research` endpoint
3. Fill in the request body:

   ```json
   {
     "query": "test query",
     "depth": "basic"
   }
   ```

4. Click "Execute"

### Using Python (Programmatic)

```python
import httpx
import asyncio

async def test_research_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/research",
            json={
                "query": "quantum computing advances 2026",
                "depth": "intermediate",
                "max_sources": 10
            }
        )
        print(response.json())

asyncio.run(test_research_agent())
```

### Using pytest (Unit Tests)

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/api/test_routes.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html
```

---

## Docker Setup (For Reproducibility)

### Build and Run with Docker Compose

```bash
# From repository root
docker-compose up --build

# Service will be available at http://localhost:8000
```

**Services**:

- `app`: FastAPI research agent (port 8000)
- `db`: PostgreSQL (optional, Phase 4, port 5432)
- `redis`: Redis cache (optional, Phase 3, port 6379)

---

## Integration Examples

### Example 1: Simple CLI Tool

```python
#!/usr/bin/env python3
# cli_research.py
import argparse
import httpx
import json

def main():
    parser = argparse.ArgumentParser(description="Research CLI")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--depth", default="intermediate", choices=["basic", "intermediate", "deep"])
    parser.add_argument("--sources", type=int, default=10)
    args = parser.parse_args()

    response = httpx.post(
        "http://localhost:8000/research",
        json={
            "query": args.query,
            "depth": args.depth,
            "max_sources": args.sources
        }
    )
    brief = response.json()

    print(f"\n📄 Summary:\n{brief['summary']}")
    print(f"\n✨ Key Points:")
    for point in brief['key_points']:
        print(f"  - {point}")
    print(f"\n📚 Sources ({len(brief['sources'])}):")
    for i, src in enumerate(brief['sources'], 1):
        print(f"  {i}. [{src['relevance']:.1%}] {src['title']}")
        print(f"     {src['url']}")
    if brief['contradictions']:
        print(f"\n⚠️  Contradictions:")
        for c in brief['contradictions']:
            print(f"  - {c}")
    print(f"\n📊 Confidence: {brief['confidence_score']:.0%}\n")

if __name__ == "__main__":
    main()
```

**Usage**:

```bash
uv run python cli_research.py "latest AI breakthroughs" --depth intermediate
```

---

### Example 2: Gradio Web UI (Phase 4)

```python
# ui_research.py (Phase 4 optional)
import gradio as gr
import httpx

def research(query, depth="intermediate", max_sources=10):
    response = httpx.post(
        "http://localhost:8000/research",
        json={"query": query, "depth": depth, "max_sources": max_sources}
    )
    brief = response.json()
    return brief["summary"]

demo = gr.Interface(
    fn=research,
    inputs=[
        gr.Textbox(label="Research Query"),
        gr.Radio(["basic", "intermediate", "deep"], label="Depth"),
        gr.Slider(1, 50, value=10, label="Max Sources")
    ],
    outputs="text",
    title="Research Agent",
    description="Get structured research briefs powered by Tavily + LLM"
)

demo.launch()
```

---

## Performance Tuning

### Optimize for Speed (Under 60 seconds)

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your query",
    "depth": "basic",          # ← Fast search
    "max_sources": 5,          # ← Fewer sources
    "time_range": "week"       # ← Narrow time window
  }'
```

### Optimize for Breadth (More Comprehensive)

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your query",
    "depth": "deep",           # ← Thorough search
    "max_sources": 20,         # ← More sources
    "time_range": "all"        # ← All time periods
  }'
```

**Latency Trade-off**:

- `basic`: ~30–60 seconds
- `intermediate`: ~60–90 seconds
- `deep`: ~90–120 seconds (close to 2-minute budget)

---

## Next Steps

### Phase 2: Reliability (In Progress)

- Deduplication of sources
- Source ranking by domain authority
- Confidence scoring refinement
- Structured logging

### Phase 3: Performance (Planned)

- Redis caching for query results
- Query fingerprinting
- Token optimization

### Phase 4: Persistence (Planned)

- PostgreSQL integration for query history
- Result archival and audit trails
- Gradio web UI (optional)

---

## Support & Feedback

For issues, feature requests, or documentation clarifications:

1. Check this document's Troubleshooting section
2. Review the data model: [data-model.md](./data-model.md)
3. Inspect API contracts: [contracts/](./contracts/)
4. Review feature specification: [spec.md](./spec.md)

---

**Version**: 1.0.0 Phase 1 MVP  
**Last Updated**: 2026-03-26
