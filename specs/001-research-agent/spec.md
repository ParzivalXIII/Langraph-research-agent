# Feature Specification: Research Agent

**Feature Branch**: `001-research-agent`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "CORE OBJECTIVE

A research agent that:

- Accepts a query
- Performs web retrieval via Tavily
- Synthesizes results into a structured research brief
- Surfaces confidence + contradictions

FUNCTIONAL REQUIREMENTS

Input:

```json
{
  "query": "string",
  "depth": "basic | intermediate | deep",
  "max_sources": int,
  "time_range": "day | week | month | year | all"
}
```

Output:

```json
{
  "summary": "string",
  "key_points": ["..."],
  "sources": [
    {"title": "...", "url": "...", "relevance": float}
    ],
  "contradictions": ["..."],
  "confidence_score": float
}
```

## Evidence & Retrieval Plan *(mandatory for research-driven features)*

- **Primary sources** (MVP, Phase 1–2): Tavily search results with built-in snippet extraction. **Full-text page fetching deferred to Phase 4** (post-MVP).
  - *Rationale*: Tavily's snippet extraction is sufficient for initial synthesis; full-page HTML fetching adds latency and external dependency not required for MVP scope.
- **Fallback behavior**: If the available evidence is sparse, conflicting, or low confidence, return a lower-confidence brief that explicitly surfaces the gaps and contradictions rather than inventing a conclusion.
- Output schema: A structured research brief containing `summary`, `key_points`, `sources`, `contradictions`, and `confidence_score`.
- Traceability: Each response must preserve the originating query, the selected sources, and the rationale used to rank or include them so the brief can be reviewed later.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a Research Brief (Priority: P1)

As a user, I can submit a research query and receive a concise, structured brief that summarizes the findings, lists supporting sources, and highlights contradictions.

**Why this priority**: This is the primary value of the feature and the minimum viable user journey.

**Independent Test**: Submit a representative query and confirm that a complete brief is returned with all required fields.

**Acceptance Scenarios**:

1. **Given** a valid query, **When** the request is submitted, **Then** the response includes a summary, key points, sources, contradictions, and a confidence score.
2. **Given** sources with conflicting claims, **When** the request is processed, **Then** the response surfaces the conflict instead of hiding it.

---

### User Story 2 - Control Research Depth (Priority: P2)

As a user, I can choose how deep the research should go and limit the number of sources and recency window so the brief matches my time and thoroughness needs.

**Why this priority**: Users need control over speed versus breadth, especially for quick checks versus deeper investigations.

**Independent Test**: Submit the same query with different depth, source, and time settings and confirm the results change accordingly.

**Acceptance Scenarios**:

1. **Given** a basic request, **When** the user selects a deeper search mode, **Then** the response includes broader coverage than the basic mode.
2. **Given** a query with a low source cap, **When** the request is submitted, **Then** the response respects the source limit.

---

### User Story 3 - Monitor Service Health (Priority: P3)

As an operator, I can check service health and operational metrics so I can tell whether the research service is available and behaving normally.

**Why this priority**: Reliable operation matters, but it supports rather than defines the user-facing research experience.

**Independent Test**: Open the health and metrics views and confirm they report service status without requiring a research request.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** the health view is checked, **Then** the service status is reported clearly.
2. **Given** the service is under load, **When** the metrics view is checked, **Then** operational signals are available for review.

### Edge Cases

- Very broad queries return too many potential sources and must still produce a bounded, readable brief.
- Sparse or recent-only queries may produce limited evidence and should lower confidence accordingly.
- Conflicting source claims must be surfaced explicitly rather than merged into a misleading summary.
- Requests with invalid input values must be rejected with clear feedback.
- If live retrieval is unavailable, the response should fail gracefully instead of returning fabricated results.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a research request containing a query, depth, maximum source count, and time range.
- **FR-002**: The system MUST return a structured research brief containing a summary, key points, sources, contradictions, and a confidence score.
- **FR-003**: The system MUST gather enough supporting evidence to justify the brief, and it MUST stop when source agreement, source count, or budget limits are reached.
- **FR-004**: The system MUST surface contradictory findings when sources disagree.
- **FR-005**: The system MUST assign a confidence score that reflects source agreement, source quality, recency, and contradiction pressure.
- **FR-006**: The system MUST respect the user’s requested depth, source cap, and time range when preparing the brief.
- **FR-007**: The system MUST expose operational health and metrics views so service availability can be checked independently of a research request.
- **FR-008**: The system SHOULD retain past queries and results when persistence is enabled so repeated research can be reviewed or reused.
- **FR-009**: The system SHOULD reuse previous retrieval results when caching is enabled so repeated queries return faster.

### Key Entities *(include if feature involves data)*

- **Research Query**: The request submitted by the user, including the query text, depth, maximum source count, and time range.
- **Research Brief**: The structured response returned to the user, including summary, key points, sources, contradictions, and confidence score.
- **Source Record**: A supporting source used in the brief, including title, URL, and relevance.
- **Contradiction Record**: A conflict between sources that should be visible in the final brief.
- **Confidence Assessment**: The score and rationale used to indicate how strongly the evidence supports the brief.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can receive a complete research brief within 2 minutes for a typical query.
- **SC-002**: At least 90% of valid requests return a brief that includes all required output fields.
- **SC-003**: When sources disagree, users can see the contradiction in the final brief in 100% of observed conflict cases.
- **SC-004**: At least 80% of typical requests include three or more credible sources when such sources are available.
- **SC-005**: Operators can confirm whether the service is healthy without starting a research request.

## Assumptions

- Users primarily submit English-language research queries.
- The system has access to the public web when a research request is made.
- Query depth is a user-facing control for breadth versus thoroughness, not a separate product tier.
- Persistent storage and caching are optional for the first release and may be disabled.
- The service is intended to return concise briefs rather than exhaustive literature reviews by default.
