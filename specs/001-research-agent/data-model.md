# Phase 1 Design: Data Model & Schemas

**Document Date**: 2026-03-26  
**Feature**: Research Agent (001-research-agent)  
**Technology Stack**: SQLModel, Pydantic v2, PostgreSQL/SQLite

---

## Overview

This document defines the data entities, their relationships, validation rules, and Pydantic/SQLModel representations for the research agent feature.

---

## Core Entities

### 1. ResearchQuery

**Purpose**: Represents a user's research request.  
**Persistence**: Required (Phase 1 in memory; Phase 4 in PostgreSQL for audit)

```python
# app/schemas/research.py
from pydantic import BaseModel, Field
from typing import Literal

class ResearchQuery(BaseModel):
    """
    User-submitted research query with search parameters.
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Research question or topic (3–500 characters)"
    )
    depth: Literal["basic", "intermediate", "deep"] = Field(
        default="intermediate",
        description="Search breadth: basic (5 sources), intermediate (10), deep (maximum per budget)"
    )
    max_sources: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum sources to retrieve (1–50)"
    )
    time_range: Literal["day", "week", "month", "year", "all"] = Field(
        default="all",
        description="Recency filter: day/week/month/year/all"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest advances in quantum computing in 2026?",
                "depth": "intermediate",
                "max_sources": 10,
                "time_range": "month"
            }
        }
```

**Validation Rules**:

- `query`: min 3 chars (prevent trivial queries), max 500 (prevent abuse)
- `depth`: enum (basic | intermediate | deep)
- `max_sources`: 1–50 (prevent runaway retrieval)
- `time_range`: enum (day | week | month | year | all)

**Relationships**: 1 ResearchQuery → N SourceRecords (retrieved in this query)

---

### 2. ResearchBrief

**Purpose**: Structured response containing synthesis of retrieved evidence.  
**Persistence**: Required (Phase 1 in memory; Phase 4 in PostgreSQL + Redis cache)

```python
# app/schemas/research.py
from typing import Optional
from pydantic import BaseModel, Field

class ResearchBrief(BaseModel):
    """
    Structured research brief synthesized from retrieved sources.
    """
    summary: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Concise narrative summary (50–2000 chars)"
    )
    key_points: list[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Bullet-point highlights (1–10 items)"
    )
    sources: list["SourceRecord"] = Field(
        ...,
        min_items=1,
        description="Supporting sources used in synthesis"
    )
    contradictions: list[str] = Field(
        default_factory=list,
        max_items=20,
        description="Any unresolved conflicts between sources (optional, 0–20)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence (0.0=no evidence, 1.0=high agreement)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Quantum computing has advanced significantly...",
                "key_points": [
                    "IBM released Condor processor with 1121 qubits",
                    "Google announced Willow with improved error correction"
                ],
                "sources": [
                    {
                        "title": "IBM Condor Quantum Processor",
                        "url": "https://example.com/ibm-condor",
                        "relevance": 0.95
                    }
                ],
                "contradictions": [
                    "Source A claims quantum advantage achieved; Source B claims still in research phase"
                ],
                "confidence_score": 0.85
            }
        }
```

**Validation Rules**:

- `summary`: 50–2000 chars (prevent empty/trivial summaries)
- `key_points`: 1–10 items (prevent bloat)
- `sources`: min 1 (must have at least one source)
- `contradictions`: 0–20 items (surface conflicts but prevent noise)
- `confidence_score`: 0.0–1.0 (float; 0 = no evidence, 1 = certainty)

**Relationships**:

- 1 ResearchBrief ← 1 ResearchQuery
- 1 ResearchBrief → N SourceRecords
- 1 ResearchBrief → N Contradictions

---

### 3. SourceRecord

**Purpose**: Represents a single retrieved source with metadata.  
**Persistence**: Required (Phase 1 in memory; Phase 4 in PostgreSQL & deduplicated by URL)

