"""Directory structure checks.

NCO Implementation Standards v11.0, Section VI.B, Table 3.
Each rule verifies that a required package subdirectory exists.
"""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    MODEL_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)

# ── Always-required directories (FAIL if missing) ─────────────────

# Each tuple: (dirname, rule_id, nco_section, description, fix_hint)
REQUIRED_DIRS: list[tuple[str, str, str, str, str]] = [
    (
        "ecf",
        "R2OSTR001",
        "VI.B Table 3",
        "ecFlow scripts and definition files directory",
        "Create the 'ecf/' directory and add ecFlow scripts (.ecf).",
    ),
    (
        "jobs",
        "R2OSTR002",
        "VI.B Table 3",
        "J-jobs directory",
        "Create 'jobs/' and add J-job scripts (JMODEL_TASK naming).",
    ),
    (
        "scripts",
        "R2OSTR003",
        "VI.B Table 3",
        "ex-scripts directory",
        "Create 'scripts/' for ex-scripts (exmodel_task.sh naming).",
    ),
    (
        "ush",
        "R2OSTR004",
        "VI.B Table 3",
        "Utility scripts directory",
        "Create 'ush/' for utility scripts called by ex-scripts.",
    ),
    (
        "sorc",
        "R2OSTR005",
        "VI.B Table 3",
        "Source code directory",
        "Create 'sorc/' containing compilable source code.",
    ),
    (
        "parm",
        "R2OSTR006",
        "VI.B Table 3",
        "Parameter files directory",
        "Create 'parm/' for parameter and configuration files.",
    ),
    (
        "versions",
        "R2OSTR007",
        "VI.B Table 3",
        "Version tracking directory (run.ver and build.ver)",
        "Create 'versions/' with run.ver and build.ver files.",
    ),
    (
        "modulefiles",
        "R2OSTR008",
        "VI.B Table 3",
        "Module files directory",
        "Create 'modulefiles/' for Lmod/Lua module files.",
    ),
]


def _check_directory(
    repo_path: Path,
    dirname: str,
    rule_id: str,
    nco_section: str,
    description: str,
    fix_hint: str,
    fail_status: Status = Status.FAIL,
) -> LintResult:
    """Check whether a directory exists under repo_path."""
    target = repo_path / dirname
    if target.is_dir():
        return LintResult(
            status=Status.PASS,
            rule_id=rule_id,
            message=(
                f"Required directory '{dirname}/' exists."
                f" [NCO v11.0 {nco_section}]"
            ),
            path=target,
        )
    return LintResult(
        status=fail_status,
        rule_id=rule_id,
        message=(
            f"Missing directory '{dirname}/'."
            f" [NCO v11.0 {nco_section}]: {description}"
        ),
        path=target,
        fix_hint=fix_hint,
    )


# ── R2OSTR001–008: Always-required (FAIL) ─────────────────────────


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR001 — Check for ecf/ directory (ecFlow scripts).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[0])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jobs_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR002 — Check for jobs/ directory (J-jobs).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[1])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_scripts_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR003 — Check for scripts/ directory (ex-scripts).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[2])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ush_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR004 — Check for ush/ directory (utility scripts).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[3])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_sorc_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR005 — Check for sorc/ directory (source code).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[4])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_parm_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR006 — Check for parm/ directory (parameter files).

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[5])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_versions_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR007 — Check for versions/ directory.

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[6])]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_modulefiles_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR008 — Check for modulefiles/ directory.

    NCO v11.0 Section VI.B, Table 3.
    """
    return [_check_directory(repo_path, *REQUIRED_DIRS[7])]


# ── R2OSTR009–014: Conditional directories (WARN, escalate) ───────

def _has_fortran_sources(repo_path: Path) -> bool:
    """Check if sorc/ contains Fortran source files."""
    sorc = repo_path / "sorc"
    if not sorc.is_dir():
        return False
    for ext in (".f", ".f90", ".F", ".F90", ".f77", ".ftn"):
        if list(sorc.rglob(f"*{ext}")):
            return True
    return False


def _has_c_sources(repo_path: Path) -> bool:
    """Check if sorc/ contains C/C++ source files."""
    sorc = repo_path / "sorc"
    if not sorc.is_dir():
        return False
    for ext in (".c", ".cpp", ".cc", ".C", ".cxx"):
        if list(sorc.rglob(f"*{ext}")):
            return True
    return False


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_doc_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR009 — Check for doc/ directory (documentation).

    NCO v11.0 Section VI.B, Table 3: release notes or other
    documentation. WARN if missing.
    """
    return [_check_directory(
        repo_path,
        "doc",
        "R2OSTR009",
        "VI.B Table 3",
        "Documentation directory (release notes)",
        "Create 'doc/' with release notes or documentation.",
        fail_status=Status.WARN,
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_exec_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR010 — Check for exec/ directory (binaries).

    NCO v11.0 Section VI.B, Table 3: binary executables.
    WARN if missing; FAIL if sorc/ contains compilable sources.
    """
    has_compilable = (
        _has_fortran_sources(repo_path)
        or _has_c_sources(repo_path)
    )
    severity = Status.FAIL if has_compilable else Status.WARN
    hint = "Create 'exec/' for compiled binary executables."
    if has_compilable:
        hint = (
            "sorc/ contains compilable sources — 'exec/' is "
            "required for the resulting binaries."
        )
    return [_check_directory(
        repo_path,
        "exec",
        "R2OSTR010",
        "VI.B Table 3",
        "Binary executables directory",
        hint,
        fail_status=severity,
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_fix_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR011 — Check for fix/ directory (static data).

    NCO v11.0 Section VI.B, Table 3: fixed fields, tables or
    other static input data. WARN if missing.
    """
    return [_check_directory(
        repo_path,
        "fix",
        "R2OSTR011",
        "VI.B Table 3",
        "Fixed fields / static input data directory",
        "Create 'fix/' for fixed fields, tables, or static data.",
        fail_status=Status.WARN,
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_lib_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR012 — Check for lib/ directory (model libraries).

    NCO v11.0 Section VI.B, Table 3: model-specific libraries.
    WARN if missing.
    """
    return [_check_directory(
        repo_path,
        "lib",
        "R2OSTR012",
        "VI.B Table 3",
        "Model-specific libraries directory",
        "Create 'lib/' for model-specific libraries.",
        fail_status=Status.WARN,
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_gempak_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR013 — Check for gempak/ directory.

    NCO v11.0 Section VI.B, Table 3: all gempak-related files.
    WARN if missing.
    """
    return [_check_directory(
        repo_path,
        "gempak",
        "R2OSTR013",
        "VI.B Table 3",
        "GEMPAK-related files directory",
        "Create 'gempak/' for GEMPAK-related files.",
        fail_status=Status.WARN,
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_parm_wmo_dir(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OSTR014 — Check for parm/wmo/ subdirectory.

    NCO v11.0 Section VI.B, Table 3: WMO GRIB headers under
    parm/. WARN if missing.
    """
    return [_check_directory(
        repo_path,
        "parm/wmo",
        "R2OSTR014",
        "VI.B Table 3",
        "WMO GRIB headers subdirectory under parm/",
        "Create 'parm/wmo/' for WMO GRIB header files.",
        fail_status=Status.WARN,
    )]
