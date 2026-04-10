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


@register_rule(
    applies_to=BUILD_REPO_TYPES,
    mutually_exclusive_with=["R2OBLD002"],
)
def check_makefile_targets(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OBLD001 — Check Makefiles have required targets.

    NCO v11.0 Section VI.A.8: four critical targets must be
    defined in every makefile: all, debug, install, clean.
    """
    makefiles = _find_makefiles(repo_path)
    if not makefiles:
        # No Makefiles — defer to R2OBLD002 (CMake) if
        # CMakeLists.txt exists; otherwise warn.
        if _find_cmake_files(repo_path):
            return []
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


# CMake equivalent targets.
CMAKE_EXPECTED_PATTERNS: list[tuple[str, str]] = [
    ("install", r"install\s*\("),
    ("project", r"project\s*\("),
]


def _find_cmake_files(repo_path: Path) -> list[Path]:
    """Find CMakeLists.txt under sorc/."""
    sorc = repo_path / "sorc"
    if not sorc.is_dir():
        return []
    return sorted(sorc.rglob("CMakeLists.txt"))


@register_rule(
    applies_to=BUILD_REPO_TYPES,
    mutually_exclusive_with=["R2OBLD001"],
)
def check_cmake_build(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OBLD002 — Check CMake build system.

    NCO v11.0 Section VI.A.8 equivalent for CMake: project()
    and install() directives should be present. WARN severity
    because CMake is the modern convention but NCO §VI.A.8
    explicitly references Makefile targets.
    """
    cmake_files = _find_cmake_files(repo_path)
    if not cmake_files:
        # No CMake — defer to R2OBLD001 (Makefile) if present.
        if _find_makefiles(repo_path):
            return []
        sorc = repo_path / "sorc"
        if not sorc.is_dir():
            return []
        return [LintResult(
            status=Status.WARN,
            rule_id="R2OBLD002",
            message=(
                "No CMakeLists.txt found under sorc/."
                " [NCO v11.0 VI.A.8]"
            ),
            path=sorc,
            fix_hint="Add a CMakeLists.txt or Makefile.",
        )]

    results: list[LintResult] = []
    for cf in cmake_files:
        content = cf.read_text(
            encoding="utf-8", errors="replace"
        )
        rel = cf.relative_to(repo_path)

        for label, pattern in CMAKE_EXPECTED_PATTERNS:
            if re.search(pattern, content):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OBLD002",
                    message=(
                        f"{rel}: has '{label}' directive."
                        " [NCO v11.0 VI.A.8]"
                    ),
                    path=cf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OBLD002",
                    message=(
                        f"{rel}: missing '{label}' directive."
                        " [NCO v11.0 VI.A.8]"
                    ),
                    path=cf,
                    fix_hint=(
                        f"Add '{label}(...)' to {rel}."
                    ),
                ))
    return results
