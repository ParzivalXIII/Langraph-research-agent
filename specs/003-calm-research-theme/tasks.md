# Tasks: Professional Calm Research Gradio UI Theme

**Feature**: 003-calm-research-theme  
**Specification**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)  
**Status**: Ready for Implementation  
**Generated**: April 9, 2026

---

## Execution Strategy

### Implementation Approach

- **MVP Focus**: Start with US1 (Calm Interface) - delivers core visual improvement with <2 days of work
- **Incremental Delivery**: Each user story independently testable; complete US1 → US3 → US2 → US4
- **Parallel Opportunities**: Test infrastructure and documentation can be scaffolded while implementing theme class
- **Milestone**: US1 + US3 = Production-ready calm research interface (all P1 requirements met)

### Dependency Graph

```
Phase 1: Setup
    ↓
Phase 2: Theme Foundation
    ├→ US1: Calm Interface (depends on Phase 2)
    ├→ US3: Research Styling (depends on Phase 2)
    ├→ US2: Customization (parallel, depends on Theme Foundation)
    └→ US4: Fine-Grained Control (parallel, depends on Phase 2)
Phase 5: Polish & Cross-Cutting
```

### Parallel Execution Examples

**Day 1 Morning - Theme Implementation Pair**:

- Developer A: T005-T007 (CalmResearchTheme class, constructor, color palette)
- Developer B: T003-T004 (Test infrastructure, fixtures)
- Run in parallel; merge when complete

**Day 1 Afternoon - Integration & Testing**:

- Developer A: T008-T010 (Dark mode, research styling)
- Developer B: T011-T013 (Integration tests, accessibility audit)
- Blocks on Day 1 Morning completion

**Day 2 - Customization & Polish**:

- Developer A: T014-T016 (Custom CSS support, admin docs)
- Developer B: T017-T019 (Performance verification, browser testing)
- Both parallel; can proceed while US1 testing continues

---

## Phase 1: Setup & Infrastructure

### Phase Goal

Prepare project structure and verify prerequisites

### Independent Test Criteria

- ✅ Feature branch exists and is tracked (`git branch` shows 003-calm-research-theme)
- ✅ Directory structure created (`ui/theme/`, `tests/ui/`)
- ✅ Dependencies verified in pyproject.toml (Gradio 6.10.0+)
- ✅ Test framework ready (pytest installed, conftest.py accessible)

**Tests**: None required for this phase (infrastructure)

### Tasks

- [x] T001 Create feature branch and initialize project structure per plan.md
- [x] T002 Create `ui/theme/` directory with `__init__.py` skeleton
- [x] T003 Create `tests/ui/` directory with test infrastructure (conftest.py, fixtures)
- [x] T004 Verify Gradio 6.10.0+ available via `pip list | grep gradio`
- [x] T005 Update project root `.gitignore` to exclude theme build artifacts (*.pyc, **pycache**)
- [x] T006 Document setup instructions in team wiki or README if needed

---

## Phase 2: Theme Foundation (Blocking - All Stories Depend)

### Phase Goal

Implement `CalmResearchTheme` base class inheriting from `gr.themes.Base`

### Independent Test Criteria

- ✅ Theme class instantiates with default parameters without errors
- ✅ Theme class instantiates with custom parameters (primary_hue, spacing_size, etc.)
- ✅ Theme CSS variables are set correctly (verified by inspecting theme object)
- ✅ Theme loads in Gradio app with no console errors or visual artifacts
- ✅ Theme file size < 50KB

**Tests**: 3 unit tests required in this phase

1. `tests/ui/test_theme_instantiation.py::test_theme_default_parameters`
2. `tests/ui/test_theme_instantiation.py::test_theme_custom_parameters`
3. `tests/ui/test_theme_instantiation.py::test_theme_css_variables_set`

### Tasks

