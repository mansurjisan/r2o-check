"""Tests for structure rules (R2OSTR001–R2OSTR008)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import LintRunner, Status
from r2o_check.rules.structure import (
    REQUIRED_DIRS,
    check_ecf_dir,
    check_jobs_dir,
    check_modulefiles_dir,
    check_parm_dir,
    check_scripts_dir,
    check_sorc_dir,
    check_ush_dir,
    check_versions_dir,
)

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "compliant_minimal"
NONCOMPLIANT = FIXTURES / "noncompliant_minimal"


@pytest.fixture
def config() -> Config:
    return Config()


# ── Individual rule tests against compliant fixture ────────────────────


class TestCompliantFixture:
    """All structure checks should PASS on the compliant fixture."""

    def test_ecf_dir_pass(self, config: Config) -> None:
        results = check_ecf_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR001"

    def test_jobs_dir_pass(self, config: Config) -> None:
        results = check_jobs_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR002"

    def test_scripts_dir_pass(self, config: Config) -> None:
        results = check_scripts_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR003"

    def test_ush_dir_pass(self, config: Config) -> None:
        results = check_ush_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR004"

    def test_sorc_dir_pass(self, config: Config) -> None:
        results = check_sorc_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR005"

    def test_parm_dir_pass(self, config: Config) -> None:
        results = check_parm_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR006"

    def test_versions_dir_pass(self, config: Config) -> None:
        results = check_versions_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR007"

    def test_modulefiles_dir_pass(self, config: Config) -> None:
        results = check_modulefiles_dir(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR008"


# ── Individual rule tests against noncompliant fixture ─────────────────


class TestNoncompliantFixture:
    """Missing directories should produce FAIL results."""

    def test_ecf_dir_fail(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR001"
        assert results[0].fix_hint is not None

    def test_jobs_dir_pass(self, config: Config) -> None:
        # jobs/ exists in noncompliant fixture
        results = check_jobs_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.PASS

    def test_scripts_dir_pass(self, config: Config) -> None:
        results = check_scripts_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.PASS

    def test_ush_dir_pass(self, config: Config) -> None:
        results = check_ush_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.PASS

    def test_sorc_dir_fail(self, config: Config) -> None:
        results = check_sorc_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR005"

    def test_parm_dir_pass(self, config: Config) -> None:
        results = check_parm_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.PASS

    def test_versions_dir_fail(self, config: Config) -> None:
        results = check_versions_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR007"

    def test_modulefiles_dir_fail(self, config: Config) -> None:
        results = check_modulefiles_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR008"


# ── Runner integration tests ──────────────────────────────────────────


class TestLintRunner:
    """Integration tests running the full suite via LintRunner."""

    def test_compliant_all_pass(self) -> None:
        runner = LintRunner(COMPLIANT)
        results = runner.run()
        assert len(results) == 8
        assert all(r.status == Status.PASS for r in results)

    def test_noncompliant_has_failures(self) -> None:
        runner = LintRunner(NONCOMPLIANT)
        results = runner.run()
        assert len(results) == 8
        failures = [r for r in results if r.status == Status.FAIL]
        # Missing: ecf, sorc, versions, modulefiles = 4 failures
        assert len(failures) == 4
        fail_ids = {r.rule_id for r in failures}
        assert fail_ids == {"R2OSTR001", "R2OSTR005", "R2OSTR007", "R2OSTR008"}

    def test_disabled_rules_skipped(self) -> None:
        config = Config(disabled_rules=["R2OSTR001", "R2OSTR005"])
        runner = LintRunner(NONCOMPLIANT, config)
        results = runner.run()
        assert len(results) == 6
        rule_ids = {r.rule_id for r in results}
        assert "R2OSTR001" not in rule_ids
        assert "R2OSTR005" not in rule_ids

    def test_run_specific_rules(self) -> None:
        runner = LintRunner(COMPLIANT)
        results = runner.run_rules(["R2OSTR001", "R2OSTR002"])
        assert len(results) == 2
        assert {r.rule_id for r in results} == {"R2OSTR001", "R2OSTR002"}


# ── LintResult field tests ────────────────────────────────────────────


class TestLintResult:
    def test_pass_result_has_no_fix_hint(self, config: Config) -> None:
        results = check_ecf_dir(COMPLIANT, config)
        assert results[0].fix_hint is None

    def test_fail_result_has_path(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert results[0].path is not None
        assert results[0].path.name == "ecf"

    def test_fail_result_message_cites_nco(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert "NCO v11.0" in results[0].message

    def test_required_dirs_count(self) -> None:
        assert len(REQUIRED_DIRS) == 8


# ── Temp directory tests (isolated) ──────────────────────────────────


class TestWithTmpDir:
    def test_empty_repo_fails_all(self, tmp_path: Path, config: Config) -> None:
        runner = LintRunner(tmp_path, config)
        results = runner.run()
        assert len(results) == 8
        assert all(r.status == Status.FAIL for r in results)

    def test_partial_repo(self, tmp_path: Path, config: Config) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "scripts").mkdir()
        runner = LintRunner(tmp_path, config)
        results = runner.run()
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) == 2
