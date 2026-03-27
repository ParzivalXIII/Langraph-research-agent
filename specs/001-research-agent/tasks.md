# Implementation Tasks: Research Agent

**Feature**: Research Agent (001-research-agent)  
**Branch**: `001-research-agent`  
**Created**: 2026-03-26  
**Specification**: [specs/001-research-agent/spec.md](./spec.md)  
**Implementation Plan**: [specs/001-research-agent/plan.md](./plan.md)  
**Data Model**: [specs/001-research-agent/data-model.md](./data-model.md)

---

## Overview

This document defines all implementation tasks organized into phases: Setup, Foundational, User Stories (P1–P3), and Polish. Each task follows the strict checklist format with task ID, parallelization marker (if applicable), story label (if applicable), and clear file paths.

**Task Checklist Format**: `- [ ] [ID] [P?] [Story?] Description with file path`

**Total Tasks**: 39 (distributed across 5 phases)  
**Setup**: 7 tasks | **Foundational**: 8 tasks | **US1 (P1)**: 11 tasks (includes T020a error handling) | **US2 (P2)**: 7 tasks | **US3 (P3)**: 3 tasks | **Polish**: 3 tasks

---

## Phase 1: Project Setup & Infrastructure

*Duration: 1–2 days | Blockers: None | Dependency: None*

### Checkpoints

- [ ] Project directory structure created
- [ ] Dependencies installed and locked
- [ ] Development environment validated (uv sync successful)
- [ ] Docker compose configured for local dev

---

### Tasks

- [ ] T001 Create project structure per plan.md layout in [/home/parzival/projects/Langraph-research-agent](/)
- [ ] T002 [P] Initialize pyproject.toml with dependencies: fastapi, uvicorn, langchain, tavily-python, openai, pydantic, sqlmodel, pytest, pytest-asyncio, structlog in [pyproject.toml](./pyproject.toml)
- [ ] T003 [P] Create `.env.example` with template keys (TAVILY_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL_ID, DATABASE_URL, REDIS_URL, LOG_LEVEL) in [.env.example](./.env.example)
- [ ] T004 Run `uv sync --dev` to lock dependencies and create virtual environment in [uv.lock](./uv.lock)
- [ ] T005 [P] Create Dockerfile (multi-stage build: builder → runtime) per research.md §8 in [docker/Dockerfile](./docker/Dockerfile)
- [ ] T006 [P] Create docker-compose.yml with app, PostgreSQL, Redis services (optional for Phase 1) in [docker-compose.yml](./docker-compose.yml)
- [ ] T007 [P] Create .gitignore and .dockerignore with standard Python exclusions in [.gitignore](./.gitignore)

---

## Phase 2: Foundational Components (Blocking Prerequisites)

*Duration: 2–3 days | Blockers: Phase 1 | Dependency: All US1–US3 depend on these*

### Checkpoints

- [ ] Core configuration framework operational
- [ ] Structured logging initialized
- [ ] Pydantic schemas validated against test data
- [ ] Mock Tavily client ready for unit tests

---

### Tasks

- [ ] T008 [P] Create app/core/config.py with Settings class (Tavily key, OpenRouter URL/model, Redis URI, DB URL, log level) in [app/core/config.py](./app/core/config.py)
- [ ] T009 [P] Create app/core/logging.py with structlog configuration (JSON format, structured fields: query, sources_retrieved, synthesis_duration) in [app/core/logging.py](./app/core/logging.py)
- [ ] T010 [P] Create app/schemas/research.py with Pydantic models: ResearchQuery, ResearchBrief, SourceRecord, ConfidenceAssessment from data-model.md in [app/schemas/research.py](./app/schemas/research.py)
- [ ] T011 [P] Create app/main.py FastAPI app initialization with startup/shutdown events and middleware for logging in [app/main.py](./app/main.py)
- [ ] T012 [P] Create tests/conftest.py with pytest fixtures: mock Tavily client, test DB, sample queries, Pydantic validators in [tests/conftest.py](./tests/conftest.py)
- [ ] T013 [P] Create tests/fixtures/sample_queries.json with 5+ representative test queries covering: (1) broad topic ("recent AI breakthroughs"), (2) factual/date-based ("recent elections results"), (3) sparse evidence (niche topic), (4) contradictory claims (political topic), (5) time-filtered ("tech news last 30 days"). Each entry: {query, depth, expected_source_count_min, expected_contradictions_count, description, sla_seconds} to match SLA tiers from data-model.md §Latency SLA in [tests/fixtures/sample_queries.json](./tests/fixtures/sample_queries.json)
- [x] T014 [P] Create tests/unit/test_schemas.py with Pydantic model validation tests (valid/invalid inputs, boundaries, enums) in [tests/unit/test_schemas.py](./tests/unit/test_schemas.py)
- [x] T015 [P] Create tests/api/conftest.py with TestClient fixture and mock auth/dependencies in [tests/api/conftest.py](./tests/api/conftest.py)

