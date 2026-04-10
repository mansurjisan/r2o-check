# Changelog

## [0.1.0] - 2026-04-10

### Added — Phase 2: Naming conventions, conditional structure, repo_type

- **`repo_type` config field**: `operational_model` (default), `workflow`, `tool`,
  `library`, `model_source`. Rules declare `applies_to` repo types; the runner skips
  non-applicable rules. r2o-check's own repo uses `repo_type: tool`.
- **`@register_rule` decorator** now supports `applies_to` parameter with proper
  `@overload` typing for both bare and parameterized usage.
- **6 conditional structure rules** (R2OSTR009–R2OSTR014): `doc/`, `exec/`, `fix/`,
  `lib/`, `gempak/`, `parm/wmo/` at WARN severity. `exec/` escalates to FAIL when
  `sorc/` contains Fortran or C/C++ sources.
- **4 naming convention rules** (R2ONAM001–R2ONAM004):
  - R2ONAM001: J-job naming (`JMODEL_TASK`, all caps, no extension) per §IV.C
  - R2ONAM002: Ex-script naming (`exmodel_task.sh`, all lowercase) per §IV.C
  - R2ONAM003: Modulefile format (`.lua` extension required) per §VI.A.5
  - R2ONAM004: Version file presence (`run.ver`, `build.ver`) and format per §VI.B
- **New test fixtures**: `rrfs_style/` (RRFS-workflow patterns), `stofs_style/`
  (STOFS-operational patterns), `bad_naming/` (naming violations), `tool_repo/`
  (repo_type filtering).
- **Self-check**: root `.r2o-check.yml` sets `repo_type: tool`; CI runs
  `r2o-check lint .` and passes cleanly.
- 98 tests, 97% coverage.

### Changed

- CLAUDE.md updated: NCO section refs corrected to Roman numerals (§VI.B Table 3),
  Phase 2 scope expanded with conditional structure rules and repo_type concept.

### Added — Phase 1: Core engine + structure checks

- Core lint engine (`engine.py`): `LintResult` dataclass, `Status` enum, `LintRunner`
  class with rule discovery and execution, `@register_rule` decorator.
- Configuration loader (`config.py`): reads `.r2o-check.yml` with schema validation.
- 8 directory structure rules (`rules/structure.py`): R2OSTR001–R2OSTR008 per NCO v11.0
  Section VI.B, Table 3.
- CLI entry point (`cli.py`): `r2o-check lint <path>` using Click.
- Rich table formatter (`formatters/cli_table.py`).
- Test fixtures and pytest suite.
- CI workflow: ruff, mypy, pytest on Python 3.9/3.12.
