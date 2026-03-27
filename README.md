# LangChain Research Agent

A bounded research agent that orchestrates web search, evidence synthesis, and contradiction detection to produce reliable research briefs with source traceability. Built with FastAPI, LangChain, and Tavily.

**Current Status**: Phase 5 Complete ✅ | 114 tests passing | 76% coverage

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [API Reference](#api-reference)
7. [Architecture](#architecture)
8. [Running Tests](#running-tests)
9. [Docker Deployment](#docker-deployment)
10. [Troubleshooting](#troubleshooting)
11. [Development](#development)

---

## Overview

### What It Does

The Research Agent accepts natural language queries and returns structured research briefs containing:

- **Summary**: AI-synthesized overview of findings
- **Key Points**: Extracted highlights from retrieved sources
- **Sources**: Ranked and scored web search results with credibility metrics
- **Contradictions**: Detected conflicts between sources with severity levels
- **Confidence Score**: Overall confidence in the research findings

### Key Features

✅ **Depth Control**: Basic (3 sources), Intermediate (10 sources), Deep (15 sources)  
✅ **Time-Range Filtering**: Search across all time, past year, month, week, or day  
✅ **Credibility Scoring**: Domain authority (50%), recency (30%), citation count (20%)  
✅ **Contradiction Detection**: Identifies and surfaces conflicting claims  
✅ **Latency SLAs**: Basic <30s, Intermediate <60s, Deep <120s  
✅ **Health Monitoring**: Real-time health checks and operational metrics  
✅ **Type Safe**: Full type hints with pyright validation (0 errors)  
✅ **Well Tested**: 114 unit and integration tests (76% coverage)  

### Architecture Highlights

- **Stateless**: Pure request-response, no session affinity required
- **Scalable**: Horizontal scaling via StatelessService pattern
- **Observable**: Structured logging with correlation IDs
- **Bounded**: Max 3 Tavily iterations per query (cost-controlled)
- **Production Ready**: Docker containerized, health endpoints, metrics

---

## Quick Start

### Prerequisites

- Python 3.12+ (tested with 3.12.3)
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- Free API keys:
  - [Tavily](https://tavily.com) (web search)
  - [OpenRouter](https://openrouter.ai) (LLM synthesis)

### 5-Minute Setup

```bash
# 1. Clone and enter directory
git clone <repo-url>
cd Langraph-research-agent

# 2. Create environment file
cp .env.example .env
# Edit .env with your API keys:
# TAVILY_API_KEY=your_key_here
# OPENROUTER_MODEL_ID=anthropic/claude-3.5-sonnet

# 3. Install and run
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 4. Test the API
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest advances in quantum computing",
    "depth": "basic"
  }'
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

---

## Installation

### Full Setup with Testing

```bash
# Clone repository
git clone <repo-url>
cd Langraph-research-agent

# Sync dependencies (creates virtual environment)
uv sync

# Verify installation
uv run python --version    # Should be 3.12+
uv run pytest --version    # Should be 9.0+

# Run all tests
uv run pytest tests/ -v

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Dependencies Installed

**Production**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` & `langchain-community` - Agent orchestration
- `pydantic` - Data validation
- `tavily-python` - Web search
- `openrouter` - LLM API
- `httpx` - Async HTTP
- `structlog` - Structured logging

**Development**:
- `pytest` & `pytest-asyncio` - Testing
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `ruff` - Linting
- `pyright` - Type checking
- `uvicorn[standard]` - Dev server

---

## Configuration

### Environment Variables

Create `.env` file in project root (see `.env.example`):

```bash
# Required: Tavily API for web search
TAVILY_API_KEY=tvly-xxxxxxxxxxxx

# Required: OpenRouter (Claude) for synthesis
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_ID=anthropic/claude-3.5-sonnet
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxx

# Optional: Database (Phase 4+)
DATABASE_URL=sqlite:///./research-agent.db
# Uncomment for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/research_agent

# Optional: Redis cache (Phase 3+)
# REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO    # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Application Settings

Edit `app/core/config.py` to customize:

```python
class Settings(BaseSettings):
    # Service
    SERVICE_NAME = "research-agent"
    VERSION = "1.0.0"
    
    # Tavily API
    TAVILY_API_KEY: str  # From environment
    TAVILY_SEARCH_DEPTH_MAP = {
        "basic": 3,
        "intermediate": 10,
        "deep": 15,
    }
    
    # Latency SLAs (seconds)
    LATENCY_SLA = {
        "basic": 30,
        "intermediate": 60,
        "deep": 120,
    }
    
    # Logging
    LOG_LEVEL: str = "INFO"
```

---

## Usage

### Basic Query

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are quantum computing breakthroughs in 2026?",
    "depth": "basic"
  }'
```

**Response** (200 OK):

```json
{
  "summary": "Recent quantum computing advances include IBM's Condor processor with improved error correction and Google's Willow chip demonstration...",
  "key_points": [
    "IBM released Condor with 1121 qubits and improved fidelity",
    "Google announced Willow with exponential error rate improvements",
    "Error rates are dropping, approaching practical quantum advantage"
  ],
  "sources": [
    {
      "title": "IBM Announces Condor Quantum Processor",
      "url": "https://example.com/ibm-condor",
      "relevance": 0.95,
      "credibility_score": 0.87,
      "snippet": "IBM's new Condor processor represents a milestone...",
      "retrieved_at": "2026-03-26T10:30:00Z"
    },
    {
      "title": "Google's Willow Chip Breakthrough",
      "url": "https://example.com/google-willow",
      "relevance": 0.92,
      "credibility_score": 0.85,
      "snippet": "Google demonstrated a quantum chip with improved error correction...",
      "retrieved_at": "2026-03-26T10:29:00Z"
    }
  ],
  "contradictions": [
    {
      "source1_title": "IBM Advances in Error Correction",
      "source2_title": "Alternative Quantum Approach",
      "severity": "MINOR",
      "claims": ["Potential disagreement about error correction methods"]
    }
  ],
  "confidence_score": 0.88
}
```

### Advanced: Deep Research with Time Filter

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

### Request Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `query` | string | required | Any natural language question |
| `depth` | string | "basic" | "basic", "intermediate", "deep" |
| `max_sources` | integer | 10 | 3-20 |
| `time_range` | string | "all" | "all", "year", "month", "week", "day" |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | AI-synthesized overview |
| `key_points` | string[] | 3-5 key findings |
| `sources` | SourceRecord[] | Ranked web results |
| `contradictions` | Contradiction[] | Detected conflicts |
| `confidence_score` | float | 0.0 - 1.0 confidence |

---

## API Reference

### Endpoints

#### POST /research

Perform a research query.

**Request**:
```json
{
  "query": "string",
  "depth": "basic|intermediate|deep",
  "max_sources": 3,
  "time_range": "all|year|month|week|day"
}
```

**Responses**:
- `200 OK` - ResearchBrief
- `422 Unprocessable Entity` - Validation error
- `503 Service Unavailable` - Dependencies offline

---

#### GET /health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-03-26T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "tavily": "ok",
    "openrouter": "ok"
  }
}
```

---

#### GET /metrics

Operational metrics.

**Response** (200 OK):
```json
{
  "total_queries": 1234,
  "average_latency_ms": 8500,
  "success_rate": 0.98,
  "error_rate": 0.02,
  "by_depth": {
    "basic": {"count": 500, "avg_latency_ms": 5000},
    "intermediate": {"count": 600, "avg_latency_ms": 8500},
    "deep": {"count": 134, "avg_latency_ms": 15000}
  },
  "by_time_range": {
    "all": {"count": 900},
    "year": {"count": 200},
    "month": {"count": 100},
    "week": {"count": 25},
    "day": {"count": 9}
  }
}
```

---

### Error Handling

Errors include descriptive messages and error codes:

```json
{
  "detail": "Invalid depth parameter: 'super-deep'. Must be basic, intermediate, or deep.",
  "error_code": "INVALID_DEPTH"
}
```

---

## Architecture

### System Diagram

```
┌─────────────────┐
│   User Client   │
└────────┬────────┘
         │ HTTP POST /research
         ▼
┌─────────────────────────────────┐
│  FastAPI Application            │
│  ├─ Request Validation          │
│  └─ Research Route Handler      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Research Agent (LangChain)     │
│  ├─ Query Planning              │
│  ├─ Tool Orchestration          │
│  └─ Max 3 Iterations            │
└────────┬────────────────────────┘
         │
    ┌────┴───────┬──────────────┐
    ▼            ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────┐
│ Tavily │  │OpenRouter│  │ Metrics │
│ Search │  │   (LLM)  │  │ Service │
└────────┘  └──────────┘  └─────────┘
```

### Service Layers

**app/api/routes/**
- `health.py` - Health checks and metrics endpoints
- `research.py` - Main research query endpoint

**app/services/**
- `retrieval_service.py` - Tavily search, credibility scoring
- `processing_service.py` - Contradiction detection, ranking
- `synthesis_service.py` - LLM synthesis, confidence calculation
- `metrics.py` - Query metrics tracking

**app/agents/**
- `research_agent.py` - LangChain agent with Tavily tool

**app/core/**
- `config.py` - Settings and environment variables
- `logging.py` - Structured logging setup
- `database.py` - Database session management (optional)

---

### Data Models

#### SourceRecord

```python
class SourceRecord(BaseModel):
    title: str                      # Article title
    url: str                        # Source URL
    relevance: float                # 0.0-1.0 relevance score
    credibility_score: float        # 0.0-1.0 credibility
    snippet: str                    # Article excerpt
    retrieved_at: str               # ISO 8601 timestamp
```

#### Contradiction

```python
class Contradiction(BaseModel):
    source1_title: str              # First source
    source2_title: str              # Second source
    severity: str                   # NONE, MINOR, MODERATE, MAJOR
    claims: list[str]               # Conflicting claims
```

#### ResearchBrief

```python
class ResearchBrief(BaseModel):
    summary: str                    # Synthesized overview
    key_points: list[str]           # Key findings
    sources: list[SourceRecord]     # Retrieved sources
    contradictions: list[Contradiction]  # Detected conflicts
    confidence_score: float         # Overall confidence
```

---

### Credibility Scoring Formula

```
credibility_score = (
    domain_authority * 0.5 +        # Major factor
    recency_score * 0.3 +           # Moderate factor
    citation_count * 0.2            # Minor factor
)
```

- **Domain Authority**: (0.0-1.0) based on domain reputation
- **Recency**: (0.0-1.0) based on publish date vs. today
- **Citation Count**: (0.0-1.0) normalized citation presence

---

### Confidence Scoring Formula

```
confidence_score = (
    agreement_score * 0.4 +         # Sources agreement
    quality_score * 0.3 +           # Source quality
    recency_score * 0.2 +           # Data freshness
    freshness_score * 0.1           # Recent sources
) - (contradiction_penalty * 0.15)  # Contradiction penalty

confidence_score = min(max(confidence_score, 0.0), 1.0)  # Clamp 0.0-1.0
```

---

## Running Tests

### All Tests

```bash
# Run all tests with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/api/test_research_endpoint.py -v

# Run tests matching a pattern
uv run pytest tests/ -k "test_research" -v

# Stop on first failure
uv run pytest tests/ -x -v
```

### Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# API tests only
uv run pytest tests/api/ -v

# By marker
uv run pytest -m "not slow" -v
```

### Test Statistics (Current)

- **Total Tests**: 114 passing ✅
- **Unit Tests**: 48 tests covering services, schemas, depth control
- **Integration Tests**: 38 tests covering pipelines, time-range filtering, metrics
- **API Tests**: 28 tests covering endpoints, depth variations
- **Code Coverage**: 76% across app modules
- **Type Safety**: pyright scan - 0 errors, 0 warnings

### Test Structure

```
tests/
├── unit/
│   ├── test_services.py           # Service logic tests
│   ├── test_metrics.py            # Metrics calculation tests
│   ├── test_depth_control.py      # Depth parameter tests
│   └── test_schemas.py            # Data model validation
│
├── integration/
│   ├── test_research_pipeline.py  # End-to-end service integration
│   ├── test_metrics_integration.py # Metrics integration tests
│   ├── test_time_range_filter.py   # Time-range filtering tests
│   └── conftest.py                # Shared fixtures
│
└── api/
    ├── test_research_endpoint.py   # /research endpoint tests
    ├── test_depth_variations.py    # Depth parameter API tests
    └── conftest.py                # API fixtures
```

---

## Docker Deployment

### Build Image

```bash
# Build production image
docker build -t research-agent:latest .

# Verify image
docker images | grep research-agent
```

### Run Container

```bash
# Create .env file with API keys
cp .env.example .env
# Edit .env with your keys

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  research-agent:latest

# Run with docker-compose
docker-compose up -d
docker-compose logs -f app
```

### Docker Compose

See `docker-compose.yml` for full setup with environment variables.

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## Troubleshooting

### Common Issues

#### 1. Tavily API Key Error

**Error**: `AuthenticationError: Invalid Tavily API key`

**Solution**:
```bash
# Verify .env file exists
cat .env | grep TAVILY_API_KEY

# Get free API key from https://tavily.com
# Update .env with your key
```

#### 2. OpenRouter Connection Timeout

**Error**: `ConnectionError: Failed to connect to OpenRouter`

**Solution**:
```bash
# Check internet connection
curl https://openrouter.ai/api/v1/models

# Verify API key is correct
grep OPENROUTER .env

# Check API quota at https://openrouter.ai
```

#### 3. Tests Failing with Deprecation Warnings

**Warning**: `datetime.utcnow() is deprecated`

**Status**: This is a known warning in test fixtures. Production code uses `datetime.now(timezone.utc)`. Not a test failure.

**Suppress warnings**:
```bash
uv run pytest tests/ -W ignore::DeprecationWarning -v
```

#### 4. Port 8000 Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Use different port
uv run uvicorn app.main:app --reload --port 8001

# Or kill existing process
lsof -i :8000
kill -9 <PID>
```

#### 5. Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Ensure dependencies are synced
uv sync

# Run from project root
cd /path/to/Langraph-research-agent
uv run pytest tests/ -v
```

---

## Development

### Code Quality

All code is validated with modern Python tools:

```bash
# Type checking (0 errors)
uv run pyright app/

# Code formatting (consistent style)
uv run black app/ tests/

# Linting (no violations)
uv run ruff check app/ tests/

# All tests passing
uv run pytest tests/ -v
```

### Code Style

- **Type Hints**: Full type hints on all functions (pyright: strict mode)
- **Formatting**: Black (88-char line width)
- **Linting**: Ruff with sensible defaults
- **Testing**: pytest with 76%+ coverage on app modules

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature

# Make changes
# Test thoroughly
uv run pytest tests/ -v

# Format and lint
uv run black app/ tests/
uv run ruff check app/ tests/ --fix

# Type check
uv run pyright app/

# Commit
git add -A
git commit -m "feat: description of changes"
git push origin feat/your-feature
```

---

## Performance Considerations

### Latency SLAs

The system is designed to meet these latency targets:

| Depth | Max Sources | Target | Notes |
|-------|-------------|--------|-------|
| Basic | 3 | <30s | Immediate results |
| Intermediate | 10 | <60s | More comprehensive |
| Deep | 15 | <120s | Maximum depth research |

**Current measured performance**:
- Basic: ~8-12 seconds (1-2 Tavily calls)
- Intermediate: ~15-25 seconds (2-3 Tavily calls)
- Deep: ~25-45 seconds (3 Tavily calls + synthesis)

### Metric Tracking

View performance metrics at `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics | jq .
```

### Optimization Tips

1. **Add Redis caching** (Phase 3+):
   ```bash
   REDIS_URL=redis://localhost:6379/0 uv run uvicorn app.main:app
   ```

2. **Use intermediate depth** for most queries (good balance)

3. **Batch requests** rather than sequential calls

---

## Support & Documentation

### Key Documents

- **Specification**: `/specs/001-research-agent/spec.md` - User requirements
- **Data Model**: `/specs/001-research-agent/data-model.md` - Entity relationships
- **API Contracts**: `/specs/001-research-agent/contracts/` - Request/response schemas
- **Quickstart**: `/specs/001-research-agent/quickstart.md` - Integration examples
- **Implementation Plan**: `/specs/001-research-agent/plan.md` - Technical decisions

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Tavily API Docs](https://docs.tavily.com/sdk/python/quick-start)
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [pytest Documentation](https://docs.pytest.org/)

### Getting Help

- **Check `/specs/001-research-agent/`** for technical decisions
- **Review test files** in `tests/` for usage examples
- **Check `/app/` source code** - extensively documented
- **Run `/health` endpoint** to verify system is operational

---

## License

See [LICENSE](LICENSE) file for details.

---

**Last Updated**: 2026-03-26  
**Project Status**: Phase 5 Complete | Production Ready  
**Version**: 1.0.0  
**Maintainer**: Research Agent Team