# Quickstart: Using the Calm Research Theme

**Status**: Ready for Phase 2 Implementation  
**Target Version**: CalmResearchTheme v1.0.0  
**Gradio Compatibility**: 6.10.0+

---

## 1. Installation & Setup

### Prerequisites

```bash
# Ensure Gradio 6.10.0+ is installed
pip install gradio>=6.10.0

# Ensure Google Fonts support is available
pip install gradio_client
```

### Project Structure

The theme will be located in:

```
ui/
  ├── theme/
  │   ├── __init__.py
  │   └── calm_research_theme.py    # Main theme class
  ├── components/
  │   ├── __init__.py
  │   ├── theme_controls.py         # Dark mode toggle
  │   ├── controls.py
  │   ├── query_input.py
  │   ├── results.py
  │   └── tabs.py
  └── app.py                         # Main Gradio app
```

---

## 2. Basic Usage

### Minimal Theme Application

```python
# ui/app.py
import gradio as gr
from ui.theme.calm_research_theme import CalmResearchTheme

# Initialize the theme with default parameters
theme = CalmResearchTheme()

# Create your Gradio blocks
with gr.Blocks(theme=theme) as demo:
    gr.Markdown("# Research Agent")
    
    with gr.Row():
        query = gr.Textbox(label="Query", placeholder="Ask a research question...")
        submit_btn = gr.Button("Research", variant="primary")
    
    results = gr.Markdown(label="Results")
    
    submit_btn.click(
        fn=run_research,
        inputs=[query],
        outputs=[results]
    )

# Launch with the theme applied
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
```

### Result

The Gradio interface will now use:

- **Cool blue** primary colors (#0284C7)
- **Slate gray** secondary colors (#64748B)
- **IBM Plex Sans** font
- **Professional calm** aesthetic with generous spacing
- **Dark mode support** (user-selectable toggle)

---

## 3. Advanced Customization

### Custom Constructor Parameters

```python
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes

# Customize the theme parameters
custom_theme = CalmResearchTheme(
    primary_hue=themes.colors.sky,      # Use sky blue instead of standard blue
    spacing_size="lg",       # Larger spacing for more breathing room
    text_size="lg",          # Larger text for better readability
    enable_dark_mode=True               # Enable dark mode toggle (default)
)

with gr.Blocks(theme=custom_theme) as demo:
    # Your components here
    pass
```

### Component-Specific Styling

```python
# Use elem_id for targeted CSS styling
with gr.Blocks(theme=CalmResearchTheme()) as demo:
    with gr.Group(elem_id="query-section"):
        gr.Markdown("### Research Query")
        query = gr.Textbox(
            label="Enter Query",
            elem_id="research-query-input",
            lines=3
        )
    
    with gr.Group(elem_id="results-section"):
        gr.Markdown("### Results")
        results = gr.Markdown(elem_id="research-results")
```

### Custom CSS Override

```python
custom_css = """
#query-section {
    background: linear-gradient(135deg, #E0F2FE 0%, #F0FAFF 100%);
    border-radius: 12px;
    padding: 24px;
}

#research-results {
    font-size: 15px;
    line-height: 1.6;
    color: var(--secondary-900);
}
"""

with gr.Blocks(theme=CalmResearchTheme(), css=custom_css) as demo:
    # Your components here
    pass
```

### For More Customization Options

See the **[Theme Customization Guide](./customization-guide.md)** for comprehensive documentation on:
- All available customization parameters
- Use case examples (accessibility, corporate branding, minimal interfaces)
- Best practices and common patterns
- Troubleshooting and deployment guidance

---

## 4. Dark Mode Toggle Integration

### Adding a Dark Mode Toggle Component

```python
# ui/components/theme_controls.py
import gradio as gr
import json

def create_theme_toggle():
    """Create a dark mode toggle that saves preference to localStorage"""
    
    toggle_html = gr.HTML("""
        <div id="theme-toggle" style="display: flex; align-items: center; gap: 8px;">
            <label for="dark-mode-checkbox">Dark Mode</label>
            <input 
                type="checkbox" 
                id="dark-mode-checkbox"
                onchange="toggleDarkMode(this.checked)"
            />
        </div>
        
        <script>
            // Load dark mode preference on page load
            (function() {
                const stored = localStorage.getItem('calmResearchTheme');
                if (stored) {
                    try {
                        const { darkMode } = JSON.parse(stored);
                        const checkbox = document.getElementById('dark-mode-checkbox');
                        if (checkbox) {
                            checkbox.checked = darkMode;
                            if (darkMode) {
                                document.documentElement.classList.add('dark-mode');
                            }
                        }
                    } catch (e) {
                        console.error('Failed to load theme preference:', e);
                    }
                }
            })();
            
            // Toggle dark mode and save preference
            function toggleDarkMode(isDark) {
                const preference = {
                    darkMode: isDark,
                    lastUpdated: new Date().toISOString()
                };
                localStorage.setItem('calmResearchTheme', JSON.stringify(preference));
                
                if (isDark) {
                    document.documentElement.classList.add('dark-mode');
                } else {
                    document.documentElement.classList.remove('dark-mode');
                }
            }
        </script>
    """)
    
    return toggle_html
```

### Using the Toggle in Your App

```python
# ui/app.py
from ui.components.theme_controls import create_theme_toggle
from ui.theme.calm_research_theme import CalmResearchTheme

with gr.Blocks(theme=CalmResearchTheme()) as demo:
    with gr.Row():
        theme_toggle = create_theme_toggle()
    
    # Rest of your interface
    gr.Markdown("# Research Agent")
```

---

## 5. Accessibility Testing

### Verify WCAG AA Compliance

```bash
# Install axe DevTools for Chrome
# https://chrome.google.com/webstore/detail/axe-devtools-web-accessibility-tester/lhdoppojpmngadmnkpklempisson

# 1. Launch the app
python ui/app.py

# 2. Open Chrome DevTools
# 3. Open axe DevTools
# 4. Run scan
# 5. Verify all contrast ratios >= 4.5:1
```

### Manual Contrast Verification

```python
# Test contrast ratios using a Python library
# pip install wcag-contrast-ratio

from wcag_contrast_ratio import contrast_ratio

# Primary text on light background
light_bg = "#FFFFFF"
dark_text = "#1A1A1A"
ratio = contrast_ratio(light_bg, dark_text)
print(f"Light background + dark text: {ratio:.2f}:1")  # Should be >= 4.5

# Primary text on dark background
dark_bg = "#0F172A"
light_text = "#F1F5F9"
ratio = contrast_ratio(dark_bg, light_text)
print(f"Dark background + light text: {ratio:.2f}:1")  # Should be >= 4.5
```

---

## 6. Responsive Design Testing

### Test Breakpoints

```bash
# Mobile (375px)
# 1. Press F12 (DevTools)
# 2. Press Ctrl+Shift+M (Device emulation)
# 3. Select "iPhone SE" (375x667)
# 4. Verify layout reflows correctly

# Tablet (768px)
# 1. Select "iPad" (768x1024)
# 2. Verify layout uses tablet spacing/fonts

# Desktop (1920px)
# 1. Select "Responsive"
# 2. Resize to 1920x1080
# 3. Verify layout optimized for desktop
```

### Responsive CSS Debugging

```python
# Add debug output to see active breakpoint
debug_info = gr.State(value={})

with gr.Blocks(theme=CalmResearchTheme()) as demo:
    with gr.Row():
        info = gr.HTML("""
            <div id="breakpoint-info" style="font-size: 12px; color: var(--secondary-500);">
                Current breakpoint: <span id="breakpoint-name">desktop</span>
            </div>
            
            <script>
                function updateBreakpoint() {
                    const width = window.innerWidth;
                    let breakpoint = 'desktop';
                    if (width < 768) breakpoint = 'mobile';
                    else if (width < 1920) breakpoint = 'tablet';
                    
                    document.getElementById('breakpoint-name').textContent = breakpoint;
                }
                
                window.addEventListener('resize', updateBreakpoint);
                updateBreakpoint();
            </script>
        """)
```

---

## 7. Performance Checklist

### Before Launch

- [ ] Theme loads in <100ms (measure with DevTools Performance tab)
- [ ] Dark mode toggle works and persists preference across reloads
- [ ] Responsive design works at 375px, 768px, 1920px viewports
- [ ] WCAG AA contrast ratios verified (>= 4.5:1 for text)
- [ ] Focus indicators visible and high contrast on all interactive elements
- [ ] Touch targets >= 44px on mobile
- [ ] Images/icons have alt text
- [ ] Keyboard navigation works (Tab, Enter, Escape)

### Performance Metrics

```python
import time
import json

# Measure theme instantiation time
start = time.perf_counter()
theme = CalmResearchTheme()
elapsed = (time.perf_counter() - start) * 1000
print(f"Theme instantiation: {elapsed:.2f}ms")

# Log to monitoring system
metrics = {
    "feature": "calm_research_theme",
    "metric": "instantiation_time_ms",
    "value": elapsed,
    "timestamp": time.time()
}
print(json.dumps(metrics))
```

---

## 8. Troubleshooting

### Theme Not Applied

```python
# Problem: Colors still look default
# Solution: Ensure theme is passed to Blocks AND launch()

with gr.Blocks(theme=CalmResearchTheme()) as demo:
    # ... components ...

# Correct
demo.launch()

# Also works (theme passed to launch)
demo2 = gr.Blocks()
# ... add components ...
demo2.launch(theme=CalmResearchTheme())
```

### Dark Mode Not Working

```python
# Problem: Checkbox doesn't toggle dark mode
# Solution: Check localStorage and CSS class name

# 1. Open Chrome DevTools Console
# 2. Check localStorage:
localStorage.getItem('calmResearchTheme')

# 3. Check root element has 'dark-mode' class:
document.documentElement.classList.contains('dark-mode')

# 4. Manually toggle:
document.documentElement.classList.add('dark-mode')
localStorage.setItem('calmResearchTheme', JSON.stringify({ darkMode: true }))
```

### Responsive Layout Broken

```python
# Problem: Layout doesn't stack on mobile
# Solution: Check media queries in browser DevTools

# 1. Open DevTools Elements tab
# 2. Select an element
# 3. Open Styles tab
# 4. Look for media query rules
# 5. Verify breakpoint values match theme schema (375px, 768px, 1920px)
```

---

## 9. Code Examples

### Complete Example App

```python
# ui/app.py
import gradio as gr
from ui.theme.calm_research_theme import CalmResearchTheme
from ui.components.theme_controls import create_theme_toggle
from ui.components.query_input import create_query_input
from ui.components.results import create_results_display


async def run_research(query: str) -> str:
    """Run research agent and return results"""
    # Your research logic here
    return f"Research results for: {query}"


# Initialize theme
theme = CalmResearchTheme(
    primary_hue="blue",
    spacing_size="md",
    enable_dark_mode=True
)

# Create Gradio interface
with gr.Blocks(
    title="Research Agent",
    theme=theme
) as demo:
    gr.Markdown("# Calm Research Interface")
    
    # Theme toggle in header
    with gr.Row():
        theme_toggle = create_theme_toggle()
    
    # Query input section
    with gr.Group(elem_id="query-section"):
        query_input = create_query_input()
        submit_btn = gr.Button("Research", variant="primary", scale=1)
    
    # Results section
    with gr.Group(elem_id="results-section"):
        results = create_results_display()
    
    # Wire events
    submit_btn.click(
        fn=run_research,
        inputs=[query_input],
        outputs=[results],
        api_name="research"
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
```

### Testing Example

```python
# tests/ui/test_theme_instantiation.py
import pytest
from ui.theme.calm_research_theme import CalmResearchTheme
from gradio import themes


def test_theme_instantiation_default():
    """Test theme can be instantiated with default parameters"""
    theme = CalmResearchTheme()
    assert theme is not None
    assert hasattr(theme, 'primary_hue')
    assert hasattr(theme, 'secondary_hue')


def test_theme_instantiation_custom():
    """Test theme can be instantiated with custom parameters"""
    theme = CalmResearchTheme(
        primary_hue=themes.colors.sky,
        spacing_size="lg"
    )
    assert theme is not None


def test_dark_mode_enabled():
    """Test dark mode can be enabled/disabled"""
    theme_light = CalmResearchTheme(enable_dark_mode=False)
    theme_dark = CalmResearchTheme(enable_dark_mode=True)
    assert theme_light is not None
    assert theme_dark is not None
```

---

## 10. Next Steps

After implementing the Calm Research Theme:

1. **Deploy to Staging**

   ```bash
   git add ui/theme/
   git commit -m "feat: Add Calm Research Theme"
   git push origin 003-calm-research-theme
   ```

2. **Run Full Test Suite**

   ```bash
   pytest tests/ui/ -v --cov
   ```

3. **Accessibility Audit**
   - Run axe DevTools
   - Verify WCAG AA compliance
   - Test with screen readers

4. **Performance Monitoring**
   - Measure theme load time
   - Monitor CSS variable application
   - Track dark mode toggle performance

5. **User Feedback**
   - Deploy to staging environment
   - Collect feedback from stakeholders
   - Iterate on color/spacing adjustments

---

## API Reference

### CalmResearchTheme Class

```python
class CalmResearchTheme(gr.themes.Base):
    """
    Professional calm-themed Gradio interface for research applications.
    
    Attributes:
        primary_hue: Cool blue primary color (default: "blue")
        secondary_hue: Slate gray secondary color (default: "slate")
        neutral_hue: Gray neutral color (default: "gray")
        spacing_size: Base spacing unit (default: "md")
        radius_size: Border radius size (default: "md")
        text_size: Base text size (default: "md")
        font_primary: Primary font stack (default: IBM Plex Sans + system fonts)
        font_mono: Monospace font stack (default: IBM Plex Mono + system fonts)
        enable_dark_mode: Enable dark mode toggle (default: True)
    
    Example:
        >>> theme = CalmResearchTheme()
        >>> with gr.Blocks(theme=theme) as demo:
        ...     gr.Markdown("# Research Agent")
    """
    
    def __init__(
        self,
        *,
        primary_hue: str = "blue",
        secondary_hue: str = "slate",
        neutral_hue: str = "gray",
        spacing_size: str = "md",
        radius_size: str = "md",
        text_size: str = "md",
        font_primary: list = None,
        font_mono: list = None,
        enable_dark_mode: bool = True
    ) -> None:
        """Initialize Calm Research Theme"""
        pass
```

---

## Resources

- [Gradio Theming Guide](https://www.gradio.app/guides/theming-guide)
- [WCAG 2.1 Accessibility Standards](https://www.w3.org/WAI/WCAG21/quickref/)
- [IBM Plex Font Family](https://github.com/IBM/plex)
- [Material Design Accessibility](https://material.io/design/usability/accessibility.html)
- [Responsive Design Best Practices](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)

---

**Status**: Ready for implementation  
**Last Updated**: April 9, 2026  
**Next Phase**: Phase 2 - Implementation & Testing
