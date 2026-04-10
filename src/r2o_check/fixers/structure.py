"""Auto-fixers for structure rules (R2OSTR001-008)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from r2o_check.rules.structure import REQUIRED_DIRS


@dataclass
class FixAction:
    """A single fix to apply."""

    rule_id: str
    description: str
    path: Path
    applied: bool = False


def fix_missing_directories(
    repo_path: Path, *, dry_run: bool = True
) -> list[FixAction]:
    """Create missing required directories with .gitkeep."""
    actions: list[FixAction] = []
    for dirname, rule_id, *_ in REQUIRED_DIRS:
        target = repo_path / dirname
        if target.is_dir():
            continue
        action = FixAction(
            rule_id=rule_id,
            description=f"Create '{dirname}/' with .gitkeep",
            path=target,
        )
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
            (target / ".gitkeep").touch()
            action.applied = True
        actions.append(action)
    return actions
