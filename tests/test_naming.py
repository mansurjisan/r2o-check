"""Tests for naming convention rules (R2ONAM001–R2ONAM005)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import LintRunner, Status
from r2o_check.rules.naming import (
    check_exscript_naming,
    check_jjob_naming,
    check_modulefile_naming,
    check_ush_naming,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"
STOFS = FIXTURES / "stofs_style"
STOFS_NESTED = FIXTURES / "stofs_nested"
BAD = FIXTURES / "bad_naming"
COMPLIANT = FIXTURES / "compliant_minimal"


@pytest.fixture
def config() -> Config:
    return Config()


# ── R2ONAM001: J-job naming ───────────────────────────────────


class TestJjobNaming:
    def test_rrfs_jjobs_pass(self, config: Config) -> None:
        results = check_jjob_naming(RRFS, config)
        assert len(results) == 4
        assert all(r.status == Status.PASS for r in results)
        assert all(r.rule_id == "R2ONAM001" for r in results)

    def test_stofs_jjobs_pass(self, config: Config) -> None:
        results = check_jjob_naming(STOFS, config)
        assert len(results) == 3
        assert all(r.status == Status.PASS for r in results)

    def test_bad_jjobs_all_fail(self, config: Config) -> None:
        results = check_jjob_naming(BAD, config)
        assert len(results) == 3
        assert all(r.status == Status.FAIL for r in results)

    def test_bad_jjob_lowercase(self, config: Config) -> None:
        results = check_jjob_naming(BAD, config)
        names = {r.path.name for r in results}  # type: ignore[union-attr]
        assert "jmodel_forecast" in names

    def test_bad_jjob_extension(self, config: Config) -> None:
        results = check_jjob_naming(BAD, config)
        names = {r.path.name for r in results}  # type: ignore[union-attr]
        assert "JMODEL_FORECAST.sh" in names

    def test_bad_jjob_no_j_prefix(self, config: Config) -> None:
        results = check_jjob_naming(BAD, config)
        names = {r.path.name for r in results}  # type: ignore[union-attr]
        assert "MODEL_FORECAST" in names

    def test_no_jobs_dir_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_jjob_naming(tmp_path, config)
        assert results == []

    def test_compliant_jjob_pass(self, config: Config) -> None:
        results = check_jjob_naming(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS


# ── R2ONAM002: Ex-script naming ───────────────────────────────


class TestExscriptNaming:
    def test_rrfs_exscripts_pass(self, config: Config) -> None:
        results = check_exscript_naming(RRFS, config)
        assert len(results) == 4
        assert all(r.status == Status.PASS for r in results)

    def test_stofs_exscripts_pass(self, config: Config) -> None:
        results = check_exscript_naming(STOFS, config)
        assert len(results) == 3
        assert all(r.status == Status.PASS for r in results)

    def test_bad_exscripts_fail(
        self, config: Config
    ) -> None:
        """Only files starting with 'ex' are checked."""
        results = check_exscript_naming(BAD, config)
        # Only exmodel_task.txt starts with 'ex'
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert "exmodel_task.txt" in results[0].message

    def test_no_scripts_dir_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_exscript_naming(tmp_path, config)
        assert results == []


# ── R2ONAM003: Modulefile naming ──────────────────────────────


class TestModulefileNaming:
    def test_rrfs_modulefiles_pass(self, config: Config) -> None:
        results = check_modulefile_naming(RRFS, config)
        # All .lua files should pass
        assert all(r.status == Status.PASS for r in results)
        assert len(results) == 3  # 2 top-level + 1 in tasks/

    def test_bad_modulefiles_fail(self, config: Config) -> None:
        results = check_modulefile_naming(BAD, config)
        assert len(results) == 2
        assert all(r.status == Status.FAIL for r in results)

    def test_no_modulefiles_dir_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_modulefile_naming(tmp_path, config)
        assert results == []

    def test_compliant_modulefiles(self, config: Config) -> None:
        results = check_modulefile_naming(COMPLIANT, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS


# R2ONAM004 retired — version checks now in R2OVER001-004.


# ── Integration: naming rules via LintRunner ──────────────────


class TestNamingIntegration:
    def test_rrfs_full_lint_no_naming_failures(self) -> None:
        runner = LintRunner(RRFS)
        results = runner.run()
        naming_fails = [
            r
            for r in results
            if r.rule_id.startswith("R2ONAM")
            and r.status == Status.FAIL
        ]
        assert len(naming_fails) == 0

    def test_bad_naming_fixture_has_failures(self) -> None:
        runner = LintRunner(BAD)
        results = runner.run()
        naming_fails = [
            r
            for r in results
            if r.rule_id.startswith("R2ONAM")
            and r.status == Status.FAIL
        ]
        # 3 bad J-jobs + 2 bad modulefiles + 1 bad ex-script
        # (exmodel_task.txt starts with 'ex' but wrong ext).
        # R2ONAM004 retired — version checks now in R2OVER.
        assert len(naming_fails) >= 6


# ── R2ONAM002: Recursive ex-script naming ─────────────────────


class TestExscriptRecursion:
    def test_stofs_nested_finds_exscripts(
        self, config: Config
    ) -> None:
        """Recurse into scripts/stofs_2d_glo/."""
        results = check_exscript_naming(STOFS_NESTED, config)
        # 2 compliant + 1 bad (exstofs_badname)
        assert len(results) == 3

    def test_stofs_nested_compliant_pass(
        self, config: Config
    ) -> None:
        results = check_exscript_naming(STOFS_NESTED, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) == 2

    def test_stofs_nested_bad_name_fails(
        self, config: Config
    ) -> None:
        results = check_exscript_naming(STOFS_NESTED, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 1
        assert "exstofs_badname" in fails[0].message

    def test_helper_not_flagged(
        self, config: Config
    ) -> None:
        """helper_utils.sh doesn't start with 'ex'."""
        results = check_exscript_naming(STOFS_NESTED, config)
        names = [
            r.path.name for r in results  # type: ignore[union-attr]
        ]
        assert "helper_utils.sh" not in names


# ── R2ONAM005: Ush script naming ──────────────────────────────


class TestUshNaming:
    def test_rrfs_ush_passes(self, config: Config) -> None:
        results = check_ush_naming(RRFS, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS

    def test_bad_ush_scripts(self, config: Config) -> None:
        results = check_ush_naming(BAD, config)
        warns = [r for r in results if r.status == Status.WARN]
        # ExBadUtil.sh (uppercase), exhelper.sh (starts with ex)
        assert len(warns) == 2

    def test_good_ush_passes(self, config: Config) -> None:
        results = check_ush_naming(BAD, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) == 1
        assert "good_util.sh" in passes[0].message

    def test_no_ush_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_ush_naming(tmp_path, config)
        assert results == []
