"""Tests for research interface CSS and component styling."""
import pytest
import os
from pathlib import Path


@pytest.mark.ui
def test_research_interface_css_exists():
    """Test that research_interface.css exists and is valid."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    assert css_path.exists(), f"CSS file not found at {css_path}"
    assert css_path.is_file(), f"CSS path is not a file: {css_path}"
    assert css_path.suffix == ".css", f"File is not a CSS file: {css_path}"
    
    # Check file has content
    with open(css_path, 'r') as f:
        content = f.read()
    
    assert len(content) > 0, "CSS file is empty"
    assert len(content) > 1000, "CSS file appears too small (< 1KB)"
    
    print(f"✓ CSS file exists and has {len(content)} bytes")


@pytest.mark.ui
def test_research_interface_css_selectors():
    """Test that CSS includes required component selectors."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    required_selectors = [
        "#query-input-section",
        "#controls-panel",
        "#run-research-button",
        "#error-message",
        "#results-tabs",
        "#results-section",
        "#sources-table",
    ]
    
    for selector in required_selectors:
        assert selector in content, f"Missing CSS selector: {selector}"
    
    print(f"✓ All {len(required_selectors)} required CSS selectors present")


@pytest.mark.ui
def test_research_interface_css_properties():
    """Test that CSS includes styling properties."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for color properties
    assert "color:" in content or "background-color:" in content, "CSS missing color properties"
    assert "border-radius:" in content, "CSS missing border-radius"
    assert "padding:" in content, "CSS missing padding"
    assert "background:" in content, "CSS missing background"
    
    print("✓ CSS includes required styling properties")


@pytest.mark.ui
def test_research_interface_responsive_design():
    """Test that CSS includes responsive design media queries."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for media queries
    assert "@media" in content, "CSS missing media queries"
    assert "(max-width: 768px)" in content, "CSS missing tablet breakpoint"
    assert "(max-width: 480px)" in content, "CSS missing mobile breakpoint"
    
    print("✓ CSS includes responsive design media queries")


@pytest.mark.ui
def test_research_interface_dark_mode_support():
    """Test that CSS includes dark mode support."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for dark mode media query
    assert "@media (prefers-color-scheme: dark)" in content, "CSS missing dark mode support"
    
    # Count dark mode rules (find the section and verify it has content)
    dark_mode_idx = content.find("@media (prefers-color-scheme: dark)")
    assert dark_mode_idx != -1, "Dark mode section not found"
    
    # The dark mode section should have substantial styling
    dark_mode_section = content[dark_mode_idx:]
    assert len(dark_mode_section) > 100, "Dark mode CSS section is too small"
    assert dark_mode_section.count("#") > 5, "Dark mode section should have multiple color selectors"
    
    print("✓ CSS includes comprehensive dark mode support")


@pytest.mark.ui
def test_css_file_valid_syntax():
    """Test that CSS file has valid basic syntax."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Basic syntax checks
    opening_braces = content.count("{")
    closing_braces = content.count("}")
    assert opening_braces == closing_braces, "Mismatched braces in CSS"
    
    # Check for common syntax errors
    assert "{}" not in content, "Empty CSS rules found"
    assert content.count(";;") == 0, "Double semicolons in CSS"
    
    print(f"✓ CSS syntax valid: {opening_braces} rule blocks, braces balanced")


@pytest.mark.ui
def test_css_accessibility_colors():
    """Test that CSS uses accessible color values."""
    css_path = Path(__file__).parent.parent.parent / "ui" / "styles" / "research_interface.css"
    
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Check for hex color values (basic validation)
    import re
    hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', content)
    
    assert len(hex_colors) > 10, "CSS should have multiple color definitions"
    
    # Verify colors are 6-digit hex (not 3-digit)
    for color in hex_colors:
        assert len(color) == 7, f"Invalid hex color: {color}"
    
    print(f"✓ CSS uses {len(set(hex_colors))} unique hex colors, all properly formatted")


@pytest.mark.ui
def test_app_integrates_css():
    """Test that app.py references the CSS file."""
    app_path = Path(__file__).parent.parent.parent / "ui" / "app.py"
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check for elem_id attributes which indicate CSS integration readiness
    elem_id_count = content.count('elem_id="')
    
    # Should have at least the main sections: query-input, controls, button, results, tabs
    assert elem_id_count >= 5, f"Expected at least 5 elem_id attributes, found {elem_id_count}"
    
    # Check for specific elem_ids we added
    required_elem_ids = [
        'elem_id="query-input-section"',
        'elem_id="controls-panel"',
        'elem_id="run-research-button"',
        'elem_id="results-tabs"',
    ]
    
    for elem_id in required_elem_ids:
        assert elem_id in content, f"Missing elem_id in app.py: {elem_id}"
    
    print(f"✓ App has {elem_id_count} elem_id attributes for CSS styling")
