"""Modulefile content checks.

NCO Implementation Standards v11.0, Section VI.A.4-5.
Validates that Lua modulefiles declare required dependencies.
"""

from __future__ import annotations

import re
from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    MODULE_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)

# Pattern matching Lua load() or depends_on() calls.
_LOAD_RE = re.compile(
    r"""(?:load|depends_on|always_load)\s*\(\s*["']([^"']+)"""
)

# Common compiler module name prefixes.
_COMPILER_PATTERNS = {
    "intel", "cce", "gcc", "cray", "oneapi", "cpe",
    "PrgEnv-intel", "PrgEnv-cray", "PrgEnv-gnu",
}

# Common MPI module name prefixes.
_MPI_PATTERNS = {
    "cray-mpich", "impi", "openmpi", "mvapich",
    "cray-pals",
}


def _find_lua_modulefiles(repo_path: Path) -> list[Path]:
    """Find .lua modulefiles under modulefiles/."""
    mf_dir = repo_path / "modulefiles"
    if not mf_dir.is_dir():
        return []
    return sorted(mf_dir.rglob("*.lua"))


def _extract_loaded_modules(content: str) -> list[str]:
    """Extract module names from load/depends_on calls."""
    return _LOAD_RE.findall(content)


def _has_compiler(modules: list[str]) -> bool:
    """Check if any loaded module is a compiler."""
    for mod in modules:
        base = mod.split("/")[0]
        if base in _COMPILER_PATTERNS:
            return True
    return False


def _has_mpi(modules: list[str]) -> bool:
    """Check if any loaded module is an MPI library."""
    for mod in modules:
        base = mod.split("/")[0]
        if base in _MPI_PATTERNS:
            return True
    return False


@register_rule(applies_to=MODULE_REPO_TYPES)
def check_modulefile_deps(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OMOD001 — Check modulefiles declare dependencies.

    NCO v11.0 Section VI.A.4-5: build modulefiles must
    define the compiler version and library versions via
    module load calls. This rule checks that at least one
    compiler module is loaded in build modulefiles.
    """
    lua_files = _find_lua_modulefiles(repo_path)
    if not lua_files:
        return []

    results: list[LintResult] = []
    for lf in lua_files:
        content = lf.read_text(
            encoding="utf-8", errors="replace"
        )
        modules = _extract_loaded_modules(content)
        name = lf.name

        # Only check build modulefiles (heuristic: filename
        # contains "build").
        is_build = "build" in lf.name.lower()

        if not modules:
            results.append(LintResult(
                status=Status.WARN,
                rule_id="R2OMOD001",
                message=(
                    f"Modulefile '{name}' loads no modules."
                    " [NCO v11.0 VI.A.4]"
                ),
                path=lf,
                fix_hint=(
                    "Add load() calls for compiler and"
                    " library dependencies."
                ),
            ))
            continue

        if is_build:
            if _has_compiler(modules):
                results.append(LintResult(
                    status=Status.PASS,
                    rule_id="R2OMOD001",
                    message=(
                        f"Build modulefile '{name}'"
                        " loads a compiler."
                        " [NCO v11.0 VI.A.4]"
                    ),
                    path=lf,
                ))
            else:
                results.append(LintResult(
                    status=Status.WARN,
                    rule_id="R2OMOD001",
                    message=(
                        f"Build modulefile '{name}'"
                        " does not load a compiler."
                        " [NCO v11.0 VI.A.4]"
                    ),
                    path=lf,
                    fix_hint=(
                        "Add load('intel/...') or"
                        " equivalent compiler module."
                    ),
                ))
        else:
            # Non-build modulefiles: just note they exist.
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OMOD001",
                message=(
                    f"Modulefile '{name}' loads"
                    f" {len(modules)} module(s)."
                    " [NCO v11.0 VI.A.5]"
                ),
                path=lf,
            ))
    return results
