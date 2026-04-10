"""Tests for the CLI interface."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from r2o_check.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "compliant_minimal"
NONCOMPLIANT = FIXTURES / "noncompliant_minimal"
TOOL_REPO = FIXTURES / "tool_repo"


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


def test_lint_compliant_shows_structure_rule_ids() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(COMPLIANT)])
    for i in range(1, 9):
        assert f"R2OSTR{i:03d}" in result.output


def test_lint_tool_repo_exits_zero() -> None:
    """Tool repo has no applicable rules — clean exit."""
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(TOOL_REPO)])
    assert result.exit_code == 0


def test_lint_shows_naming_rules() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(COMPLIANT)])
    assert "R2ONAM001" in result.output


def test_lint_json_format() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["lint", str(COMPLIANT), "--format", "json"]
    )
    assert result.exit_code == 0
    assert '"version"' in result.output
    assert '"results"' in result.output


def test_lint_markdown_format() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["lint", str(COMPLIANT), "--format", "markdown"]
    )
    assert result.exit_code == 0
    assert "## r2o-check" in result.output


def test_lint_html_format() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["lint", str(COMPLIANT), "--format", "html"]
    )
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in result.output


def test_lint_output_to_file(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(COMPLIANT), "--format", "json", "-o", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    assert '"version"' in out.read_text()