```python
# app/schemas/research.py
from pydantic import BaseModel, Field, HttpUrl

class SourceRecord(BaseModel):
    """
    A single source document used in research brief.
    """
    title: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Source title (5–500 chars)"
    )
    url: HttpUrl = Field(
        ...,
        description="Source URL (must be valid HTTP(S))"
    )
    relevance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0=low, 1.0=highly relevant)"
    )
    snippet: str = Field(
        default="",
        max_length=500,
        description="Optional excerpt from source (0–500 chars)"
    )
    retrieved_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when source was retrieved"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "IBM Announces Condor — World's Largest Quantum Processor",
                "url": "https://example.com/ibm-condor",
                "relevance": 0.95,
                "snippet": "IBM has revealed Condor, the most powerful quantum processor...",
                "retrieved_at": "2026-03-26T10:30:00Z"
            }
        }
```

**Validation Rules**:

- `title`: 5–500 chars (prevent short/empty titles)
- `url`: Valid HTTP(S) URL (Pydantic's `HttpUrl` validator)
- `relevance`: 0.0–1.0 (float; set by Tavily ranking or reranking model)
- `snippet`: 0–500 chars (optional; helps users review source content)
- `retrieved_at`: ISO 8601 format (auto-set to current time if not provided)

**Relationships**:

- N SourceRecords ← 1 ResearchBrief
- N SourceRecords ← 1 ResearchQuery

**Deduplication Key** (Phase 4): `(url, depth, time_range)` — prevent duplicate retrieval for same search params

---

### 4. ConfidenceAssessment

**Purpose**: Breakdown of how confidence score is calculated (optional, for observability).  
**Persistence**: Optional (Phase 2+ for logging; not returned in API response by default)

```python
# app/schemas/research.py
from pydantic import BaseModel, Field

class ConfidenceAssessment(BaseModel):
    """
    Inner workings of confidence scoring (optional detail for debug logs).
    """
    source_agreement: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well sources agree (0=conflicting, 1=unanimous)"
    )
    source_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average domain authority / freshness of sources"
    )
    recency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How recent the sources are (1=all <1day old, 0=all >1year old)"
    )
    contradiction_pressure: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Penalty if contradictions detected (0=many conflicts, 1=none)"
    )
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted average of above factors"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "source_agreement": 0.9,
                "source_quality": 0.85,
                "recency": 0.8,
                "contradiction_pressure": 0.95,
                "final_score": 0.875
            }
        }
```

**Calculation** (Phase 2 detailed spec):

```
final_score = 0.35*source_agreement + 0.25*source_quality + 0.2*recency + 0.2*contradiction_pressure
```

---

### 5. ContradictionRecord (Optional)

**Purpose**: Explicit representation of conflicting claims between sources.  
**Persistence**: Optional (Phase 2+ for auditing)

```python
# app/schemas/research.py
from pydantic import BaseModel, Field

class ContradictionRecord(BaseModel):
    """
    Record of conflicting claims between sources.
    """
    claim_a: str = Field(
        ...,
        max_length=500,
        description="Claim from source A (original wording or paraphrase)"
    )
    source_a_url: str = Field(
        ...,
        description="URL of source asserting claim A"
    )
    claim_b: str = Field(
        ...,
        max_length=500,
        description="Conflicting claim from source B"
    )
    source_b_url: str = Field(
        ...,
        description="URL of source asserting claim B"
    )
    severity: Literal["minor", "moderate", "major"] = Field(
        default="moderate",
        description="How significant the contradiction is"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "claim_a": "Quantum advantage achieved in 2023",
                "source_a_url": "https://example.com/source1",
                "claim_b": "Quantum advantage still in research phase (2026)",
                "source_b_url": "https://example.com/source2",
                "severity": "major"
            }
        }
```

---

## SQLModel Definitions (Database Layer, Phase 4)

Once PostgreSQL persistence is enabled (Phase 4), wrap Pydantic models in SQLModel tables:

```python
# app/db/models.py
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional

class QueryHistory(SQLModel, table=True):
    """Store past queries for audit and deduplication."""
    id: Optional[int] = Field(default=None, primary_key=True)
    query_text: str = Field(index=True)  # Full text index in Phase 4
    depth: str = Field(index=True)
    max_sources: int
    time_range: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    results: Optional[list["StoredResult"]] = Relationship(back_populates="query")

class StoredResult(SQLModel, table=True):
    """Cache research results for reuse."""
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="queryhistory.id")
    query: QueryHistory = Relationship(back_populates="results")
    summary: str
    key_points: str  # JSON-serialized list
    sources_json: str  # JSON-serialized SourceRecords
    confidence_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

class SourceIndex(SQLModel, table=True):
    """Deduplicate sources by URL to track usage across queries."""
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    title: str
    domain: str = Field(index=True)  # Extract from URL for ranking
    last_retrieved: datetime = Field(default_factory=datetime.utcnow)
    retrieval_count: int = Field(default=1)  # Popularity metric
```

**Indexes**:

- QueryHistory: `(query_text, depth)` — fast lookup for deduplication
- StoredResult: `(query_id, created_at)` — time-series queries
- SourceIndex: `(url)`, `(domain)` — prevent duplicate retrieval, rank by domain authority

---

## Confidence Scoring Algorithm

**Issue Resolution**: Addresses spec FR-005 (confidence score calculation).

Confidence score is a deterministic weighted aggregate of four factors:

```
confidence_score = (0.40 × source_agreement) 
                  + (0.30 × source_quality) 
                  + (0.20 × recency) 
                  + (0.10 × freshness) 
                  - (0.15 × contradiction_penalty)

Result: clamped to [0.0, 1.0]
```

**Component Definitions**:

| Factor | Range | Definition | Example |
|--------|-------|-----------|----------|
| **source_agreement** | 0.0–1.0 | Fraction of sources supporting main claim (e.g., 8 of 10 agree = 0.8) | 0–1 |
| **source_quality** | 0.0–1.0 | Average domain authority score from Tavily + recency boost | Avg of credibility_scores (see below) |
| **recency** | 0.0–1.0 | How recent sources are: 1.0 if all <7 days, 0.5 if 7–30 days, 0.2 if >30 days | Based on source publish dates |
| **freshness** | 0.0–1.0 | Binary: 1.0 if >50% sources <30 days old, else 0.5 | Boolean boost |
| **contradiction_penalty** | 0.0–1.0 | Severity of detected conflicts (see Contradiction Mapping below) | 0.05–0.20 |

**Example Calculation**:

```
Given:
  - 8/10 sources agree → source_agreement = 0.80
  - Avg domain quality = 0.85 → source_quality = 0.85
  - 6 sources <7 days old, 2 sources 14 days old → recency = 0.9
  - 7 sources <30 days → freshness = 1.0
  - 1 minor contradiction detected → contradiction_penalty = 0.05

Confidence = (0.40 × 0.80) + (0.30 × 0.85) + (0.20 × 0.9) + (0.10 × 1.0) - (0.15 × 0.05)
            = 0.32 + 0.255 + 0.18 + 0.10 - 0.0075
            = 0.8475 → **0.85** (rounded, clamped to [0.0, 1.0])
```

---

## Source Credibility Scoring

**Issue Resolution**: Addresses spec SC-004 ("credible sources" criteria).

Each source is assigned a credibility score used in source_quality calculation:

```
credibility_score = (0.50 × domain_authority) 
                   + (0.30 × recency_boost)
                   + (0.20 × citation_count_normalized)
```

**Component Definitions**:

| Factor | Range | Definition |
|--------|-------|------------|
| **domain_authority** | 0.0–1.0 | Tavily confidence rank (higher = more authoritative) |
| **recency_boost** | 0.0–1.0 | 1.0 if <30 days old; 0.5 if 30–90 days; 0.2 if >90 days |
| **citation_count_normalized** | 0.0–1.0 | Normalized count: (source_citations / max_citations_in_set) |

**Credibility Threshold** (for SC-004 compliance):

- **Credible Source**: `credibility_score ≥ 0.65`
- Sources with score <0.65 are included in output but marked lower in ranking
- Target: 80% of requests include ≥3 credible sources (when available)

**Example**:

```
Source: "NY Times article from 2026-03-20"
  - domain_authority = 0.95 (major news outlet)
  - recency_boost = 1.0 (6 days old)
  - citation_count_normalized = 0.8 (cited by 8 of 10 sources)
  
credibility_score = (0.50 × 0.95) + (0.30 × 1.0) + (0.20 × 0.8)
                  = 0.475 + 0.30 + 0.16
                  = 0.935 → **CREDIBLE** ✓
```

---

## Contradiction Detection & Severity Mapping

**Issue Resolution**: Addresses spec FR-004 (surface contradictions) and C3 (severity assignment).

Contradictions are classified by severity based on source disagreement:

```
Severity Level | Criteria | Confidence Penalty | When to Surface |
|---|---|---|---|
| **MINOR** | 1–2 sources disagree, rest align | -0.05 | Always (in contradictions array) |
| **MODERATE** | 3–4 sources disagree, rest align | -0.10 | Always |
| **MAJOR** | >50% sources disagree on core claim | -0.20 | Always (highlight in summary) |
```

**Detection Algorithm**:

1. Extract key claims from each source (via LLM extraction or snippet analysis)
2. Group sources by claim alignment
3. Compare largest group (agreeing sources) vs. others
4. Severity = f(disagreeing_sources / total_sources):
   - 1–2 sources ÷ 10+ total = MINOR (10% or less disagree)
   - 3–4 sources ÷ 10+ total = MODERATE (20–40% disagree)
   - 5+ sources ÷ 10 total = MAJOR (>50% disagree)

**Example**:

```
Claim: "Quantum advantage achieved in 2025"
  - 7 sources say "Yes, achieved" → agreement group
  - 2 sources say "No, still research phase" → contradiction
  - 1 source says "Achieved but not practically useful" → nuance

Severity: MODERATE (2 sources disagree, ~20%)
Penalty: -0.10
Action: Surface in contradictions[] with both claims
```

---

## Tavily Search Parameter Mapping

**Issue Resolution**: Addresses spec FR-006 (depth control) and U1 (parameter mapping).

User-selected depth enum maps to Tavily API search parameters:

```
Depth Level | search_depth | max_results | include_answer | Typical Latency |
|---|---|---|---|---|
| **basic** | 3 | 5 | false | <30 seconds |
| **intermediate** | 5 | 10 | true | <60 seconds |
| **deep** | 10 | 15+ | true | <120 seconds |
```

**Time Range Filter Mapping** (from ResearchQuery.time_range):

```
time_range | days_to_filter | Tavily include_domains param |
|---|---|---|
| day | 1 | Include only 1-day-old sources |
| week | 7 | Include only <7 day old sources |
| month | 30 | Include only <30 day old sources |
| year | 365 | Include only <365 day old sources |
| all | None | No date filter (all sources) |
```

**Implementation Detail** (for T026–T027):

In `app/services/retrieval.py`, create a mapping:

```python
DEPTH_PARAMS = {
    "basic": {"search_depth": 3, "max_results": 5},
    "intermediate": {"search_depth": 5, "max_results": 10},
    "deep": {"search_depth": 10, "max_results": 15},
}

TIME_RANGE_DAYS = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
    "all": None,  # No filter
}
```

---

## Latency Service Level Agreements

**Issue Resolution**: Addresses spec SC-001 ("typical query" SLA) and C4 (latency baselines).

**SLA Tiers** (end-to-end, from request received to response sent):

```
Depth | Target Latency | Typical Query | Remarks |
|---|---|---|---|
| **basic** | <30 seconds | "What are recent AI breakthroughs?" | Quick facts, light synthesis |
| **intermediate** | <60 seconds | "How is quantum computing advancing in 2026?" | Balanced search & synthesis |
| **deep** | <120 seconds | "Compare quantum vs. classical computing architectures" | Comprehensive, multi-sourced |
```

**Typical Query Definition**:

- **Length**: 3–7 words (e.g., "recent AI breakthroughs", "quantum computing 2026")
- **Specificity**: Broad research topic (not highly niche or recent-only)
- **Evidence Availability**: >10 relevant sources available in Tavily index
- **Contradictions**: 0–2 minor disagreements (not highly controversial)

**Monitoring** (T029):

Track per request:

```python
latency_metrics = {
    "total_latency_ms": int,          # End-to-end
    "retrieval_latency_ms": int,      # Tavily calls
    "synthesis_latency_ms": int,      # LLM synthesis
    "sources_retrieved_count": int,   # Final count
    "contradictions_found_count": int, # Final count
}
```

Log to structured logger; expose via GET /metrics endpoint (T034).

---

## Validation & Constraints

| Entity | Field | Min | Max | Type | Required | Notes |
|--------|-------|-----|-----|------|----------|-------|
| ResearchQuery | query | 3 | 500 | str | Y | Non-empty, substantive |
| ResearchQuery | depth | – | – | enum | Y | basic\|intermediate\|deep |
| ResearchQuery | max_sources | 1 | 50 | int | Y | Prevent runaway retrieval |
| ResearchQuery | time_range | – | – | enum | Y | day\|week\|month\|year\|all |
| ResearchBrief | summary | 50 | 2000 | str | Y | Minimum substantive length |
| ResearchBrief | key_points | 1 | 10 | list[str] | Y | At least 1 bullet point |
| ResearchBrief | sources | 1 | ∞ | list | Y | Must cite at least 1 source |
| ResearchBrief | contradictions | 0 | 20 | list[str] | N | Optional surface conflicts |
| ResearchBrief | confidence_score | 0.0 | 1.0 | float | Y | Uncertainty indication |
| SourceRecord | title | 5 | 500 | str | Y | Non-trivial source name |
| SourceRecord | url | – | – | HttpUrl | Y | Valid HTTP(S) |
| SourceRecord | relevance | 0.0 | 1.0 | float | Y | Ranking signal |
| SourceRecord | snippet | 0 | 500 | str | N | Optional excerpt |

---

## Relationships Diagram

```
ResearchQuery
  ├─→ 1..N SourceRecords (retrieved in this query)
  ├─→ 1 ResearchBrief (output)
  └─→ 0..N Contradictions (detected)

ResearchBrief
  ├─← 1 ResearchQuery (input)
  ├─→ 1..N SourceRecords (cited)
  ├─→ 1 ConfidenceAssessment (metadata)
  └─→ 0..N Contradictions (surfaced)

SourceRecord
  ├─← 1..N ResearchQueries (retrieved for)
  └─← 1 ResearchBrief (cited in)

ConfidenceAssessment
  └─← 1 ResearchBrief (belongs to)

Contradiction
  ├─← 1 ResearchBrief (surfaced in)
  └─→ 2 SourceRecords (conflicting sources)
```

---

## State Transitions

### ResearchBrief Lifecycle

```
PENDING (query submitted)
  ↓
RETRIEVING (Tavily API calls in progress, max 3 iterations)
  ↓
PROCESSING (deduplication, ranking, contradiction detection)
  ↓
SYNTHESIZING (LLM synthesis of summary, key points, confidence)
  ↓
COMPLETED (output delivered) OR FAILED (error, return confidence=0.0)
```

No explicit state column in Phase 1 (synchronous request/response). Phase 4+ may add state tracking for async processing.

---

## Phase 1 Scope (In-Memory)

For Phase 1 MVP (no persistence):

- ✅ ResearchQuery (request object)
- ✅ ResearchBrief (response object)
- ✅ SourceRecord (nested in response)
- ✅ ConfidenceAssessment (calculated, not persisted)
- ❌ ContradictionRecord (explicit table, deferred)
- ❌ QueryHistory (deferred to Phase 4)
- ❌ Database models (deferred to Phase 4)

---

## Phase 4 Additions (Persistence)

Once PostgreSQL enabled:

- ✅ QueryHistory (audit trail)
- ✅ StoredResult (result caching)
- ✅ SourceIndex (deduplication, domain ranking)
- ✅ Alembic migration scripts

---

## Conclusion

Core entities (ResearchQuery, ResearchBrief, SourceRecord) are fully specified with Pydantic validation rules. Phase 1 operates in memory; Phase 4 adds SQLModel tables for long-term audit and caching.

**Next**: See [contracts/](./contracts/) for API request/response schemas and [quickstart.md](./quickstart.md) for integration examples.
