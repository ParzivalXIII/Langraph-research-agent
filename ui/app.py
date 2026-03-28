"""Gradio 6 application: Controlled Research Interface.

A thin, deterministic client over the FastAPI research backend.
- Collects user queries and control settings (depth, source limit, time range)
- Submits to backend via ResearchClient  
- Renders structured response (summary, key_points, sources, contradictions, confidence)
- No logic drift: backend is single source of truth

Architecture:
- gr.Blocks(): Main layout with input section, submit button, tabbed output
- Async callbacks: run_research() event handler with try-catch error handling
- Pydantic validation: ResearchQuery and ResearchResponse models
- Logging: structlog for all request/response traces
- Form validation and submission
- Loading state display
- Error state and display
"""

import time

import gradio as gr
import structlog

from ui.client.api_client import ResearchClient
from ui.components.controls import (
    create_depth_dropdown,
    create_max_sources_slider,
    create_time_range_dropdown,
)
from ui.components.query_input import create_query_input
from ui.components.results import (
    format_confidence,
    format_contradictions,
    format_key_points,
    format_sources_table,
    format_summary,
)
from ui.models import Diagnostics, ResearchQuery, ResearchResponse

logger = structlog.get_logger(__name__)

# Initialize client at module level (reused across callbacks)
client = ResearchClient()


async def run_research(
    query: str, depth: str, max_sources: int, time_range: str
) -> tuple[str, str, list[list], str, str, str]:  # diagnostics returned as JSON string
    """Submit research request and render results.
    
    Implements T011: Form validation, backend submission, error handling.
    
    Args:
        query: User research question
        depth: 'basic', 'intermediate', or 'deep'
        max_sources: Integer in [3, 10]
        time_range: 'day', 'week', 'month', 'year', or 'all'
        
    Returns:
        Tuple of (summary, key_points, sources_table, contradictions, confidence, diagnostics_json)
        - summary: str (markdown)
        - key_points: str (bullet list)
        - sources_table: list[list] (for Dataframe)
        - contradictions: str (warning section or empty)
        - confidence: str (percentage + visual)
        - diagnostics: str (JSON for debugging)
    """
    start_time = time.time()
    request_payload = {
        "query": query,
        "depth": depth,
        "max_sources": max_sources,
        "time_range": time_range,
    }

    logger.info("run_research_start", **request_payload)

    # Step 1: Validate input using ResearchQuery pydantic model
    try:
        ResearchQuery.model_validate(request_payload)
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error("run_research_validation_failed", error=str(e))

        diagnostics = Diagnostics(
            request_payload=request_payload,
            response_status="validation_error",
            error_message=error_msg,
        )

        return (
            error_msg,
            "",
            [],
            "",
            "0%",
            _format_diagnostics(diagnostics),
        )

    # Step 2: Submit to backend
    try:
        response_data = await client.research(request_payload)
    except Exception as e:
        error_msg = _get_user_friendly_error(e)
        logger.error("run_research_backend_error", error=str(e), error_type=type(e).__name__)

        diagnostics = Diagnostics(
            request_payload=request_payload,
            response_status=_get_error_status(e),
            error_message=str(e),
        )

        return (
            error_msg,
            "",
            [],
            "",
            "0%",
            _format_diagnostics(diagnostics),
        )

    # Step 3: Validate and render response
    try:
        result = ResearchResponse.model_validate(response_data)
    except ValueError as e:
        error_msg = f"Invalid backend response: {str(e)}"
        logger.error(
            "run_research_response_validation_failed",
            error=str(e),
            response_keys=list(response_data.keys()) if isinstance(response_data, dict) else [],
        )

        diagnostics = Diagnostics(
            request_payload=request_payload,
            response_status="validation_error",
            error_message=error_msg,
            response_shape=dict(response_data) if isinstance(response_data, dict) else {},
        )

        return (
            error_msg,
            "",
            [],
            "",
            "0%",
            _format_diagnostics(diagnostics),
        )

    # Step 4: Format outputs (implemented in US2, for now return placeholders)
    summary = format_summary(result)
    key_points_str = format_key_points(result)
    sources_table = format_sources_table(result)
    contradictions_str = format_contradictions(result)
    confidence_str = format_confidence(result)

    elapsed_ms = int((time.time() - start_time) * 1000)

    diagnostics = Diagnostics(
        request_payload=request_payload,
        response_status="success",
        response_shape={"summary": "str", "key_points": "list", "sources": "list", "contradictions": "list", "confidence_score": "float"},
        execution_time_ms=elapsed_ms,
    )

    logger.info(
        "run_research_success",
        execution_time_ms=elapsed_ms,
        sources_count=len(result.sources),
        confidence_score=result.confidence_score,
    )

    return (
        summary,
        key_points_str,
        sources_table,
        contradictions_str,
        confidence_str,
        _format_diagnostics(diagnostics),
    )


