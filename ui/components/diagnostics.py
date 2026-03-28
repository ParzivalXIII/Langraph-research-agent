"""Gradio UI components for result quality diagnostics.

Implements T017-T019:
- create_confidence_display() → gr.Number + gr.HTML for visual confidence indicator
- create_contradictions_display() → gr.Markdown for warning section
- format_confidence() → (percentage_text, html_indicator) with color-coded bar
- format_contradictions() → str with warning formatting

Color-coding for confidence:
- Red (≤0.5): Low confidence
- Yellow (0.5–0.8): Medium confidence
- Green (>0.8): High confidence
"""

from typing import Tuple

import gradio as gr

from ui.models import ResearchResponse


# ============================================================================
# Component Builders (T017)
# ============================================================================


def create_confidence_display() -> Tuple[gr.Number, gr.HTML]:
    """Create confidence score display components with visual indicator bar.
    
    Returns:
        tuple: (gr.Number for the percentage, gr.HTML for the color bar)
    
    Example:
        confidence_number, confidence_bar = create_confidence_display()
        # Later, wire together with: method updates both components
    """
    confidence_number = gr.Number(
        label="Confidence Score",
        value=0.0,
        interactive=False,
        precision=0,
    )
    
    confidence_bar = gr.HTML(
        value="",
        label="Confidence Indicator",
    )
    
    return confidence_number, confidence_bar


def create_contradictions_display() -> gr.Markdown:
    """Create contradictions warning display component.
    
    Returns:
        gr.Markdown: Read-only markdown block for contradictions section
    """
    return gr.Markdown(
        value="",
        label="Contradictions",
    )


# ============================================================================
# Formatting Functions (T018-T019)
# ============================================================================


def format_confidence(confidence_score: float) -> Tuple[str, str]:
    """Format confidence score as percentage with color-coded HTML bar (T018).
    
    Color coding:
    - Red bar + "0%" for scores ≤0.5 (low confidence)
    - Yellow bar + percentage for scores 0.5–0.8 (medium confidence)
    - Green bar + percentage for scores >0.8 (high confidence)
    
    Handles invalid/missing scores: defaults to 0.0 (red bar, 0% text).
    
    Args:
        confidence_score: Float in [0.0, 1.0], or invalid/missing value
        
    Returns:
        tuple: (percentage_text: str like "78%", html_indicator: str with colored bar)
    
    Example:
        percentage, html_bar = format_confidence(0.85)
        # Returns ("85%", "<div style='background-color: green; ...'></div>")
    """
    # Handle invalid/missing scores
    try:
        score = float(confidence_score)
        if score < 0.0 or score > 1.0:
            score = 0.0
    except (TypeError, ValueError):
        score = 0.0
    
    # Format percentage text
    percentage = int(score * 100)
    percentage_text = f"{percentage}%"
    
    # Determine color based on confidence level
    if score <= 0.5:
        color = "#ef4444"  # Red
        description = "Low"
    elif score <= 0.8:
        color = "#eab308"  # Yellow
        description = "Medium"
    else:
        color = "#22c55e"  # Green
        description = "High"
    
    # Build HTML progress bar with color
    bar_width_percent = percentage
    html_indicator = (
        f"""
        <div style="margin-top: 8px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 12px; font-weight: bold;">Confidence: {description}</span>
                <span style="font-size: 12px; font-weight: bold;">{percentage_text}</span>
            </div>
            <div style="width: 100%; height: 24px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden; border: 1px solid #d1d5db;">
                <div style="height: 100%; width: {bar_width_percent}%; background-color: {color}; transition: width 0.3s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px;">
                    <span style="color: white; font-size: 11px; font-weight: bold;">{percentage_text}</span>
                </div>
            </div>
        </div>
        """
    )
    
    return percentage_text, html_indicator


def format_contradictions(contradictions: list[str]) -> str:
    """Format contradictions as warning section (T019).
    
    If empty: returns "(No contradictions detected)"
    If present: returns "⚠️ **Contradictions Detected:** \n - bullet points"
    
    Args:
        contradictions: List of contradiction strings (can be empty)
        
    Returns:
        str: Formatted markdown warning section or empty string
    
    Example:
        result = format_contradictions(["Source A says X", "Source B says Y"])
        # Returns: "⚠️ **Contradictions Detected:** \n - Source A says X\n - Source B says Y"
    """
    if not contradictions or len(contradictions) == 0:
        return "(No contradictions detected)"
    
    warning_block = "⚠️ **Contradictions Detected:**\n\n"
    for contradiction in contradictions:
        if contradiction and contradiction.strip():  # Non-empty contradiction
            warning_block += f"- {contradiction}\n"
    
    return warning_block.rstrip()


# ============================================================================
# Convenience Functions for Direct Response Formatting
# ============================================================================


def format_confidence_from_response(response: ResearchResponse) -> Tuple[str, str]:
    """Wrapper to format confidence from ResearchResponse object.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        tuple: (percentage_text, html_indicator)
    """
    return format_confidence(response.confidence_score)


def format_contradictions_from_response(response: ResearchResponse) -> str:
    """Wrapper to format contradictions from ResearchResponse object.
    
    Args:
        response: ResearchResponse model instance
        
    Returns:
        str: Formatted markdown warning section
    """
    return format_contradictions(response.contradictions)