- [x] T007 [P] Implement `CalmResearchTheme` class in `ui/theme/calm_research_theme.py` inheriting from `gr.themes.Base`
- [x] T008 [P] Define color palette constants in `CalmResearchTheme` using design tokens from data-model.md
- [x] T009 [P] Implement `__init__` constructor with parameters: primary_hue, secondary_hue, neutral_hue, spacing_size, radius_size, text_size, font_primary, font_mono, enable_dark_mode
- [x] T010 [P] Configure Gradio CSS variables via `.set()` method for all core component types (buttons, inputs, labels, panels)
- [x] T011 [P] Add dark mode CSS variables (primary_**dark, secondary***dark, neutral**_dark, text_light_on_dark)
- [x] T012 [P] Export `CalmResearchTheme` from `ui/theme/__init__.py` for public API
- [x] T013 Write unit test: `test_theme_default_parameters` verifying instantiation with defaults (tests/ui/test_theme_instantiation.py)
- [x] T014 Write unit test: `test_theme_custom_parameters` verifying custom constructor args are honored (tests/ui/test_theme_instantiation.py)
- [x] T015 Write unit test: `test_theme_css_variables_set` verifying CSS variables dict is populated (tests/ui/test_theme_instantiation.py)
- [x] T016 Run unit tests and verify all pass: `pytest tests/ui/test_theme_instantiation.py -v`
- [x] T017 Measure theme load time and verify <100ms overhead (use browser DevTools Performance tab)

---

## Phase 3: User Story 1 - Calm Focused Interface (Priority: P1)

### Phase Goal

Implement Professional Calm color palette and verify visual improvements in researchers' workflow

### Story Acceptance Criteria

1. **Given** app launches with CalmResearchTheme, **Then** cool blue/teal/gray color palette is visually apparent
2. **Given** user performs research query, **Then** result display area is visually distinct and attractive
3. **Given** user works for extended periods, **Then** interface causes no visual eye strain

### Independent Test Criteria

- ✅ Theme applies to all Gradio components (buttons, inputs, labels, panels)
- ✅ Color contrast ratios verified ≥4.5:1 (WCAG AA normal text)
- ✅ Professional calm aesthetic perceived in before/after comparison
- ✅ Browser compatibility verified (Chrome, Firefox, Safari, Edge)

**Tests**: 2 tests required in this phase

1. `tests/ui/test_theme_colors_contrast.py::test_wcag_aa_contrast_ratios`
2. `tests/ui/test_theme_visual.py::test_browser_compatibility`

### Tasks

- [x] T018 [US1] Integrate `CalmResearchTheme` into `ui/app.py` via `gr.Blocks(theme=CalmResearchTheme())`
- [x] T019 [US1] Launch app and verify theme applies: `python ui/app.py`
- [x] T020 [US1] Verify all Gradio components render with calm color palette (buttons, textboxes, dropdowns, sliders)
- [x] T021 [US1] Write WCAG AA contrast test in `tests/ui/test_theme_colors_contrast.py` verifying text contrast ≥4.5:1
- [ ] T022 [US1] Run contrast validation using axe DevTools or similar in each browser
- [ ] T023 [US1] Document before/after screenshots comparing default Gradio theme vs. CalmResearchTheme
- [ ] T024 [US1] Verify theme in Chrome, Firefox, Safari, Edge; document any browser-specific rendering issues
- [ ] T025 [US1] Get stakeholder visual approval of calm interface aesthetic

---

## Phase 4: User Story 3 - Research Interface Styling (Priority: P1+)

### Phase Goal

Implement research-specific component styling for query input, results, controls, and sources

### Story Acceptance Criteria

1. **Given** query input section visible, **Then** it has distinct styling (background, padding, borders)
2. **Given** results displayed, **Then** key elements have clear visual hierarchy
3. **Given** research controls present, **Then** they are visually grouped and distinctly styled

### Independent Test Criteria

