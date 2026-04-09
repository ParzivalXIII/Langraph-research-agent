"""Custom theme examples for testing and documentation.

This module provides working examples of CalmResearchTheme customization
for both documentation and test fixtures.
"""

from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes


def create_custom_theme_sky_primary() -> CalmResearchTheme:
    """Create a custom theme with sky blue primary color.
    
    Use case: Alternative primary color for branding or accessibility.
    
    Returns:
        CalmResearchTheme instance with sky blue primary hue.
    """
    return CalmResearchTheme(primary_hue=themes.colors.sky)


def create_custom_theme_large_spacing() -> CalmResearchTheme:
    """Create a custom theme with larger component spacing.
    
    Use case: Better separation between components, improved whitespace,
    more accessible layout for users who prefer spacious interfaces.
    
    Returns:
        CalmResearchTheme instance with lg (large) spacing.
    """
    return CalmResearchTheme(spacing_size="lg")


def create_custom_theme_compact() -> CalmResearchTheme:
    """Create a custom theme with compact spacing (smaller).
    
    Use case: Dense information display, smaller screens, data-heavy applications.
    
    Returns:
        CalmResearchTheme instance with sm (small) spacing.
    """
    return CalmResearchTheme(spacing_size="sm")


def create_custom_theme_purple_with_spacing() -> CalmResearchTheme:
    """Create a custom theme with purple primary and large spacing.
    
    Demonstrates combining multiple customization parameters.
    
    Returns:
        CalmResearchTheme instance with purple primary and lg spacing.
    """
    return CalmResearchTheme(
        primary_hue=themes.colors.purple,
        spacing_size="lg"
    )


def create_custom_theme_accessible() -> CalmResearchTheme:
    """Create a theme optimized for accessibility.
    
    Combines large text, generous spacing, and dark mode support.
    
    Returns:
        CalmResearchTheme instance with accessibility optimizations.
    """
    return CalmResearchTheme(
        primary_hue=themes.colors.indigo,  # Strong contrast
        text_size="lg",          # Large text
        spacing_size="lg",       # Spacious layout
        enable_dark_mode=True               # Dark mode support
    )


def create_custom_theme_corporate() -> CalmResearchTheme:
    """Create a theme with corporate styling.
    
    Uses cyan and slate colors with professional fonts.
    
    Returns:
        CalmResearchTheme instance with corporate styling.
    """
    return CalmResearchTheme(
        primary_hue=themes.colors.cyan,
        secondary_hue=themes.colors.slate,
        font_primary="'Roboto', 'Segoe UI', sans-serif",
        font_mono="'Source Code Pro', monospace",
        spacing_size="md",
        enable_dark_mode=True
    )


def create_custom_theme_minimal() -> CalmResearchTheme:
    """Create a minimal, compact theme.
    
    Small spacing, small text, sharp corners for dense information display.
    
    Returns:
        CalmResearchTheme instance with minimal styling.
    """
    return CalmResearchTheme(
        spacing_size="sm",
        radius_size="sm",
        text_size="sm",
        enable_dark_mode=False  # Light mode only
    )


if __name__ == "__main__":
    # Example usage - can be run to verify all example themes instantiate correctly
    examples = [
        ("Sky Blue Primary", create_custom_theme_sky_primary()),
        ("Large Spacing", create_custom_theme_large_spacing()),
        ("Compact Spacing", create_custom_theme_compact()),
        ("Purple + Spacing", create_custom_theme_purple_with_spacing()),
        ("Accessible", create_custom_theme_accessible()),
        ("Corporate", create_custom_theme_corporate()),
        ("Minimal", create_custom_theme_minimal()),
    ]
    
    print("Custom Theme Examples - Verification")
    print("=" * 50)
    for name, theme in examples:
        print(f"✓ {name}: {type(theme).__name__} instantiated successfully")
    print("=" * 50)
    print(f"Total examples: {len(examples)}")
