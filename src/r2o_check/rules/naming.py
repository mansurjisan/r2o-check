"""Naming convention checks.

NCO Implementation Standards v11.0, Section IV.C.
Validates J-job, ex-script, modulefile, and version file naming.
"""

from __future__ import annotations

import re
from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    MODEL_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)

# J-job naming: all caps, begins with J, no extension.
# Pattern: JMODEL_TASK or JMODEL (NCO v11.0 §IV.C)
_JJOB_PATTERN = re.compile(r"^J[A-Z][A-Z0-9_]*$")

# Ex-script naming: all lowercase, begins with 'ex', ends with
# .sh/.pl/.py (NCO v11.0 §IV.C)
_EXSCRIPT_PATTERN = re.compile(
    r"^ex[a-z][a-z0-9_]*\.(sh|pl|py)$"
)

# Ush-script: all lowercase, does NOT begin with 'ex',
# ends with .sh/.pl/.py (NCO v11.0 §IV.C)
_USH_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.(sh|pl|py)$")

# Version files expected in versions/
_EXPECTED_VER_FILES = {"run.ver", "build.ver"}

# Version file line pattern: export var=value
_VER_LINE_PATTERN = re.compile(
    r"^export\s+[A-Za-z_][A-Za-z0-9_]*=\S+"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_naming(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2ONAM001 — Validate J-job file naming conventions.

    NCO v11.0 Section IV.C: J-jobs must follow the naming
    convention JAAAAA — all capital letters beginning with J,
    no extension. Underscores are permitted.
    """
    jobs_dir = repo_path / "jobs"
    if not jobs_dir.is_dir():
        return []

    results: list[LintResult] = []
    for f in sorted(jobs_dir.iterdir()):
        if not f.is_file():
            continue
        if _JJOB_PATTERN.match(f.name):
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2ONAM001",
                message=(
                    f"J-job '{f.name}' follows naming convention."
                    " [NCO v11.0 IV.C]"
                ),
                path=f,
            ))
        else:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2ONAM001",
                message=(
                    f"J-job '{f.name}' violates naming convention."
                    " Must be all caps, start with J, no extension."
                    " [NCO v11.0 IV.C]"
                ),
                path=f,
                fix_hint=(
                    "Rename to match JMODEL_TASK pattern"
                    " (e.g., JMODEL_FORECAST)."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_exscript_naming(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2ONAM002 — Validate ex-script file naming conventions.

    NCO v11.0 Section IV.C: ex-scripts must follow the naming
    convention exaaaaa.sh — all lowercase beginning with 'ex'
    and ending with .sh, .pl, or .py.
    """
    scripts_dir = repo_path / "scripts"
    if not scripts_dir.is_dir():
        return []

    results: list[LintResult] = []
    # Recurse into scripts/ and subdirectories.
    # Only flag files whose name starts with 'ex' — these
    # are intended to be ex-scripts. Non-ex files (helpers,
    # utilities) are not checked by this rule.
    for f in sorted(scripts_dir.rglob("*")):
        if not f.is_file():
            continue
        if not f.name.startswith("ex"):
            continue
        if _EXSCRIPT_PATTERN.match(f.name):
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2ONAM002",
                message=(
                    f"Ex-script '{f.name}' follows naming."
                    " [NCO v11.0 IV.C]"
                ),
                path=f,
            ))
        else:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2ONAM002",
                message=(
                    f"Ex-script '{f.name}' violates naming."
                    " Must be all lowercase, start with 'ex',"
                    " end with .sh/.pl/.py. [NCO v11.0 IV.C]"
                ),
                path=f,
                fix_hint=(
                    "Rename to match exmodel_task.sh pattern."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ush_naming(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2ONAM005 — Validate ush/ script naming conventions.

    NCO v11.0 Section IV.C: ush scripts must be all lowercase,
    must not begin with 'ex', and must end with .sh, .pl, or .py.
    """
    ush_dir = repo_path / "ush"
    if not ush_dir.is_dir():
        return []

    results: list[LintResult] = []
    for f in sorted(ush_dir.rglob("*")):
        if not f.is_file():
            continue
        name = f.name
        has_valid_ext = _USH_PATTERN.match(name) is not None
        starts_with_ex = name.startswith("ex")
        is_lowercase = name == name.lower()

        if has_valid_ext and not starts_with_ex and is_lowercase:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2ONAM005",
                message=(
                    f"Ush script '{name}' follows naming."
                    " [NCO v11.0 IV.C]"
                ),
                path=f,
            ))
        else:
            parts: list[str] = []
            if not is_lowercase:
                parts.append("must be lowercase")
            if starts_with_ex:
                parts.append("must not start with 'ex'")
            if not has_valid_ext:
                parts.append("must end with .sh/.pl/.py")
            reason = "; ".join(parts)
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2ONAM005",
                message=(
                    f"Ush script '{name}': {reason}."
                    " [NCO v11.0 IV.C]"
                ),
                path=f,
                fix_hint=(
                    "Rename to lowercase, no 'ex' prefix,"
                    " with .sh/.pl/.py extension."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_modulefile_naming(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2ONAM003 — Validate modulefile naming conventions.

    NCO v11.0 Section VI.A.5: WCOSS uses Lmod, so module files
    must be in Lmod/Lua format (.lua extension).
    """
    mf_dir = repo_path / "modulefiles"
    if not mf_dir.is_dir():
        return []

    results: list[LintResult] = []
    for f in sorted(mf_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix == ".lua":
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2ONAM003",
                message=(
                    f"Modulefile '{f.name}' uses .lua extension."
                    " [NCO v11.0 VI.A.5]"
                ),
                path=f,
            ))
        else:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2ONAM003",
                message=(
                    f"Modulefile '{f.name}' is not .lua format."
                    " WCOSS requires Lmod/Lua modulefiles."
                    " [NCO v11.0 VI.A.5]"
                ),
                path=f,
                fix_hint=(
                    f"Convert '{f.name}' to Lua format"
                    f" with .lua extension."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_version_files(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2ONAM004 — Validate versions/ file naming and format.

    NCO v11.0 Section VI.B, Table 3: versions/ must contain
    run.ver and build.ver. Files must use 'export var=value'
    format and not reference unused packages/modules.
    """
    ver_dir = repo_path / "versions"
    if not ver_dir.is_dir():
        return []

    results: list[LintResult] = []

    # Check presence of expected files.
    existing = {f.name for f in ver_dir.iterdir() if f.is_file()}
    for expected in sorted(_EXPECTED_VER_FILES):
        if expected in existing:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2ONAM004",
                message=(
                    f"Version file '{expected}' exists."
                    " [NCO v11.0 VI.B Table 3]"
                ),
                path=ver_dir / expected,
            ))
        else:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2ONAM004",
                message=(
                    f"Missing version file '{expected}'."
                    " [NCO v11.0 VI.B Table 3]"
                ),
                path=ver_dir / expected,
                fix_hint=(
                    f"Create 'versions/{expected}' with "
                    f"'export model_ver=vX.Y.Z' entries."
                ),
            ))

    # Validate format of existing .ver files.
    for ver_file in sorted(ver_dir.iterdir()):
        if not ver_file.is_file() or ver_file.suffix != ".ver":
            continue
        lines = ver_file.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not _VER_LINE_PATTERN.match(stripped):
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2ONAM004",
                    message=(
                        f"{ver_file.name}:{i}: line does not "
                        f"match 'export var=value' format."
                        " [NCO v11.0 VI.B Table 3]"
                    ),
                    path=ver_file,
                    fix_hint=(
                        "Each line should be 'export var=value'"
                        " or a comment (#)."
                    ),
                ))
    return results
