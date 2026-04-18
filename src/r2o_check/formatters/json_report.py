"""JSON formatter for lint results."""

from __future__ import annotations

import json
from typing import Any

from r2o_check import __version__
from r2o_check.config import Config
from r2o_check.engine import LintResult, Status


def format_results_json(
    results: list[LintResult],
    config: Config,
) -> str:
    """Format results as a JSON string."""
    counts = {s: 0 for s in Status}
    for r in results:
        counts[r.status] += 1

    output: dict[str, Any] = {
        "version": __version__,
        "repo_type": config.repo_type.value,
        "summary": {
            "pass": counts[Status.PASS],
            "warn": counts[Status.WARN],
            "fail": counts[Status.FAIL],
            "error": counts[Status.ERROR],
            "total": len(results),
            "compliance_score": (
                round(100 * counts[Status.PASS] / len(results))
                if results else 100
            ),
        },
        "results": [
            {
                "rule_id": r.rule_id,
                "status": r.status.value,
                "message": r.message,
                "path": str(r.path) if r.path else None,
                "line": r.line,
                "fix_hint": r.fix_hint,
            }
            for r in results
        ],
    }
    return json.dumps(output, indent=2)
