"""Environment variable checks for J-jobs.

NCO Implementation Standards v11.0, Section III.A, Table 1.
Validates that J-jobs set required environment variables.
"""

from __future__ import annotations

import re
from pathlib import Path

from r2o_check._shell import strip_shell_comments
from r2o_check.config import Config
from r2o_check.engine import (
    MODEL_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)

# Core variables every J-job must set (§III.A Table 1).
JJOB_CORE_VARS: list[tuple[str, str]] = [
    ("NET", "Model name (1st level of com)"),
    ("RUN", "Model run name (3rd level of com)"),
    ("PDY", "Date in YYYYMMDD format"),
    ("cycle", "Cycle time in tHHz format"),
    ("DATA", "Job working directory"),
    ("COMIN", "Input com directory"),
    ("COMOUT", "Output com directory"),
]

# Context-dependent pattern vars — vary by job type.
JJOB_CONTEXT_VARS: list[tuple[str, str]] = [
    ("USH", "Location of model ush files"),
    ("EXEC", "Location of model exec files"),
    ("PARM", "Location of model parm files"),
    ("FIX", "Location of model fix files"),
]


def _var_is_set(content: str, var: str) -> bool:
    """Check if a variable is assigned in file content."""
    v = re.escape(var)
    pat = rf"(?:export\s+)?{v}\s*=|\$\{{{v}:-"
    return re.search(pat, content) is not None


def _pattern_var_is_set(content: str, prefix: str) -> bool:
    """Check if any variable starting with prefix is set."""
    p = re.escape(prefix)
    pat = rf"(?:export\s+)?{p}[A-Za-z_]*\s*="
    if re.search(pat, content):
        return True
    pat2 = rf"\$\{{{p}[A-Za-z_]*:-"
    return re.search(pat2, content) is not None


def _iter_jjobs(repo_path: Path) -> list[Path]:
    """Return sorted list of J-job files."""
    jobs_dir = repo_path / "jobs"
    if not jobs_dir.is_dir():
        return []
    return sorted(
        f for f in jobs_dir.iterdir() if f.is_file()
    )


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_core_vars(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OENV001 — Check J-jobs set core env vars.

    NCO v11.0 Section III.A, Table 1: every J-job must set
    NET, RUN, PDY, cycle, DATA, COMIN, COMOUT.
    """
    results: list[LintResult] = []
    for jf in _iter_jjobs(repo_path):
        content = strip_shell_comments(jf.read_text(
            encoding="utf-8", errors="replace"
        ))
        for var, desc in JJOB_CORE_VARS:
            if _var_is_set(content, var):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OENV001",
                    message=(
                        f"{jf.name}: sets ${var}."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                ))
            else:
                results.append(LintResult(
                    status=Status.FAIL,
                    rule_id="R2OENV001",
                    message=(
                        f"{jf.name}: missing ${var}"
                        f" ({desc})."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add 'export {var}=...' or"
                        f" '${{{var}:-...}}' to"
                        f" {jf.name}."
                    ),
                ))
    return results


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_context_vars(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OENV002 — Check J-jobs set context env vars.

    NCO v11.0 Section III.A, Table 1: J-jobs should set
    model-specific location vars (USH*, EXEC*, PARM*, FIX*)
    when used. WARN because some job types legitimately
    omit these.
    """
    results: list[LintResult] = []
    for jf in _iter_jjobs(repo_path):
        content = strip_shell_comments(jf.read_text(
            encoding="utf-8", errors="replace"
        ))
        for prefix, desc in JJOB_CONTEXT_VARS:
            if _pattern_var_is_set(content, prefix):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OENV002",
                    message=(
                        f"{jf.name}: sets ${prefix}* var."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OENV002",
                    message=(
                        f"{jf.name}: missing ${prefix}*"
                        f" var ({desc})."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add 'export {prefix}model=...'"
                        f" to {jf.name}."
                    ),
                ))
    return results
