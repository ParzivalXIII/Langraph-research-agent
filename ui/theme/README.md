# CalmResearchTheme - Admin & Maintainer Documentation

**Version**: 1.0  
**Audience**: Administrators, DevOps Engineers, Maintainers, Deployment Specialists  
**Purpose**: Guide for deploying and managing the CalmResearchTheme in production environments

---

## Overview

The `CalmResearchTheme` is a production-ready Gradio theme for the research agent application. This guide covers deployment, configuration, monitoring, and maintenance.

## Directory Structure

```
ui/theme/
├── __init__.py                    # Public API exports
├── calm_research_theme.py         # Main theme class (300 LOC)
└── [future: dark_mode_handler.js] # JavaScript for dark mode persistence

tests/ui/
├── test_theme_instantiation.py    # Unit tests for theme creation
├── test_theme_customization.py    # Tests for custom parameters
├── test_theme_colors_contrast.py  # WCAG AA contrast validation
├── test_research_interface_styling.py  # Integration tests
└── test_theme_visual.py           # Visual regression tests
```

## Deployment

### Prerequisites

Before deploying the theme, verify:

```bash
# 1. Check Python version (3.11+)
python --version

# 2. Verify Gradio version (6.10.0+)
pip list | grep gradio

# 3. Run pre-deployment tests
pytest tests/ui/ -v --tb=short

# 4. Check for theme build artifacts
find . -name "*.pyc" -o -name "__pycache__" | wc -l
```

### Basic Deployment

1. **Theme is already integrated into `ui/app.py`**:

```python
from ui.theme.calm_research_theme import CalmResearchTheme

theme = CalmResearchTheme()  # Uses default parameters

with gr.Blocks(theme=theme) as demo:
    # ... your components
    pass

demo.launch(...)
```

2. **No additional build steps required** - The theme is pure Python and loads at runtime.

3. **Start the application**:

```bash
# From project root
python ui/app.py
```

The theme will be loaded and applied automatically to all Gradio components.

### Custom Theme Deployment

Deploy with custom theme parameters via environment variables:

```python
# ui/app.py (updated for production)
import os
from gradio import themes
from ui.theme.calm_research_theme import CalmResearchTheme

# Load configuration from environment
PRIMARY_HUE = os.getenv("THEME_PRIMARY_HUE", "blue")
SPACING_SIZE = os.getenv("THEME_SPACING_SIZE", "md")
TEXT_SIZE = os.getenv("THEME_TEXT_SIZE", "md")
DARK_MODE_ENABLED = os.getenv("THEME_DARK_MODE", "true").lower() == "true"

# Create theme with environment configuration
theme = CalmResearchTheme(
    primary_hue=getattr(themes.colors, PRIMARY_HUE),
    spacing_size=getattr(themes.sizes, SPACING_SIZE),
    text_size=getattr(themes.sizes, TEXT_SIZE),
    enable_dark_mode=DARK_MODE_ENABLED
)

# ... rest of app
```

### Environment Configuration

Create `.env` file or set environment variables:

```bash
# .env or deployment configuration
THEME_PRIMARY_HUE=blue              # blue, cyan, sky, indigo, purple
THEME_SPACING_SIZE=md               # sm, md, lg
THEME_TEXT_SIZE=md                  # sm, md, lg
THEME_DARK_MODE=true                # true, false
```

### Docker Deployment

When deploying in Docker:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy theme files
COPY ui/theme/ ui/theme/

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .

# Set theme configuration
ENV THEME_PRIMARY_HUE=blue
ENV THEME_SPACING_SIZE=md
ENV THEME_DARK_MODE=true

EXPOSE 7860

