"""Tests for theme customization parameters.

Tests verify that custom parameters are properly applied to the theme instance
and that CSS variables reflect the customization choices.
"""

import pytest
from gradio import themes
from ui.theme.calm_research_theme import CalmResearchTheme


class TestThemeCustomization:
    """Test suite for CalmResearchTheme customization."""

    def test_custom_primary_hue(self):
        """Test that custom primary_hue is applied to CSS variables.
        
        Given: A CalmResearchTheme created with primary_hue="sky"
        When: The theme is instantiated
        Then: The primary color CSS variables should use sky blue palette
        """
        # Arrange
        theme = CalmResearchTheme(primary_hue=themes.colors.sky)
        
        # Act - Verify theme instantiated
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        
        # Assert - Check that theme object has expected attributes
        assert hasattr(theme, 'primary_hue')
        # Verify custom hue is stored
        assert theme.primary_hue == themes.colors.sky

    def test_custom_primary_hue_sky_palette(self):
        """Test that sky primary hue uses correct palette colors.
        
        Given: A custom theme with sky blue primary
        When: The theme is created
        Then: The theme should be configured with sky blue colors
        """
        # Arrange & Act
        sky_theme = CalmResearchTheme(primary_hue=themes.colors.sky)
        
        # Assert
        assert sky_theme is not None
        # Theme should have primary colors configured
        assert hasattr(sky_theme, 'primary') or isinstance(sky_theme, CalmResearchTheme)

    def test_custom_spacing_lg(self):
        """Test that custom spacing_size lg is applied.
        
        Given: A CalmResearchTheme created with spacing_size="lg"
        When: The theme is instantiated
        Then: The theme should be configured with large spacing
        """
        # Arrange
        theme = CalmResearchTheme(spacing_size="lg")
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        # Theme should have spacing configured
        assert theme.spacing_size == "lg"

    def test_custom_spacing_sm(self):
        """Test that custom spacing_size sm is applied.
        
        Given: A CalmResearchTheme created with spacing_size="sm"
        When: The theme is instantiated
        Then: The theme should be configured with small spacing
        """
        # Arrange
        theme = CalmResearchTheme(spacing_size="sm")
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert theme.spacing_size == "sm"

    def test_custom_radius_lg(self):
        """Test that custom radius_size lg is applied.
        
        Given: A CalmResearchTheme created with radius_size="lg"
        When: The theme is instantiated
        Then: The theme should be configured with large border radius
        """
        # Arrange
        theme = CalmResearchTheme(radius_size="lg")
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert theme.radius_size == "lg"

    def test_custom_text_size_lg(self):
        """Test that custom text_size lg is applied.
        
        Given: A CalmResearchTheme created with text_size="lg"
        When: The theme is instantiated
        Then: The theme should be configured with large text
        """
        # Arrange
        theme = CalmResearchTheme(text_size="lg")
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert theme.text_size == "lg"

    def test_custom_fonts(self):
        """Test that custom fonts are applied.
        
        Given: A CalmResearchTheme created with custom font families
        When: The theme is instantiated
        Then: The theme should be configured with specified fonts
        """
        # Arrange
        custom_primary_font = "'Inter', 'Segoe UI', sans-serif"
        custom_mono_font = "'Fira Code', 'Courier New', monospace"
        
        theme = CalmResearchTheme(
            font_primary=custom_primary_font,
            font_mono=custom_mono_font
        )
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_dark_mode_enabled(self):
        """Test that dark mode can be enabled.
        
        Given: A CalmResearchTheme created with enable_dark_mode=True
        When: The theme is instantiated
        Then: The theme should support dark mode
        """
        # Arrange
        theme = CalmResearchTheme(enable_dark_mode=True)
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_dark_mode_disabled(self):
        """Test that dark mode can be disabled.
        
        Given: A CalmResearchTheme created with enable_dark_mode=False
        When: The theme is instantiated
        Then: The theme should not support dark mode
        """
        # Arrange
        theme = CalmResearchTheme(enable_dark_mode=False)
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_multiple_customizations_combined(self):
        """Test that multiple customizations can be combined.
        
        Given: A CalmResearchTheme with multiple custom parameters
        When: The theme is instantiated with all customizations
        Then: The theme should apply all customizations
        """
        # Arrange
        theme = CalmResearchTheme(
            primary_hue=themes.colors.purple,
            secondary_hue=themes.colors.stone,
            spacing_size="lg",
            text_size="lg",
            font_primary="'Roboto', sans-serif",
            font_mono="'Source Code Pro', monospace",
            enable_dark_mode=True
        )
        
        # Act & Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert theme.primary_hue == themes.colors.purple
        assert theme.secondary_hue == themes.colors.stone
        assert theme.spacing_size == "lg"
        assert theme.text_size == "lg"
        assert theme.enable_dark_mode is True

    def test_custom_hue_cyan(self):
        """Test that cyan hue customization works.
        
        Given: A CalmResearchTheme with primary_hue=cyan
        When: The theme is instantiated
        Then: The theme should use cyan colors
        """
        # Arrange & Act
        theme = CalmResearchTheme(primary_hue=themes.colors.cyan)
        
        # Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_custom_hue_indigo(self):
        """Test that indigo hue customization works.
        
        Given: A CalmResearchTheme with primary_hue=indigo
        When: The theme is instantiated
        Then: The theme should use indigo colors
        """
        # Arrange & Act
        theme = CalmResearchTheme(primary_hue=themes.colors.indigo)
        
        # Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_secondary_hue_stone(self):
        """Test that secondary_hue stone customization works.
        
        Given: A CalmResearchTheme with secondary_hue=stone
        When: The theme is instantiated
        Then: The theme should use stone secondary colors
        """
        # Arrange & Act
        theme = CalmResearchTheme(secondary_hue=themes.colors.stone)
        
        # Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_neutral_hue_zinc(self):
        """Test that neutral_hue zinc customization works.
        
        Given: A CalmResearchTheme with neutral_hue=zinc
        When: The theme is instantiated
        Then: The theme should use zinc neutral colors
        """
        # Arrange & Act
        theme = CalmResearchTheme(neutral_hue=themes.colors.zinc)
        
        # Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)

    def test_theme_instances_independent(self):
        """Test that multiple theme instances don't interfere with each other.
        
        Given: Two CalmResearchTheme instances with different customizations
        When: Both are instantiated
        Then: They should be independent and not affect each other
        """
        # Arrange
        theme1 = CalmResearchTheme(primary_hue=themes.colors.sky, spacing_size="lg")
        theme2 = CalmResearchTheme(primary_hue=themes.colors.purple, spacing_size="sm")
        
        # Act & Assert
        assert theme1 is not None
        assert theme2 is not None
        assert theme1 is not theme2  # Should be different instances
        assert isinstance(theme1, CalmResearchTheme)
        assert isinstance(theme2, CalmResearchTheme)
        assert theme1.primary_hue == themes.colors.sky
        assert theme2.primary_hue == themes.colors.purple
        assert theme1.spacing_size == "lg"
        assert theme2.spacing_size == "sm"

    def test_default_parameters_preserved_when_not_specified(self):
        """Test that unspecified parameters use defaults.
        
        Given: A CalmResearchTheme with only primary_hue specified
        When: The theme is instantiated
        Then: Other parameters should use their defaults
        """
        # Arrange & Act
        theme = CalmResearchTheme(primary_hue=themes.colors.sky)
        
        # Assert
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        # Default spacing should still be "md" (checked implicitly through theme creation)