- ✅ Query input section has distinct visual treatment (background color, padding, border-radius)
- ✅ Results display has header/summary/details hierarchy
- ✅ Controls panel visually grouped (background, borders, spacing)
- ✅ Sources table has readable formatting with proper contrast

**Tests**: 2 tests required in this phase

1. `tests/ui/test_theme_research_components.py::test_query_input_styling`
2. `tests/ui/test_theme_research_components.py::test_results_display_styling`

### Tasks

- [x] T026 [P] [US3] Create `ui/styles/research_interface.css` with research-specific component styling
- [ ] T027 [US3] Implement query input section styling: background `#F9FAFB`, padding `16px`, border-radius `8px`, prominent submit button
- [ ] T028 [US3] Implement results display styling: card layout, summary text bold/large, key points bulleted with background
- [ ] T029 [US3] Implement controls panel styling: grouped with background `#F3F4F6`, borders, logical spacing
- [ ] T030 [US3] Implement sources/citations table styling: header background, alternating row colors, link underlines
- [ ] T031 [P] [US3] Add CSS to theme via `custom_css` attribute in `CalmResearchTheme`
- [x] T032 [US3] Add elem_id attributes to research components in `ui/app.py` for CSS targeting (query-section, results-section, controls-section, sources-section)
- [ ] T033 [US3] Write test: `test_query_input_styling` verifying query section has distinct background (tests/ui/test_theme_research_components.py)
- [ ] T034 [US3] Write test: `test_results_display_styling` verifying results have header styling (tests/ui/test_theme_research_components.py)
- [ ] T035 [US3] Take screenshots of each research component and verify visual distinction
- [ ] T036 [US3] Verify research interface styling doesn't break layout responsiveness

---

## Phase 5: User Story 2 - Theme Customization (Priority: P2)

### Phase Goal

Verify theme parameters can be customized and changes apply to UI

### Story Acceptance Criteria

1. **Given** developer creates custom theme with modified primary_hue, **Then** primary color elements update
2. **Given** developer sets custom spacing_size, **Then** component spacing reflects change
3. **Given** developer specifies custom fonts, **Then** chosen fonts render

### Independent Test Criteria

- ✅ Custom theme instance created with non-default parameters
- ✅ Custom parameters are applied to CSS variables
- ✅ Customization affects rendered UI visibly
- ✅ Multiple theme instances can coexist without conflicts

**Tests**: 2 tests required in this phase

1. `tests/ui/test_theme_customization.py::test_custom_primary_hue`
2. `tests/ui/test_theme_customization.py::test_custom_spacing`

### Tasks

- [ ] T037 [US2] Write documentation: "Theme Customization Guide" in `specs/003-calm-research-theme/customization-guide.md` with code examples
- [ ] T038 [US2] Create example: Custom theme with different primary_hue in `tests/fixtures/custom_theme_example.py`
- [ ] T039 [US2] Create example: Custom theme with larger spacing in `tests/fixtures/custom_theme_example.py`
- [ ] T040 [US2] Write test: `test_custom_primary_hue` creating theme with primary_hue="sky" and verifying CSS var set (tests/ui/test_theme_customization.py)
- [ ] T041 [US2] Write test: `test_custom_spacing` creating theme with spacing_size="lg" and verifying CSS var set (tests/ui/test_theme_customization.py)
- [ ] T042 [US2] Create admin/maintainer documentation on how to deploy with custom theme parameters (README for theme module)
- [ ] T043 [US2] Verify theme documentation available in `quickstart.md` section 3 (Advanced Customization)

---

## Phase 6: User Story 4 - Fine-Grained Visual Control (Priority: P3)

### Phase Goal

Support custom CSS extensions and verify they integrate without conflicts

### Story Acceptance Criteria

1. **Given** designer adds custom CSS via theme.custom_css, **Then** custom styles apply without breaking defaults
2. **Given** custom CSS targets elem_id, **Then** styling is visible and functional

### Independent Test Criteria

