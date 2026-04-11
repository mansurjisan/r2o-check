"""Shell script content validation.

NCO Implementation Standards v11.0, Section IV.C.
Validates script content for required patterns and forbidden ones.
"""

from __future__ import annotations

import os
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


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_no_absolute_symlinks(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT005 — Check for symlinks to absolute paths.

    NCO v11.0 Section IV.A.vii: symbolic links to resources
    outside the application directory (e.g. links to absolute
    paths) are not allowed within the package.
    """
    results: list[LintResult] = []
    bad_links: list[tuple[Path, str]] = []

    for item in repo_path.rglob("*"):
        if not item.is_symlink():
            continue
        target = str(item.resolve())
        link_target = str(Path(os.readlink(item)))
        if link_target.startswith("/"):
            bad_links.append((item, link_target))

    if bad_links:
        for link_path, target in bad_links:
            rel = link_path.relative_to(repo_path)
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OCNT005",
                message=(
                    f"{rel}: symlink to absolute path"
                    f" '{target}'. [NCO v11.0 IV.A.vii]"
                ),
                path=link_path,
                fix_hint=(
                    "Use environment variables or module"
                    " variables instead of absolute symlinks."
                ),
            ))
    else:
        results.append(LintResult(
            status=Status.PASS,
            rule_id="R2OCNT005",
            message=(
                "No absolute symlinks found."
                " [NCO v11.0 IV.A.vii]"
            ),
            path=repo_path,
        ))
    return results


# Patterns for production utility checks.
_CP_CALL = re.compile(r"\bcp\s+(?!-)", re.MULTILINE)
_CPREQ_CALL = re.compile(r"\bcpreq\b")
_PREP_STEP_CALL = re.compile(r"\bprep_step\b")
_DBN_ALERT = re.compile(r"\bdbn_alert\b")
_SENDDBN_CHECK = re.compile(
    r"SENDDBN.*=.*YES|if.*SENDDBN"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_production_utilities(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT006 — Check production utility usage.

    NCO v11.0 Section III.C:
    - Use cpreq (not cp) for essential file copies
    - Use prep_step before Fortran executable calls
    - Wrap dbn_alert calls with $SENDDBN checks
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
        name = sf.name

        # Check dbn_alert wrapped with SENDDBN.
        has_dbn = bool(_DBN_ALERT.search(content))
        if has_dbn:
            has_senddbn = bool(_SENDDBN_CHECK.search(content))
            if has_senddbn:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OCNT006",
                    message=(
                        f"{name}: dbn_alert wrapped with"
                        " SENDDBN check."
                        " [NCO v11.0 III.C]"
                    ),
                    path=sf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OCNT006",
                    message=(
                        f"{name}: dbn_alert used without"
                        " SENDDBN check."
                        " [NCO v11.0 III.C/V]"
                    ),
                    path=sf,
                    fix_hint=(
                        "Wrap dbn_alert calls with"
                        " 'if [ $SENDDBN = YES ]; then'."
                    ),
                ))

        # Check for exec calls without prep_step.
        has_exec = bool(_EXEC_CALL.search(content))
        if has_exec:
            has_prep = bool(_PREP_STEP_CALL.search(content))
            if not has_prep:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OCNT006",
                    message=(
                        f"{name}: calls executables without"
                        " prep_step. [NCO v11.0 III.C]"
                    ),
                    path=sf,
                    fix_hint=(
                        "Add 'prep_step' before each"
                        " Fortran executable call."
                    ),
                ))

    return results


# Dangerous rm patterns.
_DANGEROUS_RM = re.compile(
    r"rm\s+(-rf?|-fr?)\s+\$\{?COM(ROOT|OUT|IN)"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_working_dir_hygiene(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OCNT007 — Check working directory hygiene.

    NCO v11.0 Section IV.A.viii / IV.C.7:
    - J-jobs should reference $KEEPDATA for cleanup control
    - Scripts must not rm -rf $COMROOT level directories
    """
    results: list[LintResult] = []

    # Check J-jobs for KEEPDATA reference.
    jobs_dir = repo_path / "jobs"
    if jobs_dir.is_dir():
        for jf in sorted(jobs_dir.iterdir()):
            if not jf.is_file() or jf.name.startswith("."):
                continue
            content = jf.read_text(
                encoding="utf-8", errors="replace"
            )
            if "KEEPDATA" in content:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OCNT007",
                    message=(
                        f"{jf.name}: references KEEPDATA."
                        " [NCO v11.0 IV.A.viii]"
                    ),
                    path=jf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OCNT007",
                    message=(
                        f"{jf.name}: does not reference"
                        " KEEPDATA. [NCO v11.0 IV.A.viii]"
                    ),
                    path=jf,
                    fix_hint=(
                        "Add KEEPDATA check to control"
                        " working directory cleanup."
                    ),
                ))

    # Check all scripts for dangerous rm commands.
    for dirname in ("jobs", "scripts", "ush"):
        d = repo_path / dirname
        for sf in _iter_shell_files(d):
            content = sf.read_text(
                encoding="utf-8", errors="replace"
            )
            if _DANGEROUS_RM.search(content):
                results.append(LintResult(
                    status=Status.FAIL,
                    rule_id="R2OCNT007",
                    message=(
                        f"{dirname}/{sf.name}: dangerous"
                        " rm on $COM* directory."
                        " [NCO v11.0 IV.C.7]"
                    ),
                    path=sf,
                    fix_hint=(
                        "Production uses centralized COM"
                        " cleanup. Do not rm -rf $COMROOT"
                        " or $COMOUT level directories."
                    ),
                ))
    return results
