"""Environment variable checks for J-jobs.

NCO Implementation Standards v11.0, Section III.A, Table 1.
Validates that J-jobs set required environment variables.
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

# Variables that §III.A Table 1 says are set in the J-job.
# These are the ones r2o-check can verify statically by
# checking for assignment or export patterns in J-job files.
JJOB_REQUIRED_VARS: list[tuple[str, str]] = [
    ("NET", "Model name (1st level of com)"),
    ("RUN", "Model run name (3rd level of com)"),
    ("PDY", "Date in YYYYMMDD format"),
    ("cycle", "Cycle time in tHHz format"),
    ("DATA", "Job working directory"),
    ("COMIN", "Input com directory"),
    ("COMOUT", "Output com directory"),
]

# Pattern-based vars — the "model" part varies per package.
# We check for any variable matching USH*, EXEC*, PARM*, FIX*.
JJOB_PATTERN_VARS: list[tuple[str, str]] = [
    ("USH", "Location of model ush files"),
    ("EXEC", "Location of model exec files"),
    ("PARM", "Location of model parm files"),
    ("FIX", "Location of model fix files"),
]

# Matches: export VAR=..., VAR=..., or ${VAR:-...}
def _var_is_set(content: str, var: str) -> bool:
    """Check if a variable is assigned in file content."""
    v = re.escape(var)
    pat = rf"(?:export\s+)?{v}\s*=|\$\{{{v}:-"
    return re.search(pat, content) is not None


def _pattern_var_is_set(content: str, prefix: str) -> bool:
    """Check if any variable starting with prefix is assigned."""
    pat = rf"(?:export\s+)?{re.escape(prefix)}[A-Za-z_]*\s*="
    if re.search(pat, content):
        return True
    pat2 = rf"\$\{{{re.escape(prefix)}[A-Za-z_]*:-"
    return re.search(pat2, content) is not None


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_jjob_env_vars(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OENV001 — Check J-jobs set required env vars.

    NCO v11.0 Section III.A, Table 1: J-jobs must set
    NET, RUN, PDY, cycle, DATA, COMIN, COMOUT and the
    model-specific location vars (USH*, EXEC*, PARM*, FIX*).
    """
    jobs_dir = repo_path / "jobs"
    if not jobs_dir.is_dir():
        return []

    results: list[LintResult] = []
    for jf in sorted(jobs_dir.iterdir()):
        if not jf.is_file():
            continue
        content = jf.read_text(encoding="utf-8", errors="replace")

        # Check exact-name vars.
        for var, desc in JJOB_REQUIRED_VARS:
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
                    status=Status.WARN,
                    rule_id="R2OENV001",
                    message=(
                        f"{jf.name}: missing ${var}"
                        f" ({desc})."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add 'export {var}=...' or"
                        f" '${{{var}:-...}}' to {jf.name}."
                    ),
                ))

        # Check pattern vars (USH*, EXEC*, PARM*, FIX*).
        for prefix, desc in JJOB_PATTERN_VARS:
            if _pattern_var_is_set(content, prefix):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OENV001",
                    message=(
                        f"{jf.name}: sets ${prefix}* var."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OENV001",
                    message=(
                        f"{jf.name}: missing ${prefix}*"
                        f" var ({desc})."
                        " [NCO v11.0 III.A Table 1]"
                    ),
                    path=jf,
                    fix_hint=(
                        f"Add 'export {prefix}model=...' to"
                        f" {jf.name}."
                    ),
                ))
    return results
