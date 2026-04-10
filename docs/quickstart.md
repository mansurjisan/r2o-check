# Quickstart Guide

## Installation

```bash
pip install r2o-check
```

For development:
```bash
git clone https://github.com/mansurjisan/r2o-check.git
cd r2o-check
pip install -e ".[dev]"
```

## Basic Usage

Lint a repository:
```bash
r2o-check lint /path/to/your/model/repo
```

The tool will check for NCO Implementation Standards v11.0 compliance
and display a colored table of results.

## Output Formats

```bash
# Default rich table
r2o-check lint .

# JSON (for CI/CD pipelines)
r2o-check lint . --format json

# Markdown (for PR comments)
r2o-check lint . --format markdown

# HTML report (open in browser)
r2o-check lint . --format html -o report.html
```

## Configuration

Create `.r2o-check.yml` in your repository root:

```yaml
# Required: what type of repo is this?
repo_type: operational_model  # or: workflow, tool, library, model_source

# Pin to a standards version
standards_version: "11.0.0"

# Disable specific rules
disabled_rules:
  - R2OSTR013  # No GEMPAK output for this model

# ecFlow-specific settings
ecflow:
  hardcoded_path_prefixes:
    - /lfs/
    - /work/
    - /scratch/
    - /gpfs/
```

### Repo Types

| Type | Description | Rules Applied |
|---|---|---|
| `operational_model` | Full NCO delivery package | All rules |
| `workflow` | Workflow orchestration repo | Structure, naming, env, modules, versions, ecflow |
| `model_source` | Model source code (e.g., UFS) | Build, modules |
| `library` | Shared library | Build only |
| `tool` | Python tool / utility | No rules (clean self-check) |

## Auto-Fix

For safe, unambiguous violations:

```bash
# Preview what would be fixed
r2o-check fix /path/to/repo

# Apply fixes
r2o-check fix /path/to/repo --apply
```

Auto-fix creates missing required directories and stubs version files.
It does NOT auto-fix naming, environment, build, or ecFlow rules.

## GitHub Actions Integration

Add to your workflow:

```yaml
- uses: mansurjisan/r2o-check/action@v0.1.0
  with:
    path: "."
    fail-on: "fail"  # or "warn" for strict mode
```

The action posts a Markdown summary as a PR comment and uploads
the full JSON report as a workflow artifact.

## Interpreting Results

- **PASS**: Rule satisfied
- **WARN**: Potential issue, review recommended
- **FAIL**: NCO standard violation, must fix before delivery
- **ERROR**: Rule execution failed (bug in r2o-check)

Each result includes the NCO v11.0 section reference and a fix hint.
See [rules.md](rules.md) for the full rule reference.
