"""Cross-reference checks between package components.

Validates consistency between jobs/, ecf/, and scripts/.
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

# Pattern to find ex-script calls in J-jobs:
# $SCRIPTSmodel/exmodel_task.sh or ${SCRIPTSmodel}/ex...
_EXSCRIPT_CALL = re.compile(
    r"\$\{?\w+\}?/(ex[a-z][a-z0-9_]*\.(?:sh|pl|py))"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_ecf_match(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF001 — Check J-jobs have matching ecf files.

    Every J-job in jobs/ should have a corresponding .ecf
    file in ecf/. The ecf filename is typically the
    lowercase version of the J-job name.
    """
    jobs_dir = repo_path / "jobs"
    ecf_dir = repo_path / "ecf"
    if not jobs_dir.is_dir() or not ecf_dir.is_dir():
        return []

    jjobs = {
        f.name for f in jobs_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    }
    ecf_stems = {
        f.stem for f in ecf_dir.rglob("*.ecf")
    }

    results: list[LintResult] = []
    for jname in sorted(jjobs):
        # ecf file is usually lowercase J-job name
        expected = jname.lower()
        if expected in ecf_stems:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OXRF001",
                message=(
                    f"J-job '{jname}' has matching"
                    f" ecf file. [NCO v11.0 II]"
                ),
                path=jobs_dir / jname,
            ))
        else:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OXRF001",
                message=(
                    f"J-job '{jname}' has no matching"
                    f" .ecf file in ecf/."
                    " [NCO v11.0 II]"
                ),
                path=jobs_dir / jname,
                fix_hint=(
                    f"Add 'ecf/{expected}.ecf' for"
                    f" this J-job."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_exscript_exists(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF002 — Check ex-scripts called from J-jobs exist.

    Parse J-job files for ex-script calls and verify the
    referenced scripts exist in scripts/.
    """
    jobs_dir = repo_path / "jobs"
    scripts_dir = repo_path / "scripts"
    if not jobs_dir.is_dir() or not scripts_dir.is_dir():
        return []

    # Collect all ex-scripts in scripts/ (recursive).
    existing_scripts = {
        f.name for f in scripts_dir.rglob("*")
        if f.is_file() and f.name.startswith("ex")
    }

    results: list[LintResult] = []
    for jf in sorted(jobs_dir.iterdir()):
        if not jf.is_file() or jf.name.startswith("."):
            continue
        content = jf.read_text(
            encoding="utf-8", errors="replace"
        )
        called = set(_EXSCRIPT_CALL.findall(content))
        for script_name in sorted(called):
            if script_name in existing_scripts:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF002",
                    message=(
                        f"{jf.name} calls '{script_name}'"
                        " — found in scripts/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=jf,
                ))
            else:
                results.append(LintResult(
                    status=Status.FAIL,
                    rule_id="R2OXRF002",
                    message=(
                        f"{jf.name} calls '{script_name}'"
                        " — not found in scripts/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add '{script_name}' to scripts/."
                    ),
                ))
    return results
