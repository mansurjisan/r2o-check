"""Shell script content validation.

NCO Implementation Standards v11.0, Section IV.C.
Validates script content for required patterns and forbidden ones.
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


def _iter_shell_files(
    directory: Path,
) -> list[Path]:
    """Find shell script files in a directory."""
    if not directory.is_dir():
        return []
    return sorted(
        f for f in directory.rglob("*")
        if f.is_file()
        and not f.name.startswith(".")
        and f.suffix in (".sh", ".ksh", "")
    )


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_debug_settings(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT001 — Check J-jobs have debug logging.

    NCO v11.0 Section IV.C.1: enable debug logging at
    the top of each shell script with 'set -x' and add
    timing info with "export PS4='+ $SECONDS + '".
    """
    jobs_dir = repo_path / "jobs"
    if not jobs_dir.is_dir():
        return []

    results: list[LintResult] = []
    for jf in sorted(jobs_dir.iterdir()):
        if not jf.is_file() or jf.name.startswith("."):
            continue
        content = jf.read_text(
            encoding="utf-8", errors="replace"
        )
        has_set_x = bool(re.search(r"\bset\s+-x\b", content))
        has_ps4 = "PS4" in content

        if has_set_x and has_ps4:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OCNT001",
                message=(
                    f"{jf.name}: has 'set -x' and PS4."
                    " [NCO v11.0 IV.C.1]"
                ),
                path=jf,
            ))
        else:
            missing = []
            if not has_set_x:
                missing.append("set -x")
            if not has_ps4:
                missing.append("export PS4='+ $SECONDS + '")
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OCNT001",
                message=(
                    f"{jf.name}: missing"
                    f" {', '.join(missing)}."
                    " [NCO v11.0 IV.C.1]"
                ),
                path=jf,
                fix_hint=(
                    "Add 'set -x' and"
                    " \"export PS4='+ $SECONDS + '\""
                    " near the top of the J-job."
                ),
            ))
    return results


# Pattern: executable call followed by err_chk or export err=
_EXEC_CALL = re.compile(
    r"\$\{?EXEC\w*\}?/\w+"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_err_chk_usage(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT002 — Check ex-scripts use err_chk.

    NCO v11.0 Section IV.C.5: each execution of a C or
    Fortran code must be wrapped with err_chk. Check that
    ex-scripts containing executable calls also use err_chk.
    """
    scripts_dir = repo_path / "scripts"
    if not scripts_dir.is_dir():
        return []

    results: list[LintResult] = []
    for sf in sorted(scripts_dir.rglob("ex*")):
        if not sf.is_file():
            continue
        content = sf.read_text(
            encoding="utf-8", errors="replace"
        )
        has_exec = bool(_EXEC_CALL.search(content))
        if not has_exec:
            continue

        has_err_chk = "err_chk" in content
        if has_err_chk:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OCNT002",
                message=(
                    f"{sf.name}: uses err_chk with"
                    " executable calls."
                    " [NCO v11.0 IV.C.5]"
                ),
                path=sf,
            ))
        else:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OCNT002",
                message=(
                    f"{sf.name}: calls executables but"
                    " does not use err_chk."
                    " [NCO v11.0 IV.C.5]"
                ),
                path=sf,
                fix_hint=(
                    "Add 'export err=$?; err_chk'"
                    " after each executable call."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_shebang(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT003 — Check shell scripts have shebang.

    NCO v11.0 Section IV.C.16: the interpreter must be
    added to the top of all shell scripts with a '#!'
    statement.
    """
    results: list[LintResult] = []
    for dirname in ("jobs", "scripts", "ush"):
        d = repo_path / dirname
        for sf in _iter_shell_files(d):
            try:
                first_line = sf.read_text(
                    encoding="utf-8", errors="replace"
                ).split("\n", 1)[0]
            except Exception:
                continue

            if first_line.startswith("#!"):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OCNT003",
                    message=(
                        f"{dirname}/{sf.name}: has shebang."
                        " [NCO v11.0 IV.C.16]"
                    ),
                    path=sf,
                ))
            else:
                results.append(LintResult(
                    status=Status.FAIL,
                    rule_id="R2OCNT003",
                    message=(
                        f"{dirname}/{sf.name}: missing"
                        " shebang (#!)."
                        " [NCO v11.0 IV.C.16]"
                    ),
                    path=sf,
                    fix_hint=(
                        "Add '#!/bin/bash' or '#!/bin/sh'"
                        " as the first line."
                    ),
                ))
    return results


# Pattern: command with & at end (background process).
# Excludes: comments, && chains, heredocs, variable assignments.
_BACKGROUND_PROC = re.compile(
    r"^[^#]*[^&|]\s*&\s*$", re.MULTILINE
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_no_background_procs(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT004 — Check for background processes.

    NCO v11.0 Section IV.A.vi: PBS Pro loses control of
    processes when they are put in the background. Background
    processing must be avoided.
    """
    results: list[LintResult] = []
    for dirname in ("jobs", "scripts", "ush"):
        d = repo_path / dirname
        for sf in _iter_shell_files(d):
            content = sf.read_text(
                encoding="utf-8", errors="replace"
            )
            matches = _BACKGROUND_PROC.findall(content)
            if matches:
                count = len(matches)
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OCNT004",
                    message=(
                        f"{dirname}/{sf.name}: {count}"
                        " background process(es) detected."
                        " [NCO v11.0 IV.A.vi]"
                    ),
                    path=sf,
                    fix_hint=(
                        "Remove '&' — PBS Pro loses control"
                        " of background processes."
                    ),
                ))
            else:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OCNT004",
                    message=(
                        f"{dirname}/{sf.name}: no background"
                        " processes. [NCO v11.0 IV.A.vi]"
                    ),
                    path=sf,
                ))
    return results
