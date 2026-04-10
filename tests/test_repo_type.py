"""Tests for repo_type filtering logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config, RepoType, load_config
from r2o_check.engine import LintRunner, Status

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "compliant_minimal"
TOOL_REPO = FIXTURES / "tool_repo"
RRFS = FIXTURES / "rrfs_style"


class TestRepoTypeConfig:
    """Config correctly parses and validates repo_type."""

    def test_default_is_operational_model(self) -> None:
        c = Config()
        assert c.repo_type == RepoType.OPERATIONAL_MODEL

    def test_load_tool_type(self) -> None:
        c = load_config(TOOL_REPO)
        assert c.repo_type == RepoType.TOOL

    def test_load_operational_model_type(self) -> None:
        c = load_config(RRFS)
        assert c.repo_type == RepoType.OPERATIONAL_MODEL

    def test_all_repo_types_valid(self, tmp_path: Path) -> None:
        for rt in RepoType:
            yml = tmp_path / ".r2o-check.yml"
            yml.write_text(f"repo_type: {rt.value}\n")
            c = load_config(tmp_path)
            assert c.repo_type == rt

    def test_invalid_repo_type_raises(
        self, tmp_path: Path
    ) -> None:
        yml = tmp_path / ".r2o-check.yml"
        yml.write_text("repo_type: spaceship\n")
        with pytest.raises(ValueError, match="repo_type must be"):
            load_config(tmp_path)

    def test_non_string_repo_type_raises(
        self, tmp_path: Path
    ) -> None:
        yml = tmp_path / ".r2o-check.yml"
        yml.write_text("repo_type: 42\n")
        with pytest.raises(ValueError, match="repo_type must be"):
            load_config(tmp_path)


class TestRepoTypeFiltering:
    """LintRunner skips rules not applicable to the repo type."""

    def test_tool_repo_gets_zero_results(self) -> None:
        """tool type has no applicable structure/naming rules."""
        c = Config(repo_type=RepoType.TOOL)
        runner = LintRunner(COMPLIANT, c)
        results = runner.run()
        assert len(results) == 0

    def test_library_repo_gets_only_build_rules(self) -> None:
        """Library repos only get build rules."""
        c = Config(repo_type=RepoType.LIBRARY)
        runner = LintRunner(COMPLIANT, c)
        results = runner.run()
        rule_ids = {r.rule_id for r in results}
        # Only build rules apply.
        assert all(
            rid.startswith("R2OBLD") for rid in rule_ids
        )

    def test_model_source_gets_build_and_module_rules(
        self,
    ) -> None:
        """Model source repos get build + module rules."""
        c = Config(repo_type=RepoType.MODEL_SOURCE)
        runner = LintRunner(COMPLIANT, c)
        results = runner.run()
        rule_ids = {r.rule_id for r in results}
        # Only build and module rules apply.
        assert all(
            rid.startswith(("R2OBLD", "R2OMOD"))
            for rid in rule_ids
        )

    def test_operational_model_gets_all_rules(self) -> None:
        c = Config(repo_type=RepoType.OPERATIONAL_MODEL)
        runner = LintRunner(COMPLIANT, c)
        results = runner.run()
        assert len(results) > 0
        rule_ids = {r.rule_id for r in results}
        # Must include structure and naming rules
        assert "R2OSTR001" in rule_ids

    def test_workflow_gets_all_rules(self) -> None:
        c = Config(repo_type=RepoType.WORKFLOW)
        runner = LintRunner(COMPLIANT, c)
        results = runner.run()
        rule_ids = {r.rule_id for r in results}
        assert "R2OSTR001" in rule_ids

    def test_tool_repo_fixture_self_check(self) -> None:
        """tool_repo fixture with repo_type: tool passes clean."""
        c = load_config(TOOL_REPO)
        runner = LintRunner(TOOL_REPO, c)
        results = runner.run()
        assert len(results) == 0

    def test_rrfs_fixture_has_results(self) -> None:
        """RRFS fixture with operational_model gets results."""
        c = load_config(RRFS)
        runner = LintRunner(RRFS, c)
        results = runner.run()
        assert len(results) > 0
        # All RRFS struct dirs present — no FAIL on R2OSTR001-008
        required_fails = [
            r
            for r in results
            if r.rule_id.startswith("R2OSTR00")
            and r.status == Status.FAIL
        ]
        assert len(required_fails) == 0