- ✅ Custom CSS rule applied to theme renders without console errors
- ✅ Custom CSS doesn't override critical theme variables
- ✅ Custom CSS coexists with theme defaults

**Tests**: 1 test required in this phase

1. `tests/ui/test_theme_custom_css.py::test_custom_css_integration`

### Tasks

- [ ] T044 [US4] Create optional advanced styling guide in `specs/003-calm-research-theme/advanced-styling-guide.md` with custom CSS patterns
- [ ] T045 [US4] Document common custom CSS patterns: gradients, animations, advanced layouts
- [ ] T046 [US4] Provide example custom_css for a "research summary card" with gradient background
- [ ] T047 [US4] Write test: `test_custom_css_integration` adding custom CSS rule and verifying no console errors (tests/ui/test_theme_custom_css.py)
- [ ] T048 [US4] Verify custom CSS examples work in multiple browsers

---

## Phase 7: Dark Mode & Accessibility

### Phase Goal

Implement user-selectable dark mode with localStorage persistence and verify accessibility compliance

### Independent Test Criteria

- ✅ Dark mode toggle component renders without errors
- ✅ Toggle switches between light/dark mode visibly
- ✅ Dark mode preference persists across page reload
- ✅ All text contrast ratios ≥4.5:1 in dark mode
- ✅ Focus indicators visible in both modes
- ✅ Keyboard navigation works (Tab, Enter, Escape)

**Tests**: 3 tests required in this phase

1. `tests/ui/test_dark_mode_toggle.py::test_toggle_renders`
2. `tests/ui/test_dark_mode_toggle.py::test_dark_mode_persistence`
3. `tests/ui/test_dark_mode_toggle.py::test_wcag_aa_dark_mode_contrast`

### Tasks

- [ ] T049 Implement dark mode toggle component in `ui/components/theme_controls.py` with checkbox UI
- [ ] T050 Implement JavaScript dark mode handler with localStorage persistence (see quickstart.md section 4)
- [ ] T051 Add dark mode CSS variables to `CalmResearchTheme` (dark_background, text_light_on_dark, etc.)
- [ ] T052 Integrate dark mode toggle into `ui/app.py` app layout
- [ ] T053 Write test: `test_toggle_renders` verifying dark mode toggle component instantiates (tests/ui/test_dark_mode_toggle.py)
- [ ] T054 Write test: `test_dark_mode_persistence` verifying localStorage stores/retrieves preference (tests/ui/test_dark_mode_toggle.py)
- [ ] T055 Write test: `test_wcag_aa_dark_mode_contrast` verifying dark mode meets WCAG AA (≥4.5:1 text contrast) (tests/ui/test_dark_mode_toggle.py)
- [ ] T056 Manually verify dark mode toggle works: Check DevTools → Application → localStorage for calmResearchTheme key
- [ ] T057 Verify dark mode rendering in light/dark browser settings
- [ ] T058 Test keyboard navigation: Tab to dark mode toggle, Enter to toggle, Shift+Tab to return focus

---

## Phase 8: Mobile Responsiveness

### Phase Goal

Verify theme renders correctly at mobile (375px), tablet (768px), and desktop (1920px) breakpoints

### Independent Test Criteria

- ✅ Theme renders without layout breaking at 375px viewport
- ✅ Theme renders without layout breaking at 768px viewport
- ✅ Theme renders correctly at 1920px viewport
- ✅ Text remains readable at all breakpoints
- ✅ Touch targets ≥44px on mobile

**Tests**: 1 test required in this phase

1. `tests/ui/test_responsive_design.py::test_mobile_breakpoints`

### Tasks

