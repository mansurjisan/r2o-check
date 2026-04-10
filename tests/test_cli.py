"""Tests for the CLI interface."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from r2o_check.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "compliant_minimal"
NONCOMPLIANT = FIXTURES / "noncompliant_minimal"


def test_lint_compliant_exits_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(COMPLIANT)])
    assert result.exit_code == 0
    assert "PASS" in result.output


def test_lint_noncompliant_exits_one() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(NONCOMPLIANT)])
    assert result.exit_code == 1
    assert "FAIL" in result.output


def test_lint_nonexistent_path() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", "/nonexistent/path"])
    assert result.exit_code != 0


def test_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_lint_shows_rule_ids() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(NONCOMPLIANT)])
    assert "R2OSTR001" in result.output
    assert "R2OSTR005" in result.output


def test_lint_compliant_shows_all_rule_ids() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(COMPLIANT)])
    for i in range(1, 9):
        assert f"R2OSTR{i:03d}" in result.output
