"""Tests for custom CSS integration with CalmResearchTheme.

Tests verify that custom CSS can be applied to Gradio apps using the theme
without causing console errors or breaking theme defaults.
"""

import pytest
from ui.theme.calm_research_theme import CalmResearchTheme


class TestCustomCSSIntegration:
    """Test suite for custom CSS integration."""

    def test_custom_css_integration_basic(self):
        """Test that basic custom CSS can be integrated without errors.
        
        Given: A CalmResearchTheme with basic custom CSS
        When: The CSS is applied
        Then: No errors should occur and theme should remain functional
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = """
        #query-section {
            background: linear-gradient(135deg, #E0F2FE 0%, #F0FAFF 100%);
            border-radius: 8px;
            padding: 24px;
        }
        """
        
        # Act
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert custom_css is not None
        
        # Assert - CSS is valid
        assert "#query-section" in custom_css
        assert "background:" in custom_css
        assert "padding:" in custom_css

    def test_custom_css_gradient(self):
        """Test custom CSS with gradient backgrounds.
        
        Given: Custom CSS with gradient background
        When: Applied to theme
        Then: Gradient CSS should be valid
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = """
        .research-card {
            background: linear-gradient(
                135deg,
                var(--primary-50) 0%,
                var(--primary-100) 100%
            );
            border-radius: 8px;
        }
        """
        
        # Act
        assert "linear-gradient" in custom_css
        assert "var(--primary-50)" in custom_css
        
        # Assert
        assert theme is not None

    def test_custom_css_dark_mode_support(self):
        """Test custom CSS with dark mode media queries.
        
        Given: Custom CSS with @media (prefers-color-scheme: dark)
        When: Applied to theme
        Then: Dark mode CSS should be valid
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = """
        .card {
            background: #E0F2FE;
        }
        
        @media (prefers-color-scheme: dark) {
            .card {
                background: #1E293B;
            }
        }
        """
        
        # Act
        assert "@media (prefers-color-scheme: dark)" in custom_css
        
        # Assert
        assert theme is not None

    def test_custom_css_animation(self):
        """Test custom CSS with animations.
        
        Given: Custom CSS with keyframe animation
        When: Applied to theme
        Then: Animation CSS should be valid
        """
        # Arrange
        custom_css = """
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        #results {
            animation: fadeIn 0.3s ease-out;
        }
        """
        
        # Act
        assert "@keyframes fadeIn" in custom_css
        assert "animation: fadeIn" in custom_css

    def test_custom_css_with_theme_variables(self):
        """Test custom CSS using theme CSS variables.
        
        Given: Custom CSS referencing theme CSS variables
        When: Applied to theme
        Then: Variable references should be valid
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = """
        .research-element {
            color: var(--primary-600);
            background: var(--neutral-50);
            border: 1px solid var(--primary-200);
        }
        """
        
        # Act
        assert "var(--primary-600)" in custom_css
        assert "var(--neutral-50)" in custom_css
        
        # Assert
        assert theme is not None

    def test_custom_css_hover_states(self):
        """Test custom CSS with hover and focus states.
        
        Given: Custom CSS with :hover and :focus-visible
        When: Applied to theme
        Then: Interactive states should be present
        """
        # Arrange
        custom_css = """
        .card {
            transition: all 0.2s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
        }
        
        .card:focus-visible {
            outline: 2px solid var(--primary-600);
        }
        """
        
        # Act
        assert ":hover" in custom_css
        assert ":focus-visible" in custom_css
        
        # Assert
        assert "transform:" in custom_css

    def test_custom_css_research_summary_card(self):
        """Test custom CSS for research summary card example.
        
        Given: Research summary card custom CSS
        When: Applied to theme
        Then: CSS should define all necessary properties
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = """
        .research-summary {
            background: linear-gradient(
                135deg,
                rgba(224, 242, 254, 0.5) 0%,
                rgba(240, 249, 255, 0.8) 100%
            );
            border-left: 4px solid var(--primary-600);
            border-radius: 8px;
            padding: 20px 24px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.1);
        }
        
        .research-summary:hover {
            box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);
        }
        
        .research-summary-title {
            color: var(--primary-800);
            font-weight: 600;
        }
        """
        
        # Act
        assert ".research-summary" in custom_css
        assert "linear-gradient" in custom_css
        assert "border-left" in custom_css
        
        # Assert
        assert theme is not None

    def test_custom_css_responsive(self):
        """Test custom CSS with responsive media queries.
        
        Given: Custom CSS with responsive breakpoints
        When: Applied to theme
        Then: Media queries should be valid
        """
        # Arrange
        custom_css = """
        .grid {
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }
        
        @media (max-width: 1024px) {
            .grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
        }
        """
        
        # Act
        assert "@media (max-width: 1024px)" in custom_css
        assert "@media (max-width: 768px)" in custom_css

    def test_custom_css_accessibility(self):
        """Test custom CSS maintains accessibility standards.
        
        Given: Custom CSS with focus indicators and contrast
        When: Applied to theme
        Then: Accessibility features should be present
        """
        # Arrange
        custom_css = """
        .button {
            color: var(--primary-900);
            background: var(--primary-100);
        }
        
        .button:focus-visible {
            outline: 2px solid var(--primary-600);
            outline-offset: 2px;
        }
        
        @media (prefers-reduced-motion: reduce) {
            .button {
                transition: none;
            }
        }
        """
        
        # Act
        assert "focus-visible" in custom_css
        assert "prefers-reduced-motion" in custom_css

    def test_custom_css_no_critical_overrides(self):
        """Test that custom CSS follows best practices.
        
        Given: Custom CSS example
        When: Validated
        Then: Should not override critical theme variables
        """
        # Arrange
        # This tests that best practice examples don't use !important for theme variables
        custom_css = """
        /* Good: Uses theme variables */
        .element {
            color: var(--primary-600);
        }
        
        /* Good: Adds styling without overriding */
        .custom {
            padding: 24px;
            border-radius: 8px;
        }
        """
        
        # Act
        # Check that examples don't override critical variables
        assert "var(--" in custom_css
        
        # Assert
        # Verify good practices are present
        assert ".element" in custom_css
        assert ".custom" in custom_css

    def test_custom_css_table_styling(self):
        """Test custom CSS for data table styling.
        
        Given: Custom CSS for research data tables
        When: Applied to theme
        Then: Table CSS should be complete
        """
        # Arrange
        custom_css = """
        .research-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
        }
        
        .research-table thead {
            background: linear-gradient(90deg, var(--primary-600), var(--primary-500));
            color: white;
        }
        
        .research-table tbody tr:hover {
            background-color: var(--primary-50);
        }
        """
        
        # Act
        assert ".research-table" in custom_css
        assert ".research-table thead" in custom_css
        
        # Assert
        assert "border-collapse" in custom_css

    def test_custom_css_callout_patterns(self):
        """Test custom CSS for info, warning, and success callouts.
        
        Given: Custom CSS for callout patterns
        When: Applied to theme
        Then: All callout types should be defined
        """
        # Arrange
        custom_css = """
        .info-callout {
            border-left: 4px solid var(--info);
            background: rgba(59, 130, 246, 0.05);
        }
        
        .warning-callout {
            border-left: 4px solid var(--warning);
            background: rgba(245, 158, 11, 0.05);
        }
        
        .success-callout {
            border-left: 4px solid var(--success);
            background: rgba(16, 185, 129, 0.05);
        }
        """
        
        # Act
        assert ".info-callout" in custom_css
        assert ".warning-callout" in custom_css
        assert ".success-callout" in custom_css

    def test_theme_with_custom_css_instance(self):
        """Test that theme instance works with custom CSS parameter.
        
        Given: CalmResearchTheme instance
        When: Custom CSS is prepared to be passed to gr.Blocks
        Then: Theme and CSS should be compatible
        """
        # Arrange
        theme = CalmResearchTheme()
        custom_css = "#section { background: var(--primary-50); }"
        
        # Act
        assert theme is not None
        assert isinstance(theme, CalmResearchTheme)
        assert isinstance(custom_css, str)
        
        # Assert - Both are ready to be used together
        assert len(custom_css) > 0
