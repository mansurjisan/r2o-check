"""Directory structure checks.

NCO Implementation Standards v11.0, Section VI.B, Table 3.
Each rule verifies that a required package subdirectory exists.
"""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import LintResult, Status, register_rule

# Required directories from NCO v11.0 §VI.B Table 3, with metadata.
# Each tuple: (directory_name, rule_id, nco_section, description, fix_hint)
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
        "Create the 'jobs/' directory and add your J-job scripts (JMODEL_TASK naming).",
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
        "Create the 'ush/' directory for utility scripts called by ex-scripts.",
    ),
    (
        "sorc",
        "R2OSTR005",
        "VI.B Table 3",
        "Source code directory",
        "Create the 'sorc/' directory containing compilable source code.",
    ),
    (
        "parm",
        "R2OSTR006",
        "VI.B Table 3",
        "Parameter files directory",
        "Create the 'parm/' directory for parameter and configuration files.",
    ),
    (
        "versions",
        "R2OSTR007",
        "VI.B Table 3",
        "Version tracking directory (run.ver and build.ver)",
        "Create the 'versions/' directory with run.ver and build.ver files.",
    ),
    (
        "modulefiles",
        "R2OSTR008",
        "VI.B Table 3",
        "Module files directory",
        "Create the 'modulefiles/' directory for Lmod/Lua module files.",
    ),
]


def _check_directory(
    repo_path: Path,
    dirname: str,
    rule_id: str,
    nco_section: str,
    description: str,
    fix_hint: str,
) -> LintResult:
    """Check whether a required directory exists under repo_path."""
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
        status=Status.FAIL,
        rule_id=rule_id,
        message=(
            f"Missing required directory '{dirname}/'."
            f" [NCO v11.0 {nco_section}]: {description}"
        ),
        path=target,
        fix_hint=fix_hint,
    )


@register_rule
def check_ecf_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR001 — Check for ecf/ directory (ecFlow scripts).

    NCO v11.0 Section VI.B, Table 3: ecFlow scripts and definition files.
    """
    d = REQUIRED_DIRS[0]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_jobs_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR002 — Check for jobs/ directory (J-jobs).

    NCO v11.0 Section VI.B, Table 3: J-jobs.
    """
    d = REQUIRED_DIRS[1]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_scripts_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR003 — Check for scripts/ directory (ex-scripts).

    NCO v11.0 Section VI.B, Table 3: ex-scripts.
    """
    d = REQUIRED_DIRS[2]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_ush_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR004 — Check for ush/ directory (utility scripts).

    NCO v11.0 Section VI.B, Table 3: utility scripts (ush-scripts).
    """
    d = REQUIRED_DIRS[3]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_sorc_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR005 — Check for sorc/ directory (source code).

    NCO v11.0 Section VI.B, Table 3: source code that can be compiled.
    """
    d = REQUIRED_DIRS[4]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_parm_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR006 — Check for parm/ directory (parameter files).

    NCO v11.0 Section VI.B, Table 3: parameter files.
    """
    d = REQUIRED_DIRS[5]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_versions_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR007 — Check for versions/ directory.

    NCO v11.0 Section VI.B, Table 3: contains run.ver and build.ver.
    """
    d = REQUIRED_DIRS[6]
    return [_check_directory(repo_path, *d)]


@register_rule
def check_modulefiles_dir(repo_path: Path, config: Config) -> list[LintResult]:
    """R2OSTR008 — Check for modulefiles/ directory.

    NCO v11.0 Section VI.B, Table 3: model module files.
    """
    d = REQUIRED_DIRS[7]
    return [_check_directory(repo_path, *d)]
