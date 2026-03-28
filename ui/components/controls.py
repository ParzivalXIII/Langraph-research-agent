"""Gradio UI control components for research query submission.

Implements T007: Depth, max_sources, and time_range dropdown/slider controls.
"""

import gradio as gr


def create_depth_dropdown() -> gr.Dropdown:
    """Create depth dropdown component with 'basic', 'intermediate', 'deep' options.
    
    Returns:
        gr.Dropdown: Dropdown with value='intermediate' as default
    """
    return gr.Dropdown(
        choices=["basic", "intermediate", "deep"],
        value="intermediate",
        label="Research Depth",
        info="Choose how thorough the research should be",
    )


def create_max_sources_slider() -> gr.Slider:
    """Create max_sources slider component with range [3, 10].
    
    Returns:
        gr.Slider: Slider with value=5, minimum=3, maximum=10, step=1
    """
    return gr.Slider(
        minimum=3,
        maximum=10,
        value=5,
        step=1,
        label="Maximum Sources",
        info="Number of sources to retrieve (3–10)",
    )


def create_time_range_dropdown() -> gr.Dropdown:
    """Create time_range dropdown component with temporal scope options.
    
    Returns:
        gr.Dropdown: Dropdown with choices ['day', 'week', 'month', 'year', 'all'], value='all'
    """
    return gr.Dropdown(
        choices=["day", "week", "month", "year", "all"],
        value="all",
        label="Time Range",
        info="Limit sources to a specific time period",
    )
