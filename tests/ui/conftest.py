"""Test configuration and fixtures for UI theme testing."""
import pytest
from pathlib import Path


@pytest.fixture
def theme_module():
    """Provide access to theme module."""
    from ui.theme import CalmResearchTheme
    return CalmResearchTheme


@pytest.fixture
def default_theme():
    """Create a theme instance with default parameters."""
    from ui.theme import CalmResearchTheme
    return CalmResearchTheme()


@pytest.fixture
def custom_theme():
    """Create a theme instance with custom parameters."""
    from ui.theme import CalmResearchTheme
    return CalmResearchTheme(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="gray",
        spacing_size="md",
        radius_size="md",
        text_size="md",
        enable_dark_mode=True
    )


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "theme: mark test as a theme instantiation test"
    )
    config.addinivalue_line(
        "markers", "colors: mark test as a theme color/contrast test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI component test"
    )
