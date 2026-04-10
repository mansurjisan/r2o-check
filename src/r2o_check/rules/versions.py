"""Version file content checks.

NCO Implementation Standards v11.0, Section VI.B, Table 3.
Deeper validation of run.ver and build.ver beyond presence.
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

# Expected: export var_ver=vX.Y.Z or export var_ver=X.Y.Z
_VER_ASSIGNMENT = re.compile(
    r"^export\s+(\w+)=(.+)$"
)

# Version value pattern (loose): vX.Y.Z or X.Y.Z
_VERSION_VALUE = re.compile(
    r"^v?\d+\.\d+(\.\d+)?$"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_run_ver_content(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER001 — Validate run.ver content.

    NCO v11.0 Section VI.B, Table 3: run.ver tracks package
    and module versions used at runtime. Each line must be
    'export var=value'. Must not reference unused packages.
    """
    ver_file = repo_path / "versions" / "run.ver"
    if not ver_file.is_file():
        return []

    return _check_ver_file(ver_file, "R2OVER001", "run.ver")


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_build_ver_content(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER002 — Validate build.ver content.

    NCO v11.0 Section VI.B, Table 3: build.ver tracks package
    and module versions used at compile time.
    """
    ver_file = repo_path / "versions" / "build.ver"
    if not ver_file.is_file():
        return []

    return _check_ver_file(ver_file, "R2OVER002", "build.ver")


def _check_ver_file(
    ver_file: Path, rule_id: str, label: str
) -> list[LintResult]:
    """Validate a .ver file's content."""
    results: list[LintResult] = []
    lines = ver_file.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()

    has_exports = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        m = _VER_ASSIGNMENT.match(stripped)
        if not m:
            results.append(LintResult(
                status=Status.WARN,
                rule_id=rule_id,
                message=(
                    f"{label}:{i}: not 'export var=value'"
                    f" format. [NCO v11.0 VI.B Table 3]"
                ),
                path=ver_file,
                fix_hint=(
                    "Each line should be"
                    " 'export var=value' or a comment."
                ),
            ))
            continue

        has_exports = True
        var_name = m.group(1)

        # Check naming convention: *_ver suffix.
        if not var_name.endswith("_ver"):
            results.append(LintResult(
                status=Status.WARN,
                rule_id=rule_id,
                message=(
                    f"{label}:{i}: '{var_name}' does not"
                    " end with '_ver' suffix."
                    " [NCO v11.0 VI.B Table 3]"
                ),
                path=ver_file,
                fix_hint=(
                    f"Rename to '{var_name}_ver' or"
                    " similar *_ver pattern."
                ),
            ))

    if has_exports:
        results.insert(0, LintResult(
            status=Status.PASS,
            rule_id=rule_id,
            message=(
                f"{label} has valid export statements."
                " [NCO v11.0 VI.B Table 3]"
            ),
            path=ver_file,
        ))
    elif not results:
        results.append(LintResult(
            status=Status.WARN,
            rule_id=rule_id,
            message=(
                f"{label} is empty or has no exports."
                " [NCO v11.0 VI.B Table 3]"
            ),
            path=ver_file,
            fix_hint=(
                f"Add 'export model_ver=vX.Y.Z' to {label}."
            ),
        ))

    return results