---

## Phase 3: User Story 1 (P1) — Get a Research Brief

**Requirement**: FR-001, FR-002, FR-003, FR-004, FR-005 | **Entities**: ResearchQuery, ResearchBrief, SourceRecord, ContradictionRecord | **Success Criteria**: SC-002, SC-003, SC-004

**Independent Test**: Submit a representative query and confirm a complete brief with all required fields (summary, key_points, sources, contradictions, confidence_score) is returned.

**Acceptance Criteria**:

1. Given a valid query, when submitted, then response includes all required fields
2. Given sources with conflicting claims, when processed, then contradictions surface in response

*Duration: 4–5 days | Blockers: Phase 1, Phase 2 | Parallel: US1 and US2 have partial independence (separate service/config code)*

---

### Checkpoints

- [ ] Tavily search integration operational
- [ ] LangChain agent with max_iterations=3 initialized
- [ ] Contradiction detection algorithm implemented
- [ ] Confidence scoring formula operational
- [ ] Research brief endpoint (POST /research) returns complete, valid responses
- [ ] Unit tests for agent, services, and route handlers >80% coverage
- [ ] Integration test: end-to-end query → brief with contradiction detection

---

### Tasks

- [ ] T016 [US1] Create app/tools/tavily_tool.py with TavilySearchTool class wrapping Tavily client (search method, Tavily parameter mapping per data-model.md §Tavily Search Parameter Mapping, error handling with retry logic for transients per T020a, max_results tuned to depth: basic→5, intermediate→10, deep→15) in [app/tools/tavily_tool.py](./app/tools/tavily_tool.py)
- [ ] T017 [P] [US1] Create app/services/retrieval.py with retrieval logic: Tavily queries per depth mapping (data-model.md), result scoring by credibility (domain_authority=0.50, recency_boost=0.30, citation_count=0.20), deduplication on URL, filtering sources with credibility_score ≥0.65 for SC-004 compliance in [app/services/retrieval.py](./app/services/retrieval.py)
- [ ] T018 [P] [US1] Create app/services/processing.py with contradiction detection: find conflicting claims between sources, assign severity per data-model.md §Contradiction Detection (minor=1–2 sources disagree -0.05, moderate=3–4 disagree -0.10, major=>50% disagree -0.20), integrate severity into confidence_score calculation in [app/services/processing.py](./app/services/processing.py)
- [ ] T019 [P] [US1] Create app/services/synthesis.py with LLM synthesis: take retrieved sources → synthesize summary, key_points, confidence_score using deterministic formula from data-model.md §Confidence Scoring Algorithm (weights: agreement=0.40, quality=0.30, recency=0.20, freshness=0.10, minus contradiction_penalty), error handling for LLM timeouts (T020a), and structured logging of synthesis duration in [app/services/synthesis.py](./app/services/synthesis.py)
- [ ] T020 [US1] Create app/agents/research_agent.py with LangChain create_agent: Tavily tool, max_iterations=3, early_stopping_method="generate", prompt engineering for source citation in [app/agents/research_agent.py](./app/agents/research_agent.py)
- [ ] T020a [P] [US1] Create error handling layer in app/core/errors.py with custom exceptions (TavilyAPIError, SynthesisError, InvalidInputError) and recovery strategies (retry logic with exponential backoff for Tavily transients, graceful fallback response if LLM synthesis fails) in [app/core/errors.py](./app/core/errors.py)
- [ ] T021 [P] [US1] Implement POST /research endpoint in app/api/routes.py with request validation, agent call wrapped in error handling (per app/core/errors.py), response serialization per contracts/research_brief.schema.json, and HTTP error responses (502/503 for retrieval/synthesis failures) in [app/api/routes.py](./app/api/routes.py)
- [ ] T022 [P] [US1] Create tests/unit/test_services.py with unit tests for retrieval, processing, synthesis services (mocked Tavily, LLM responses) in [tests/unit/test_services.py](./tests/unit/test_services.py)
- [ ] T023 [P] [US1] Create tests/unit/test_agents.py with unit tests for research agent logic (max iterations, tool calls, stopping conditions) in [tests/unit/test_agents.py](./tests/unit/test_agents.py)
- [ ] T024 [US1] Create tests/api/test_research_endpoint.py with API tests: valid query → 200 with brief containing all required fields, contradictions surfaced at 100% (per SC-003), invalid query → 400, Tavily API errors → 502 with error_details (T020a), LLM synthesis failure → 503 with fallback brief (confidence=0.0), edge cases (empty query, extremely broad query, sparse results) all handled in [tests/api/test_research_endpoint.py](./tests/api/test_research_endpoint.py)
- [ ] T025 [US1] Create tests/integration/test_end_to_end_research.py with end-to-end test: full query pipeline with mocked Tavily and LLM, verify brief completeness in [tests/integration/test_end_to_end_research.py](./tests/integration/test_end_to_end_research.py)