# ============================================================================
# Helper Functions for Error Handling
# ============================================================================


def _get_user_friendly_error(error: Exception) -> str:
    """Convert backend error to user-friendly message for display in UI.
    
    Maps technical exception types to human-readable error messages appropriate
    for end-user display. Hides implementation details while explaining the issue.
    
    Args:
        error: An exception raised during backend communication or response validation.
               Expected types: httpx.TimeoutException, httpx.HTTPError, httpx.ConnectError,
               ValueError (validation), or generic Exception.
    
    Returns:
        str: User-friendly error message describing what went wrong and suggesting recovery.
        
    Examples:
        >>> import httpx
        >>> timeout_err = httpx.TimeoutException("...")
        >>> msg = _get_user_friendly_error(timeout_err)
        >>> "timed out" in msg.lower()
        True
    """
    error_type = type(error).__name__

    if error_type == "TimeoutException":
        return "Request timed out after 60 seconds. Backend may be unavailable or processing is too slow."
    elif error_type in ("HTTPError", "ConnectError"):
        return f"Backend error: {str(error)}. Please try again later."
    else:
        return f"Error: {str(error)}"


def _get_error_status(error: Exception) -> str:
    """Map exception type to diagnostic status code for logging and debugging.
    
    Converts exception types to standardized status strings for the Diagnostics model.
    Used to categorize errors in the request/response metadata displayed to users.
    
    Args:
        error: An exception instance.
        
    Returns:
        str: One of 'timeout', 'http_error', or 'unknown_error'.
        
    See Also:
        Diagnostics.response_status field in ui/models.py
    """
    error_type = type(error).__name__

    if error_type == "TimeoutException":
        return "timeout"
    elif error_type == "HTTPError":
        return "http_error"
    elif error_type == "ConnectError":
        return "http_error"
    else:
        return "unknown_error"


def _format_diagnostics(diagnostics: Diagnostics) -> str:
    """Format Diagnostics object as JSON string for raw inspection in UI.
    
    Serializes the Diagnostics model to pretty-printed JSON for display in the
    Diagnostics tab. Enables users to inspect request payloads, response shapes,
    error details, and execution timing for debugging and transparency.
    
    Args:
        diagnostics: A Diagnostics instance containing request/response metadata.
        
    Returns:
        str: Indented JSON string representation of the Diagnostics object.
        
    See Also:
        Diagnostics class in ui/models.py
    """
    return diagnostics.model_dump_json(indent=2)


# ============================================================================
# Form Validation Callback (T010)
# ============================================================================


