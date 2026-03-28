"""Gradio UI components for rendering research results.

Implements T012–T015:
- create_summary_output(), create_key_points_output(), create_sources_table()
- format_summary(), format_key_points(), format_sources_table()
- format_contradictions(), format_confidence()

Note: format_confidence() and format_contradictions() now use enhanced formatting
from diagnostics.py module (imported locally to avoid circular imports).
"""

import gradio as gr

from ui.models import ResearchResponse


# ============================================================================
# Component Builders (T012)
# ============================================================================


def create_summary_output() -> gr.Markdown:
    """Create summary markdown output component.
    
    Returns:
        gr.Markdown: Read-only markdown block for rendered summary
    """
    return gr.Markdown(label="Summary", value="")


def create_key_points_output() -> gr.Textbox:
    """Create key points output component.
    
    Returns:
        gr.Textbox: Read-only textbox for bullet-list formatted key points
    """
    return gr.Textbox(
        label="Key Points",
        lines=6,
        interactive=False,
        value="",
        show_label=True,
    )


def create_sources_table() -> gr.Dataframe:
    """Create sources table component.
    
    Returns:
        gr.Dataframe: Read-only dataframe with columns [Title, URL, Relevance]
    """
    return gr.Dataframe(
        headers=["Title", "URL", "Relevance"],
        label="Sources",
        interactive=False,
        type="numpy",
    )


def create_contradictions_output() -> gr.Markdown:
    """Create contradictions warning component.
    
    Returns:
        gr.Markdown: Read-only markdown block for contradictions section
    """
    return gr.Markdown(label="Contradictions", value="")


def create_confidence_output() -> gr.Textbox:
    """Create confidence score component.
    
    Returns:
        gr.Textbox: Read-only textbox for confidence percentage and indicator
    """
    return gr.Textbox(
        label="Confidence Score",
        value="",
        interactive=False,
        show_label=True,
    )


# ============================================================================
# Formatting Functions (T013–T015)
# ============================================================================


def format_summary(response: ResearchResponse) -> str:
    """Format summary field from response (T013).
    
    Passes summary through as-is. Backend is the source of truth;
    UI does not synthesize or modify summary text.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        str: Summary text as provided by backend, or placeholder if empty
    """
    if not response.summary or not response.summary.strip():
        return "(No summary available)"
    return response.summary


def format_key_points(response: ResearchResponse) -> str:
    """Format key_points array as markdown bullet list (T014).
    
    Preserves order from backend (no re-sorting).
    Each point is rendered as a bullet.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        str: Bullet-list formatted string, or placeholder if empty
    """
    if not response.key_points:
        return "(No key points available)"
    
    return "\n".join(f"• {point}" for point in response.key_points)


def format_sources_table(response: ResearchResponse) -> list[list]:
    """Format sources array as list-of-lists for Dataframe (T015).
    
    Columns: title, url, relevance (formatted as percentage 0–100%).
    URLs are rendered as plain text (Gradio Dataframe handles linking).
    Preserves backend order (no re-sorting).
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        list[list]: Each row is [title, url, relevance_pct]. Empty list if no sources.
    """
    if not response.sources:
        return []
    
    table = []
    for source in response.sources:
        relevance_pct = f"{int(source.relevance * 100)}%"
        table.append([source.title, source.url, relevance_pct])
    
    return table


def format_contradictions(response: ResearchResponse) -> str:
    """Format contradictions as warning section (T019).
    
    Delegates to diagnostics.format_contradictions() for consistent formatting
    with enhanced warning visualization.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        str: Warning-formatted markdown, or placeholder if none
    """
    # Import locally to avoid circular imports
    from ui.components.diagnostics import format_contradictions as format_contradictions_formatted
    return format_contradictions_formatted(response.contradictions)


def format_confidence(response: ResearchResponse) -> str:
    """Format confidence score as percentage (T018).
    
    Returns just the percentage text (e.g., "78%").
    For full HTML bar visualization, use format_confidence_with_bar() or see diagnostics.py.
    This maintains backward compatibility with existing UI layouts.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        str: Percentage string, e.g., "78%"
    """
    # Import locally to avoid circular imports
    from ui.components.diagnostics import format_confidence as format_confidence_with_bar
    percentage_text, _ = format_confidence_with_bar(response.confidence_score)
    return percentage_text