---

## Phase 4: User Story 2 (P2) — Control Research Depth

**Requirement**: FR-001, FR-006 | **Entities**: ResearchQuery (depth, max_sources, time_range parameters) | **Success Criteria**: SC-001 (2min latency), SC-004 (≥3 sources)

**Independent Test**: Submit same query with different depth, max_sources, and time_range values and confirm results vary accordingly (basic → fewer/faster, deep → more/thorough).

**Acceptance Criteria**:

1. Given a basic request, when depth is increased, then response includes broader coverage
2. Given a low source cap, when submitted, then response respects the limit

*Duration: 2–3 days | Blockers: Phase 1, Phase 2, T016–T021 from US1 | Parallel: Can start after T016 (Tavily tool)*

---

### Checkpoints

- [ ] Depth parameter affects Tavily search strategy (basic=5 results, intermediate=10, deep=15+)
- [ ] max_sources parameter honored in response (never exceeds user-specified limit)
- [ ] time_range parameter applied to Tavily queries
- [ ] Latency monitoring in service logs (track per-request duration)
- [ ] Integration tests: depth variations produce different result counts

---

### Tasks

- [x] T026 [P] [US2] Enhance app/services/retrieval.py to map depth → Tavily search_depth parameter (basic/intermediate/deep) in [app/services/retrieval.py](./app/services/retrieval.py)
- [x] T027 [P] [US2] Enhance app/services/retrieval.py to apply time_range filter to Tavily queries (convert enum to days: day→0, week→7, month→30, year→365, all→None) in [app/services/retrieval.py](./app/services/retrieval.py)
- [x] T028 [P] [US2] Enhance app/services/synthesis.py to cap key_points and sources in output to match max_sources constraint in [app/services/synthesis.py](./app/services/synthesis.py)
- [x] T029 [US2] Add latency tracking to app/services/synthesis.py and propagate to logging: track retrieval_latency_ms, synthesis_latency_ms, total_latency_ms, sources_retrieved_count, contradictions_found_count; log to structured logger per app/core/logging.py; ensure latency targets (basic=<30s, intermediate=<60s, deep=<120s per data-model.md) are met in [app/services/synthesis.py](./app/services/synthesis.py)
- [x] T030 [P] [US2] Create tests/unit/test_depth_control.py with unit tests: depth parameter maps to correct Tavily params per data-model.md (basic→search_depth=3/max_results=5, intermediate→5/10, deep→10/15+), time_range parameter correctly filters by days (day→0, week→7, month→30, year→365) in [tests/unit/test_depth_control.py](./tests/unit/test_depth_control.py)
- [x] T031 [P] [US2] Create tests/api/test_depth_variations.py with API tests: same query with depth=basic/intermediate/deep → different response field counts, latency within SLA (basic <30s, intermediate <60s, deep <120s) per data-model.md, sources count respects max_sources parameter, time_range filters applied correctly in [tests/api/test_depth_variations.py](./tests/api/test_depth_variations.py)
- [x] T032 [US2] Create tests/integration/test_time_range_filter.py with integration tests: time_range parameter honored, recent sources preferred when specified in [tests/integration/test_time_range_filter.py](./tests/integration/test_time_range_filter.py)

---

## Phase 5: User Story 3 (P3) — Monitor Service Health

**Requirement**: FR-007 | **Entities**: Health status, metrics (uptime, requests, latency, Tavily calls, cache hit rate, memory) | **Success Criteria**: SC-005

**Independent Test**: Open health/metrics endpoints without starting a research request; confirm service status reported clearly.

**Acceptance Criteria**:

1. Given the service is running, when health endpoint is called, then status is reported clearly
2. Given the service is under load, when metrics endpoint is called, then operational signals available

*Duration: 1 day | Blockers: Phase 1, Phase 2 | Parallel: Can begin immediately after Phase 2 (no dependency on US1 or US2)*

---

### Checkpoints

- [ ] GET /health endpoint returns HTTP 200 (healthy) or 503 (unhealthy) with service status
- [ ] GET /metrics endpoint returns operational metrics (uptime, requests, latency, Tavily calls)
- [ ] Health checks for API, Tavily, database, cache (if enabled) all working
- [ ] Metrics updated in real-time as requests are processed
- [ ] Unit tests for health and metrics logic

---

### Tasks

- [x] T033 [P] [US3] Create app/services/health.py with HealthCheckService: check API, Tavily, database, cache connectivity in [app/services/health.py](./app/services/health.py)
- [x] T034 [P] [US3] Create app/services/metrics.py with MetricsService: track uptime, request counts, average latency, Tavily calls, cache hit rate, memory usage in [app/services/metrics.py](./app/services/metrics.py)
- [x] T035 [US3] Implement GET /health and GET /metrics endpoints in app/api/routes.py per contracts/health_metrics.schema.json, HTTP status codes (200 healthy / 503 unhealthy) in [app/api/routes.py](./app/api/routes.py)

---

## Phase 6: Polish & Cross-Cutting Concerns

*Duration: 1–2 days | Blockers: All user stories complete | For: Production readiness*

### Checkpoints

- [ ] All tests passing (>80% coverage on core services)
- [ ] Code linting (black, ruff) compliant
- [ ] Type checking (mypy) clean
- [ ] Error handling and input validation comprehensive
- [ ] Observability (query logging, error tracking)
- [ ] Documentation complete (README, API docs)

---

### Tasks

- [x] T036 [P] Run type checker (pyright) and fix type errors across all .py files in [app/](./app/), [tests/](./tests/) - ✅ 0 errors, 0 warnings
- [x] T037 [P] Format code with `uv run black app/ tests/` and lint with `uv run ruff check app/ tests/` in [app/](./app/), [tests/](./tests/) - ✅ All passing
- [x] T038 Create README.md with setup instructions, usage examples, API docs link per quickstart.md in [README.md](./README.md) - ✅ 809 lines comprehensive

---

## Task Dependency Graph

```
Phase 1 (Setup)
  ├── T001–T007 (Project structure, Dockerfile, .env)
  │
  └─→ Phase 2 (Foundational)
      ├── T008–T015 (Config, logging, schemas, fixtures)
      │
      ├─→ Phase 3 (US1 — P1)
      │   ├── T016–T025, T020a (Tavily tool, agent, synthesis, error handling, endpoints, tests)
      │   │
      │   └─→ Phase 4 (US2 — P2) [Parallel Start: After T016 available]
      │       ├── T026–T032 (Depth control, latency tracking, tests)
      │       │
      │       └─→ Phase 6 (Polish)
      │           └── T036–T038 (Linting, typing, docs)
      │
      └─→ Phase 5 (US3 — P3) [Parallel Start: Immediate after Phase 2]
          ├── T033–T035 (Health checks, metrics, endpoints)
          │
          └─→ Phase 6 (Polish) [Converges with US1/US2]
              └── T036–T038
```

**Note**: T020a (error handling) blocks finalization of T016, T019, T021, T024 but can be developed in parallel with agent logic.

---

## Parallelization Strategy

### Batch 1 (Immediate, Phase 1)

Tasks **T001–T007** (Project setup) — sequential, ~1 day

### Batch 2 (After Batch 1, Phase 2)

Tasks **T008–T015** (Foundational) — can run in parallel, ~2–3 days

- T008, T009: Config & logging (independent) ✓ Parallel
- T010: Schemas (independent) ✓ Parallel
- T011: Main app (independent) ✓ Parallel
- T012–T015: Tests & fixtures (independent) ✓ Parallel

### Batch 3 (After Batch 2)

**US1 (P1)**: Tasks **T016–T025** (Tavily tool, agent, synthesis, endpoints, tests)
**US3 (P3)**: Tasks **T033–T035** (Health/metrics) — **INDEPENDENT, run in parallel** ✓
**US2 (P2)**: Tasks **T026–T032** (Depth control) — **Start after T016 available** (not fully independent; builds on Tavily tool)

Recommendation:

- After Phase 2 complete, start **US1** and **US3** in parallel (8 person-days vs. sequential 15)
- Start **US2** once **T016** is complete (not blocked on full US1)
- Convergence point: Phase 6 (Polish) after all user stories done

### Time Estimate

| Phase | Tasks | Duration | Parallelizable | Notes |
|-------|-------|----------|-----------------|-------|
| 1 (Setup) | T001–T007 | 1–2 days | Partial | Docker & pyproject can build in parallel |
| 2 (Foundational) | T008–T015 | 2–3 days | 70% | Config, logging, schemas, tests independent |
| 3 (US1 + US3) | T016–T035 | 5–6 days | 60% | US1 and US3 can run in parallel; US2 waits for T016 |
| 4 (US2 finish) | T026–T032 | 2–3 days | 80% | Depth control refinements; can overlap with final US1 integration |
| 5 (Polish) | T036–T038 | 1 day | 80% | Code quality, type checking, docs |
| **Total** | **38** | **10–15 days** (single dev) | — | **5–8 days** (2-person team with parallelization) |

---

## User Story Completion Criteria & Checkpoints

### US1 (P1) — Get a Research Brief

**Independent Test Criteria**:

- [ ] T016: Tavily tool retrieves results without error
- [ ] T022: Retrieval service deduplicates sources by URL
- [ ] T018: Contradiction detection identifies 2+ sources with conflicting claims
- [ ] T023: LangChain agent respects max_iterations=3
- [ ] T024: POST /research returns 200 with ResearchBrief containing summary, key_points, sources, contradictions, confidence_score
- [ ] T025: Integration test: end-to-end query → brief with contradictions surfaced

**Acceptance Gates**:

- All sources cited with URL and title
- Contradictions surfaced when sources disagree (SC-003: 100% detection)
- Confidence score reflects evidence (0.0–1.0)
- Response includes ≥1 source (SC-004: 80% include ≥3 when available)

---

### US2 (P2) — Control Research Depth

**Independent Test Criteria**:

- [ ] T026: depth parameter → correct Tavily search_depth value
- [ ] T027: time_range parameter → correct time filter
- [ ] T029: Latency tracking logs request duration
- [ ] T030: Unit tests verify depth mappings
- [ ] T031: API tests confirm result counts vary with depth (basic < intermediate < deep)
- [ ] T032: Integration test: time_range filters sources correctly

**Acceptance Gates**:

- Latency <2 min for typical query (SC-001, especially basic depth)
- max_sources parameter honored in response
- Different depth values produce different coverage breadth
- Response latency tracked and logged per request

---

### US3 (P3) — Monitor Service Health

**Independent Test Criteria**:

- [ ] T033: HealthCheckService checks API, Tavily, DB, cache
- [ ] T034: MetricsService tracks uptime, requests, latency, Tavily calls, cache hit rate
- [ ] T035: GET /health returns 200 (healthy) / 503 (unhealthy); GET /metrics returns metrics JSON

**Acceptance Gates**:

- Health check succeeds without triggering research request (SC-005)
- Metrics available even under load
- Service status reported clearly (healthy / degraded / unhealthy)

---

## Coverage & Quality Gates

**Minimum Test Coverage**: >80% on core modules

- `app/services/` (retrieval, processing, synthesis, health, metrics): >85%
- `app/agents/` (research_agent): >80%
- `app/api/` (routes): >75%
- `app/tools/` (tavily_tool): >75%

**Code Quality**:

- [ ] Format: `black` compliant (T037)
- [ ] Lint: `ruff` clean (T037)
- [ ] Types: `mypy` strict mode (T036)
- [ ] Docstrings: All public functions and classes documented

**Runtime Validation**:

- [ ] Pydantic schemas validate all inputs (T014)
- [ ] Error responses follow contracts/research_brief.schema.json format
- [ ] Structured logging captures queries, source counts, synthesis duration (T009)

---

## Reference Files

**Specification**: [spec.md](./spec.md)  
**Implementation Plan**: [plan.md](./plan.md)  
**Data Model**: [data-model.md](./data-model.md)  
**API Contracts**: [contracts/](./contracts/)  
**Quickstart**: [quickstart.md](./quickstart.md)  
**Technology Research**: [research.md](./research.md)

---

**Total Estimated Effort**: 10–15 person-days (single developer) | 5–8 person-days (2-person team with parallelization)  
**MVP Target**: Phase 3 + Phase 2 Foundational complete (core research brief capability)  
**Phase Dependency Order**: Setup → Foundational → {US1, US3 in parallel} → US2 → Polish
