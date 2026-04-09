# Advanced Styling Guide - Custom CSS for CalmResearchTheme

**Version**: 1.0  
**Audience**: Designers, Frontend Developers, Advanced Customizers  
**Purpose**: Provide custom CSS patterns and examples for extending the CalmResearchTheme

---

## Overview

The CalmResearchTheme supports custom CSS extensions through Gradio's `css` parameter. This guide demonstrates patterns for advanced visual customization without breaking the theme's defaults or accessibility standards.

## Design Philosophy

- **Layer on top**: Custom CSS extends the theme, never replaces core variables
- **Use CSS variables**: Reference theme colors via CSS custom properties
- **Maintain accessibility**: Preserve contrast ratios and focus indicators
- **Test across browsers**: Verify patterns work in Chrome, Firefox, Safari, Edge
- **Document examples**: Provide real-world patterns for common scenarios

## CSS Variables Reference

The CalmResearchTheme exposes these CSS custom properties for use in custom CSS:

### Color Variables

```css
/* Primary Colors */
--primary-50: #F0F9FF;
--primary-100: #E0F2FE;
--primary-200: #BAE6FD;
--primary-300: #7DD3FC;
--primary-400: #38BDF8;
--primary-500: #0EA5E9;  /* Standard */
--primary-600: #0284C7;  /* Hover */
--primary-700: #0369A1;  /* Active */
--primary-800: #075985;
--primary-900: #0C3D66;

/* Secondary Colors */
--secondary-50: #F8FAFC;
--secondary-100: #F1F5F9;
--secondary-200: #E2E8F0;
--secondary-300: #CBD5E1;
--secondary-400: #94A3B8;
--secondary-500: #64748B;  /* Standard */
--secondary-600: #475569;  /* Hover */
--secondary-700: #334155;  /* Active */
--secondary-800: #1E293B;
--secondary-900: #0F172A;

/* Neutral Colors */
--neutral-50: #F9FAFB;
--neutral-100: #F3F4F6;
--neutral-200: #E5E7EB;
--neutral-300: #D1D5DB;
--neutral-400: #9CA3AF;
--neutral-500: #6B7280;
--neutral-600: #4B5563;
--neutral-700: #374151;
--neutral-800: #1F2937;
--neutral-900: #111827;

/* Semantic Colors */
--success: #10B981;
--warning: #F59E0B;
--error: #EF4444;
--info: #3B82F6;

/* Dark Mode Colors */
--text-light: #F1F5F9;
--background-dark: #0F172A;
--border-dark: #334155;
```

## Common CSS Patterns

### 1. Gradient Backgrounds

Create subtle or bold gradient backgrounds using theme colors:

```css
/* Subtle gradient (research query section) */
#query-section {
    background: linear-gradient(
        135deg,
        var(--primary-50) 0%,
        var(--primary-100) 100%
    );
    border-radius: 8px;
    padding: 24px;
    border: 1px solid var(--primary-200);
}

/* Bold gradient (hero banner) */
#research-hero {
    background: linear-gradient(
        90deg,
        var(--primary-600) 0%,
        var(--primary-800) 50%,
        var(--secondary-700) 100%
    );
    color: white;
    padding: 48px 24px;
    border-radius: 12px;
}

/* Diagonal gradient (accent stripe) */
.accent-stripe {
    background: repeating-linear-gradient(
        45deg,
        var(--primary-100),
        var(--primary-100) 10px,
        var(--primary-50) 10px,
        var(--primary-50) 20px
    );
    padding: 16px;
    border-left: 4px solid var(--primary-600);
}
```

### 2. Glassmorphism Effect

Create frosted glass effect using backdrop blur and transparency:

```css
/* Frosted glass card */
.glass-card {
    background: rgba(241, 245, 249, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(100, 116, 139, 0.2);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* Dark mode glassmorphism */
@media (prefers-color-scheme: dark) {
    .glass-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(51, 65, 85, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
}
```

### 3. Animations & Transitions

Add smooth animations to research components:

```css
/* Fade-in animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

#results-section {
    animation: fadeIn 0.3s ease-out;
}

/* Hover scaling */
.result-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
}

.result-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

/* Gradient animation */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.animated-gradient {
    background: linear-gradient(
        270deg,
        var(--primary-500),
        var(--primary-600),
        var(--primary-500)
    );
    background-size: 200% 200%;
    animation: gradientShift 3s ease infinite;
}
```

### 4. Research Summary Card

Styled card for displaying research results with gradient and shadow:

```css
/* Research Summary Card */
.research-summary {
    background: linear-gradient(
        135deg,
        rgba(224, 242, 254, 0.5) 0%,
        rgba(240, 249, 255, 0.8) 100%
    );
    border-left: 4px solid var(--primary-600);
    border-radius: 8px;
    padding: 20px 24px;
    margin: 16px 0;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.1);
    transition: all 0.2s ease;
}

.research-summary:hover {
    box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);
    transform: translateX(4px);
}

.research-summary-title {
    font-weight: 600;
    color: var(--primary-800);
    margin-bottom: 8px;
    font-size: 16px;
}

.research-summary-content {
    color: var(--secondary-700);
    line-height: 1.6;
    font-size: 14px;
}

.research-summary-tags {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    flex-wrap: wrap;
}

.research-tag {
    display: inline-block;
    background: var(--primary-100);
    color: var(--primary-800);
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid var(--primary-200);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    .research-summary {
        background: linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.6) 0%,
            rgba(15, 23, 42, 0.8) 100%
        );
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
    }
    
    .research-summary-title {
        color: #0EA5E9;
    }
    
    .research-summary-content {
        color: var(--text-light);
    }
}
```

### 5. Responsive Layouts with CSS Grid

Create responsive component layouts:

```css
/* Research results grid */
.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

@media (max-width: 768px) {
    .results-grid {
        grid-template-columns: 1fr;
        gap: 12px;
    }
}

/* Two-column layout (query + results) */
.research-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 24px;
    align-items: start;
}

@media (max-width: 1024px) {
    .research-layout {
        grid-template-columns: 1fr;
    }
}
```

### 6. Typography Enhancements

Style text elements with theme colors:

```css
/* Emphasized text */
.research-keyword {
    color: var(--primary-600);
    font-weight: 600;
    padding: 2px 4px;
    background: var(--primary-50);
    border-radius: 4px;
}

/* Info callout */
.info-callout {
    border-left: 4px solid var(--info);
    background: rgba(59, 130, 246, 0.05);
    padding: 12px 16px;
    border-radius: 4px;
    color: var(--secondary-800);
}

/* Warning callout */
.warning-callout {
    border-left: 4px solid var(--warning);
    background: rgba(245, 158, 11, 0.05);
    padding: 12px 16px;
    border-radius: 4px;
    color: var(--secondary-800);
}

/* Success callout */
.success-callout {
    border-left: 4px solid var(--success);
    background: rgba(16, 185, 129, 0.05);
    padding: 12px 16px;
    border-radius: 4px;
    color: var(--secondary-800);
}
```

### 7. Tables & Data Visualization

Style data tables with theme colors:

```css
/* Data table */
.research-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.research-table thead {
    background: linear-gradient(
        90deg,
        var(--primary-600),
        var(--primary-500)
    );
    color: white;
    font-weight: 600;
}

.research-table th {
    padding: 12px 16px;
    text-align: left;
    border: none;
}

.research-table tbody tr {
    border-bottom: 1px solid var(--neutral-200);
    transition: background-color 0.2s ease;
}

.research-table tbody tr:hover {
    background-color: var(--primary-50);
}

.research-table td {
    padding: 12px 16px;
    color: var(--secondary-700);
}

/* Alternating rows */
.research-table tbody tr:nth-child(even) {
    background-color: var(--neutral-50);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    .research-table {
        background: var(--secondary-800);
        color: var(--text-light);
    }
    
    .research-table tbody tr:hover {
        background-color: var(--secondary-700);
    }
    
    .research-table tbody tr:nth-child(even) {
        background-color: var(--secondary-900);
    }
}
```

### 8. Focus States (Accessibility)

Ensure custom CSS maintains accessibility:

```css
/* Custom focus states */
.custom-input:focus {
    outline: 2px solid var(--primary-600);
    outline-offset: 2px;
    box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.1);
}

.custom-button:focus-visible {
    outline: 2px solid var(--primary-600);
    outline-offset: 2px;
}

/* High contrast mode */
@media (prefers-contrast: more) {
    .custom-input:focus {
        outline: 3px solid var(--primary-800);
        outline-offset: 3px;
    }
}
```

## Usage Examples

### Example 1: Research Summary Card in Application

