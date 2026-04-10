# r2o-check — Claude Code Development Guide

## Project Vision
Automated NCO Implementation Standards v11.0 compliance checker for NOAA operational
model code. Modeled architecturally on nf-core/tools lint. Target users: every NOAA team
doing R2O delivery (STOFS, RRFS, global-workflow, Land DA, SECOFS, NOSOFS).

Single sentence: "nf-core lint for NOAA operational model delivery."

## Architecture Principles
1. **Rule-based engine**: each NCO requirement is an independently testable Python function
   returning a LintResult (pass/warn/fail + message + fix suggestion).
2. **Config-driven**: `.r2o-check.yml` lets projects disable rules, pin standards version,
   and declare variants.
3. **No heavy dependencies for core lint**: do NOT require the ecFlow Python library for
   basic lint — parse .ecf files as text. ecFlow lib is optional for deep validation.
4. **Multiple output formats**: rich CLI table (default), JSON, Markdown (PR comments), HTML.
5. **GitHub Action wrapper**: `uses: r2o-check/action@v1` must work out of the box.
6. **Self-check**: r2o-check must be able to lint its own repo conventions.

## Tech Stack
- Python 3.9+
- Click (CLI), Rich (output), PyYAML, pytest
- ruff for linting, mypy for type checking
- Packaging: pyproject.toml, hatchling
- CI: GitHub Actions

## Key References
- NCO Implementation Standards v11.0: https://www.nco.ncep.noaa.gov/idsb/implementation_standards/
- nf-core lint source (architectural reference): https://github.com/nf-core/tools/tree/master/nf_core/pipelines/lint
- Reference compliant repos:
  - https://github.com/NOAA-EMC/rrfs-workflow (declares NCO v11.0.0 compliance)
  - https://github.com/noaa-ocs-modeling/STOFS-operational
  - https://github.com/NOAA-EMC/global-workflow

## Development Phases (work one phase at a time, commit at end of each)

### Phase 1 — Core engine + structure checks (MVP, ~1 week)
Deliverables:
- `pyproject.toml` with hatchling, dependencies, entry point `r2o-check`
- `src/r2o_check/engine.py`: `LintResult` dataclass (status, rule_id, message, path, fix_hint),
  `LintRunner` class that discovers and runs rules
- `src/r2o_check/config.py`: loads `.r2o-check.yml` with schema validation
- `src/r2o_check/rules/structure.py`: 8 directory checks mapped to NCO v11.0 §4
  (ecf/, jobs/, scripts/, ush/, sorc/, modulefiles/, versions/, parm/)
- `src/r2o_check/cli.py`: `r2o-check lint <path>` with rich table output
- `src/r2o_check/formatters/cli_table.py`: rich-based table formatter
- `tests/fixtures/compliant_minimal/`: minimal compliant repo fixture
- `tests/fixtures/noncompliant_minimal/`: missing-directory fixture
- `tests/test_structure.py`: pytest tests for every structure rule
- Working end-to-end: `pip install -e . && r2o-check lint tests/fixtures/compliant_minimal`

### Phase 2 — Naming convention checks (~1 week)
- `src/r2o_check/rules/naming.py`: J-job pattern `J<MODEL>_<TASK>`, ex-script pattern
  `ex<model>_<task>.sh`, modulefile naming, versions/ file naming
- Tests against RRFS-workflow and STOFS-operational naming patterns (as fixtures, not live repos)

### Phase 3 — Environment + module + build checks (~1 week)
- `src/r2o_check/rules/environment.py`: parse J-jobs for required env vars from NCO Table 1
  (HOMEmodel, COMROOT, DATAROOT, etc. — enumerate all ~30)
- `src/r2o_check/rules/modules.py`: modulefile structure (compiler, MPI, libs declared)
- `src/r2o_check/rules/build.py`: Makefile must have targets: all, debug, install, clean
- `src/r2o_check/rules/versions.py`: versions/run.ver and versions/build.ver format

### Phase 4 — ecFlow validation (~1-2 weeks)
- `src/r2o_check/rules/ecflow.py`: parse .ecf files as text (no ecflow lib required)
- Checks: `%include <head.h>` and `%include <tail.h>` present, trap handlers set,
  `ecflow_client --init` and `--complete` paired, PBS/Slurm directives well-formed,
  no hard-coded absolute paths in runtime code
- Optional deep mode: if ecflow Python lib is available, parse .def file and validate
  trigger expressions + dependency graph

### Phase 5 — GitHub Action + alt formatters (~1 week)
- `action/action.yml`: composite action taking `path`, `standards-version`, `fail-on` inputs
- `action/entrypoint.sh`: installs r2o-check, runs, posts Markdown comment to PR
- `src/r2o_check/formatters/json_report.py`, `markdown.py`, `html.py`
- Self-hosted test: add `.github/workflows/self-check.yml` that runs r2o-check on itself

### Phase 6 — Auto-fix + release (~1 week)
- `src/r2o_check/fixers/`: auto-create missing directories, stub missing versions/ files
- `r2o-check fix <path> --dry-run` / `--apply`
- Full docs in `docs/`: quickstart.md, rules.md (every rule with rationale + fix),
  nco-standards-mapping.md (rule_id → NCO v11.0 section)
- PyPI release as `r2o-check`, tag v0.1.0

## Rule ID Convention
`R2O<CATEGORY><NNN>` — e.g., `R2OSTR001` (structure), `R2ONAM001` (naming),
`R2OENV001` (environment), `R2OECF001` (ecflow), `R2OMOD001` (modules),
`R2OBLD001` (build), `R2OVER001` (versions).

Every rule must be documented in `docs/rules.md` with: rule_id, severity default,
NCO standards section reference, rationale, example failure, example fix.

## Testing Requirements
- Every rule module has a matching test file
- Fixtures in `tests/fixtures/` represent both compliant and non-compliant patterns
- Integration test: run full lint on fixture repos, assert expected pass/fail counts
- Self-check must pass on the r2o-check repo itself
- Minimum 85% coverage enforced in CI

## Coding Standards
- Type hints on every public function
- Docstrings on every rule function explaining what NCO section it checks
- No hard-coded paths — use `pathlib.Path` throughout
- Rules must be pure functions: `(repo_path: Path, config: Config) -> list[LintResult]`
- Errors in rule execution must not crash the runner — catch and report as `ERROR` status

## Do Not
- Do NOT require network access for core lint (must work fully offline)
- Do NOT require the ecFlow Python library for Phases 1-3
- Do NOT hard-code NOAA-internal paths or hostnames
- Do NOT add rules without a citation to NCO Standards v11.0

## Definition of Done for Each Phase
1. All new rules documented in docs/rules.md
2. Unit tests passing with >85% coverage on new code
3. Self-check (r2o-check lint .) passes or has only intentional warnings
4. CHANGELOG.md updated
5. Phase branch merged to main with a descriptive commit