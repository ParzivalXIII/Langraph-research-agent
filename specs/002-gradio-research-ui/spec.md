# Feature Specification: Controlled Research Interface

**Feature Branch**: `002-gradio-research-ui`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "I am building a thin client over a deterministic backend. The UI should not introduce logic drift—treat it as a controlled interface + visualization layer, not an 'agent UI."

## Evidence & Retrieval Plan *(mandatory for research-driven features)*

- Primary sources: The existing research backend response for a single research request, including its structured summary, ranked sources, contradiction notes, and confidence value.
- Fallback behavior: If the backend returns partial evidence, the interface still renders the available sections and clearly marks missing or conflicting sections instead of inventing content.
- Output schema: A structured research result containing a summary, key points, sources with title/link/relevance, contradictions, and a confidence score.
- Traceability: Each submitted query, the selected controls, the backend response shape, and render status are preserved in diagnostics so users can verify what was requested and what was returned.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit Research Query (Priority: P1)

As a user, I can enter a research question, choose the depth of the search, limit the number of sources, and set the time range so I can request a tailored research result.

**Why this priority**: This is the core value of the feature; without query submission and control selection, nothing else is useful.

**Independent Test**: Enter a query, adjust the controls, submit the request, and confirm the backend receives the selected values.

**Acceptance Scenarios**:

1. **Given** an empty page, **When** I enter a query and submit it, **Then** the system sends the request with the selected controls.
2. **Given** the form is filled out, **When** I change one control and submit again, **Then** the new request reflects the updated selection.

### User Story 2 - Review Structured Results (Priority: P1)

As a user, I can review the returned summary, key points, source list, contradiction notes, and confidence so I can understand the research result quickly.

**Why this priority**: The feature must present the research result in a way that is readable and actionable.

**Independent Test**: Provide a valid backend response and verify each output section appears with the expected content.

**Acceptance Scenarios**:

1. **Given** a completed research request, **When** the response is returned, **Then** the summary, key points, sources, contradictions, and confidence are rendered in separate sections.
2. **Given** source URLs are present, **When** the source list is shown, **Then** each URL is clickable.

### User Story 3 - Understand Result Quality (Priority: P2)

As a user, I can see the confidence score and any contradictions so I can judge whether the answer is stable enough to trust.

**Why this priority**: Transparency matters, but it is secondary to getting the structured answer itself.

**Independent Test**: Return a response containing a confidence value and contradictions, then verify the interface highlights them clearly.

**Acceptance Scenarios**:

1. **Given** the result includes contradictions, **When** I view diagnostics, **Then** the contradictions are shown as a warning section.
2. **Given** the result includes a confidence score, **When** I view the output, **Then** the confidence is displayed as a percentage and visual indicator.

### User Story 4 - Handle Loading and Failure States (Priority: P2)

As a user, I can see when the request is in progress and what went wrong if the request fails so I am not left with an ambiguous blank screen.

**Why this priority**: Reliable feedback is essential for a controlled interface.

**Independent Test**: Trigger a slow or failing backend response and verify the interface shows loading and error states.

**Acceptance Scenarios**:

1. **Given** a request is in progress, **When** I submit a query, **Then** the interface shows a loading state until the response is received.
2. **Given** the backend fails or returns invalid data, **When** I submit a query, **Then** the interface shows a clear error message and does not present fabricated results.

### Edge Cases

- The query is empty or whitespace only.
- The requested depth, source count, or time range is outside the allowed selection.
- The backend returns no sources, no contradictions, or no key points.
- The backend returns a partial response or a malformed response.
- The confidence score is missing, outside the expected range, or not numeric.
- One or more source links are unavailable or invalid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The interface MUST allow a user to enter a research query before initiating a request.
- **FR-002**: The interface MUST allow a user to choose one research depth from basic, intermediate, or deep.
- **FR-003**: The interface MUST allow a user to limit the number of returned sources within the permitted range of 3 to 10.
- **FR-004**: The interface MUST allow a user to choose a time range from day, week, month, year, or all.
- **FR-005**: The interface MUST send the selected query and controls to the research backend as a single request.
- **FR-006**: The interface MUST prevent a submission when the query is empty or contains only whitespace.
- **FR-007**: The interface MUST display a loading state while a request is in progress.
- **FR-008**: The interface MUST render the returned summary as a readable markdown block.
- **FR-009**: The interface MUST render returned key points as a structured bullet list.
- **FR-010**: The interface MUST render returned sources in a table with title, clickable URL, and relevance score.
- **FR-011**: The interface MUST render returned contradictions in a clearly marked warning section when contradictions are present.
- **FR-012**: The interface MUST display the confidence score as both a numeric percentage and a visual progress indicator.
- **FR-013**: The interface MUST preserve transparency by showing only what the backend returned and MUST NOT invent missing sources, contradictions, or quality indicators.
- **FR-014**: The interface MUST surface a clear error message when the request fails or the response cannot be rendered safely.
- **FR-015**: The interface MUST keep the summary, sources, contradictions, and diagnostics visually separated so users can inspect result quality quickly.

### Key Entities *(include if feature involves data)*

- **Research Query**: The user-entered topic plus the selected depth, source limit, and time range.
- **Research Result**: The structured response returned by the backend, including summary, key points, sources, contradictions, and confidence. (Also referred to as "ResearchResponse" in the data model and implementation; see [data-model.md](data-model.md) Section 3)
- **Source**: A cited item in the result with a title, destination link, and relevance score.
- **Diagnostics**: Rendered metadata that helps the user understand request status, completeness, and failure states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a valid research request and see a structured result without needing to interpret raw backend data in at least 95% of successful runs.
- **SC-002**: Users can identify the summary, sources, contradictions, and confidence sections in under 10 seconds after results load in at least 90% of usability test sessions.
- **SC-003**: At least 95% of rendered source links are usable as clickable destinations.
- **SC-004**: In error scenarios, users receive a clear failure state instead of a blank or misleading result in 100% of tested cases.
- **SC-005**: Users can distinguish higher-confidence and lower-confidence results at a glance in at least 90% of test observations.

## Assumptions

- The backend already provides a deterministic research response and the interface is only responsible for request submission and rendering.
- Mobile-first optimization is out of scope for the first version unless it falls out naturally from the layout.
- The allowed control values are fixed by the product requirements and do not need to be user-configurable.
- Authentication, if required by the backend, is handled outside this feature.
