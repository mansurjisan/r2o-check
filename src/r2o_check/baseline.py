"""Baseline support for incremental adoption.

A baseline records the set of current violations in a repo so
subsequent ``r2o-check lint --baseline …`` runs only report *new*
violations. Paths are stored relative to the repo root so the
baseline is portable across checkout locations.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from r2o_check.engine import LintResult, Status

BASELINE_VERSION = 2
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


# Strip the ``file:line:`` prefix a rule may embed in the message
# so the digest is stable across file moves / line drifts (those
# are already carried by the other fingerprint components).
_LINE_PREFIX = re.compile(r"^[^:\s]+:\d+:?\s*")


def _message_digest(message: str) -> str:
    """Short, stable hash of a finding's distinguishing text.

    We strip any leading ``file:line`` because the relpath and
    line are already separate fingerprint fields; duplicating
    them would make the digest flip whenever the line shifts,
    defeating the point of having a separate line component.
    """
    trimmed = _LINE_PREFIX.sub("", message).strip()
    return hashlib.sha1(
        trimmed.encode("utf-8", errors="replace")
    ).hexdigest()[:8]


def fingerprint(
    result: LintResult, repo_path: Path
) -> str:
    """Stable identity for a finding.

    Format: ``rule_id|relpath|line|detail`` where ``detail`` is an
    8-char SHA-1 of the distinguishing portion of the message.
    The detail component disambiguates two findings from the same
    rule at the same (path, line) but targeting different things
    (e.g. two missing ex-scripts referenced on one line).
    """
    line = "" if result.line is None else str(result.line)
    detail = _message_digest(result.message)
    return (
        f"{result.rule_id}"
        f"|{_rel_path(result.path, repo_path)}"
        f"|{line}"
        f"|{detail}"
    )


@dataclass
class Baseline:
    """An on-disk record of accepted (ignored) findings."""

    fingerprints: set[str]
    created: str
    version: int = BASELINE_VERSION

    @classmethod
    def empty(cls) -> Baseline:
        return cls(
            fingerprints=set(),
            created=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_results(
        cls,
        results: Iterable[LintResult],
        repo_path: Path,
    ) -> Baseline:
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
    def load(cls, path: Path) -> Baseline:
        data = json.loads(path.read_text(encoding="utf-8"))
        version = data.get("version", 1)
        if version != BASELINE_VERSION:
            hint = (
                " Regenerate with 'r2o-check baseline"
                f" {path.parent}'."
                if version < BASELINE_VERSION else ""
            )
            raise ValueError(
                f"Unsupported baseline version {version};"
                f" expected {BASELINE_VERSION}.{hint}"
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

    def find_stale(
        self,
        results: Iterable[LintResult],
        repo_path: Path,
    ) -> set[str]:
        """Return baseline entries no longer matching any finding.

        A "stale" entry is one whose fingerprint does not appear in
        the current FAIL/WARN results — typically because the
        underlying violation was fixed. Stale entries silently mask
        regressions if left in the baseline.
        """
        current = {
            fingerprint(r, repo_path)
            for r in results
            if r.status in (Status.FAIL, Status.WARN)
        }
        return self.fingerprints - current
