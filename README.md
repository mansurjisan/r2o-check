# r2o-check

**Automated NCO Implementation Standards v11.0 compliance checker for NOAA operational model and workflow code.**

[![CI](https://github.com/mansurjisan/r2o-check/actions/workflows/ci.yml/badge.svg)](https://github.com/mansurjisan/r2o-check/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/r2o-check)](https://pypi.org/project/r2o-check/)
[![Python](https://img.shields.io/pypi/pyversions/r2o-check)](https://pypi.org/project/r2o-check/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

---

r2o-check validates your model package against the [NCO WCOSS Implementation Standards v11.0](https://www.nco.ncep.noaa.gov/idsb/implementation_standards/) before you submit to IDSB. Think of it as **nf-core lint for NOAA operational model delivery**.

## Install

```bash
pip install r2o-check
```

## Usage

```bash
# Lint a repository
r2o-check lint /path/to/your/repo

# Preview auto-fixes for safe violations
r2o-check fix /path/to/your/repo

# Apply fixes
r2o-check fix /path/to/your/repo --apply
```

### Output Formats

```bash
r2o-check lint . --format table      # Rich CLI table (default)
r2o-check lint . --format json       # Structured JSON
r2o-check lint . --format markdown   # PR-comment-ready Markdown
r2o-check lint . --format html -o report.html  # Self-contained HTML
```

### Example Output

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Status     ┃ Rule         ┃ Message                             ┃ Fix hint                ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✔ PASS     │ R2OSTR001    │ Required directory 'ecf/' exists.   │                         │
│ ✔ PASS     │ R2OSTR002    │ Required directory 'jobs/' exists.  │                         │
│ ✘ FAIL     │ R2OSTR008    │ Missing directory 'modulefiles/'.   │ Create 'modulefiles/'   │
│ ✘ FAIL     │ R2OECF001    │ Missing %include <head.h>, <tail.h> │ Add head.h/tail.h       │
└────────────┴──────────────┴─────────────────────────────────────┴─────────────────────────┘
```

## What It Checks

| Category | Rules | What it validates |
|---|---|---|
| **Structure** | R2OSTR001–014 | Required directories: `ecf/`, `jobs/`, `scripts/`, `ush/`, `sorc/`, `parm/`, `versions/`, `modulefiles/`, and 6 conditional dirs |
| **Naming** | R2ONAM001–005 | J-job naming (`JMODEL_TASK`), ex-script naming (`exmodel_task.sh`), modulefile format (`.lua`), ush script naming |
| **Environment** | R2OENV001–002 | J-job environment variables from NCO Table 1 (`NET`, `RUN`, `PDY`, `COMIN`, `COMOUT`, etc.) |
| **Build** | R2OBLD001–002 | Makefile targets (`all`, `debug`, `install`, `clean`) and CMake equivalents |
| **Modules** | R2OMOD001 | Modulefile dependencies (compiler, libraries) |
| **Versions** | R2OVER001–004 | `run.ver` / `build.ver` existence and format |
| **ecFlow** | R2OECF001–006 | `%include <head.h>/<tail.h>`, paired `ecflow_client` calls, trap handlers, PBS/Slurm directives, hard-coded paths |

Every rule cites the specific NCO v11.0 section it enforces. See the [full rules reference](docs/rules.md) and [NCO standards mapping](docs/nco-standards-mapping.md).

## Repo Types

Not all NOAA repos are the same shape. r2o-check auto-filters rules based on your repo type:

```yaml
# .r2o-check.yml
repo_type: operational_model  # all rules apply
```

| Type | Description | Example |
|---|---|---|
| `operational_model` | Full NCO delivery package | STOFS-operational |
| `workflow` | Workflow orchestration | nos-workflow |
| `model_source` | Model source code | ufs-weather-model |
| `library` | Shared library | Build rules only |
| `tool` | Python tool / utility | No rules (clean pass) |

## GitHub Actions

Add NCO compliance checks to any repo:

```yaml
# .github/workflows/r2o-check.yml
name: NCO Compliance
on: [push, pull_request]
jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install r2o-check
      - run: r2o-check lint .
```

## Configuration

```yaml
# .r2o-check.yml
repo_type: workflow
standards_version: "11.0.0"

disabled_rules:
  - R2OSTR013  # No GEMPAK output for this model

ecflow:
  hardcoded_path_prefixes:
    - /lfs/
    - /work/
    - /scratch/
```

## Documentation

| Doc | Description |
|---|---|
| [Quickstart Guide](docs/quickstart.md) | Install, configure, integrate with CI |
| [Rules Reference](docs/rules.md) | Every rule with severity, rationale, examples |
| [NCO Standards Mapping](docs/nco-standards-mapping.md) | Rule ID to NCO v11.0 section table |
| [Contributing](CONTRIBUTING.md) | Dev setup, adding rules, PR checklist |

## License

Apache-2.0. See [LICENSE](LICENSE).
