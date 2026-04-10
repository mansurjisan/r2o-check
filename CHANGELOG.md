# Changelog

## [0.1.0] - 2026-04-10

### Added — Phase 6: Auto-fix, documentation, release prep

- **Auto-fix** (`r2o-check fix <path>`): creates missing required directories
  (R2OSTR001–008) with `.gitkeep`, stubs `versions/run.ver` and `build.ver`
  (R2OVER001/002). `--dry-run` (default) and `--apply` modes. Idempotent.
- **HTML column sorting**: vanilla JS inline sort on click, `aria-sort` attributes.
- **Markdown truncation**: default shows only FAIL/WARN, passes summarized.
  `--markdown-include-passes` flag. 60k character hard truncation.
- **GitHub Action**: now uploads JSON results as workflow artifact.
- **Documentation**: `docs/quickstart.md`, `docs/nco-standards-mapping.md`,
  expanded `README.md`, `CONTRIBUTING.md`.
- **License**: Apache-2.0.
- **PyPI metadata**: complete `pyproject.toml`, `python -m build` + `twine check` pass.
- 194 tests, 97% coverage.

### Added — Phase 5: Formatters, GitHub Action, refinements

**Phase 4 refinements (breaking, pre-release):**
- R2OECF006 (WARN): verify custom `include/head.h`/`tail.h` content for
  `ecflow_client --init`/`--complete`. Skips when files don't exist.
- **Namespaced config sections**: `.r2o-check.yml` now supports `ecflow:`
  namespace with `hardcoded_path_prefixes` field. R2OECF005 reads from config.
- `EcflowConfig` dataclass added to `config.py`.

**Phase 5: Formatters and GitHub Action:**
- **JSON formatter** (`--format json`): structured output with version, repo_type,
  summary counts, and full results array.
- **Markdown formatter** (`--format markdown`): PR-comment-friendly with collapsible
  category sections, emoji status indicators, and summary table.
- **HTML formatter** (`--format html`): self-contained single-file HTML report with
  inline CSS, no external dependencies.
- **`-o`/`--output` flag**: write output to file.
- **GitHub Action** (`action/action.yml`): composite action with `path`,
  `standards-version`, `fail-on`, `config-file` inputs. Posts Markdown PR comment.
- CI: added `action-self-check` job, JSON format self-check.
- 182 tests, 97% coverage.

### Added — Phase 4: ecFlow validation + Phase 3 refinements

**Phase 3 refinements (breaking, pre-release):**
- Split R2OENV001 into R2OENV001 (FAIL, core vars) and R2OENV002 (WARN, context).
- Added R2OBLD002 (CMake build validation, WARN) with mutual exclusion — Makefile
  and CMake rules defer to each other rather than both warning.
- Added `mutually_exclusive_with` parameter to `@register_rule`.
- **Retired R2ONAM004** — merged into R2OVER001 (run.ver presence, FAIL), R2OVER002
  (build.ver presence, FAIL), R2OVER003 (run.ver content, WARN), R2OVER004
  (build.ver content, WARN).

**Phase 4: ecFlow validation (text parsing, no ecflow library required):**
- R2OECF001 (FAIL): .ecf files must contain `%include <head.h>` and `<tail.h>`.
- R2OECF002 (FAIL): paired `ecflow_client --init`/`--complete` (or via head/tail).
- R2OECF003 (FAIL): trap handler set (`trap ... EXIT` or via head.h).
- R2OECF004 (WARN): PBS/Slurm directives well-formed.
- R2OECF005 (WARN): no hard-coded absolute paths outside variable assignments.
- New fixtures: `ecflow_compliant/`, `ecflow_broken/`, `ecflow_hardcoded/`.
- 156 tests, 97% coverage. Repo Type Rule Matrix in CLAUDE.md.

### Added — Phase 3: Environment, build, modules, versions, naming fixes

- **Fixed R2ONAM002** to recurse into `scripts/` subdirectories. Only files
  starting with `ex` are checked. Supports STOFS-style nested layout.
- **R2ONAM005**: ush/ script naming (WARN) — lowercase, no `ex` prefix,
  `.sh`/`.pl`/`.py` extension per §IV.C.
- **R2OENV001**: J-job environment variable checks — verifies NET, RUN, PDY,
  cycle, DATA, COMIN, COMOUT and model-specific vars (USH*, EXEC*, PARM*, FIX*)
  per §III.A Table 1. WARN severity.
- **R2OBLD001**: Makefile target checks — `all`, `debug`, `install`, `clean`
  per §VI.A.8. FAIL severity. Applies to all build repo types.
- **R2OMOD001**: Modulefile dependency checks — build modulefiles must load
  a compiler per §VI.A.4. WARN severity.
- **R2OVER001/R2OVER002**: run.ver/build.ver content validation — `export`
  format, `*_ver` variable naming per §VI.B Table 3. WARN severity.
- **Repo Type Rule Matrix** added to CLAUDE.md as authoritative source for
  `applies_to`. BUILD_REPO_TYPES and MODULE_REPO_TYPES constants in engine.
- New constants: `BUILD_REPO_TYPES`, `MODULE_REPO_TYPES` in engine.py.
- New fixture: `stofs_nested/` for recursive ex-script testing.
- WARN-only justification notes added to docs/rules.md for R2OSTR009, 011–014.
- 128 tests, 97% coverage.

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
