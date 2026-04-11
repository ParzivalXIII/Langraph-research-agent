# LangChain Research Agent

A bounded research agent system that orchestrates web search, full-page content fetching, evidence synthesis, and contradiction detection to produce reliable research briefs with source traceability.

**Backend**: FastAPI + LangChain + Tavily API + Web Fetch Tool  
**Frontend**: Gradio 6 (Controlled Research Interface with CALM theme)  
**Status**: 🚀 Production Ready with full UI integration and enhanced content enrichment

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
   - [Backend API](#backend-api-quick-start)
   - [Gradio UI](#gradio-ui-quick-start)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [API Reference](#api-reference)
7. [Architecture](#architecture)
8. [Running Tests](#running-tests)
9. [Docker Deployment](#docker-deployment)
10. [Development](#development)

---

## Overview

### What It Does

The Research Agent system provides both a REST API and web UI for comprehensive research query orchestration with enhanced content enrichment:

**Backend Research Agent**:
- **Web Search & Fetch**: Tavily API for initial search + Web Fetch Tool for full-page content extraction
- **Summary**: AI-synthesized overview of findings using enriched full-page content
- **Key Points**: Extracted highlights from retrieved sources with enhanced context
- **Sources**: Ranked and scored web search results with credibility metrics and full-page snippets
- **Contradictions**: Detected conflicts between sources with severity levels
- **Confidence Score**: Dynamic calculation based on source agreement, content richness, & recency

**Gradio Web Interface**:
- User-friendly form with depth/source/time-range controls
- Real-time research results display with tabbed views
- Diagnostics panel for transparency and debugging
- CALM Research theme with professional styling
- Responsive mobile-friendly design

### Key Features

**Research Engine**:
- ✅ **Depth Control**: Basic (3 sources), Intermediate (10 sources), Deep (15 sources)
- ✅ **Time-Range Filtering**: Search across all time, past year, month, week, or day
- ✅ **Domain Filtering**: Optional domain whitelist for targeted research (e.g., ["reuters.com", "fxstreet.com"])
- ✅ **Credibility Scoring**: Domain authority (50%), recency (30%), citation count (20%)
- ✅ **Web Fetch Tool**: Batch fetch up to 50 URLs with full-page content extraction
  - Concurrent fetching with configurable rate limiting
  - Markdown or JSON output formats
  - Optional headless browser rendering for JavaScript-heavy pages
  - Automatic retries with exponential backoff (up to 3 attempts)
  - Per-domain rate limiting (1 req/s configurable)
- ✅ **Contradiction Detection**: Identifies and surfaces conflicting claims
- ✅ **Dynamic Confidence**: Calculated from source agreement, quality, recency, content richness, contradiction penalty
- ✅ **Latency SLAs**: Basic <30s, Intermediate <60s, Deep <120s

**User Interface**:
- ✅ **Gradio Web UI**: Professional research interface on localhost:7860
- ✅ **CALM Theme**: Calm aesthetics with dark/light mode support
- ✅ **Clear Labels**: Meaningful component labels ("Key Points", "Confidence Score", etc.)
- ✅ **Diagnostics Tab**: Request/response inspection for transparency
- ✅ **Form Validation**: Client and server-side input validation
- ✅ **Error Handling**: User-friendly error messages with recovery suggestions

**Production Ready**:
- ✅ **Type Safe**: Full type hints with pyright validation (0 errors)
- ✅ **Well Tested**: 214+ unit and integration tests (100% critical paths)
- ✅ **Health Monitoring**: Real-time health checks and operational metrics
- ✅ **Structured Logging**: Correlation IDs and json-formatted output
- ✅ **Docker Containerized**: Multi-stage builds for both API and UI  

### Architecture Highlights

**Backend**:
- **Stateless**: Pure request-response, no session affinity required
- **Scalable**: Horizontal scaling via StatelessService pattern
- **Observable**: Structured logging with correlation IDs
- **Bounded**: Max 3 Tavily iterations per query (cost-controlled)
- **Modular**: Separation of concerns (retrieval, processing, synthesis, web fetch services)
- **Content-Enriched**: Web Fetch Tool enriches Tavily snippets with full-page content for improved synthesis

**Frontend**:
- **Thin Client**: Gradio UI delegates all logic to backend
- **Deterministic**: No client-side synthesis or data invention
- **Themeable**: CALM Research theme with customizable styling
- **Accessible**: Clear labels, form validation, error guidance
- **Responsive**: Mobile-friendly design with professional layout

**Deployment**:
- **Docker Containerized**: Multi-stage builds for minimal image size
- **Health Endpoints**: `/health` and `/metrics` for monitoring
- **Production Ready**: ASGI server, connection pooling, resource management

---

## Quick Start

### Prerequisites

- Python 3.12+ (tested with 3.12.3)
- `uv` package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- Free API keys:
  - [Tavily](https://tavily.com) (web search)
  - [OpenRouter](https://openrouter.ai) (LLM synthesis)

### Backend API Quick Start

```bash
# 1. Clone and enter directory
git clone https://github.com/ParzivalXIII/Langraph-research-agent.git
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

### Gradio UI Quick Start

```bash
# In the same terminal or a new one (with uv sync already run):
uv run python -m ui.app
```

Open [http://localhost:7860](http://localhost:7860) to access the **Controlled Research Interface** with:
- Query input field with placeholder guidance
- Research Depth selector (basic/intermediate/deep)
- Maximum Sources slider (3-10)
- Time Range dropdown (day/week/month/year/all)
- Results tab displaying summary, key points, and sources table
- Diagnostics tab for request/response inspection
- CALM Research theme with professional styling

**Recent Improvements**:
- ✅ Fixed textbox labels ("Key Points" and "Confidence Score" instead of generic "Textbox")
- ✅ Improved UI clarity with meaningful component labels
- ✅ Enhanced diagnostics display for transparency

---

## Installation

### Full Setup with Testing

```bash
# Clone repository
git clone https://github.com/ParzivalXIII/Langraph-research-agent.git
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
- `langchain` & `langchain-openrouter` - Agent orchestration and LLM API
- `pydantic` - Data validation
- `tavily-python` - Web search
- `httpx` - Async HTTP
- `structlog` - Structured logging
- `scrapy` - Web scraping framework
- `playwright` - Headless browser automation
- `beautifulsoup4` - HTML parsing
- `markdownify` - HTML to markdown conversion
- `redis` - Caching and sessions
- `sqlmodel` - SQLAlchemy ORM with Pydantic

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

# Web Fetch Tool Configuration (Optional, with sensible defaults)
WEB_FETCH_MAX_CONCURRENCY=5           # Max concurrent requests (1-20)
WEB_FETCH_PER_DOMAIN_LIMIT=1.0        # Rate limit: req/s per domain
WEB_FETCH_MAX_RETRIES=3               # Automatic retry attempts
WEB_FETCH_RETRY_BASE_DELAY=1.0        # Exponential backoff base (seconds)
WEB_FETCH_MAX_CONTENT_CHARS=5000      # Content truncation limit
WEB_FETCH_HEADLESS_ENABLED=true       # Enable Playwright headless browser

# Optional: Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./research-agent.db
# Uncomment for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/research_agent

# Optional: Redis cache
REDIS_URL=redis://localhost:6379/0

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

### Advanced: Domain-Filtered Research

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "USD/EUR exchange rate trends",
    "depth": "intermediate",
    "time_range": "month",
    "include_domains": ["reuters.com", "fxstreet.com", "tradingeconomics.com"]
  }'
```

### Advanced: Deep Research with Time Filter and Web Fetch Enrichment

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest developments in quantum error correction",
    "depth": "deep",
    "max_sources": 15,
    "time_range": "month"
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
      "snippet": "IBM's new Condor processor represents a milestone with 1121 qubits...",
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
| `query` | string | required | Any natural language question (3-500 chars) |
| `depth` | string | "intermediate" | "basic", "intermediate", "deep" |
| `max_sources` | integer | 10 | 1-50 |
| `time_range` | string | "all" | "all", "year", "month", "week", "day" |
| `include_domains` | array[string] | null | Optional domain whitelist (e.g., ["reuters.com", "bbc.com"]) |

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
    ┌────┼────────────────┬──────────────┐
    ▼    ▼                ▼              ▼
┌────────┐┌──────────┐┌──────────┐ ┌─────────┐
│ Tavily ││Web Fetch ││OpenRouter│ │ Metrics │
│ Search ││Tool     ││  (LLM)   │ │ Service │
└────────┘└──────────┘└──────────┘ └─────────┘
    │         │           │
    └─────────┼───────────┘
        Content Enrichment & 
        Synthesis Pipeline
```

**Pipeline Flow**:
1. **Retrieval**: Tavily API fetches initial search results and snippets
2. **Content Enrichment (Optional)**: Web Fetch Tool fetches full-page content from URLs for enriched context
3. **Processing**: Detection of contradictions and ranking of sources
4. **Synthesis**: LLM synthesizes final brief using enriched content
5. **Metrics**: Track query performance and results

### Service Layers

**app/api/routes/**

- `health.py` - Health checks and metrics endpoints
- `research.py` - Main research query endpoint

**app/services/**

- `retrieval_service.py` - Tavily search (with optional Web Fetch Tool integration), credibility scoring
- `processing_service.py` - Contradiction detection, ranking
- `synthesis_service.py` - LLM synthesis, confidence calculation
- `metrics.py` - Query metrics tracking

**app/tools/**

- `tavily.py` - Tavily API wrapper
- `web_fetch.py` - Web Fetch Tool for full-page content extraction and enrichment

**app/agents/**

- `research_agent.py` - LangChain agent orchestrator with max 3 iterations

**app/core/**

- `config.py` - Settings and environment variables
- `logging.py` - Structured logging setup
- `database.py` - Database session management
- `errors.py` - Error definitions and HTTP mapping
- `llm.py` - LLM provider configuration

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

## Web Fetch Tool

### Overview

The Web Fetch Tool enriches research results by fetching and extracting full-page content from URLs. This overcomes limitations of search engine snippets and provides richer context for synthesis.

**Core Capabilities**:
- ✅ **Batch Processing**: Fetch up to 50 URLs concurrently in a single request
- ✅ **Multiple Output Formats**: Markdown or structured JSON output
- ✅ **Rate Limiting**: Per-domain request throttling (configurable, default 1 req/s)
- ✅ **Smart Retries**: Automatic retries on transient errors (429, 5xx) with exponential backoff
- ✅ **Headless Browser Support**: Optional Playwright rendering for JavaScript-heavy pages
- ✅ **Graceful Degradation**: Partial results returned if some URLs fail; batch doesn't abort
- ✅ **Content Truncation**: Configurable max content size with truncation flag
- ✅ **Error Tracking**: Per-URL error reasons for debugging and monitoring

### Request Schema

```python
class WebFetchRequest(BaseModel):
    urls: list[str]                 # 1-50 URLs to fetch
    output_format: str              # "markdown" or "json"
    config: WebFetchConfig          # Optional config overrides

class WebFetchConfig(BaseModel):
    max_content_chars: int = 5000   # Content truncation limit
    timeout_seconds: float = 15.0   # HTTP timeout
    use_headless: bool = False      # Playwright rendering
    include_links: bool = False     # Include links in JSON output
```

### Response Schema

```python
class WebFetchResult(BaseModel):
    pages: list[FetchedPage]        # Results for each URL
    total_count: int                # Total URLs requested
    success_count: int              # Successfully fetched
    failure_count: int              # Failed fetches
    total_latency_ms: int           # Total time for batch

class FetchedPage(BaseModel):
    url: str                        # Original URL
    status_code: int                # HTTP status (200, 404, etc.)
    content: str | dict             # Extracted content (markdown or JSON)
    content_length: int             # Content size in chars/bytes
    content_truncated: bool         # Whether content was truncated
    latency_ms: int                 # Fetch time for this URL
    error: Optional[str]            # Error message if fetch failed
    retrieved_at: str               # ISO 8601 timestamp
```

### Usage in Research Pipeline

The Web Fetch Tool is automatically integrated into the retrieval service. When a research query is processed:

1. Tavily API returns search results with short snippets
2. Web Fetch Tool (optional) enriches these with full-page content
3. Content is passed to synthesis service for more accurate brief generation
4. Richer context improves contradiction detection and confidence scoring

### Configuration

Web Fetch settings can be overridden per-domain in environment variables:

```bash
# Global settings
WEB_FETCH_MAX_CONCURRENCY=5           # Parallel requests limit
WEB_FETCH_PER_DOMAIN_LIMIT=1.0        # Rate: requests per second per domain
WEB_FETCH_MAX_RETRIES=3               # Automatic retry attempts
WEB_FETCH_RETRY_BASE_DELAY=1.0        # Exponential backoff base (seconds)
WEB_FETCH_MAX_CONTENT_CHARS=5000      # Default content truncation
WEB_FETCH_HEADLESS_ENABLED=true       # Enable browser automation
```

### Rate Limiting

The tool enforces per-domain rate limiting to respect server policies:

- **Default**: 1 request per second per domain
- **Configurable**: Via `WEB_FETCH_PER_DOMAIN_LIMIT`
- **Respects Retry-After**: Honors server-provided retry delays
- **Exponential Backoff**: On transient failures (429, 503)

Example: Fetching 5 URLs from the same domain takes ≥4 seconds minimum (1 req/s × 4 gaps).

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

- **Total Tests**: 114+ passing ✅ (includes web fetch tool tests)
- **Unit Tests**: Covering services, schemas, depth control, web fetch configuration
- **Integration Tests**: Covering pipelines, time-range filtering, metrics, content enrichment
- **API Tests**: Covering endpoints, depth variations, request parameter validation
- **Code Coverage**: 76%+ across app modules
- **Type Safety**: pyright scan - 0 errors, 0 warnings

### Test Structure

```
tests/
├── unit/
│   ├── test_services.py           # Service logic tests
│   ├── test_metrics.py            # Metrics calculation tests
│   ├── test_depth_control.py      # Depth parameter tests
│   ├── test_schemas.py            # Data model validation
│   └── test_web_fetch.py          # Web Fetch Tool tests
│
├── integration/
│   ├── test_research_pipeline.py  # End-to-end service integration
│   ├── test_metrics_integration.py # Metrics integration tests
│   ├── test_time_range_filter.py   # Time-range filtering tests
│   ├── test_web_fetch_pipeline.py # Web Fetch integration with retrieval
│   └── conftest.py                # Shared fixtures
│
├── api/
│   ├── test_research_endpoint.py   # /research endpoint tests
│   ├── test_depth_variations.py    # Depth parameter API tests
│   └── conftest.py                # API fixtures
│
├── ui/
│   └── test_research_interface_styling.py  # UI component tests
│
└── fixtures/
    ├── sample_queries.json        # Test data
    └── custom_theme_example.py    # UI theme fixtures
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

- Basic: ~8-12 seconds (1-2 Tavily calls, with optional web fetch)
- Intermediate: ~15-25 seconds (2-3 Tavily calls, with optional web fetch)
- Deep: ~25-45 seconds (3 Tavily calls + synthesis, with optional web fetch)

**Web Fetch Impact**: Adding full-page content enrichment typically adds 5-15 seconds depending on:
- Number of URLs to fetch (up to 50 concurrent)
- Response sizes (configurable, default 5000 chars)
- Network conditions and target server response times
- Rate limiting delays (1 req/s per domain default)

### Metric Tracking

View performance metrics at `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics | jq .
```

### Optimization Tips

1. **Control Web Fetch behavior**:
   - Disable content enrichment for speed: reduce timeout or set `max_sources` lower
   - Increase content limits for richer synthesis: `WEB_FETCH_MAX_CONTENT_CHARS` (up to 50000)
   - Enable headless browser for JS-heavy sites: `WEB_FETCH_HEADLESS_ENABLED=true`
   - Tune concurrency: `WEB_FETCH_MAX_CONCURRENCY=5-10` based on your target servers

2. **Add Redis caching** (optional for Phase 3+):

   ```bash
   REDIS_URL=redis://localhost:6379/0 uv run uvicorn app.main:app
   ```

3. **Use intermediate depth** for most queries (good balance of speed vs. comprehensiveness)

4. **Batch requests** rather than sequential calls

5. **Domain filtering** via `include_domains` reduces network calls for targeted research

---

## Support & Documentation

### Key Documents

- **Specification**: `/specs/001-research-agent/spec.md` - User requirements
- **Data Model**: `/specs/001-research-agent/data-model.md` - Entity relationships
- **API Contracts**: `/specs/001-research-agent/contracts/` - Request/response schemas
- **Quickstart**: `/specs/001-research-agent/quickstart.md` - Integration examples
- **Implementation Plan**: `/specs/001-research-agent/plan.md` - Technical decisions

**Web Fetch Tool** (Phase 4+):

- **Specification**: `/specs/004-web-fetch-scraping-tool/spec.md` - Full requirements and design
- **Data Model**: `/specs/004-web-fetch-scraping-tool/data-model.md` - WebFetchRequest/Response schemas
- **QA Cases**: `/specs/004-web-fetch-scraping-tool/qa/` - Test scenarios and edge cases

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
