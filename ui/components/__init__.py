"""Gradio UI component definitions and layout builders."""

from ui.components.controls import (
    create_depth_dropdown,
    create_max_sources_slider,
    create_time_range_dropdown,
)
from ui.components.query_input import create_query_input
from ui.components.results import (
    create_confidence_output,
    create_contradictions_output,
    create_key_points_output,
    create_sources_table,
    create_summary_output,
    format_confidence,
    format_contradictions,
    format_key_points,
    format_sources_table,
    format_summary,
)

__all__ = [
    "create_depth_dropdown",
    "create_max_sources_slider",
    "create_time_range_dropdown",
    "create_query_input",
    "create_summary_output",
    "create_key_points_output",
    "create_sources_table",
    "create_contradictions_output",
    "create_confidence_output",
    "format_summary",
    "format_key_points",
    "format_sources_table",
    "format_contradictions",
    "format_confidence",
]
