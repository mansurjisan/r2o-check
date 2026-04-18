"""Tests for SARIF formatter."""

from __future__ import annotations

import json
from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import LintResult, LintRunner, Status
from r2o_check.formatters.sarif import format_results_sarif

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


class TestSarifFormatter:
    def test_valid_sarif(self) -> None:
        config = Config()
        runner = LintRunner(RRFS, config)
        results = runner.run()
        text = format_results_sarif(results, config)
        data = json.loads(text)
        assert data["version"] == "2.1.0"
        assert "runs" in data
        assert data["runs"][0]["tool"]["driver"]["name"] == "r2o-check"

    def test_only_non_pass_results(self) -> None:
        config = Config()
        results = [
            LintResult(status=Status.PASS, rule_id="R2OTEST", message="ok"),
            LintResult(status=Status.FAIL, rule_id="R2OTEST", message="bad"),
        ]
        text = format_results_sarif(results, config)
        data = json.loads(text)
        assert len(data["runs"][0]["results"]) == 1
        assert data["runs"][0]["results"][0]["level"] == "error"

    def test_empty_results(self) -> None:
        config = Config()
        text = format_results_sarif([], config)
        data = json.loads(text)
        assert data["runs"][0]["results"] == []

    def test_line_populates_start_line(
        self, tmp_path: Path
    ) -> None:
        config = Config()
        target = tmp_path / "scripts" / "exmodel.sh"
        target.parent.mkdir(parents=True)
        target.write_text("#!/bin/bash\n", encoding="utf-8")
        results = [
            LintResult(
                status=Status.WARN,
                rule_id="R2OECF005",
                message="bad",
                path=target,
                line=17,
            ),
        ]
        text = format_results_sarif(
            results, config, repo_path=tmp_path
        )
        data = json.loads(text)
        loc = data["runs"][0]["results"][0]["locations"][0]
        assert loc["physicalLocation"]["region"]["startLine"] == 17
        assert loc["physicalLocation"]["artifactLocation"]["uri"] == (
            "scripts/exmodel.sh"
        )
