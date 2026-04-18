"""Baseline support for incremental adoption.

A baseline records the set of current violations in a repo so
subsequent ``r2o-check lint --baseline …`` runs only report *new*
violations. Paths are stored relative to the repo root so the
baseline is portable across checkout locations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from r2o_check.engine import LintResult, Status

BASELINE_VERSION = 1
DEFAULT_BASELINE_NAME = ".r2o-check-baseline.json"


def _rel_path(p: Path | None, repo_path: Path) -> str:
    if p is None:
        return ""
    try:
        return p.resolve().relative_to(
            repo_path.resolve()
        ).as_posix()
    except ValueError:
        return str(p)


def fingerprint(
    result: LintResult, repo_path: Path
) -> str:
    """Stable identity for a finding: rule|relpath|line."""
    line = "" if result.line is None else str(result.line)
    return f"{result.rule_id}|{_rel_path(result.path, repo_path)}|{line}"


@dataclass
class Baseline:
    """An on-disk record of accepted (ignored) findings."""

    fingerprints: set[str]
    created: str
    version: int = BASELINE_VERSION

    @classmethod
    def empty(cls) -> "Baseline":
        return cls(
            fingerprints=set(),
            created=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_results(
        cls,
        results: Iterable[LintResult],
        repo_path: Path,
    ) -> "Baseline":
        fps = {
            fingerprint(r, repo_path)
            for r in results
            if r.status in (Status.FAIL, Status.WARN)
        }
        return cls(
            fingerprints=fps,
            created=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def load(cls, path: Path) -> "Baseline":
        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("version", 1)
        if version != BASELINE_VERSION:
            raise ValueError(
                f"Unsupported baseline version {version};"
                f" expected {BASELINE_VERSION}."
            )
        fps = set(data.get("findings", []))
        created = data.get("created", "")
        return cls(
            fingerprints=fps,
            created=created,
            version=version,
        )

    def save(self, path: Path) -> None:
        payload = {
            "version": self.version,
            "created": self.created,
            "findings": sorted(self.fingerprints),
        }
        path.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )

    def filter(
        self,
        results: Iterable[LintResult],
        repo_path: Path,
    ) -> list[LintResult]:
        """Drop FAIL/WARN results whose fingerprint is baselined.

        PASS and ERROR results pass through unchanged. ERROR is
        surfaced so baseline misuse (e.g. rule crashes) is still
        visible.
        """
        kept: list[LintResult] = []
        for r in results:
            if r.status in (Status.FAIL, Status.WARN):
                fp = fingerprint(r, repo_path)
                if fp in self.fingerprints:
                    continue
            kept.append(r)
        return kept