def validate_query(query: str) -> tuple[bool, str]:
    """Validate query field and return (is_valid, error_message) for UI feedback.
    
    Called on query textbox change event to check validity and enable/disable the
    submit button accordingly. Provides immediate user feedback on query input.
    
    Args:
        query: Raw string from the query textbox input.
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if query passes validation, False otherwise.
            - error_message: Empty string if valid; descriptive message if invalid.
            
    Validation rules:
        - Cannot be empty or whitespace-only
        - Must be at least 3 characters (after strip)
        
    Examples:
        >>> validate_query("")
        (False, "Query cannot be empty")
        >>> validate_query("  ab  ")
        (False, "Query must be at least 3 characters")
        >>> validate_query("Valid query")
        (True, "")
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"
    if len(query.strip()) < 3:
        return False, "Query must be at least 3 characters"
    return True, ""


# ============================================================================
# Main Gradio App Layout (T009)
# ============================================================================


def build_app() -> gr.Blocks:
    """Build and return the Gradio Blocks app with full layout.
    
    Implements T009: Title, input section, three controls, submit button,
    tabbed output (Results, Diagnostics).
    """
    with gr.Blocks(title="Controlled Research Interface", theme=None) as app:
        # Header
        gr.Markdown(
            """
            # Controlled Research Interface
            
            Submit a research query with your preferred depth, source limit, and time range.
            The interface collects your request and renders the backend's structured response.
            """
        )

        # Input Section
        with gr.Group():
            with gr.Row():
                query_input = create_query_input()

            with gr.Row():
                depth_dropdown = create_depth_dropdown()
                max_sources_slider = create_max_sources_slider()
                time_range_dropdown = create_time_range_dropdown()

            # Error message display (shows during validation failure)
            error_message = gr.Textbox(
                value="",
                interactive=False,
                visible=False,
            )

            # Submit button
            with gr.Row():
                submit_btn = gr.Button(
                    "Run Research",
                    variant="primary",
                    interactive=True,
                    scale=1,
                )
                clear_btn = gr.Button(
                    "Clear",
                    variant="secondary",
                    scale=1,
                )
            
            # Loading state (T020): Hidden by default, shown during request
            loading_state = gr.Markdown(
                value="⏳ Processing your research request...",
                visible=False,
            )
            
            # Error display (T022): Hidden by default, shown on backend error
            error_display = gr.Markdown(
                value="",
                visible=False,
            )

        # Output Section: Results Tab
        with gr.Tabs():
            with gr.Tab():
                with gr.Group():
                    summary_output = gr.Markdown(value="")

                    key_points_output = gr.Textbox(
                        lines=6,
                        interactive=False,
                        value="",
                    )

                with gr.Group():
                    sources_table = gr.Dataframe(
                        headers=["Title", "URL", "Relevance"],
                        interactive=False,
                        type="numpy",
                    )

                with gr.Group():
                    contradictions_output = gr.Markdown(value="")
                    confidence_output = gr.Textbox(
                        value="",
                        interactive=False,
                    )

            with gr.Tab():
                diagnostics_output = gr.Textbox(
                    label="Request/Response Metadata",
                    lines=12,
                    interactive=False,
                    value="",
                    show_label=False,
                )

        # Event Handlers
        # (T010) Form validation on query change
        def check_query_validity(q: str):
            is_valid, msg = validate_query(q)
            return gr.update(
                visible=not is_valid,
                value=msg,
            ), gr.update(interactive=is_valid)

        query_input.change(
            check_query_validity,
            inputs=[query_input],
            outputs=[error_message, submit_btn],
        )

        # (T011) Submit button: Call async run_research()
        # (T020-T022) With loading state and error display management
        async def handle_submit(query: str, depth: str, max_sources: int, time_range: str):
            """Handle submit with loading state and error display (T020-T022).
            
            Args:
                query, depth, max_sources, time_range: Form inputs
                
            Returns:
                tuple: (
                    loading_state_update,
                    submit_btn_update,
                    error_display_update,
                    summary, key_points, sources, contradictions, confidence, diagnostics
                )
            """
            # Call research
            summary, key_points, sources, contradictions, confidence, diagnostics = await run_research(
                query, depth, max_sources, time_range
            )
            
            # Check if error occurred
            is_error = any(x in summary for x in ["Validation", "Backend", "Invalid", "Error", "timed out"])
            
            if is_error:
                # Error: hide loading, re-enable button, show error display, clear results
                return (
                    gr.update(visible=False),  # Hide loading_state
                    gr.update(interactive=True),  # Re-enable submit_btn
                    gr.update(visible=True, value=f"❌ {summary}"),  # Show error_display
                    "",  # summary_output - clear on error
                    "",  # key_points_output - clear on error
                    [],  # sources_table - clear on error
                    "",  # contradictions_output - clear on error
                    "",  # confidence_output - clear on error
                    diagnostics,  # diagnostics_output - keep diagnostics
                )
            else:
                # Success: hide loading and error, re-enable button, show results
                return (
                    gr.update(visible=False),  # Hide loading_state
                    gr.update(interactive=True),  # Re-enable submit_btn
                    gr.update(visible=False, value=""),  # Hide error_display
                    summary,  # summary_output
                    key_points,  # key_points_output
                    sources,  # sources_table
                    contradictions,  # contradictions_output
                    confidence,  # confidence_output
                    diagnostics,  # diagnostics_output
                )
        
        submit_btn.click(
            fn=handle_submit,
            inputs=[query_input, depth_dropdown, max_sources_slider, time_range_dropdown],
            outputs=[
                loading_state,
                submit_btn,
                error_display,
                summary_output,
                key_points_output,
                sources_table,
                contradictions_output,
                confidence_output,
                diagnostics_output,
            ],
        )

        # Clear button: Reset all fields
        clear_btn.click(
            lambda: (
                "",  # query_input
                "intermediate",  # depth_dropdown
                5,  # max_sources_slider
                "all",  # time_range_dropdown
                "",  # summary_output
                "",  # key_points_output
                [],  # sources_table
                "",  # contradictions_output
                "",  # confidence_output
                "",  # diagnostics_output
                gr.update(visible=False),  # loading_state
                gr.update(interactive=True),  # submit_btn
                gr.update(visible=False, value=""),  # error_display
            ),
            outputs=[
                query_input,
                depth_dropdown,
                max_sources_slider,
                time_range_dropdown,
                summary_output,
                key_points_output,
                sources_table,
                contradictions_output,
                confidence_output,
                diagnostics_output,
                loading_state,
                submit_btn,
                error_display,
            ],
        )

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch()
