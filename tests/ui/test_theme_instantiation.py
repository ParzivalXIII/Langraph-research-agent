"""Unit tests for CalmResearchTheme class instantiation."""
import pytest


@pytest.mark.theme
def test_theme_default_parameters(default_theme):
    """Test that theme instantiates with default parameters without errors."""
    assert default_theme is not None
    assert hasattr(default_theme, 'primary_hue')
    assert default_theme.primary_hue == "blue"
    assert default_theme.secondary_hue == "slate"
    assert default_theme.neutral_hue == "gray"
    assert default_theme.spacing_size == "md"
    assert default_theme.radius_size == "md"
    assert default_theme.text_size == "md"
    assert default_theme.enable_dark_mode is True


@pytest.mark.theme
def test_theme_custom_parameters(custom_theme):
    """Test that custom constructor arguments are honored."""
    assert custom_theme is not None
    assert custom_theme.primary_hue == "blue"
    assert custom_theme.secondary_hue == "slate"
    assert custom_theme.neutral_hue == "gray"
    assert custom_theme.spacing_size == "md"
    assert custom_theme.radius_size == "md"
    assert custom_theme.text_size == "md"
    assert custom_theme.enable_dark_mode is True


@pytest.mark.theme
def test_theme_css_variables_set():
    """Test that CSS variables dictionary is properly populated."""
    from ui.theme import CalmResearchTheme

    theme = CalmResearchTheme()
    
    # Verify color palettes are accessible
    assert hasattr(theme, 'colors_primary')
    assert hasattr(theme, 'colors_secondary')
    assert hasattr(theme, 'colors_neutral')
    assert hasattr(theme, 'colors_semantic')

    # Verify primary palette has all expected colors
    primary = theme.colors_primary
    assert isinstance(primary, dict)
    assert len(primary) == 10
    assert primary["500"] == "#0EA5E9"
    assert primary["600"] == "#0284C7"
    assert primary["700"] == "#0369A1"

    # Verify secondary palette
    secondary = theme.colors_secondary
    assert isinstance(secondary, dict)
    assert len(secondary) == 10
    assert secondary["600"] == "#475569"

    # Verify neutral palette
    neutral = theme.colors_neutral
    assert isinstance(neutral, dict)
    assert len(neutral) == 10
    assert neutral["50"] == "#F9FAFB"

    # Verify semantic colors
    semantic = theme.colors_semantic
    assert isinstance(semantic, dict)
    assert semantic["success"] == "#10B981"
    assert semantic["error"] == "#EF4444"


@pytest.mark.theme
def test_theme_as_dict_export():
    """Test that theme can be exported as a dictionary."""
    from ui.theme import CalmResearchTheme

    theme = CalmResearchTheme()
    theme_dict = theme.as_dict()

    assert isinstance(theme_dict, dict)
    assert theme_dict["name"] == "calm_research"
    assert theme_dict["primary_hue"] == "blue"
    assert "colors" in theme_dict
    assert "primary" in theme_dict["colors"]
    assert "secondary" in theme_dict["colors"]
    assert "neutral" in theme_dict["colors"]
    assert "semantic" in theme_dict["colors"]
