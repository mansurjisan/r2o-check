"""Tests for the core lint engine."""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import (
    ALL_REPO_TYPES,
    MODEL_REPO_TYPES,
    LintResult,
    LintRunner,
    RuleEntry,
    Status,
    _infer_rule_id,
    register_rule,
)


def test_status_values() -> None:
    assert Status.PASS.value == "pass"
    assert Status.WARN.value == "warn"
    assert Status.FAIL.value == "fail"
    assert Status.ERROR.value == "error"


def test_lint_result_defaults() -> None:
    r = LintResult(
        status=Status.PASS, rule_id="R2OTEST", message="ok"
    )
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
    def my_rule(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """R2OSTR099 — Test rule."""
        return []

    assert _infer_rule_id(my_rule) == "R2OSTR099"


def test_infer_rule_id_fallback() -> None:
    def my_rule(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """No rule ID here."""
        return []

    assert _infer_rule_id(my_rule) == "my_rule"


def test_runner_catches_exceptions(tmp_path: Path) -> None:
    """A rule that raises produces ERROR, not a crash."""

    def bad_rule(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """R2OTEST001 — Always raises."""
        raise RuntimeError("boom")

    runner = LintRunner(tmp_path)
    runner._rules = {
        "bad_rule": RuleEntry(
            func=bad_rule, applies_to=ALL_REPO_TYPES
        )
    }
    results = runner.run()
    assert len(results) == 1
    assert results[0].status == Status.ERROR
    assert "boom" in results[0].message


def test_runner_discover_rules(tmp_path: Path) -> None:
    runner = LintRunner(tmp_path)
    runner.discover_rules()
    assert len(runner._rules) >= 8


def test_register_rule_with_applies_to() -> None:
    """@register_rule(applies_to=[...]) sets metadata."""

    @register_rule(applies_to=MODEL_REPO_TYPES)
    def _test_rule_meta(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """R2OTEST999 — test."""
        return []

    from r2o_check.engine import _RULE_REGISTRY

    entry = _RULE_REGISTRY.get("_test_rule_meta")
    assert entry is not None
    assert entry.applies_to == MODEL_REPO_TYPES

    # Clean up.
    del _RULE_REGISTRY["_test_rule_meta"]


def test_register_rule_bare_decorator() -> None:
    """@register_rule without parens defaults to ALL types."""

    @register_rule
    def _test_rule_bare(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """R2OTEST998 — test."""
        return []

    from r2o_check.engine import _RULE_REGISTRY

    entry = _RULE_REGISTRY.get("_test_rule_bare")
    assert entry is not None
    assert entry.applies_to == ALL_REPO_TYPES

    del _RULE_REGISTRY["_test_rule_bare"]


def test_run_rules_applies_disabled_and_suppression(
    tmp_path: Path,
) -> None:
    """run_rules shares post-processing with run."""
    from r2o_check.engine import _RULE_REGISTRY

    @register_rule(applies_to=ALL_REPO_TYPES)
    def _test_rule_parity(
        repo_path: Path, config: Config
    ) -> list[LintResult]:
        """R2OTEST900 — parity."""
        return [
            LintResult(
                status=Status.FAIL,
                rule_id="R2OTEST900",
                message="should be filtered",
            ),
        ]

    try:
        # Disabled via config should drop the result.
        config = Config(disabled_rules=["R2OTEST900"])
        runner = LintRunner(tmp_path, config)
        out = runner.run_rules(["R2OTEST900"])
        assert out == []

        # Severity override should flip the status.
        config = Config(
            severity_overrides={"R2OTEST900": "warn"},
        )
        runner = LintRunner(tmp_path, config)
        out = runner.run_rules(["R2OTEST900"])
        assert len(out) == 1
        assert out[0].status == Status.WARN
    finally:
        del _RULE_REGISTRY["_test_rule_parity"]
