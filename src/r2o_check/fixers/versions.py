"""Auto-fixers for versions rules (R2OVER001-002)."""

from __future__ import annotations

from pathlib import Path

from r2o_check.fixers.structure import FixAction

_RUN_VER_TEMPLATE = """\
# Runtime package and module versions.
# See NCO v11.0 Section VI.B, Table 3.
export model_ver=v0.0.0
"""

_BUILD_VER_TEMPLATE = """\
# Build-time package and module versions.
# See NCO v11.0 Section VI.B, Table 3.
export model_ver=v0.0.0
"""


def fix_missing_version_files(
    repo_path: Path, *, dry_run: bool = True
) -> list[FixAction]:
    """Stub versions/run.ver and build.ver if missing."""
    actions: list[FixAction] = []
    ver_dir = repo_path / "versions"

    for fname, rule_id, template in [
        ("run.ver", "R2OVER001", _RUN_VER_TEMPLATE),
        ("build.ver", "R2OVER002", _BUILD_VER_TEMPLATE),
    ]:
        target = ver_dir / fname
        if target.is_file():
            continue
        action = FixAction(
            rule_id=rule_id,
            description=f"Create 'versions/{fname}' stub",
            path=target,
        )
        if not dry_run:
            ver_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(template, encoding="utf-8")
            action.applied = True
        actions.append(action)
    return actions
