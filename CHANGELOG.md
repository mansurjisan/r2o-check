# Changelog

## [Unreleased]

### Added

- **Baseline hygiene**:
  - `Baseline.find_stale()` returns fingerprints present in the
    baseline but absent from the current run (findings that were
    fixed upstream). `lint --baseline` now prints a stderr warning
    when stale entries are detected, so a latent regression on a
    different line cannot be silently masked.
  - `r2o-check baseline --update` refreshes an existing baseline,
    dropping stale entries and adding new ones with a
    `+N new, -M resolved` summary.
- **CLI ergonomics on `lint`**:
  - `--fail-on {fail,warn}` — default `fail`; `warn` treats WARN
    results as failures for exit code, for strict CI gates.
  - `--only RULE[,RULE…]` — restrict a run to specific rule IDs,
    useful for rule authors iterating on one rule.
- **R2OCNT006 cp-vs-cpreq check**: bare `cp ` usage inside
  ex-scripts now produces a WARN per offending line, matching the
  rule's documented scope from NCO v11.0 §III.C. Flagged `cp` calls
  are distinct from `cp -<flag>` (which is not emitted).
- **Optional deep ecFlow mode**: new `R2OECF007` rule parses `.def`
  files via the `ecflow` Python binding when available. Surfaced
  through the `r2o-check[ecflow]` extra — the binding is not on PyPI
  and is expected to come from a system package. Missing binding is
  inert, not a compliance failure.

### Changed

- **`LintRunner.run_rules()` pipeline parity**: `run_rules` now
  applies the same post-processing as `run` — disabled rules are
  dropped, inline `r2o-check:disable` suppression is honored, and
  `severity_overrides` rewrites statuses. `applies_to` is also
  respected, so asking for a rule that doesn't apply to the current
  `repo_type` returns no results.
- **Line-numbered findings**: `LintResult` now carries an optional
  `line` field. Rules that scan content line-by-line (`R2OCNT004`,
  `R2OECF004`, `R2OECF005`) emit one result per offending line with
  its line number. Cross-reference rules (`R2OXRF002/003/004`) record
  the line of each call site.
- **Line rendering in formatters**: SARIF `region.startLine` is now
  populated (previously always 1), JSON results include a `line`
  field, HTML reports show a `Location` column with `path:line`, and
  rule messages embed `file:line` wherever the underlying rule knows
  it. SARIF paths are also now relative to the linted repo, not
  `Path.cwd()`.
- **Baseline support** for incremental adoption:
  - `r2o-check baseline <path>` records current `FAIL`/`WARN`
    findings to `.r2o-check-baseline.json` (configurable with `-o`).
    `--force` overwrites an existing baseline.
  - `r2o-check lint --baseline <file>` suppresses any finding whose
    fingerprint (rule_id + relpath + line) appears in the baseline,
    so only *new* violations surface. `PASS` and `ERROR` results
    always pass through.
- **Markdown categories** for `R2OCNT` (Content) and `R2OXRF`
  (Cross-reference) — they no longer fall into the generic "Other"
  group in PR-comment output.

### Fixed

- **Cross-reference rules now strip shell comments**: R2OXRF002,
  R2OXRF003, R2OXRF004, and R2OXRF005 previously treated
  `# ${SCRIPTS}/exfoo.sh` as a real call — producing spurious
  FAILs and, worse, rescuing orphan scripts whose only "caller"
  was commented out. Parity with the environment/content rules.
- **`--only` validates rule IDs**: an unknown rule ID now errors
  out instead of exiting 0 with an empty result set. A typo in a
  CI `--only` list no longer becomes a silent false green.
- **Baseline fingerprint disambiguates same-location findings**:
  fingerprint format bumped to `rule|relpath|line|detail`, where
  `detail` is an 8-char SHA-1 of the distinguishing text
  (message with any leading `file:line:` prefix stripped, so the
  hash is stable when line numbers drift). A baselined
  `R2OXRF002: 'exfoo.sh'` no longer hides a new
  `R2OXRF002: 'exbar.sh'` on the same J-job line. `BASELINE_VERSION`
  is now 2; v1 baselines raise with a regenerate hint.
- **`--only` + `--baseline` stale detection**: stale-entry warnings
  are skipped when `--only` is in effect, so subset runs do not
  mis-report every non-selected baseline entry as stale.
- **R2OCNT004 regex swallowed multiple lines**: the character class
  allowed newlines, so a file with several `cmd &` lines reported
  only one match spanning the whole remainder. Now anchored to a
  single line.
- **Comment stripping in shell-text rules**: `R2OENV001`, `R2OENV002`,
  `R2OCNT001`, `R2OCNT002`, `R2OCNT004`, `R2OCNT006`, and `R2OCNT007` no
  longer treat commented-out lines as compliance signals. Introduced
  `r2o_check._shell.strip_shell_comments` which handles single/double
  quoting and preserves the shebang.
- **Cross-reference path matching (R2OXRF002, R2OXRF004, R2OXRF005)**:
  the call regex now captures optional subdirectory segments, so
  `${SCRIPTS}/sub/exfoo.sh` is recognised. Script identity uses the
  repo-relative path, eliminating the false positives that occurred
  when two scripts shared a basename. Orphan detection resolves each
  call to a single script rather than doing a basename substring search.
- **`r2o-check fix` honors `repo_type`**: scaffolding of `ecf/`, `jobs/`,
  `scripts/`, etc. now only runs for `operational_model` and `workflow`
  repos. `tool`, `library`, and `model_source` repos receive an explicit
  "no auto-fixes apply" message instead of an operational layout.
- **R2OECF005 export exemption**: the hardcoded-path rule now treats
  `export VAR=/lfs/...`, `readonly VAR=...`, `declare`, `local`, and
  `typeset` assignments as assignments, matching the rule's documented
  intent.
- **`lint -o` for the default table format**: table output is now
  written to the given file (as plain text) instead of silently going
  to stdout.

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
