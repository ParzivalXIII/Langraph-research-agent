# Contracts: Calm Research Theme API

This directory contains JSON schemas defining the contracts for the Calm Research Theme feature.

## Files

- **theme-config.schema.json**: Defines the constructor parameters for `CalmResearchTheme` class
- **theme-output.schema.json**: Documents the 400+ CSS variables output by the theme
- **dark-mode-config.schema.json**: Browser localStorage schema for dark mode user preference
- **mobile-breakpoints.schema.json**: Responsive design breakpoint specifications

## Schema Validation

Use `ajv` or similar JSON schema validator to validate:

```bash
ajv validate -s theme-config.schema.json -d theme-instance.json
```

## Contract Enforcement

- All theme instantiation must conform to `theme-config.schema.json`
- All CSS variable output must conform to `theme-output.schema.json`
- Dark mode state must conform to `dark-mode-config.schema.json`
