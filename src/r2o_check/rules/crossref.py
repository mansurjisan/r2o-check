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

# Pattern to find ex-script calls in J-jobs. Captures an optional
# subdirectory path so $SCRIPTSmodel/sub/exfoo.sh is recognised.
_EXSCRIPT_CALL = re.compile(
    r"\$\{?\w+\}?/"
    r"((?:[A-Za-z0-9_.-]+/)*ex[a-z][a-z0-9_]*\.(?:sh|pl|py))"
)

# Pattern: $USHmodel/script.sh or ${USHmodel}/sub/script.sh
_USH_CALL = re.compile(
    r"\$\{?\w+\}?/"
    r"((?:[A-Za-z0-9_.-]+/)*(?!ex)[a-z][a-z0-9_]*\.(?:sh|pl|py))"
)


def _collect_scripts(
    base: Path, name_filter: "re.Pattern[str] | None" = None,
    prefix: str | None = None,
) -> dict[str, Path]:
    """Return {posix_relpath: Path} for files under ``base``."""
    scripts: dict[str, Path] = {}
    if not base.is_dir():
        return scripts
    for p in base.rglob("*"):
        if not p.is_file() or p.name.startswith("."):
            continue
        if prefix is not None and not p.name.startswith(prefix):
            continue
        if name_filter is not None and not name_filter.search(p.name):
            continue
        rel = p.relative_to(base).as_posix()
        scripts[rel] = p
    return scripts


def _resolve_call(
    called: str, scripts: dict[str, Path]
) -> Path | None:
    """Resolve a captured call path against a repo-relative index.

    - If the call includes a subdirectory, the exact relative path
      must match.
    - If only a basename is given, match it to a script whose
      basename is unique. Ambiguous basename calls resolve to the
      first match to preserve ``exists`` semantics.
    """
    if called in scripts:
        return scripts[called]
    if "/" in called:
        return None
    matches = [
        (rel, p) for rel, p in scripts.items()
        if Path(rel).name == called
    ]
    if not matches:
        return None
    matches.sort()
    return matches[0][1]


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
    referenced scripts exist in scripts/. Calls with
    explicit subdirectory paths (``$SCRIPTS/sub/exfoo.sh``)
    must match by relative path; bare basenames resolve to
    unique matches.
    """
    jobs_dir = repo_path / "jobs"
    scripts_dir = repo_path / "scripts"
    if not jobs_dir.is_dir() or not scripts_dir.is_dir():
        return []

    existing = _collect_scripts(scripts_dir, prefix="ex")

    results: list[LintResult] = []
    for jf in sorted(jobs_dir.iterdir()):
        if not jf.is_file() or jf.name.startswith("."):
            continue
        content = jf.read_text(
            encoding="utf-8", errors="replace"
        )
        called = set(_EXSCRIPT_CALL.findall(content))
        for script_path in sorted(called):
            if _resolve_call(script_path, existing) is not None:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF002",
                    message=(
                        f"{jf.name} calls '{script_path}'"
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
                        f"{jf.name} calls '{script_path}'"
                        " — not found in scripts/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add '{script_path}' to scripts/."
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


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_exscript_ush_exists(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF004 — Check ush scripts called from ex-scripts exist.

    Parse ex-scripts for ush script calls and verify the
    referenced scripts exist in ush/. Calls carrying a
    subdirectory must match by relative path.
    """
    scripts_dir = repo_path / "scripts"
    ush_dir = repo_path / "ush"
    if not scripts_dir.is_dir() or not ush_dir.is_dir():
        return []

    existing_ush = _collect_scripts(ush_dir)

    results: list[LintResult] = []
    for sf in sorted(scripts_dir.rglob("ex*")):
        if not sf.is_file():
            continue
        content = sf.read_text(
            encoding="utf-8", errors="replace"
        )
        called = set(_USH_CALL.findall(content))
        for script_path in sorted(called):
            if _resolve_call(script_path, existing_ush) is not None:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF004",
                    message=(
                        f"{sf.name} calls '{script_path}'"
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
                        f"{sf.name} calls '{script_path}'"
                        " — not found in ush/."
                        " [NCO v11.0 IV.C]"
                    ),
                    path=sf,
                    fix_hint=(
                        f"Add '{script_path}' to ush/."
                    ),
                ))
    return results


def _called_ex_set(text: str) -> set[str]:
    return set(_EXSCRIPT_CALL.findall(text))


def _called_ush_set(text: str) -> set[str]:
    return set(_USH_CALL.findall(text))


def _resolve_calls(
    called_paths: set[str], scripts: dict[str, Path]
) -> set[str]:
    """Map each call to the specific script it references.

    Returns a set of repo-relative paths actually referenced.
    Qualified calls (``sub/foo.sh``) only hit an exact match.
    Bare basename calls prefer a top-level match; otherwise
    they resolve only when a single candidate exists.
    """
    resolved: set[str] = set()
    for call in called_paths:
        if call in scripts:
            resolved.add(call)
            continue
        if "/" in call:
            continue
        matches = [
            rel for rel in scripts
            if Path(rel).name == call
        ]
        if len(matches) == 1:
            resolved.add(matches[0])
    return resolved


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_orphan_scripts(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OXRF005 — Detect orphan scripts never called.

    Find ex-scripts in scripts/ that are not referenced by
    any J-job, and ush scripts not referenced by any
    ex-script. Identity uses the captured call path (or
    basename if the call omits a subdirectory) rather than a
    raw substring search, so two scripts with the same name
    at different paths are disambiguated.
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

    jjob_ex_calls = _called_ex_set(jjob_text)
    exscript_ush_calls = _called_ush_set(exscript_text)
    jjob_ush_calls = _called_ush_set(jjob_text)

    # Check ex-scripts: are they called from any J-job?
    if scripts_dir.is_dir() and jobs_dir.is_dir():
        ex_scripts = _collect_scripts(scripts_dir, prefix="ex")
        referenced_ex = _resolve_calls(jjob_ex_calls, ex_scripts)
        for rel, sf in sorted(ex_scripts.items()):
            if rel in referenced_ex:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ex-script '{rel}' is"
                        " referenced by a J-job."
                    ),
                    path=sf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ex-script '{rel}' is not"
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
        ush_scripts = _collect_scripts(ush_dir)
        referenced_ush = (
            _resolve_calls(exscript_ush_calls, ush_scripts)
            | _resolve_calls(jjob_ush_calls, ush_scripts)
        )
        for rel, uf in sorted(ush_scripts.items()):
            if rel in referenced_ush:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ush script '{rel}' is"
                        " referenced."
                    ),
                    path=uf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OXRF005",
                    message=(
                        f"Ush script '{rel}' is not"
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
