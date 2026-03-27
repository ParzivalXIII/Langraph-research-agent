# Phase 0: Research & Technology Decisions

**Document Date**: 2026-03-26  
**Feature**: Research Agent (001-research-agent)  
**Status**: Complete — All NEEDS CLARIFICATION items resolved

---

## Executive Summary

This document captures technology decisions and rationale for the research agent feature. All architectural choices align with the Langraph-research-agent Constitution v1.0.0 (Determinism, Retrieval-First, Bounded Autonomy, Structured Outputs, Observability, Cost+Latency, Stateless Core).

---

## 1. Web Retrieval Strategy: Tavily API

### Decision

**Primary Retrieval**: Tavily Search API  
**Fallback**: None (fail explicitly if Tavily unavailable)  
**Parallelization**: Async HTTP calls (httpx, not aiohttp) for multiple Tavily requests if depth='deep'

### Rationale

- **Reliability**: Tavily is specifically designed for AI agent use; returns structured results with source metadata
- **Speed**: Native JSON response format; minimal parsing overhead; 5–10s per query depending on depth
- **Source Quality**: Filters out spam/low-quality sources; includes domain authority signals
- **Cost Clarity**: Per-call pricing model allows explicit budget tracking (Constitution Principle VI)
- **Constitution Alignment**: Determinism (all results traceable to URL) + Retrieval First (primary signal before synthesis)

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Google Custom Search API | Higher cost; requires CSE setup; no JSON-native source ranking |
| Serper / SerpAPI | Good option but less specialized for AI agents; Tavily pricing more favorable for research volume |
| Direct web scraping (crawler) | Violates robots.txt; slow; maintenance overhead; no authority ranking |
| Multi-source aggregation (Tavily + Google + Bing) | Exceeds Phase 1 budget; deferred to Phase 2+ |

### Implementation Notes

- Tavily client: `tavily-python` package
- Max results per call: 5–10 (tunable per depth)
- Fallback error handling: Return `confidence_score=0.0` + empty `contradictions` if Tavily unavailable (fail-fast per Constitution)

---

## 2. Agent Orchestration: LangChain create_agent

### Decision

**Framework**: LangChain 0.1.x (or 0.2.x compatible)  
**Agent Type**: `create_agent()` with Tavily tool and max_iterations=3  
**Stopping Condition**: `early_stopping_method="generate"` (agent decides when to stop)

### Rationale

- **Bounded Autonomy**: `max_iterations=3` enforces hard cap on tool usage (Constitution Principle III)
- **Tool Composition**: Single Tavily tool + LLM synthesis; minimal loop complexity
- **Maturity**: LangChain agents widely tested; extensive community support
- **Constitution Alignment**: Explicit iteration budget + early stopping prevents runaway loops

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Custom state machine (e.g., LangGraph for v2) | Higher complexity; MVP doesn't need state persistence; LangChain sufficient |
| AutoGPT-style loop | Violates Bounded Autonomy; unbounded recursive tool use; difficult to cost-bound |
| Simple if/else (no agent) | Lacks flexibility for dynamic query reformulation; violates design intent |

### Implementation Notes

- Tool definition: Single `TavilySearchTool` with `search(query, depth)` method
- LLM model: OpenRouter API with configurable `base_url` and `model_id` (user-configurable)
- Prompt template: Explicitly instruct agent to cite sources and surface contradictions
- Max tokens: Constrain LLM output length to ~2000 tokens (cost + latency optimization)

---

## 3. Language & Web Framework: Python 3.11 + FastAPI

### Decision

**Language**: Python 3.11+  
**Web Framework**: FastAPI (async, Pydantic validation, OpenAPI docs)  
**ASGI Server**: Uvicorn (production)  
**HTTP Client**: httpx (async-first, type-safe)

### Rationale

