"""Tests for the core lint engine."""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    LintResult,
    LintRunner,
    Status,
    _infer_rule_id,
)


def test_status_values() -> None:
    assert Status.PASS.value == "pass"
    assert Status.WARN.value == "warn"
    assert Status.FAIL.value == "fail"
    assert Status.ERROR.value == "error"


def test_lint_result_defaults() -> None:
    r = LintResult(status=Status.PASS, rule_id="R2OTEST", message="ok")
    assert r.path is None
    assert r.fix_hint is None


def test_lint_result_with_all_fields(tmp_path: Path) -> None:
    r = LintResult(
        status=Status.FAIL,
        rule_id="R2OTEST",
        message="bad",
        path=tmp_path,
        fix_hint="fix it",
    )
    assert r.path == tmp_path
    assert r.fix_hint == "fix it"


def test_infer_rule_id_from_docstring() -> None:
    def my_rule(repo_path: Path, config: Config) -> list[LintResult]:
        """R2OSTR099 — Test rule."""
        return []

    assert _infer_rule_id(my_rule) == "R2OSTR099"


def test_infer_rule_id_fallback() -> None:
    def my_rule(repo_path: Path, config: Config) -> list[LintResult]:
        """No rule ID here."""
        return []

    assert _infer_rule_id(my_rule) == "my_rule"


def test_runner_catches_exceptions(tmp_path: Path) -> None:
    """A rule that raises should produce an ERROR result, not crash."""

    def bad_rule(repo_path: Path, config: Config) -> list[LintResult]:
        """R2OTEST001 — Always raises."""
        raise RuntimeError("boom")

    runner = LintRunner(tmp_path)
    # Manually inject a bad rule.
    runner._rules = {"bad_rule": bad_rule}
    results = runner.run()
    assert len(results) == 1
    assert results[0].status == Status.ERROR
    assert "boom" in results[0].message


def test_runner_discover_rules(tmp_path: Path) -> None:
    runner = LintRunner(tmp_path)
    runner.discover_rules()
    assert len(runner._rules) >= 8  # At least the 8 structure rules