- [ ] T059 Test mobile viewport (375px) using Chrome DevTools device emulation: iPhone SE
- [ ] T060 Test tablet viewport (768px) using Chrome DevTools device emulation: iPad
- [ ] T061 Test desktop viewport (1920px) using Chrome DevTools responsive mode
- [ ] T062 Verify component spacing scales down on mobile (space_md → space_sm)
- [ ] T063 Verify font sizes remain readable: body text ≥14px on mobile
- [ ] T064 Verify touch targets ≥44px on mobile (buttons, sliders, dropdowns)
- [ ] T065 Write test: `test_mobile_breakpoints` with media query validation (tests/ui/test_responsive_design.py)
- [ ] T066 Document responsive breakpoints in README or theme module docstring
- [ ] T067 Test layout on actual mobile devices or use responsive testing service

---

## Phase 9: Integration & Performance

### Phase Goal

Integrate theme fully with existing research agent and verify performance

### Independent Test Criteria

- ✅ All existing research agent functionality works unchanged (query submission, results display, filtering)
- ✅ Theme load time <100ms additional overhead
- ✅ No console errors or warnings
- ✅ No visual regressions in existing components

**Tests**: 2 tests required in this phase

1. `tests/api/test_research_endpoint.py` (existing tests must pass with theme applied)
2. `tests/ui/test_theme_performance.py::test_theme_load_time`

### Tasks

- [ ] T068 [P] Run full test suite with theme applied: `pytest tests/ -v`
- [ ] T069 [P] Verify API tests pass: `pytest tests/api/ -v`
- [ ] T070 [P] Verify integration tests pass: `pytest tests/integration/ -v`
- [ ] T071 Measure theme instantiation performance: Add timing logs to CalmResearchTheme.**init**()
- [ ] T072 Write test: `test_theme_load_time` verifying theme loads in <100ms (tests/ui/test_theme_performance.py)
- [ ] T073 Profile app startup time with theme applied (baseline vs. theme added)
- [ ] T074 Verify no console errors when launching `python ui/app.py`
- [ ] T075 Verify no console warnings about missing fonts or CSS
- [ ] T076 Test research workflow end-to-end: Submit query → Display results → Filter by depth/time

---

## Phase 10: Accessibility & Compliance

### Phase Goal

Verify WCAG AA compliance and accessibility for all users

### Independent Test Criteria

- ✅ All text contrast ≥4.5:1 (WCAG AA normal)
- ✅ All form labels associated with inputs
- ✅ Focus indicators visible on all interactive elements
- ✅ Keyboard navigation works for all controls
- ✅ Screen reader can read all content
- ✅ No color-only information conveyed

**Tests**: 2 tests required in this phase

1. `tests/ui/test_theme_accessibility.py::test_wcag_aa_compliance`
2. `tests/ui/test_theme_accessibility.py::test_keyboard_navigation`

### Tasks

- [ ] T077 Install axe DevTools browser extension (Chrome) or use WAVE tool
- [ ] T078 Run axe DevTools scan on app with theme applied
- [ ] T079 Document all contrast ratios in theme color palette (primary, secondary, neutral, semantic colors)
- [ ] T080 Verify color contrast for all interactive elements (buttons, links, labels)
- [ ] T081 Test focus indicators: Tab through all interactive elements, verify visible focus state
- [ ] T082 Test keyboard navigation: Submit via Enter, navigate dropdowns with arrows, close modals with Escape
- [ ] T083 Write test: `test_wcag_aa_compliance` with contrast ratio assertions (tests/ui/test_theme_accessibility.py)
- [ ] T084 Write test: `test_keyboard_navigation` verifying focus management (tests/ui/test_theme_accessibility.py)
- [ ] T085 Test with screen reader (NVDA, JAWS, or VoiceOver) to verify context and labels readable
- [ ] T086 Document accessibility features in theme README

---

## Phase 11: Documentation & Examples

### Phase Goal

Provide comprehensive documentation for theme usage, customization, and troubleshooting

### Independent Test Criteria

- ✅ Quickstart guide enables new developer to use theme in <10 minutes
- ✅ API reference documents all constructor parameters
- ✅ Code examples are runnable and correct
- ✅ Troubleshooting guide addresses common issues

**Tests**: None required for this phase (documentation)

### Tasks

