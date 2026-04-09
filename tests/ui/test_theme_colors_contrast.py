"""Tests for theme color contrast validation (WCAG AA compliance)."""
import pytest
from ui.theme import CalmResearchTheme


def get_contrast_ratio(rgb_hex1: str, rgb_hex2: str) -> float:
    """Calculate contrast ratio between two colors.
    
    Formula from WCAG 2.0:
    L1 = (0.299 * R + 0.587 * G + 0.114 * B) / 255
    Contrast = (L_light + 0.05) / (L_dark + 0.05)
    
    Args:
        rgb_hex1: Color in hex format (e.g., "#0EA5E9")
        rgb_hex2: Color in hex format (e.g., "#FFFFFF")
    
    Returns:
        Contrast ratio (minimum 4.5:1 for WCAG AA normal text)
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def luminance(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    rgb1 = hex_to_rgb(rgb_hex1)
    rgb2 = hex_to_rgb(rgb_hex2)
    
    l1 = luminance(rgb1)
    l2 = luminance(rgb2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.colors
def test_wcag_aa_contrast_ratios():
    """Test that critical text-on-background combinations meet WCAG AA (4.5:1).
    
    WCAG AA requires:
    - 4.5:1 contrast for normal text (14px or less)
    - 3:1 contrast for large text (18px+ or bold 14px+)
    
    Note: Semantic accent colors (success, error, warning) may have lower ratios
    as they're meant for UI accent elements, not body text. When used as text,
    they should only be used for large/bold headings.
    """
    theme = CalmResearchTheme()
    
    # Test primary text contrast on white
    text_color = theme.colors_secondary["700"]  # Dark slate for text
    white_bg = "#FFFFFF"
    
    primary_on_light = get_contrast_ratio(text_color, white_bg)
    assert primary_on_light >= 4.5, f"Primary text on white: {primary_on_light:.2f}:1 < 4.5:1 (WCAG AA)"
    
    # Test primary CTA button color
    cta_color = theme.colors_primary["700"]  # Use 700 for better contrast
    cta_contrast = get_contrast_ratio(cta_color, white_bg)
    assert cta_contrast >= 4.5, f"CTA color on white: {cta_contrast:.2f}:1 < 4.5:1 (WCAG AA)"
    
    # Semantic colors are for accents - when used as text, they should meet 3:1 minimum
    # Error color meets this for large/bold text
    error_color = theme.colors_semantic["error"]  # #EF4444
    error_contrast = get_contrast_ratio(error_color, white_bg)
    assert error_contrast >= 3.0, f"Error color on white: {error_contrast:.2f}:1 < 3:1 (Large text minimum)"
    
    # Info color is acceptable for large text
    info_color = theme.colors_semantic["info"]  # #0EA5E9
    info_contrast = get_contrast_ratio(info_color, white_bg)
    assert info_contrast >= 3.0, f"Info color on white: {info_contrast:.2f}:1 < 3:1 (Large text minimum)"
    
    print(f"✓ Primary text on white: {primary_on_light:.2f}:1 (WCAG AA)")
    print(f"✓ CTA on white: {cta_contrast:.2f}:1 (WCAG AA)")
    print(f"✓ Error on white: {error_contrast:.2f}:1 (Large text)")
    print(f"✓ Info on white: {info_contrast:.2f}:1 (Large text)")


@pytest.mark.colors
def test_dark_mode_contrast_ratios():
    """Test that dark mode colors meet WCAG AA contrast."""
    theme = CalmResearchTheme()
    
    # Get dark mode colors from as_dict()
    theme_dict = theme.as_dict()
    dark_mode = theme_dict["colors"]["dark_mode"]
    
    dark_bg = dark_mode["background"]  # #0F172A
    light_text = dark_mode["text_light"]  # #F1F5F9
    primary_light = dark_mode["primary_light"]  # #60A5FA
    
    light_on_dark = get_contrast_ratio(light_text, dark_bg)
    assert light_on_dark >= 4.5, f"Light text on dark: {light_on_dark:.2f}:1 < 4.5:1"
    
    primary_on_dark = get_contrast_ratio(primary_light, dark_bg)
    assert primary_on_dark >= 4.5, f"Primary light on dark: {primary_on_dark:.2f}:1 < 4.5:1"
    
    print(f"✓ Light text on dark: {light_on_dark:.2f}:1")
    print(f"✓ Primary light on dark: {primary_on_dark:.2f}:1")


@pytest.mark.colors
def test_grayscale_contrast():
    """Test that neutral colors have sufficient contrast for text."""
    theme = CalmResearchTheme()
    
    # Neutral palette text colors on neutral backgrounds
    text_neutral = theme.colors_neutral["700"]  # #374151
    bg_neutral = theme.colors_neutral["50"]  # #F9FAFB
    
    neutral_contrast = get_contrast_ratio(text_neutral, bg_neutral)
    assert neutral_contrast >= 4.5, f"Neutral text on neutral: {neutral_contrast:.2f}:1 < 4.5:1"
    
    print(f"✓ Neutral text on neutral: {neutral_contrast:.2f}:1")
