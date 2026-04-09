# Theme Customization Guide

**Version**: 1.0  
**Last Updated**: April 9, 2026  
**Target Audience**: Developers, Researchers, Customizers

---

## Overview

The `CalmResearchTheme` is fully customizable through constructor parameters, allowing you to adapt the look and feel to your specific needs while maintaining the professional calm aesthetic and accessibility standards.

## Customization Parameters

### 1. Color Customization

The theme supports customizable color palettes through hue parameters:

#### Primary Hue (Primary Colors)

Controls the main accent color used for CTAs (Call-To-Action buttons), links, and interactive elements.

**Available Options**: `"blue"`, `"cyan"`, `"sky"`, `"indigo"`, `"purple"`

**Default**: `"blue"` (#0284C7)

**Example: Using Sky Blue**

```python
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes

theme = CalmResearchTheme(primary_hue=themes.colors.sky)
```

**Result**: All primary buttons and CTAs will use sky blue (#0369A1 hover state) instead of standard blue.

#### Secondary Hue (Supporting Colors)

Controls the secondary accent color used for supporting UI elements and secondary buttons.

**Available Options**: `"slate"`, `"stone"`, `"zinc"`, `"gray"`, `"neutral"`

**Default**: `"slate"` (#64748B)

**Example: Using Stone Gray**

```python
theme = CalmResearchTheme(secondary_hue=themes.colors.stone)
```

#### Neutral Hue (Backgrounds & Borders)

Controls the neutral color palette for backgrounds, borders, and subtle UI elements.

**Available Options**: `"gray"`, `"stone"`, `"zinc"`, `"slate"`, `"neutral"`

**Default**: `"gray"`

**Example: Using Zinc**

```python
theme = CalmResearchTheme(neutral_hue=themes.colors.zinc)
```

### 2. Spacing Customization

Controls the padding and margin scale throughout the interface.

**Available Options**: `"sm"` (compact), `"md"` (balanced), `"lg"` (spacious)

**Default**: `"md"`

**Impact**:
- Component padding and margins scale proportionally
- Touch target sizes remain ≥44px on mobile
- Layout breathing room increases

**Example: Spacious Layout**

```python
from gradio import themes

theme = CalmResearchTheme(spacing_size="lg")
```

**Result**: All components have 1.5x the default spacing, creating a more open, breathable interface.

**Example: Compact Layout**

```python
theme = CalmResearchTheme(spacing_size="sm")
```

**Result**: All components have 0.75x the default spacing, creating a denser, more compact interface.

### 3. Border Radius Customization

Controls the roundedness of component corners.

**Available Options**: `"sm"` (sharp corners), `"md"` (balanced), `"lg"` (very rounded)

**Default**: `"md"`

**Example: Very Rounded Corners**

```python
theme = CalmResearchTheme(radius_size="lg")
```

### 4. Text Size Customization

Controls the base font size scale across the interface.

**Available Options**: `"sm"` (12px base), `"md"` (14px base), `"lg"` (16px base)

**Default**: `"md"`

**Example: Large Text for Accessibility**

```python
theme = CalmResearchTheme(text_size="lg")
```

**Result**: All text is increased by ~14%, improving readability for users with visual impairments.

### 5. Font Customization

Control the typeface used throughout the interface.

#### Primary Font (All Text)

**Default**: `"'IBM Plex Sans', 'Helvetica Neue', sans-serif"`

**Example: Using Inter Font**

```python
theme = CalmResearchTheme(
    font_primary="'Inter', 'Segoe UI', sans-serif"
)
```

#### Monospace Font (Code, Terminal Output)

**Default**: `"'IBM Plex Mono', 'Courier New', monospace"`

**Example: Using Fira Code**

```python
theme = CalmResearchTheme(
    font_mono="'Fira Code', 'Courier New', monospace"
)
```

**Note**: Ensure chosen fonts are available via Google Fonts or are pre-installed on target systems.

### 6. Dark Mode

Enable or disable dark mode support and the toggle button.

**Default**: `True` (Dark mode enabled)

**Example: Disabling Dark Mode**

```python
theme = CalmResearchTheme(enable_dark_mode=False)
```

## Complete Customization Example

Combine multiple parameters for complete customization:

```python
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes
import gradio as gr

# Create a fully customized theme
custom_theme = CalmResearchTheme(
    # Colors: Use purple primary with stone secondary
    primary_hue=themes.colors.purple,
    secondary_hue=themes.colors.stone,
    
    # Spacing: More spacious layout
    spacing_size="lg",
    
    # Text: Larger text for accessibility
    text_size="lg",
    
    # Fonts: Custom font stack
    font_primary="'Inter', sans-serif",
    font_mono="'Fira Code', monospace",
    
    # Dark mode: Enabled
    enable_dark_mode=True
)

# Use the theme
with gr.Blocks(theme=custom_theme) as demo:
    gr.Markdown("# Research Agent with Custom Theme")
    
    with gr.Row():
        query = gr.Textbox(label="Query", placeholder="Ask a research question...")
        submit_btn = gr.Button("Research", variant="primary")
    
    results = gr.Markdown(label="Results")

if __name__ == "__main__":
    demo.launch()
```

## Use Case Examples

### Example 1: High Contrast for Accessibility

```python
theme = CalmResearchTheme(
    primary_hue=themes.colors.indigo,  # Strong contrast
    text_size="lg",          # Larger text
    spacing_size="lg",       # More breathing room
    enable_dark_mode=True               # Support both modes
)
```

### Example 2: Minimalist Compact Interface

```python
theme = CalmResearchTheme(
    spacing_size="sm",       # Compact spacing
    radius_size="sm",        # Sharp corners
    text_size="sm",          # Smaller text
    enable_dark_mode=False              # Light mode only
)
```

### Example 3: Corporate Branding

```python
theme = CalmResearchTheme(
    primary_hue=themes.colors.cyan,     # Corporate cyan
    secondary_hue=themes.colors.slate,  # Professional slate
    font_primary="'Roboto', sans-serif",
    font_mono="'Source Code Pro', monospace",
    spacing_size="md",
    enable_dark_mode=True
)
```

## Best Practices

### ✅ Do

- **Test in all browsers**: Chrome, Firefox, Safari, Edge
- **Verify text contrast**: Ensure WCAG AA compliance (4.5:1) with chosen colors
- **Test on mobile**: Use Chrome DevTools device emulation (375px, 768px viewports)
- **Preserve accessibility**: Keep `enable_dark_mode=True` for WCAG compliance
- **Use standardized fonts**: Stick to Google Fonts or system-safe fonts

### ❌ Don't

- **Override theme variables via CSS**: Use constructor parameters instead
- **Use custom fonts not available on target systems**: Verify font availability
- **Disable dark mode for accessibility compliance**: Keep enabled by default
- **Reduce text size below 12px base**: Violates WCAG AA readability standards
- **Create themes on-the-fly per request**: Pre-define and test theme configurations

## Testing Your Custom Theme

### 1. Visual Testing

```python
# ui/app.py
import gradio as gr
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes

# Your custom theme
theme = CalmResearchTheme(
    primary_hue=themes.colors.sky,
    spacing_size="lg"
)

with gr.Blocks(theme=theme) as demo:
    gr.Markdown("# Custom Theme Preview")
    
    gr.Textbox(label="Test Input")
    gr.Button("Test Button", variant="primary")
    gr.Button("Test Secondary", variant="secondary")
    gr.Markdown("### Test Text")

demo.launch()
```

Then:
1. Open `http://localhost:7860` in a browser
2. Verify colors match expectations
3. Check spacing visually
4. Test dark mode toggle (if enabled)

### 2. Contrast Testing

```bash
# Use axe DevTools in browser or run headless testing
# See tests/ui/test_theme_colors_contrast.py
pytest tests/ui/test_theme_colors_contrast.py -v
```

### 3. Responsiveness Testing

1. Open app in Chrome DevTools
2. Toggle device emulation (iPhone SE, iPad, Desktop)
3. Verify layout at each breakpoint
4. Check text readability

## Deployment

### Production Deployment with Custom Theme

```python
# ui/app.py
import os
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes

# Load theme configuration from environment
PRIMARY_HUE = os.getenv("THEME_PRIMARY_HUE", "blue")
SPACING_SIZE = os.getenv("THEME_SPACING_SIZE", "md")
DARK_MODE = os.getenv("THEME_DARK_MODE", "true").lower() == "true"

theme = CalmResearchTheme(
    primary_hue=getattr(themes.colors, PRIMARY_HUE),
    spacing_size=getattr(themes.sizes, SPACING_SIZE),
    enable_dark_mode=DARK_MODE
)
```

### Environment Configuration

```bash
# .env or deployment config
THEME_PRIMARY_HUE=sky
THEME_SPACING_SIZE=lg
THEME_DARK_MODE=true
```

## Troubleshooting

### Issue: Custom font not loading

**Solution**: 
- Verify font is available via Google Fonts
- Check browser console for font loading errors
- Use fallback fonts: `"'Font Name', 'Fallback', sans-serif"`

### Issue: Colors don't match expectations

**Solution**:
- Use browser DevTools Inspector to check computed CSS variables
- Verify theme instantiation by printing theme object
- Check for CSS conflicts in custom_css

### Issue: Layout breaks with custom spacing

**Solution**:
- Test at all viewport sizes (375px, 768px, 1920px)
- Keep spacing_size within "sm", "md", "lg" range
- Avoid mixing custom CSS padding with theme spacing

### Issue: Dark mode toggle not appearing

**Solution**:
- Verify `enable_dark_mode=True`
- Check browser console for JavaScript errors
- Test in different browser (may be browser-specific)

## Support & Questions

For issues or questions about theme customization:

1. Check this guide's Troubleshooting section
2. Review `tests/fixtures/custom_theme_example.py` for working examples
3. Inspect browser DevTools for CSS variable values
4. Check `ui/theme/calm_research_theme.py` docstring for parameter definitions

---

## Related Documentation

- [Quickstart Guide](./quickstart.md) - Basic theme usage
- [Advanced Styling Guide](./advanced-styling-guide.md) - Custom CSS patterns
- [Specification](./spec.md) - Feature requirements and acceptance criteria
