"""Deep ecFlow .def validation (optional).

Uses the ``ecflow`` Python library (installed via system package
manager, not PyPI) to parse ``.def`` files and surface structural
problems the text-based rules cannot detect.

When the ``ecflow`` module is not importable, the rule emits a
single informational PASS result and returns — the feature is
opt-in via the ``r2o-check[ecflow]`` extra, and a missing library
is not itself an NCO violation.
"""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    MODEL_REPO_TYPES,
    LintResult,
    Status,
    register_rule,
)


def _find_def_files(repo_path: Path) -> list[Path]:
    """Locate .def files under common ecFlow layout directories."""
    roots = [
        repo_path / "ecf",
        repo_path / "def",
        repo_path,
    ]
    seen: set[Path] = set()
    ordered: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.def")):
            if p.is_file() and p not in seen:
                seen.add(p)
                ordered.append(p)
    return ordered


@register_rule(applies_to=MODEL_REPO_TYPES)
def check_ecf_def_parses(
    repo_path: Path, config: Config
) -> list[LintResult]:
    """R2OECF007 — Parse .def files with the ecflow library.

    Requires the optional ``ecflow`` Python module. When the
    library is available and ``.def`` files exist, each file is
    parsed via ``ecflow.Defs``; a parse failure is reported as
    FAIL with the ecflow error message. When the library is not
    installed the rule is inert (no results emitted).
    """
    def_files = _find_def_files(repo_path)
    if not def_files:
        return []

    try:
        import ecflow  # type: ignore[import-not-found]
    except Exception:
        return []

    results: list[LintResult] = []
    for df in def_files:
        try:
            defs = ecflow.Defs()
            defs.load(str(df))
        except Exception as exc:
            results.append(LintResult(
                status=Status.FAIL,
                rule_id="R2OECF007",
                message=(
                    f"{df.name}: failed to parse as ecFlow"
                    f" .def — {exc.__class__.__name__}:"
                    f" {exc}."
                    " [NCO v11.0 II]"
                ),
                path=df,
                fix_hint=(
                    "Load the file with 'ecflow_client"
                    " --load=<file>' locally to see the"
                    " parser error in context."
                ),
            ))
        else:
            results.append(LintResult(
                status=Status.PASS,
                rule_id="R2OECF007",
                message=(
                    f"{df.name}: parsed successfully via"
                    " ecflow lib. [NCO v11.0 II]"
                ),
                path=df,
            ))
    return results
