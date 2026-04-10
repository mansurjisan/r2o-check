"""Build system checks.

NCO Implementation Standards v11.0, Section VI.A.8.
Validates that Makefiles have required targets.
"""

from __future__ import annotations

import re
from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    BUILD_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)

# Required makefile targets per NCO v11.0 §VI.A.8.
REQUIRED_TARGETS: list[str] = [
    "all",
    "debug",
    "install",
    "clean",
]

# Pattern to find a make target definition: "target:" at start
# of line (possibly with prerequisites after the colon).
_TARGET_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:", re.M)


def _find_makefiles(repo_path: Path) -> list[Path]:
    """Find Makefiles under sorc/."""
    sorc = repo_path / "sorc"
    if not sorc.is_dir():
        return []
    makefiles: list[Path] = []
    for name in ("Makefile", "makefile", "GNUmakefile"):
        makefiles.extend(sorc.rglob(name))
    return sorted(makefiles)


def _extract_targets(content: str) -> set[str]:
    """Extract all target names from makefile content."""
    return {m.group(1) for m in _TARGET_RE.finditer(content)}


@register_rule(applies_to=BUILD_REPO_TYPES)
def check_makefile_targets(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OBLD001 — Check Makefiles have required targets.

    NCO v11.0 Section VI.A.8: four critical targets must be
    defined in every makefile: all, debug, install, clean.
    """
    makefiles = _find_makefiles(repo_path)
    if not makefiles:
        # No makefiles found — not necessarily an error;
        # some repos use CMake or other build systems.
        sorc = repo_path / "sorc"
        if not sorc.is_dir():
            return []
        return [LintResult(
            status=Status.WARN,
            rule_id="R2OBLD001",
            message=(
                "No Makefile found under sorc/."
                " [NCO v11.0 VI.A.8]"
            ),
            path=sorc,
            fix_hint=(
                "Add a Makefile with targets: "
                "all, debug, install, clean."
            ),
        )]

    results: list[LintResult] = []
    for mf in makefiles:
        content = mf.read_text(
            encoding="utf-8", errors="replace"
        )
        targets = _extract_targets(content)
        rel = mf.relative_to(repo_path)

        for req in REQUIRED_TARGETS:
            if req in targets:
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OBLD001",
                    message=(
                        f"{rel}: has '{req}' target."
                        " [NCO v11.0 VI.A.8]"
                    ),
                    path=mf,
                ))
            else:
                results.append(LintResult(
                    status=Status.FAIL,
                    rule_id="R2OBLD001",
                    message=(
                        f"{rel}: missing '{req}' target."
                        " [NCO v11.0 VI.A.8]"
                    ),
                    path=mf,
                    fix_hint=(
                        f"Add '{req}:' target to {rel}."
                    ),
                ))
    return results
