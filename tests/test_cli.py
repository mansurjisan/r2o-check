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


def test_lint_table_output_to_file(tmp_path: Path) -> None:
    out = tmp_path / "report.txt"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(COMPLIANT), "-o", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()
    body = out.read_text()
    assert "PASS" in body
    assert "R2OSTR001" in body


def test_fix_skips_scaffolding_for_tool_repo(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "toolproj"
    repo.mkdir()
    (repo / ".r2o-check.yml").write_text(
        "repo_type: tool\n", encoding="utf-8"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["fix", str(repo), "--apply"])
    assert result.exit_code == 0
    for d in (
        "ecf", "jobs", "scripts", "ush", "sorc",
        "parm", "modulefiles", "versions",
    ):
        assert not (repo / d).exists(), (
            f"fix should not scaffold '{d}/' for tool repos"
        )
    assert "tool" in result.output


def test_fix_scaffolds_for_operational_model(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "opmodel"
    repo.mkdir()
    (repo / ".r2o-check.yml").write_text(
        "repo_type: operational_model\n", encoding="utf-8"
    )
    runner = CliRunner()
    result = runner.invoke(main, ["fix", str(repo), "--apply"])
    assert result.exit_code == 0
    assert (repo / "ecf").is_dir()
    assert (repo / "jobs").is_dir()


def test_baseline_creates_file_and_lint_filters(
    tmp_path: Path,
) -> None:
    # Copy noncompliant fixture into tmp so we can write a
    # baseline next to it.
    import shutil
    repo = tmp_path / "repo"
    shutil.copytree(NONCOMPLIANT, repo)

    runner = CliRunner()
    # Generate baseline.
    result = runner.invoke(
        main, ["baseline", str(repo)]
    )
    assert result.exit_code == 0, result.output
    bl_file = repo / ".r2o-check-baseline.json"
    assert bl_file.exists()
    assert "Baselined" in result.output

    # Lint with baseline: all existing FAILs should be
    # suppressed, so exit code is 0.
    result = runner.invoke(
        main,
        ["lint", str(repo), "--baseline", str(bl_file)],
    )
    assert result.exit_code == 0
    # Passes still surface.
    assert "PASS" in result.output


def test_baseline_refuses_overwrite_without_force(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".r2o-check.yml").write_text(
        "repo_type: tool\n", encoding="utf-8"
    )
    existing = repo / ".r2o-check-baseline.json"
    existing.write_text("{}", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["baseline", str(repo)])
    assert result.exit_code != 0
    assert "--force" in result.output

    result = runner.invoke(
        main, ["baseline", str(repo), "--force"]
    )
    assert result.exit_code == 0


def test_lint_baseline_missing_file_errors(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".r2o-check.yml").write_text(
        "repo_type: tool\n", encoding="utf-8"
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(repo), "--baseline", str(repo / "nope.json")],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_lint_baseline_warns_about_stale_entries(
    tmp_path: Path,
) -> None:
    import json
    import shutil
    repo = tmp_path / "repo"
    shutil.copytree(NONCOMPLIANT, repo)

    runner = CliRunner(mix_stderr=False) if (
        "mix_stderr"
        in CliRunner.__init__.__code__.co_varnames
    ) else CliRunner()
    runner.invoke(main, ["baseline", str(repo)])
    bl_file = repo / ".r2o-check-baseline.json"

    # Inject a fake finding into the baseline that can't
    # possibly match a real rule output.
    data = json.loads(bl_file.read_text())
    data["findings"].append("R2OSTR999|doesnotexist|42")
    bl_file.write_text(json.dumps(data), encoding="utf-8")

    result = runner.invoke(
        main,
        ["lint", str(repo), "--baseline", str(bl_file)],
    )
    # Depending on Click version stderr may be merged into
    # output or available separately. Both are acceptable.
    combined = result.output
    if getattr(result, "stderr_bytes", None):
        combined += result.stderr
    assert "stale" in combined
    assert "baseline --update" in combined


def test_baseline_update_refreshes_existing(
    tmp_path: Path,
) -> None:
    import json
    import shutil
    repo = tmp_path / "repo"
    shutil.copytree(NONCOMPLIANT, repo)

    runner = CliRunner()
    runner.invoke(main, ["baseline", str(repo)])
    bl_file = repo / ".r2o-check-baseline.json"

    # Add a stale entry that update should drop.
    data = json.loads(bl_file.read_text())
    original_count = len(data["findings"])
    data["findings"].append("R2OSTR999|fictional|1")
    bl_file.write_text(json.dumps(data), encoding="utf-8")

    result = runner.invoke(
        main, ["baseline", str(repo), "--update"]
    )
    assert result.exit_code == 0
    assert "resolved" in result.output

    refreshed = json.loads(bl_file.read_text())
    assert len(refreshed["findings"]) == original_count


def test_baseline_update_requires_existing_file(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".r2o-check.yml").write_text(
        "repo_type: tool\n", encoding="utf-8"
    )
    runner = CliRunner()
    result = runner.invoke(
        main, ["baseline", str(repo), "--update"]
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_fail_on_warn_escalates_exit_code() -> None:
    runner = CliRunner()
    # COMPLIANT fixture has warns but no fails — default exit 0.
    default_result = runner.invoke(
        main, ["lint", str(COMPLIANT)]
    )
    strict_result = runner.invoke(
        main, ["lint", str(COMPLIANT), "--fail-on", "warn"]
    )
    # At least one of them must differ; if COMPLIANT truly
    # has warnings, strict mode should exit 1.
    has_warnings = "WARN" in default_result.output
    if has_warnings:
        assert strict_result.exit_code == 1
    else:
        assert strict_result.exit_code == default_result.exit_code


def test_only_filter_runs_subset() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(COMPLIANT), "--only", "R2OSTR001",
         "--format", "json"],
    )
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    rule_ids = {r["rule_id"] for r in data["results"]}
    assert rule_ids == {"R2OSTR001"}


def test_only_rejects_unknown_rule_id() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(COMPLIANT), "--only", "R2ONOTREAL"],
    )
    assert result.exit_code != 0
    assert "Unknown rule ID" in result.output


def test_only_rejects_one_unknown_among_valid() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["lint", str(COMPLIANT),
         "--only", "R2OSTR001,R2OTYPO999"],
    )
    assert result.exit_code != 0
    assert "R2OTYPO999" in result.output


def test_only_skips_baseline_stale_detection(
    tmp_path: Path,
) -> None:
    """Subset run must not flag unrelated baseline entries as stale."""
    import shutil
    repo = tmp_path / "repo"
    shutil.copytree(NONCOMPLIANT, repo)

    runner = CliRunner()
    runner.invoke(main, ["baseline", str(repo)])
    bl_file = repo / ".r2o-check-baseline.json"

    combined_result = runner.invoke(
        main,
        [
            "lint", str(repo),
            "--baseline", str(bl_file),
            "--only", "R2OSTR001",
        ],
    )
    combined = combined_result.output
    if getattr(combined_result, "stderr_bytes", None):
        combined += combined_result.stderr
    assert "stale" not in combined
