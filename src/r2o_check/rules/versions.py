"""Version file checks.

NCO Implementation Standards v11.0, Section VI.B, Table 3.
R2OVER001/002: presence checks (FAIL).
R2OVER003/004: content format checks (WARN).
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

_VER_ASSIGNMENT = re.compile(r"^export\s+(\w+)=(.+)$")


# ── Presence checks (FAIL) ────────────────────────────────────


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_run_ver_exists(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER001 — Check versions/run.ver exists.

    NCO v11.0 Section VI.B, Table 3: versions/ must contain
    run.ver to track runtime package/module versions.
    """
    ver_file = repo_path / "versions" / "run.ver"
    if ver_file.is_file():
        return [LintResult(
            status=Status.PASS,
            rule_id="R2OVER001",
            message=(
                "Version file 'run.ver' exists."
                " [NCO v11.0 VI.B Table 3]"
            ),
            path=ver_file,
        )]
    return [LintResult(
        status=Status.FAIL,
        rule_id="R2OVER001",
        message=(
            "Missing version file 'run.ver'."
            " [NCO v11.0 VI.B Table 3]"
        ),
        path=repo_path / "versions" / "run.ver",
        fix_hint=(
            "Create 'versions/run.ver' with"
            " 'export model_ver=vX.Y.Z' entries."
        ),
    )]


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_build_ver_exists(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER002 — Check versions/build.ver exists.

    NCO v11.0 Section VI.B, Table 3: versions/ must contain
    build.ver to track compile-time package/module versions.
    """
    ver_file = repo_path / "versions" / "build.ver"
    if ver_file.is_file():
        return [LintResult(
            status=Status.PASS,
            rule_id="R2OVER002",
            message=(
                "Version file 'build.ver' exists."
                " [NCO v11.0 VI.B Table 3]"
            ),
            path=ver_file,
        )]
    return [LintResult(
        status=Status.FAIL,
        rule_id="R2OVER002",
        message=(
            "Missing version file 'build.ver'."
            " [NCO v11.0 VI.B Table 3]"
        ),
        path=repo_path / "versions" / "build.ver",
        fix_hint=(
            "Create 'versions/build.ver' with"
            " 'export model_ver=vX.Y.Z' entries."
        ),
    )]


# ── Content format checks (WARN) ──────────────────────────────


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_run_ver_content(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER003 — Validate run.ver content format.

    NCO v11.0 Section VI.B, Table 3: each line must be
    'export var=value' or a comment. Vars should use
    *_ver suffix.
    """
    ver_file = repo_path / "versions" / "run.ver"
    if not ver_file.is_file():
        return []
    return _check_ver_content(ver_file, "R2OVER003", "run.ver")


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_build_ver_content(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OVER004 — Validate build.ver content format.

    NCO v11.0 Section VI.B, Table 3: same rules as run.ver.
    """
    ver_file = repo_path / "versions" / "build.ver"
    if not ver_file.is_file():
        return []
    return _check_ver_content(
        ver_file, "R2OVER004", "build.ver"
    )


def _check_ver_content(
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