- **Async-Native**: FastAPI + httpx support concurrent Tavily calls; reduces per-query latency (SC-001: <2min)
- **Type Safety**: Pydantic enforces schema validation at API boundary (Constitution Principle IV)
- **Observability**: FastAPI middleware simplifies request/response logging (Constitution Principle V)
- **Cost Efficiency**: Python has mature Tavily and OpenRouter libraries; no bridge/FFI overhead
- **Ecosystem**: LangChain is Python-first; extensive testing and ML integration libraries

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Node.js / TypeScript | Good option; LangChain.js less mature than Python LangChain; Tavily integration simpler in Python |
| Go / Rust | Faster execution but excessive complexity for MVP; overkill given Tavily latency dominates |
| Gradio (as primary framework) | Fine for UI but weak for production API; use as optional Phase 4 wrapper |

### Implementation Notes

- Use `uv` for dependency management (per uv-guidelines.instructions.md)
- `pyproject.toml` defines dependencies; `uv.lock` ensures reproducibility
- Uvicorn worker count: 2–4 for single-instance MVP (tune based on load testing)

---

## 4. LLM API: OpenRouter (Configurable Model)

### Decision

**Provider**: OpenRouter: via `langchain-openrouter` package
**Model**: User-configurable (e.g., GLM 4.5 air, GPT-4, Mixtral via API)  
**Base URL**: Configurable via environment variable `OPENROUTER_BASE_URL`  
**Model ID**: Configurable via environment variable `OPENROUTER_MODEL_ID`

### Rationale

- **Flexibility**: OpenRouter supports 100+ models; easy to swap without code change
- **Cost Control**: User can choose cost/latency tradeoff (e.g., Mistral for speed, Claude for quality)
- **Constitution Alignment**: Explicit model selection + token budgeting (Principle VI: Cost + Latency)
- **No Vendor Lock-in**: If OpenRouter goes down, switching to OpenAI / Anthropic requires only env var change

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Direct Anthropic / OpenAI | Less flexibility; higher cost per token; requires separate integrations |
| Open-source LLMs (Ollama, vLLM) | Viable for Phase 2+ but requires self-hosted infra; OpenRouter better for Phase 1 MVP |
| Claude API directly | Good quality but no flexibility; OpenRouter provides same quality with multi-model option |

### Implementation Notes

- LangChain integration: `ChatOpenAI(base_url=openrouter_url, model=model_id)`
- Token limit per request: Constrain to 2000 output tokens (cost control)
- Retry logic: Implement exponential backoff for rate limits (100 req/min typical)

---

## 5. Database: PostgreSQL (Production) + SQLite (Development)

### Decision

**Production**: PostgreSQL 15+ with connection pooling (pgbouncer or sqlalchemy pool)  
**Development**: SQLite (single file, no setup)  
**ORM**: SQLModel (SQLAlchemy 2.0-compatible, Pydantic validation)  
**Persistence Scope**: Phase 4 (not Phase 1) — optional for query history audit trail

### Rationale

- **Type Safety**: SQLModel merges SQLAlchemy ORM + Pydantic; schema validation at DB layer
- **Schema Migrations**: Alembic for schema versioning (long-term maintenance)
- **Constitution Alignment**: Stateless core (Phase 1–3) with optional stateful extensions (Phase 4, Principle VII)
- **Dev/Prod Parity**: SQLite for fast local iteration; PostgreSQL for scale/reliability

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| NoSQL (MongoDB, DynamoDB) | Overkill for Phase 1 MVP with structured schema; document store introduces validation complexity |
| File-based persistence (JSON, CSV) | No concurrent access control; not production-suitable; SQLite handles Phase 1–2 efficiently |
| Direct SQLAlchemy (no Pydantic) | Loses input validation at ORM boundary; Pydantic + SQLModel provides defense-in-depth |

### Implementation Notes

- Phase 1–3: SQLite `:memory:` for testing; file-based for dev (research-agent.db)
- Phase 4: Add `PostgreSQL` as optional extension in `docker-compose.yml`; Alembic migrations included
- Connection pooling: SQLAlchemy `create_engine(..., pool_size=10, max_overflow=20)` for production
- Tables: `research_queries` (audit), `research_results` (cache), `source_records` (de-duplication)

---

## 6. Caching: Redis (Phase 3+, Optional)

### Decision

**Technology**: Redis 7.x  
**Scope**: Phase 3+ (optional; deferred from MVP)  
**Use Cases**: Query result caching, fingerprint-based deduplication  
**Invalidation**: TTL-based (24h default for research results)

