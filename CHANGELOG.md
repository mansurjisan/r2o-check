# Changelog

## [0.1.0] - 2026-04-10

### Added — Phase 1: Core engine + structure checks

- Core lint engine (`engine.py`): `LintResult` dataclass, `Status` enum, `LintRunner`
  class with rule discovery and execution, `@register_rule` decorator.
- Configuration loader (`config.py`): reads `.r2o-check.yml` with schema validation,
  supports `standards_version`, `disabled_rules`, and `variants`.
- 8 directory structure rules (`rules/structure.py`): R2OSTR001–R2OSTR008 checking for
  `ecf/`, `jobs/`, `scripts/`, `ush/`, `sorc/`, `parm/`, `versions/`, `modulefiles/`
  per NCO v11.0 Section VI.B, Table 3.
- CLI entry point (`cli.py`): `r2o-check lint <path>` using Click.
- Rich table formatter (`formatters/cli_table.py`): coloured pass/fail output with
  summary counts.
- Test fixtures: `compliant_minimal/` (all 8 dirs) and `noncompliant_minimal/` (missing 4 dirs).
- Pytest test suite with >85% coverage target.
- CI workflow: ruff, mypy, pytest on every push.
- Rules documentation in `docs/rules.md`.
