"""Gradio tabs organization for structured result presentation.

Implements T016b: Results Tab and Diagnostics Tab layout builder.
"""

import gradio as gr

from ui.components.results import (
    create_confidence_output,
    create_contradictions_output,
    create_key_points_output,
    create_sources_table,
    create_summary_output,
)


def create_results_tabs() -> tuple[
    gr.Tabs,
    gr.Markdown,
    gr.Textbox,
    gr.Dataframe,
    gr.Markdown,
    gr.Textbox,
    gr.Textbox,
]:
    """Create tabbed layout for Results and Diagnostics sections.
    
    Returns:
        Tuple of (tabs_component, summary, key_points, sources, contradictions, confidence, diagnostics)
    
    Note: The outer Tabs component should be created by the caller to be wired to
    the Gradio Blocks layout. This function returns component references for event binding.
    """
    with gr.Tabs() as tabs:
        with gr.Tab():
            with gr.Group():
                summary_output = create_summary_output()

                key_points_output = create_key_points_output()

            with gr.Group():
                sources_table = create_sources_table()

            with gr.Group():
                contradictions_output = create_contradictions_output()
                confidence_output = create_confidence_output()

        with gr.Tab():
            diagnostics_output = gr.Textbox(
                label="Request/Response Metadata",
                lines=12,
                interactive=False,
                value="",
                show_label=False,
            )

    return tabs, summary_output, key_points_output, sources_table, contradictions_output, confidence_output, diagnostics_output
