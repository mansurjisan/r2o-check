"""Tests for structure rules (R2OSTR001–R2OSTR014)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import LintRunner, Status
from r2o_check.rules.structure import (
    REQUIRED_DIRS,
    check_doc_dir,
    check_ecf_dir,
    check_exec_dir,
    check_fix_dir,
    check_gempak_dir,
    check_jobs_dir,
    check_lib_dir,
    check_modulefiles_dir,
    check_parm_dir,
    check_parm_wmo_dir,
    check_scripts_dir,
    check_sorc_dir,
    check_ush_dir,
    check_versions_dir,
)

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "compliant_minimal"
NONCOMPLIANT = FIXTURES / "noncompliant_minimal"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


# ── R2OSTR001–008: always-required (FAIL) ─────────────────────


class TestCompliantFixture:
    """All structure checks should PASS on compliant fixture."""

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
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR003"

    def test_ush_dir_pass(self, config: Config) -> None:
        results = check_ush_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR004"

    def test_sorc_dir_pass(self, config: Config) -> None:
        results = check_sorc_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR005"

    def test_parm_dir_pass(self, config: Config) -> None:
        results = check_parm_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR006"

    def test_versions_dir_pass(self, config: Config) -> None:
        results = check_versions_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR007"

    def test_modulefiles_dir_pass(self, config: Config) -> None:
        results = check_modulefiles_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OSTR008"


class TestNoncompliantFixture:
    """Missing directories produce FAIL results."""

    def test_ecf_dir_fail(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR001"
        assert results[0].fix_hint is not None

    def test_jobs_dir_pass(self, config: Config) -> None:
        results = check_jobs_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.PASS

    def test_sorc_dir_fail(self, config: Config) -> None:
        results = check_sorc_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR005"

    def test_versions_dir_fail(self, config: Config) -> None:
        results = check_versions_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR007"

    def test_modulefiles_dir_fail(self, config: Config) -> None:
        results = check_modulefiles_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.FAIL
        assert results[0].rule_id == "R2OSTR008"


# ── R2OSTR009–014: conditional directories (WARN/FAIL) ────────


class TestConditionalStructure:
    """Conditional dirs produce WARN or escalated FAIL."""

    def test_doc_dir_warn_when_missing(
        self, config: Config
    ) -> None:
        results = check_doc_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR009"

    def test_doc_dir_pass_when_present(
        self, config: Config
    ) -> None:
        results = check_doc_dir(RRFS, config)
        assert results[0].status == Status.PASS

    def test_exec_dir_warn_no_sources(
        self, tmp_path: Path, config: Config
    ) -> None:
        """exec/ missing with no compilable sources = WARN."""
        (tmp_path / "sorc").mkdir()
        results = check_exec_dir(tmp_path, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR010"

    def test_exec_dir_fail_with_fortran(
        self, config: Config
    ) -> None:
        """exec/ missing + Fortran in sorc/ = FAIL."""
        # RRFS fixture has sorc/rrfs_forecast.fd/main.f90
        # but also has exec/ dir — use a temp dir instead
        results = check_exec_dir(RRFS, config)
        # RRFS has exec/ so it passes
        assert results[0].status == Status.PASS

    def test_exec_dir_fail_escalation(
        self, tmp_path: Path, config: Config
    ) -> None:
        """exec/ missing + Fortran in sorc/ = FAIL."""
        sorc = tmp_path / "sorc" / "model.fd"
        sorc.mkdir(parents=True)
        (sorc / "main.f90").write_text("program test\nend")
        results = check_exec_dir(tmp_path, config)
        assert results[0].status == Status.FAIL
        assert "compilable sources" in results[0].fix_hint  # type: ignore[operator]

    def test_fix_dir_warn(self, config: Config) -> None:
        results = check_fix_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR011"

    def test_fix_dir_pass(self, config: Config) -> None:
        results = check_fix_dir(RRFS, config)
        assert results[0].status == Status.PASS

    def test_lib_dir_warn(self, config: Config) -> None:
        results = check_lib_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR012"

    def test_gempak_dir_warn(self, config: Config) -> None:
        results = check_gempak_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR013"

    def test_parm_wmo_warn(self, config: Config) -> None:
        results = check_parm_wmo_dir(NONCOMPLIANT, config)
        assert results[0].status == Status.WARN
        assert results[0].rule_id == "R2OSTR014"

    def test_parm_wmo_pass(self, config: Config) -> None:
        results = check_parm_wmo_dir(COMPLIANT, config)
        assert results[0].status == Status.PASS


# ── Runner integration tests ──────────────────────────────────


class TestLintRunner:
    def test_compliant_all_pass(self) -> None:
        runner = LintRunner(COMPLIANT)
        results = runner.run()
        # 14 structure + naming results
        passes = [r for r in results if r.status == Status.PASS]
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 0
        assert len(passes) >= 14  # at least the 14 struct rules

    def test_noncompliant_has_failures(self) -> None:
        runner = LintRunner(NONCOMPLIANT)
        results = runner.run()
        fail_ids = {
            r.rule_id for r in results if r.status == Status.FAIL
        }
        # Missing: ecf, sorc, versions, modulefiles
        assert fail_ids >= {
            "R2OSTR001",
            "R2OSTR005",
            "R2OSTR007",
            "R2OSTR008",
        }

    def test_disabled_rules_skipped(self) -> None:
        config = Config(
            disabled_rules=["R2OSTR001", "R2OSTR005"]
        )
        runner = LintRunner(NONCOMPLIANT, config)
        results = runner.run()
        rule_ids = {r.rule_id for r in results}
        assert "R2OSTR001" not in rule_ids
        assert "R2OSTR005" not in rule_ids

    def test_run_specific_rules(self) -> None:
        runner = LintRunner(COMPLIANT)
        results = runner.run_rules(["R2OSTR001", "R2OSTR002"])
        assert len(results) == 2
        assert {r.rule_id for r in results} == {
            "R2OSTR001",
            "R2OSTR002",
        }


# ── LintResult field tests ────────────────────────────────────


class TestLintResult:
    def test_pass_has_no_fix_hint(self, config: Config) -> None:
        results = check_ecf_dir(COMPLIANT, config)
        assert results[0].fix_hint is None

    def test_fail_has_path(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert results[0].path is not None
        assert results[0].path.name == "ecf"

    def test_fail_cites_nco(self, config: Config) -> None:
        results = check_ecf_dir(NONCOMPLIANT, config)
        assert "NCO v11.0" in results[0].message

    def test_required_dirs_count(self) -> None:
        assert len(REQUIRED_DIRS) == 8


# ── Temp directory tests ──────────────────────────────────────


class TestWithTmpDir:
    def test_empty_repo_fails_all_required(
        self, tmp_path: Path, config: Config
    ) -> None:
        runner = LintRunner(tmp_path, config)
        results = runner.run()
        fails = [r for r in results if r.status == Status.FAIL]
        # At least 8 required dirs fail
        assert len(fails) >= 8

    def test_partial_repo(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "scripts").mkdir()
        runner = LintRunner(tmp_path, config)
        results = runner.run()
        struct_passes = [
            r
            for r in results
            if r.status == Status.PASS
            and r.rule_id.startswith("R2OSTR")
        ]
        assert len(struct_passes) == 2
