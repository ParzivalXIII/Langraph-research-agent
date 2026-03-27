# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

A bounded research agent that accepts user queries, retrieves evidence via Tavily, synthesizes findings into a structured research brief (with source traceability and contradiction surfacing), and exposes operational health endpoints. Integrates with LangChain for agent orchestration, Tavily for web retrieval, and FastAPI for HTTP routing. Implements Constitution principles: determinism over creativity, retrieval-first discipline, bounded tool usage (max 3 iterations), structured JSON outputs, comprehensive observability, explicit cost/latency budgets, and optional stateful extensions (Redis caching, PostgreSQL persistence).

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, LangChain, Tavily API client(Doc: <https://docs.tavily.com/sdk/python/quick-start>), OpenRouter API client, Pydantic, SQLModel (optional: SQLAlchemy for ORM), Redis (optional)  
**Storage**: PostgreSQL (production), SQLite (development)  
**Testing**: pytest with async support (pytest-asyncio), TestClient for FastAPI endpoints  
**Target Platform**: Linux server / containerized (Docker)  
**Project Type**: Web service / REST API backend with stateless core  
**Performance Goals**: SC-001 requires 2-minute latency for typical queries; breadth-first retrieval strategy (Tavily search depth tuned to balance speed vs. evidence quality)  
**Constraints**: SC-001 / <2min per query; SC-004 ≥3 credible sources when available; Cost constraint: Tavily call budget capped at 5-10 calls per request (Bounded Autonomy principle); Token budget managed per request  
**Scale/Scope**: MVP assumes <100 concurrent users; single-instance FastAPI server with optional Redis for caching and optional PostgreSQL for history/audit trail

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Verification Status**: ✅ PASS (Phase 0 Pre-Research)

- ✅ **Determinism**: Every output includes source references (spec FR-001, output schema includes `sources` array with title/URL/relevance); synthesis follows retrieval-first; LLM does not fill gaps
- ✅ **Retrieval First**: Tavily is primary retrieval signal (spec Evidence & Retrieval Plan); synthesis only after evidence gathered; output schema includes source provenance
- ✅ **Bounded Autonomy**: Max iterations capped at 3 (LangChain `max_iterations=3`, `early_stopping_method="generate"`); explicit termination conditions in spec FR-003 (source agreement, source count, budget limits)
- ✅ **Structured Outputs**: JSON schema defined in spec (summary, key_points, sources[], contradictions[], confidence_score); Pydantic validation planned
- ✅ **Observability**: Spec FR-007 requires operational health/metrics; Phase 2 (Reliability) will add structured logging of queries, retrieved documents, and outputs (per Operational Constraints section 4)
- ✅ **Cost + Latency**: SC-001 defines <2min latency constraint; Tavily call budget implicit in max_iterations=3 (max 5-10 calls per request); token budget to be documented in Phase 1
- ✅ **Stateless Core**: Core research flow remains stateless (query → retrieval → synthesis → output); Redis caching and PostgreSQL persistence scoped as optional Phase 4 extensions

**Gate Result**: Feature spec satisfies all Constitution principle requirements. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

## Project Structure

### Documentation (this feature)

```text
specs/001-research-agent/
├── spec.md              # User-facing specification (Requirement source)
├── plan.md              # This file (Technical planning)
├── research.md          # Phase 0 output (Technology decisions, rationales)
├── data-model.md        # Phase 1 output (SQLModel schemas, Pydantic, entity relationships)
├── quickstart.md        # Phase 1 output (Integration guide, usage examples)
├── contracts/           # Phase 1 output (API request/response schemas)
│   ├── research_request.schema.json
│   ├── research_brief.schema.json
│   └── health_metrics.schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
research-agent/
│
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                    # FastAPI endpoints (/research, /health, /metrics)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings (Tavily API key, OpenRouter BASE URL & API Key, Redis config)
│   │   ├── logging.py                   # Structured logging setup (Loguru)
│   │   └── security.py                  # Auth/rate limiting (if applicable)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   └── research_agent.py            # LangChain agent with Tavily tool, max_iterations=3
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── tavily_tool.py               # Tavily search wrapper with result ranking
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── retrieval.py                 # Tavily query logic, deduplication
│   │   ├── processing.py                # Result ranking, filtering, conflict detection
│   │   ├── synthesis.py                 # LLM synthesis → structured brief
│   │   └── health.py                    # Health and metrics reporting
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── research.py                  # Pydantic models (ResearchQuery, ResearchBrief, SourceRecord, etc.)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                    # SQLModel tables (optional: Query history, results cache)
│   │   └── session.py                   # Database session management
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── redis.py                     # Redis client wrapper (optional, Phase 3)
│   │
│   └── main.py                          # FastAPI app initialization
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_agents.py               # Agent logic with mocked Tavily
│   │   ├── test_services.py             # Service layer (retrieval, synthesis, processing)
│   │   └── test_schemas.py              # Pydantic model validation
│   │
│   ├── integration/
│   │   ├── test_db.py                   # Database integration (if persistence enabled)
│   │   ├── test_redis.py                # Cache integration (if caching enabled)
│   │   └── test_end_to_end.py           # Full pipeline with mocked Tavily
│   │
│   ├── api/
│   │   ├── test_routes.py               # FastAPI endpoints (TestClient)
│   │   └── test_auth.py                 # Rate limiting, input validation
│   │
│   ├── conftest.py                      # pytest fixtures (mock Tavily, test DB, Redis)
│   └── fixtures/
│       └── sample_queries.json           # Representative test queries and expected outputs
│
├── docker/
│   ├── Dockerfile                       # Multi-stage build (builder + runtime)
│   └── docker-compose.yml               # Services: app, PostgreSQL, Redis, (optional Gradio)
│
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions: test, lint, coverage
│
├── pyproject.toml                       # Dependency declaration (FastAPI, LangChain, Tavily, etc.)
├── uv.lock                              # Locked dependency versions (for reproducibility)
├── .env.example                         # Example config (TAVILY_API_KEY, OPENROUTER_BASE_URL, REDIS_URL, DATABASE_URL)
├── README.md                            # Project overview, setup, usage
├── LICENSE                              # Apache 2.0 or equivalent
└── .gitignore
```

**Structure Decision**: Option 1 (Single project) selected for MVP; vertical layering (API → Services → Tools → DB); optional horizontal components (Cache, Persistence) for Phase 3–4.

## Complexity Tracking

> No Constitution Check violations detected. This table documents intentional feature additions that exceed the MVP baseline.

| Architectural Addition | Rationale | Deferred Until |
|------------------------|-----------|----------------|
| PostgreSQL persistence | Query history, audit trail, result reuse (Phase 4) | Post-MVP; SQLite sufficient for dev |
| Redis caching | Query deduplication, faster repeated searches (Phase 3) | Post-MVP; in-memory cache sufficient for Phase 1 |
| Gradio UI | Optional web interface for manual queries (Phase 4) | Post-MVP; FastAPI OpenAPI docs sufficient for Phase 1 |
| Embedding-based reranking | Higher quality source selection (v2.0) | Post-Phase 1; Tavily ranking sufficient for MVP |

## Next Steps

**Phase 0 Research Output** → `research.md` (decision rationale, technology justification)  
**Phase 1 Design Output** → `data-model.md`, `contracts/`, `quickstart.md` (entity schemas, API contracts, integration guide)  
**Phase 1 Sync** → Update agent context files with tech stack and project metadata  
**Phase 2 Tasks** → Run `/speckit.tasks` to generate implementation task breakdown  
**Implementation** → Run `/speckit.implement` to execute Phase 1 (Setup), Phase 2 (Foundational), Phase 3+ (User Stories)