# Start application
CMD ["python", "ui/app.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-agent
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: research-agent
        image: research-agent:latest
        ports:
        - containerPort: 7860
        env:
        - name: THEME_PRIMARY_HUE
          value: "blue"
        - name: THEME_SPACING_SIZE
          value: "md"
        - name: THEME_DARK_MODE
          value: "true"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Configuration Management

### Parameter Validation

When deploying with custom parameters, ensure:

```python
# Validate parameter values
VALID_HUES = ["blue", "cyan", "sky", "indigo", "purple"]
VALID_SIZES = ["sm", "md", "lg"]

primary_hue = os.getenv("THEME_PRIMARY_HUE", "blue")
if primary_hue not in VALID_HUES:
    raise ValueError(f"Invalid primary_hue: {primary_hue}. Must be one of {VALID_HUES}")

spacing = os.getenv("THEME_SPACING_SIZE", "md")
if spacing not in VALID_SIZES:
    raise ValueError(f"Invalid spacing_size: {spacing}. Must be one of {VALID_SIZES}")
```

### Pre-Deployment Checklist

```bash
# Run this script before deploying to production
#!/bin/bash

echo "Pre-Deployment Checks:"
echo "========================"

# 1. Run all tests
echo "Running test suite..."
pytest tests/ui/ -v --tb=short || exit 1

# 2. Check contrast compliance
echo "Verifying WCAG AA compliance..."
pytest tests/ui/test_theme_colors_contrast.py -v || exit 1

# 3. Verify theme instantiation
echo "Verifying theme instantiation..."
python -c "from ui.theme import CalmResearchTheme; t = CalmResearchTheme(); print('✓ Theme OK')" || exit 1

# 4. Check dependencies
echo "Verifying Gradio version..."
python -c "import gradio as gr; assert gr.__version__ >= '6.10.0'; print(f'✓ Gradio {gr.__version__}')" || exit 1

echo "========================"
echo "✓ All checks passed"
```

## Monitoring

### Health Checks

Create a health endpoint to verify theme is working:

```python
# ui/health.py
import gradio as gr
from ui.theme.calm_research_theme import CalmResearchTheme

def health_check():
    """Simple health check that verifies theme loads."""
    try:
        theme = CalmResearchTheme()
        return {
            "status": "healthy",
            "theme": "CalmResearchTheme",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    result = health_check()
    print(result)
```

### Performance Monitoring

Monitor theme load time:

```python
import time
from ui.theme.calm_research_theme import CalmResearchTheme

# Measure theme instantiation time
start = time.time()
theme = CalmResearchTheme()
elapsed_ms = (time.time() - start) * 1000

# Budget: <100ms
if elapsed_ms > 100:
    print(f"⚠ WARNING: Theme load took {elapsed_ms:.2f}ms (budget: 100ms)")
else:
    print(f"✓ Theme load OK: {elapsed_ms:.2f}ms")
```

### Logging

Theme initialization is logged via structlog:

```python
import structlog
logger = structlog.get_logger()

try:
    theme = CalmResearchTheme()
    logger.info("theme_loaded", theme_name="CalmResearchTheme", version="1.0.0")
except Exception as e:
    logger.error("theme_load_failed", error=str(e))
    raise
```

Monitor logs for theme-related issues:

```bash
# In production logs, look for:
grep -E "theme_loaded|theme_load_failed" /var/log/app.log
```

## Maintenance

### Updating the Theme

#### Minor Updates (Bug Fixes)

1. Update `calm_research_theme.py`
2. Run test suite: `pytest tests/ui/ -v`
3. Deploy with no parameter changes

#### Major Updates (Feature Additions)

1. Update `calm_research_theme.py`
2. Add new tests in `tests/ui/`
3. Update `customization-guide.md`
4. Run full test suite with contrast validation
5. Update version in documentation
6. Deploy and monitor

### Version Management

```python
# ui/theme/__init__.py
__version__ = "1.0.0"
__theme_name__ = "CalmResearchTheme"
```

### Backup & Rollback

Before deploying changes:

```bash
# Create backup
cp ui/theme/calm_research_theme.py ui/theme/calm_research_theme.py.backup

# If deployment fails, restore
cp ui/theme/calm_research_theme.py.backup ui/theme/calm_research_theme.py

# Restart application
systemctl restart research-agent
```

## Troubleshooting

### Theme Not Loading

```python
# Test theme instantiation directly
python -c "
from ui.theme.calm_research_theme import CalmResearchTheme
try:
    theme = CalmResearchTheme()
    print('✓ Theme loads successfully')
except Exception as e:
    print(f'✗ Theme load failed: {e}')
"
```

### CSS Variables Not Applied

1. Check browser DevTools → Inspect Element
2. Verify Gradio version ≥6.10.0
3. Check for conflicting CSS in `custom_css`
4. Clear browser cache

### Dark Mode Not Working

1. Verify `enable_dark_mode=True` in theme config
2. Check browser console for JavaScript errors
3. Verify localStorage is enabled in browser
4. Test in incognito/private mode (may be cache issue)

### Performance Issues

If theme load time exceeds 100ms:

1. Check system resources (CPU, memory)
2. Profile Python startup: `python -m cProfile ui/app.py`
3. Consider caching theme instance
4. File GitHub issue if persistent

### Browser Compatibility Issues

Test in all supported browsers:

```bash
# Supported browsers: Chrome, Firefox, Safari, Edge
# Test checklist:
# - [ ] Colors render correctly
# - [ ] Dark mode toggle works
# - [ ] Spacing is consistent
# - [ ] Fonts load properly
# - [ ] No console errors
```

## Support & Escalation

### Reporting Issues

When reporting theme issues, include:

```
- Gradio version: `pip list | grep gradio`
- Python version: `python --version`
- Browser & OS: Chrome 120.0 on Windows 11
- Theme configuration: Primary hue=blue, spacing=md
- Error message/screenshots
```

### Resolution Paths

1. **Visual glitch** → Check theme parameters, clear cache, test in different browser
2. **Performance** → Monitor theme load time, check system resources
3. **Accessibility** → Run contrast tests, verify WCAG AA compliance
4. **Integration** → Check Gradio component compatibility, verify theme application

## Related Documentation

- [Theme Customization Guide](./customization-guide.md) - User customization options
- [Quickstart Guide](./quickstart.md) - Basic usage for developers
- [Specification](./spec.md) - Feature requirements and acceptance criteria
- [Advanced Styling Guide](./advanced-styling-guide.md) - CSS patterns and extensions