### Rationale

- **Speed**: In-memory cache eliminates Tavily API calls for repeated queries
- **Cost Reduction**: Cached results cost \$0 (vs. \$0.01–0.05 per Tavily call)
- **Constitution Alignment**: Optional stateful extension (Principle VII); stateless core unaffected if Redis unavailable
- **Observability**: Redis key patterns enable audit of cache hit/miss rates

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| In-memory cache (Python dict) | Fine for Phase 1–2 but not persistent across server restarts; Redis enables multi-instance setups |
| Memcached | Simpler but less introspection; Redis offers richer data types (sets, sorted sets for dedup) |
| Database-only caching (PostgreSQL) | Works but slower than in-memory; Redis is specialized for cache workloads |

### Implementation Notes

- Phase 1: Skip Redis (use in-memory Cache Manager)
- Phase 3: Add `redis` service to `docker-compose.yml`; implement CacheService wrapper
- Cache key format: `research:{query_fingerprint}:{depth}:{max_sources}:{time_range}`
- Graceful degradation: If Redis unavailable, fall back to Tavily (no 404 error)

---

## 7. Observability & Logging: Structured JSON Logging

### Decision

**Logging Library**: `loguru` (structured, JSON-formatted)  
**Log Levels**: DEBUG, INFO, WARNING, ERROR  
**Sink**: stdout (container logs) + optional file rotation  
**Tracing**: Add correlation IDs to trace requests end-to-end

### Rationale

- **Auditability**: JSON logs enable easy grep/parsing for compliance audits
- **Diagnostics**: Structured fields (user_id, query, sources_retrieved, synthesis_duration) aid debugging
- **Constitution Alignment**: Principle V (Observability); logs cover queries, retrieved documents, outputs
- **Aggregation**: Compatible with ELK, Datadog, CloudWatch for production monitoring

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Python logging (stdlib) | Plain-text logs harder to parse; no built-in JSON support |
| Custom logging | Reinventing the wheel; structlog is production-grade and actively maintained |
| Print statements | No timestamp, no level classification; unusable in production |

### Implementation Notes

- Configure in `app/core/logging.py`; initialize in app startup
- Log queries, retrieved docs (with URLs), synthesis steps, and final output
- Avoid logging sensitive data (API keys, user emails); sanitize before log
- Phase 2: Add Sentry integration for error tracking

---

## 8. Container & Deployment: Docker + docker-compose

### Decision

**Base Image**: `python:3.11-slim` (minimal, faster builds)  
**Build Strategy**: Multi-stage Dockerfile (builder → runtime)  
**Orchestration (Dev)**: docker-compose.yml (FastAPI, PostgreSQL, Redis)  
**Orchestration (Prod)**: Kubernetes or ECS (out of scope for Phase 1)

### Rationale

- **Reproducibility**: Container ensures same environment across dev/staging/prod
- **Dependency Isolation**: No conflicts with system Python; clean dependency snapshot with `uv.lock`
- **Scaling**: docker-compose enables local multi-service setup; Kubernetes deployment straightforward
- **Cost Efficiency**: Multi-stage build reduces image size (security + push speed)

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Serverless (AWS Lambda, Google Cloud Functions) | Cold-start latency exceeds 2min requirement for typical query |
| Virtual machines (EC2) | Higher operational overhead; containers preferred for agility |
| Native development (no Docker) | Works for local dev only; production deployment requires standardization |

### Implementation Notes

- `docker-compose.yml`: 3 services (app, db, redis); healthchecks for all
- Dockerfile uses `.dockerignore` to exclude tests, git history, pycache
- Environment: `.env` file for development (TAVILY_API_KEY, OPENROUTER_BASE_URL, DATABASE_URL, REDIS_URI)
- CI/CD: GitHub Actions for test + lint + build on PR; push image on merge to main

---

## 9. API Design: REST + JSON (AsyncIO)

### Decision

**API Style**: REST (POST /research, GET /health, GET /metrics)  
**Data Format**: JSON (request/response)  
**Async**: All endpoints `async def` (FastAPI default)  
**Validation**: Pydantic models at boundary

### Rationale

