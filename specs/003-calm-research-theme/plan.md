# Implementation Plan: Professional Calm Research Gradio UI Theme

**Branch**: `003-calm-research-theme` | **Date**: April 9, 2026 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-calm-research-theme/spec.md`

## Summary

Create a custom Gradio theme with professional aesthetics and calm color psychology to improve researcher focus and reduce cognitive load during research workflows. The theme leverages Gradio 6.x theming system (inherited from `gr.themes.Base`), is fully customizable via constructor parameters (colors, spacing, fonts), supports light/dark modes with localStorage persistence, and provides research-specific UI styling without modifying existing Python logic. The implementation maintains WCAG AA accessibility standards and loads within 200ms performance budget.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**:

- `gradio>=6.10.0` (UI framework with theming system)
- `structlog>=24.1.0` (structured logging for theme initialization)
  
**Storage**: N/A (UI-only, client-side theme state via localStorage for dark mode toggle)  

**Testing**:

- pytest (unit tests for theme class instantiation)
- Visual regression testing via browser inspection tools
- WCAG contrast ratio validation (axe DevTools or similar)

**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge)  

**Project Type**: Web service (FastAPI backend + Gradio 6 frontend)  

**Performance Goals**:

- Theme load time: <100ms additional overhead vs default Gradio theme
- Theme file size: <50KB CSS + metadata
- Render latency: No additional render delay observed by user

**Constraints**:

- WCAG AA contrast compliance (4.5:1 normal text, 3:1 large text)
- Gradio 5.x/6.x API surface (not Gradio 4.x or earlier)
- No custom font uploads (Google Fonts only)
- Mobile responsive: 375px (phone), 768px (tablet), 1920px (desktop)

**Scale/Scope**:

- Single Gradio theme class (~200–300 lines Python)
- Research-specific component styling (4 major UI regions: query input, results, controls, sources)
- Dark mode toggle with client-side persistence

## Constitution Check

**GATE ZERO: Before Phase 0**

✅ **Determinism over Agentic Creativity**  

- All color choices documented with hex values and rationale
- Theme CSS variables traceable to Gradio 6.x theming API documentation
- No generated/invented styling; all based on Gradio theming guide examples
  
✅ **Retrieval First, Generation Second**  

- Gradio Theming Guide and Custom CSS & JS documentation scraped and referenced
- Color palette based on color psychology best practices (cool hues for calm)
- No assumptions made without supporting evidence from Gradio docs
  
✅ **Bounded Autonomy**  

- Theme implementation has clear termination: "Done when all 9 FRs met + 8 SCs pass"
- Tool usage: No external API calls needed (Gradio local rendering only)
- No speculation on dark mode, mobile, or font sources (all clarified in spec)
  
✅ **Structured Outputs Only**  

- Theme output: Gradio theme class instance with defined CSS variables
- No free-form styling; all via Gradio `gr.themes.Base.set()` method
  
✅ **Observability by Default**  

- Theme initialization logged via structlog
- Browser console warnings logged if fonts fail to load
- Dark mode toggle state persisted to localStorage (observable)
  
✅ **Cost + Latency Constraints**  

- No external dependencies beyond gradio (no design system libraries)
- <200ms load overhead budget established
- No Tavily/LLM calls required for this feature

## Project Structure

### Documentation (this feature)

```text
specs/003-calm-research-theme/
├── spec.md              ✅ Complete specification with 4 user stories, 9 FRs, 8 SCs
├── plan.md              ← You are here
├── research.md          → Phase 0 output (design research deliverable)
├── data-model.md        → Phase 1 output (design tokens, color palette, component specs)
├── quickstart.md        → Phase 1 output (how to use the theme)
├── contracts/           → Phase 1 output (theme interface contracts)
│   ├── README.md
│   ├── theme-config.schema.json    (theme constructor parameters)
│   ├── theme-output.schema.json    (CSS variables output)
│   └── dark-mode-config.schema.json (dark mode toggle persistence)
└── checklists/
    └── requirements.md  ✅ Quality checklist (all items pass)
```

### Source Code (repository)

```text
ui/
├── app.py                    ← Current Gradio app (will integrate theme here)
├── theme/                    ← NEW: Theme module
│   ├── __init__.py
│   └── calm_research_theme.py    (custom theme class, ~250 lines)
├── components/
│   ├── controls.py          (existing: depth dropdown, source slider, time range)
│   ├── results.py           (existing: result formatting)
│   ├── query_input.py       (existing: query textbox)
│   └── theme_controls.py    ← NEW: Dark mode toggle UI component
└── styles/                   ← NEW: Custom CSS (optional, for advanced styling)
    └── research_interface.css   (custom CSS for research-specific elements)

tests/
├── ui/
│   ├── test_theme_instantiation.py     ← NEW
│   ├── test_theme_colors_contrast.py   ← NEW
│   └── test_dark_mode_toggle.py        ← NEW
```

**Structure Decision**: Single theme module (`ui/theme/calm_research_theme.py`) with optional research-specific CSS. Theme class inherits from `gr.themes.Base`, customizes core parameters (colors, spacing, fonts), and provides custom CSS for research component styling. Dark mode toggle component added to existing `ui/components/` structure. No changes to FastAPI backend; UI-only feature.

## Complexity Tracking

No Constitution Check violations identified. All decisions grounded in Gradio documentation and color psychology best practices.
