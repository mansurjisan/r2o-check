"""ecFlow script validation.

NCO Implementation Standards v11.0, Section II (Workflow).
Validates .ecf files as text — no ecflow Python library required.
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

# Default path prefixes now in config.py (EcflowConfig).
# R2OECF005 reads from config.ecflow.hardcoded_path_prefixes.

# Pattern: lines that are assignments (VAR=... or export VAR=...,
# also readonly/declare/local/typeset) are excluded from hardcoded
# path checks — it's valid to set a default.
_ASSIGNMENT_LINE = re.compile(
    r"^\s*(?:export|readonly|declare|local|typeset)?\s*\w+="
)

# PBS directive pattern: #PBS -<flag> <value>
_PBS_DIRECTIVE = re.compile(r"^#PBS\s+-\w")

# SBATCH directive pattern: #SBATCH --<flag>=<value>
_SBATCH_DIRECTIVE = re.compile(r"^#SBATCH\s+--\w")


def _find_ecf_files(repo_path: Path) -> list[Path]:
    """Find .ecf files under ecf/."""
    ecf_dir = repo_path / "ecf"
    if not ecf_dir.is_dir():
        return []
    return sorted(ecf_dir.rglob("*.ecf"))


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_includes(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF001 — Check .ecf files have head/tail includes.

    NCO v11.0 Section II: ecFlow scripts must include
    %include <head.h> and %include <tail.h> directives to
    set up and tear down the job environment.
    """
    ecf_files = _find_ecf_files(repo_path)
    if not ecf_files:
        return []

    results: list[LintResult] = []
    for ef in ecf_files:
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        name = ef.name
        has_head = "%include <head.h>" in content
        has_tail = "%include <tail.h>" in content

        if has_head and has_tail:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF001",
                message=(
                    f"{name}: has head.h and tail.h includes."
                    " [NCO v11.0 II]"
                ),
                path=ef,
            ))
        else:
            missing = []
            if not has_head:
                missing.append("%include <head.h>")
            if not has_tail:
                missing.append("%include <tail.h>")
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OECF001",
                message=(
                    f"{name}: missing {', '.join(missing)}."
                    " [NCO v11.0 II]"
                ),
                path=ef,
                fix_hint=(
                    "Add %include <head.h> at the top and"
                    " %include <tail.h> at the bottom."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_init_complete(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF002 — Check paired ecflow_client init/complete.

    NCO v11.0 Section II: ecFlow scripts must call
    ecflow_client --init at start and ecflow_client --complete
    at end, typically within head.h/tail.h. We check the .ecf
    file or its included content for these patterns.
    """
    ecf_files = _find_ecf_files(repo_path)
    if not ecf_files:
        return []

    results: list[LintResult] = []
    for ef in ecf_files:
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        name = ef.name
        has_init = "ecflow_client --init" in content
        has_complete = "ecflow_client --complete" in content

        # If head.h/tail.h are included, init/complete are
        # typically in those files — skip check.
        has_includes = (
            "%include <head.h>" in content
            and "%include <tail.h>" in content
        )
        if has_includes:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF002",
                message=(
                    f"{name}: uses head.h/tail.h (init/"
                    "complete expected in includes)."
                    " [NCO v11.0 II]"
                ),
                path=ef,
            ))
        elif has_init and has_complete:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF002",
                message=(
                    f"{name}: has paired init/complete."
                    " [NCO v11.0 II]"
                ),
                path=ef,
            ))
        else:
            missing = []
            if not has_init:
                missing.append("ecflow_client --init")
            if not has_complete:
                missing.append("ecflow_client --complete")
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OECF002",
                message=(
                    f"{name}: missing {', '.join(missing)}"
                    " (and no head.h/tail.h includes)."
                    " [NCO v11.0 II]"
                ),
                path=ef,
                fix_hint=(
                    "Add %include <head.h>/<tail.h> or"
                    " explicit ecflow_client calls."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_trap(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF003 — Check .ecf files set a trap handler.

    NCO v11.0 Section II/IV.A: jobs must handle errors.
    ecFlow scripts should set 'trap ... EXIT' or similar
    to ensure cleanup on failure.
    """
    ecf_files = _find_ecf_files(repo_path)
    if not ecf_files:
        return []

    results: list[LintResult] = []
    for ef in ecf_files:
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        name = ef.name
        # Check for trap in file or via head.h include.
        has_trap = bool(re.search(
            r"\btrap\b.*\b(EXIT|ERR|0)\b", content
        ))
        has_head = "%include <head.h>" in content

        if has_trap or has_head:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF003",
                message=(
                    f"{name}: has trap handler"
                    f"{' (via head.h)' if has_head else ''}."
                    " [NCO v11.0 II]"
                ),
                path=ef,
            ))
        else:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OECF003",
                message=(
                    f"{name}: no trap handler found."
                    " [NCO v11.0 II]"
                ),
                path=ef,
                fix_hint=(
                    "Add 'trap ... EXIT' or use"
                    " %include <head.h> which sets traps."
                ),
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_directives(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF004 — Check PBS/Slurm directives are well-formed.

    NCO v11.0 Section II: PBS directives (#PBS -l ...) and
    SBATCH directives (#SBATCH --...) must be syntactically
    valid.
    """
    ecf_files = _find_ecf_files(repo_path)
    if not ecf_files:
        return []

    results: list[LintResult] = []
    for ef in ecf_files:
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        name = ef.name
        has_pbs = False
        has_sbatch = False
        bad_lines: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#PBS"):
                has_pbs = True
                if not _PBS_DIRECTIVE.match(stripped):
                    bad_lines.append(f"{name}:{i}")
            elif stripped.startswith("#SBATCH"):
                has_sbatch = True
                if not _SBATCH_DIRECTIVE.match(stripped):
                    bad_lines.append(f"{name}:{i}")

        if not has_pbs and not has_sbatch:
            # No scheduler directives — may be in ecFlow vars.
            continue

        if bad_lines:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OECF004",
                message=(
                    f"{name}: malformed scheduler directives"
                    f" at {', '.join(bad_lines[:3])}."
                    " [NCO v11.0 II]"
                ),
                path=ef,
                fix_hint=(
                    "Use '#PBS -<flag> <value>' or"
                    " '#SBATCH --<flag>=<value>' syntax."
                ),
            ))
        else:
            scheduler = "PBS" if has_pbs else "SBATCH"
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF004",
                message=(
                    f"{name}: {scheduler} directives"
                    " well-formed. [NCO v11.0 II]"
                ),
                path=ef,
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_hardcoded_paths(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF005 — Check for hard-coded absolute paths.

    NCO v11.0 Section IV.A.vii / IV.B.4: no external-pointing
    symlinks or hard-coded paths. Flag /lfs/, /work/, /scratch/,
    /gpfs/ etc. outside of variable assignments.
    """
    ecf_files = _find_ecf_files(repo_path)
    if not ecf_files:
        return []

    results: list[LintResult] = []
    for ef in ecf_files:
        content = ef.read_text(
            encoding="utf-8", errors="replace"
        )
        name = ef.name
        bad_lines: list[str] = []

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Skip comments and empty lines.
            if not stripped or stripped.startswith("#"):
                continue
            # Skip variable assignments (defaults are ok).
            if _ASSIGNMENT_LINE.match(stripped):
                continue
            # Check for hard-coded paths.
            prefixes = config.ecflow.hardcoded_path_prefixes
            for prefix in prefixes:
                if prefix in stripped:
                    bad_lines.append(f"{name}:{i}")
                    break

        if bad_lines:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OECF005",
                message=(
                    f"{name}: hard-coded paths at"
                    f" {', '.join(bad_lines[:3])}."
                    " [NCO v11.0 IV.A.vii]"
                ),
                path=ef,
                fix_hint=(
                    "Use environment variables instead of"
                    " hard-coded absolute paths."
                ),
            ))
        else:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF005",
                message=(
                    f"{name}: no hard-coded paths found."
                    " [NCO v11.0 IV.A.vii]"
                ),
                path=ef,
            ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_custom_head_tail(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF006 — Verify custom head.h/tail.h content.

    If include/head.h or include/tail.h exists in the repo,
    parse them to verify they contain ecflow_client --init
    and --complete. Skip when files don't exist (standard
    NCO head/tail presumed correct).
    """
    results: list[LintResult] = []
    include_dir = repo_path / "include"
    if not include_dir.is_dir():
        return []

    head = include_dir / "head.h"
    tail = include_dir / "tail.h"

    if head.is_file():
        content = head.read_text(
            encoding="utf-8", errors="replace"
        )
        if "ecflow_client --init" in content:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF006",
                message=(
                    "include/head.h contains"
                    " ecflow_client --init."
                    " [NCO v11.0 II]"
                ),
                path=head,
            ))
        else:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OECF006",
                message=(
                    "Custom include/head.h missing"
                    " ecflow_client --init."
                    " [NCO v11.0 II]"
                ),
                path=head,
                fix_hint=(
                    "Add ecflow_client --init to head.h"
                    " or use standard NCO head.h."
                ),
            ))

    if tail.is_file():
        content = tail.read_text(
            encoding="utf-8", errors="replace"
        )
        if "ecflow_client --complete" in content:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF006",
                message=(
                    "include/tail.h contains"
                    " ecflow_client --complete."
                    " [NCO v11.0 II]"
                ),
                path=tail,
            ))
        else:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OECF006",
                message=(
                    "Custom include/tail.h missing"
                    " ecflow_client --complete."
                    " [NCO v11.0 II]"
                ),
                path=tail,
                fix_hint=(
                    "Add ecflow_client --complete to"
                    " tail.h or use standard NCO tail.h."
                ),
            ))

    return results
