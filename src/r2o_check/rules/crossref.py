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


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_references_jjob(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF003 — Check ecf files reference real J-jobs.

    Each .ecf file in ecf/ should call a J-job that exists
    in jobs/. The J-job name is extracted from lines like
    $HOMEmodel/jobs/JMODEL_TASK.
    """
    ecf_dir = repo_path / "ecf"
    jobs_dir = repo_path / "jobs"
    if not ecf_dir.is_dir() or not jobs_dir.is_dir():
        return []

    jjobs = {
        f.name for f in jobs_dir.iterdir()
        if f.is_file() and not f.name.startswith(".")
    }

    # Pattern: $HOMEmodel/jobs/JNAME or ${HOMEmodel}/jobs/JNAME
    jjob_call = re.compile(
        r"\$\{?\w+\}?/jobs/(J[A-Z][A-Z0-9_]*)"
    )

    results: list[LintResult] = []
    for ef in sorted(ecf_dir.rglob("*.ecf")):
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        called = set(jjob_call.findall(content))
        for jname in sorted(called):
            if jname in jjobs:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF003",
                    message=(
                        f"{ef.name} calls '{jname}'"
                        " — found in jobs/."
                        " [NCO v11.0 II]"
                    ),
                    path=ef,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF003",
                    message=(
                        f"{ef.name} calls '{jname}'"
                        " — not found in jobs/."
                        " [NCO v11.0 II]"
                    ),
                    path=ef,
                    fix_hint=(
                        f"Add '{jname}' to jobs/."
                    ),
                ))
    return results


# Pattern: $USHmodel/script.sh or ${USHmodel}/script.sh
_USH_CALL = re.compile(
    r"\$\{?\w+\}?/((?!ex)[a-z][a-z0-9_]*\.(?:sh|pl|py))"
)


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_exscript_ush_exists(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF004 — Check ush scripts called from ex-scripts exist.

    Parse ex-scripts for ush script calls and verify the
    referenced scripts exist in ush/.
    """
    scripts_dir = repo_path / "scripts"
    ush_dir = repo_path / "ush"
    if not scripts_dir.is_dir() or not ush_dir.is_dir():
        return []

    existing_ush = {
        f.name for f in ush_dir.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    }

    results: list[LintResult] = []
    for sf in sorted(scripts_dir.rglob("ex*")):
        if not sf.is_file():
            continue
        content = sf.read_text(
            encoding="utf-8", errors="replace"
        )
        called = set(_USH_CALL.findall(content))
        for script_name in sorted(called):
            if script_name in existing_ush:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF004",
                    message=(
                        f"{sf.name} calls '{script_name}'"
                        " — found in ush/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=sf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF004",
                    message=(
                        f"{sf.name} calls '{script_name}'"
                        " — not found in ush/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=sf,
                    fix_hint=(
                        f"Add '{script_name}' to ush/."
                    ),
                ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_orphan_scripts(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF005 — Detect orphan scripts never called.

    Find ex-scripts in scripts/ that are not referenced by
    any J-job, and ush scripts not referenced by any
    ex-script. WARN severity — orphans may indicate dead
    code or missing wiring.
    """
    jobs_dir = repo_path / "jobs"
    scripts_dir = repo_path / "scripts"
    ush_dir = repo_path / "ush"
    results: list[LintResult] = []

    # Collect all text from J-jobs.
    jjob_text = ""
    if jobs_dir.is_dir():
        for jf in jobs_dir.iterdir():
            if jf.is_file() and not jf.name.startswith("."):
                jjob_text += jf.read_text(
                    encoding="utf-8", errors="replace"
                )

    # Collect all text from ex-scripts.
    exscript_text = ""
    if scripts_dir.is_dir():
        for sf in scripts_dir.rglob("ex*"):
            if sf.is_file():
                exscript_text += sf.read_text(
                    encoding="utf-8", errors="replace"
                )

    # Check ex-scripts: are they called from any J-job?
    if scripts_dir.is_dir() and jobs_dir.is_dir():
        for sf in sorted(scripts_dir.rglob("ex*")):
            if not sf.is_file():
                continue
            if sf.name in jjob_text:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ex-script '{sf.name}' is"
                        " referenced by a J-job."
                    ),
                    path=sf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ex-script '{sf.name}' is not"
                        " referenced by any J-job"
                        " (possible orphan)."
                    ),
                    path=sf,
                    fix_hint=(
                        "Remove if unused, or add a"
                        " J-job call to this script."
                    ),
                ))

    # Check ush scripts: are they called from any ex-script?
    if ush_dir.is_dir() and scripts_dir.is_dir():
        for uf in sorted(ush_dir.rglob("*")):
            if not uf.is_file() or uf.name.startswith("."):
                continue
            if uf.name in exscript_text or uf.name in jjob_text:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ush script '{uf.name}' is"
                        " referenced."
                    ),
                    path=uf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ush script '{uf.name}' is not"
                        " referenced by any script"
                        " (possible orphan)."
                    ),
                    path=uf,
                    fix_hint=(
                        "Remove if unused, or add a"
                        " call to this script."
                    ),
                ))
    return results
