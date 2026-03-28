"""Gradio UI component for research query text input.

Implements T008: Query textbox with validation cues for users.
"""

import gradio as gr


def create_query_input() -> gr.Textbox:
    """Create query textbox component for research question input.
    
    The actual validation (non-empty, whitespace check) is performed by Pydantic
    ResearchQuery model when form is submitted, not in the component itself.
    This component provides UX guidance via placeholder text and max_length.
    
    Returns:
        gr.Textbox: Textbox with 2 lines, placeholder text, max 500 characters
    """
    return gr.Textbox(
        label="Research Query",
        placeholder="Enter your research question...",
        lines=2,
        max_length=500,
        info="What would you like to research?",
    )
