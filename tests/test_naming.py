"""Tests for naming convention rules (R2ONAM001–R2ONAM004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import LintRunner, Status
from r2o_check.rules.naming import (
    check_exscript_naming,
    check_jjob_naming,
    check_modulefile_naming,
    check_version_files,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"
STOFS = FIXTURES / "stofs_style"
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

    def test_bad_exscripts_all_fail(
        self, config: Config
    ) -> None:
        results = check_exscript_naming(BAD, config)
        assert len(results) == 3
        assert all(r.status == Status.FAIL for r in results)

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


# ── R2ONAM004: Version file naming and format ─────────────────


class TestVersionFiles:
    def test_rrfs_versions_pass(self, config: Config) -> None:
        results = check_version_files(RRFS, config)
        # 2 presence checks (pass) + format checks (pass)
        passes = [r for r in results if r.status == Status.PASS]
        fails = [r for r in results if r.status == Status.FAIL]
        warns = [r for r in results if r.status == Status.WARN]
        assert len(fails) == 0
        assert len(warns) == 0
        assert len(passes) >= 2

    def test_bad_versions_missing_build_ver(
        self, config: Config
    ) -> None:
        results = check_version_files(BAD, config)
        fail_msgs = [
            r.message
            for r in results
            if r.status == Status.FAIL
        ]
        assert any("build.ver" in m for m in fail_msgs)

    def test_bad_versions_format_warning(
        self, config: Config
    ) -> None:
        results = check_version_files(BAD, config)
        warns = [r for r in results if r.status == Status.WARN]
        # run.ver has 2 lines: "model_ver=v1.0.0" (missing export)
        # and "this is not valid"
        assert len(warns) >= 2

    def test_no_versions_dir_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_version_files(tmp_path, config)
        assert results == []

    def test_stofs_versions_pass(self, config: Config) -> None:
        results = check_version_files(STOFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 0
        assert len(passes) >= 2


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
        # 3 bad J-jobs + 3 bad ex-scripts + 2 bad modulefiles
        # + 1 missing build.ver = 9+
        assert len(naming_fails) >= 9