```python
import gradio as gr
from ui.theme.calm_research_theme import CalmResearchTheme

# Custom CSS for research summary cards
custom_css = """
.research-summary {
    background: linear-gradient(135deg, rgba(224, 242, 254, 0.5) 0%, rgba(240, 249, 255, 0.8) 100%);
    border-left: 4px solid var(--primary-600);
    border-radius: 8px;
    padding: 20px 24px;
    margin: 16px 0;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.1);
}

.research-summary:hover {
    box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);
    transform: translateX(4px);
}

.research-summary-title {
    font-weight: 600;
    color: var(--primary-800);
    margin-bottom: 8px;
}

.research-summary-content {
    color: var(--secondary-700);
    line-height: 1.6;
}
"""

with gr.Blocks(theme=CalmResearchTheme(), css=custom_css) as demo:
    gr.Markdown("# Research Results")
    
    # Results displayed in custom styled cards
    result_html = gr.HTML(
        '<div class="research-summary">'
        '<div class="research-summary-title">Finding 1</div>'
        '<div class="research-summary-content">This is a styled research result...</div>'
        '</div>'
    )

demo.launch()
```

### Example 2: Animated Results Display

```python
custom_css = """
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

#results {
    animation: fadeIn 0.3s ease-out;
}

.result-card {
    transition: all 0.2s ease;
    cursor: pointer;
}

.result-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}
"""

with gr.Blocks(theme=CalmResearchTheme(), css=custom_css) as demo:
    # Components that benefit from animation
    results = gr.Markdown(elem_id="results", label="Results")
```

### Example 3: Dark Mode Support

```python
custom_css = """
.research-card {
    background: linear-gradient(135deg, #E0F2FE 0%, #F0FAFF 100%);
    color: var(--secondary-800);
}

@media (prefers-color-scheme: dark) {
    .research-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: var(--text-light);
    }
}
"""
```

## Best Practices

### ✅ Do

- **Use CSS variables**: Reference theme colors via `var(--primary-600)` etc.
- **Test across browsers**: Verify patterns work in all supported browsers
- **Maintain contrast**: Ensure WCAG AA compliance (4.5:1 text contrast)
- **Preserve focus states**: Keep visible focus indicators for accessibility
- **Layer on top**: Add to theme via `css` parameter, don't override
- **Document patterns**: Comment complex animations or layouts

### ❌ Don't

- **Override theme variables**: Use custom properties, don't redefine `:root`
- **Remove focus indicators**: Always maintain visible keyboard navigation
- **Use hardcoded colors**: Reference theme variables instead
- **Ignore dark mode**: Test and support `prefers-color-scheme: dark`
- **Create inaccessible animations**: Respect `prefers-reduced-motion`
- **Add heavy performance**: Keep animations smooth (60fps)

## Responsive Design Patterns

### Mobile-First Grid

```css
/* Start with single column on mobile */
.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
}

/* Two columns on tablet */
@media (min-width: 768px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
}

/* Three columns on desktop */
@media (min-width: 1024px) {
    .grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

## Testing Custom CSS

### Browser Testing Checklist

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (iOS/Android)
- [ ] Mobile Safari (iOS)

### Accessibility Testing

- [ ] Text contrast ≥4.5:1
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Dark mode rendering correct
- [ ] High contrast mode supported
- [ ] Animations respect `prefers-reduced-motion`

### Performance Testing

- [ ] CSS file size reasonable (<50 KB)
- [ ] Animations smooth (60fps)
- [ ] No layout thrashing
- [ ] Transitions/animations performant

## Troubleshooting

### Issue: CSS not applying

**Solution**: 
- Check selector specificity (use `!important` only if necessary)
- Verify elem_id in HTML matches CSS selector
- Check browser DevTools for conflicting styles

### Issue: Colors look wrong in dark mode

**Solution**:
- Use theme CSS variables
- Add `@media (prefers-color-scheme: dark)` rules
- Test in dark mode browser setting

### Issue: Animation performance poor

**Solution**:
- Use `transform` and `opacity` (GPU-accelerated)
- Avoid animating `width/height`
- Keep frame rate steady (60fps)

### Issue: Custom CSS breaks existing components

**Solution**:
- Use specific selectors with elem_id
- Avoid overly broad selectors (e.g., `div` or `*`)
- Test with theme defaults before custom CSS

## Related Documentation

- [Customization Guide](./customization-guide.md) - Parameter customization
- [Quickstart Guide](./quickstart.md) - Basic theme usage
- [Specification](./spec.md) - Feature requirements
- [Admin README](../theme/README.md) - Deployment guide

---

## Additional Resources

- [MDN CSS Gradients](https://developer.mozilla.org/en-US/docs/Web/CSS/gradient)
- [CSS Animations & Transitions](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations)
- [WCAG Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum)
- [Prefers Color Scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