- [ ] T087 Review and update `quickstart.md` with final code examples
- [ ] T088 Create API reference documenting `CalmResearchTheme` class and all parameters
- [ ] T089 Add code example: "Minimal theme application" (Theme → Blocks → launch)
- [ ] T090 Add code example: "Custom theme with different primary color"
- [ ] T091 Add code example: "Theme with custom CSS for advanced styling"
- [ ] T092 Create troubleshooting guide addressing:
  - Theme doesn't apply
  - Colors don't match expected palette
  - Dark mode toggle not working
  - Responsive layout broken on mobile
  - Fonts not loading
- [ ] T093 Add FAQs to theme README
- [ ] T094 Create diagram: Theme class inheritance and CSS variable flow
- [ ] T095 Document design decisions in `research.md` section 10 (References)

---

## Phase 12: Polish & Cross-Cutting Concerns

### Phase Goal

Final verification, quality assurance, and release preparation

### Independent Test Criteria

- ✅ All 9 FRs verified as complete
- ✅ All 8 SCs verified as passing
- ✅ All 4 user stories tested and accepted
- ✅ Code adheres to project standards (PEP 8, type hints, docstrings)
- ✅ Dependencies are minimal and specified in pyproject.toml
- ✅ No breaking changes to existing code

**Tests**: Full regression suite must pass

### Tasks

- [ ] T096 [P] Run full test suite one final time: `pytest tests/ -v --cov`
- [ ] T097 [P] Verify code coverage for theme module >80%: `pytest tests/ui/ --cov=ui/theme`
- [ ] T098 [P] Run linters: `black`, `ruff`, `mypy` on `ui/theme/` and `ui/components/theme_controls.py`
- [ ] T099 [P] Add type hints to all CalmResearchTheme methods and parameters
- [ ] T100 [P] Add comprehensive docstrings to CalmResearchTheme class and all public methods
- [ ] T101 Verify all 9 FRs against implementation:
  - [ ] FR-001: Color palette defined ✓
  - [ ] FR-002: Constructor parameters customizable ✓
  - [ ] FR-003: Research components styled distinctly ✓
  - [ ] FR-004: Gradio components styled consistently ✓
  - [ ] FR-005: Dark mode supported with toggle ✓
  - [ ] FR-006: Custom CSS supported via custom_css attr ✓
  - [ ] FR-007: Theme shareable/reproducible ✓
  - [ ] FR-008: WCAG AA accessibility met ✓
  - [ ] FR-009: Existing functionality unchanged ✓
- [ ] T102 Verify all 8 SCs passing:
  - [ ] SC-001: Renders in all browsers ✓
  - [ ] SC-002: Research components visually distinct ✓
  - [ ] SC-003: Theme reproducible across sessions ✓
  - [ ] SC-004: Research agent functionality unchanged ✓
  - [ ] SC-005: Theme loads in <100ms ✓
  - [ ] SC-006: WCAG AA contrast met ✓
  - [ ] SC-007: Customizable parameters work ✓
  - [ ] SC-008: Custom CSS integrates without errors ✓
- [ ] T103 Create release checklist and verify all items complete
- [ ] T104 Prepare pull request describing changes:
  - Summary of feature (calm theme implementation)
  - Files changed and impact
  - Testing performed
  - Screenshots/before-after comparison
  - Migration/breaking changes (none expected)
- [ ] T105 Get stakeholder approval before merge
- [ ] T106 Merge feature branch to main: `git merge 003-calm-research-theme`
- [ ] T107 Tag release: `git tag -a v1.0.0-calm-theme -m "Calm Research Theme v1.0.0"`
- [ ] T108 Update project README or CHANGELOG with theme feature announcement

---

## Task Summary

**Total Tasks**: 108  
**Phases**: 12  

### Task Distribution by Phase

- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundation): 11 tasks
- Phase 3 (US1 - Calm Interface): 8 tasks
- Phase 4 (US3 - Research Styling): 11 tasks
- Phase 5 (US2 - Customization): 7 tasks
- Phase 6 (US4 - Fine-Grained Control): 5 tasks
- Phase 7 (Dark Mode & Accessibility): 10 tasks
- Phase 8 (Mobile Responsiveness): 9 tasks
- Phase 9 (Integration & Performance): 9 tasks
- Phase 10 (Accessibility & Compliance): 10 tasks
- Phase 11 (Documentation): 9 tasks
- Phase 12 (Polish & Release): 13 tasks

### Task Distribution by User Story

- **US1 (P1 - Calm Interface)**: T018-T025, T057-T058 (10 tasks)
- **US3 (P1+ - Research Styling)**: T026-T036 (11 tasks)
- **US2 (P2 - Customization)**: T037-T043 (7 tasks)
- **US4 (P3 - Fine-Grained Control)**: T044-T048 (5 tasks)
- **Blocking/Cross-cutting**: T001-T017, T049-T108 (70 tasks)

### Test Tasks Count

- **Total Tests**: 13 test suites across 8 files
- **Unit Tests**: 3 (theme instantiation, customization, CSS integration)
- **Integration Tests**: 4 (research components, dark mode, responsiveness, performance)
- **Accessibility Tests**: 2 (contrast, keyboard navigation)
- **Regression Tests**: 4 (endpoint tests, etc.)

### Parallelizable Tasks [P]

- T005, T007-T015, T026-T031, T057, T059-T067, T068-T070, T096-T100 (17 tasks can run in parallel)

---

## Suggested MVP Scope

**Minimum Viable Product** for Production Release:

- **Phases Required**: 1, 2, 3, 4, 7, 9, 12
- **Tasks Required**: T001-T025, T026-T036, T049-T076, T096-T108 (~80 tasks)
- **User Stories**: US1 (P1) + US3 (P1+) + partial Phase 7 dark mode
- **Estimated Duration**: 3-4 days for small team
- **Delivery Value**: Calm interface + research-specific styling + dark mode + full accessibility + integration verified

**Full Feature Completion**:

- All 12 phases, all 108 tasks
- All 4 user stories (US1, US3, US2, US4)
- Full customization support + fine-grained CSS control
- Estimated Duration: 5-6 days for small team

---

## Dependencies & Critical Path

**Critical Path** (blocking all other work):

1. T001-T005: Setup & structure
2. T007-T017: Theme foundation
3. T018-T025: US1 integration & visual approval
4. T049-T058: Dark mode implementation

**Can start in parallel with critical path**:

- T026-T036: US3 research styling (after T015)
- T037-T043: US2 customization (after T017)
- T044-T048: US4 fine-grained control (after T017)

---

## Exit Criteria (Definition of Done)

✅ **All Tasks Complete**

- [ ] All 108 tasks marked complete and tested
- [ ] All test suites passing (pytest exit code 0)
- [ ] Code coverage >80% for ui/theme module

✅ **Requirements Met**

- [ ] All 9 FRs verified (FR-001 through FR-009)
- [ ] All 8 SCs passing (SC-001 through SC-008)
- [ ] All edge cases from spec addressed

✅ **Quality Gates**

- [ ] No console errors or warnings
- [ ] WCAG AA compliance verified (contrast, focus, keyboard)
- [ ] Performance verified <100ms overhead
- [ ] No regressions in existing tests

✅ **Documentation Complete**

- [ ] Quickstart guide finalized
- [ ] API documentation published
- [ ] Troubleshooting guide created
- [ ] Code examples working and tested

✅ **Approved & Merged**

- [ ] PR reviewed and approved by stakeholders
- [ ] Code review checklist completed
- [ ] Feature branch merged to main
- [ ] Release tagged and published

---

**Next Step**: Start Phase 1 (Setup & Infrastructure)  
**Command**: Run `uv run pytest tests/ui/ -v` after implementing first tests in Phase 2
