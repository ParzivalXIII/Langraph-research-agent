<!--
Sync Impact Report
- Version change: unversioned/template -> 1.0.0
- Modified principles: template placeholders -> Determinism over Agentic Creativity; Retrieval First, Generation Second; Bounded Autonomy; Structured Outputs Only; Observability by Default; Cost + Latency Constraints; Stateless Core, Stateful Extensions
- Added sections: Operational Constraints; Development Workflow and Governance
- Removed sections: none
- Templates requiring updates: ✅ .specify/templates/plan-template.md; ✅ .specify/templates/spec-template.md; ✅ .specify/templates/tasks-template.md
- Follow-up TODOs: TODO(RATIFICATION_DATE): original adoption date not available in repo history
-->
# Langraph-research-agent Constitution

## Core Principles

### I. Determinism over Agentic Creativity

Every non-trivial claim, recommendation, or extracted fact MUST be traceable to a source
that is recorded with the output. If evidence is insufficient, the system MUST fail fast
instead of inventing a plausible answer. Reproducibility and auditability take precedence
over fluency or breadth.

### II. Retrieval First, Generation Second

Tavily is the primary retrieval signal. The LLM MAY synthesize, rank, or compress only after
evidence has been retrieved. The LLM MUST NOT fill gaps without supporting sources, and all
retrieval queries MUST be logged before synthesis begins.

### III. Bounded Autonomy

Each query MUST have explicit termination criteria: confidence threshold met, source saturation
reached, or query exhausted. Tool usage MUST be capped per request, with a default maximum of
three tool iterations unless a spec explicitly overrides the budget.

### IV. Structured Outputs Only

Outputs MUST conform to a declared schema. Free-form blobs are not allowed when a structured
response is feasible. Research results MUST include, at minimum: summary, key_points, sources,
confidence_score, and contradictions.

### V. Observability by Default

The system MUST log queries, retrieved documents, and intermediate model outputs in structured
form. Logs MUST be sufficient to replay the reasoning path and diagnose retrieval failures,
ranking errors, or unsupported conclusions.

### VI. Cost + Latency Constraints

Every workflow MUST respect explicit budgets for tokens and Tavily calls. Shallow breadth-first
search is the default strategy; deepening is allowed only when the evidence gap justifies the
extra cost and latency.

### VII. Stateless Core, Stateful Extensions

The core research flow MUST remain stateless. Caching and persistence are optional extensions,
and Redis or PostgreSQL MAY be added only when they measurably improve reuse, traceability, or
delivery guarantees without weakening the stateless core.

## Operational Constraints

These constraints are mandatory for all research-oriented features and prompts:

- All externally visible assertions MUST include source references.
- If retrieval returns conflicting evidence, the conflict MUST be surfaced in contradictions
 rather than hidden.
- All structured outputs SHOULD be validated before delivery, preferably with Pydantic or a
 compatible schema validator.
- Logging MUST capture the query text, retrieval parameters, retrieved document identifiers,
 and the final answer metadata.
- Any proposed stateful component MUST be justified by a concrete need such as caching,
 persistence, or workload isolation.

## Development Workflow and Governance

- Spec, plan, and tasks artifacts MUST be created or updated before implementation begins.
- Any change that increases autonomy, token usage, or external tool usage MUST document its
 budget impact and termination condition.
- Amendments require a written rationale, a version bump, and updates to dependent templates
 or prompts when the new rule changes their expected output.
- Versioning follows semantic versioning: MAJOR for incompatible governance changes, MINOR for
 new principles or materially expanded rules, PATCH for clarifications and wording fixes.
- Compliance review MUST verify source traceability, schema adherence, observability coverage,
 and explicit cost/latency bounds before a change is considered complete.

## Governance

This constitution supersedes conflicting procedural guidance for this repository. Any exception
MUST be documented in the implementing spec or plan, together with the reason the exception is
required and the scope of impact.

All pull requests affecting research behavior MUST verify that outputs remain evidence-backed,
structured, bounded, and observable. Runtime guidance should remain aligned with this document;
if a conflict appears, the constitution wins.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE) | **Last Amended**: 2026-03-26
