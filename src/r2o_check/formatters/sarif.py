"""SARIF formatter for GitHub Code Scanning integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from r2o_check import __version__
from r2o_check.config import Config
from r2o_check.engine import LintResult, Status

_SARIF_LEVEL = {
    Status.PASS: "none",
    Status.WARN: "warning",
    Status.FAIL: "error",
    Status.ERROR: "error",
}


def format_results_sarif(
    results: list[LintResult],
    config: Config,
    repo_path: Path | None = None,
) -> str:
    """Format results as SARIF 2.1.0 for Code Scanning.

    Paths are made relative to ``repo_path`` when provided,
    falling back to the current working directory otherwise.
    """
    base = (repo_path or Path.cwd()).resolve()
    # Only include non-passing results in SARIF.
    findings = [
        r for r in results if r.status != Status.PASS
    ]

    sarif_results: list[dict[str, Any]] = []
    for r in findings:
        result: dict[str, Any] = {
            "ruleId": r.rule_id,
            "level": _SARIF_LEVEL[r.status],
            "message": {"text": r.message},
        }
        if r.path and r.path.is_file():
            try:
                rel = r.path.resolve().relative_to(base).as_posix()
            except ValueError:
                rel = str(r.path)
            result["locations"] = [{
                "physicalLocation": {
                    "artifactLocation": {"uri": rel},
                    "region": {
                        "startLine": r.line if r.line else 1,
                    },
                }
            }]
        if r.fix_hint:
            result["fixes"] = [{
                "description": {"text": r.fix_hint}
            }]
        sarif_results.append(result)

    sarif: dict[str, Any] = {
        "$schema": (
            "https://raw.githubusercontent.com/oasis-tcs/"
            "sarif-spec/main/sarif-2.1/"
            "schema/sarif-schema-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "r2o-check",
                    "version": __version__,
                    "informationUri": (
                        "https://github.com/mansurjisan"
                        "/r2o-check"
                    ),
                }
            },
            "results": sarif_results,
        }],
    }
    return json.dumps(sarif, indent=2)