- **Simplicity**: REST is standard; no GraphQL complexity for Phase 1
- **Async**: Enables concurrent Tavily calls within single request (latency reduction)
- **Validation**: Pydantic catches invalid input before processing (security + UX)
- **Constitution Alignment**: Structured outputs (Principle IV); explicit request/response schemas

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| GraphQL | Overkill for 3 endpoints; higher complexity and latency for single query |
| gRPC | Excellent for service-to-service but overkill for public-facing research API; REST standard for flexibility |
| WebSocket | Not needed; requests are stateless and short-lived |

### Implementation Notes

- Endpoints: `POST /research` (query submission), `GET /health` (status), `GET /metrics` (operational signals)
- Request validation: Pydantic `ResearchRequest(query, depth, max_sources, time_range)`
- Response schema: Pydantic `ResearchBrief(summary, key_points, sources, contradictions, confidence_score)`
- No authentication in Phase 1 (can add API keys in Phase 2)

---

## 10. Testing Strategy

### Decision

**Framework**: pytest (with pytest-asyncio for async tests)  
**Mocking**: `unittest.mock` + `pytest-mock` for external APIs  
**Coverage Target**: >80% (focus on service logic, LangChain integration, route validation)  
**Test Categories**: Unit (services, models), Integration (Tavily mocked + DB), API (FastAPI TestClient)

### Rationale

- **Determinism**: Mock Tavily results ensure tests are reproducible and fast
- **Budget**: No expensive external API calls in CI
- **Constitution Alignment**: Tests verify schema conformance, source traceability, contradiction surfacing

### Alternatives Considered & Rejected

| Alternative | Why Rejected |
|------------|------------|
| Only integration tests | Slower feedback; harder to isolate bugs; CI cost higher |
| Only API tests | Misses service logic errors; doesn't validate models in isolation |
| No mocking (live Tavily calls) | Slow (5–10s per test), expensive, flaky (internet dependency) |

### Implementation Notes

- `tests/fixtures/sample_queries.json`: Representative test cases with expected outputs
- `tests/conftest.py`: Mock Tavily client, test SQLite DB, fixture factory
- CI: GitHub Actions runs full test suite on each PR (target: <2 min)
- Coverage report: HTML + terminal summary

---

## 11. Risk Mitigation Summary

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Tavily API unavailable | Fail-fast with `confidence_score=0.0`; no hallucination fallback | Implementation (Phase 1) |
| Agent over-iteration | Hard cap `max_iterations=3`; Constitution review gate | Design (Constitution) |
| Synthesis hallucination | Require source citations; reject outputs without attribution | LLM prompt engineering (Phase 2) |
| Latency explosion (>2min) | Parallelize Tavily calls; tune search depth; implement caching (Phase 3) | Implementation + testing (Phase 1–3) |
| Weak source quality | Leverage Tavily's built-in domain authority ranking; consider reranking (Phase 2, if needed) | Implementation (Phase 1) |

---

## 12. Phase Breakdown (4-Phase Plan)

| Phase | Focus | SLOC | Duration | Blockers |
|-------|-------|------|----------|----------|
| **Phase 1 (MVP)** | Core API + LangChain agent + Tavily retrieval + structured output | ~800 | 2–3 weeks | None (design complete) |
| **Phase 2 (Reliability)** | Deduplication, source ranking, confidence scoring, logging, error handling | ~400 | 1–2 weeks | Phase 1 complete |
| **Phase 3 (Performance)** | Redis caching, query fingerprinting, token optimization, load testing | ~300 | 1 week | Phase 2 complete |
| **Phase 4 (Persistence)** | PostgreSQL setup, query history, result archival, Gradio UI (optional) | ~400 | 1–2 weeks | Phase 3 complete (optional) |

---

## Conclusion

All technology decisions align with the Langraph-research-agent Constitution v1.0.0. The stack is production-viable, type-safe, cost-controlled, and observable. MVP (Phase 1) can be delivered in 2–3 weeks with 4-person team.

---

**Approved By**: Speckit Agent (speckit.plan)  
**Date**: 2026-03-26  
**Next Action**: Generate data-model.md, contracts/, and quickstart.md (Phase 1 design outputs)
