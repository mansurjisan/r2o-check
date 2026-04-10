"""Tests for build system rules (R2OBLD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.build import (
    check_cmake_build,
    check_makefile_targets,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestMakefileTargets:
    def test_rrfs_makefile_has_all_targets(
        self, config: Config
    ) -> None:
        results = check_makefile_targets(RRFS, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 0
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 4  # all, debug, install, clean

    def test_missing_target_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        sorc = tmp_path / "sorc" / "model.fd"
        sorc.mkdir(parents=True)
        (sorc / "Makefile").write_text(
            "all: model\n\nclean:\n\trm -f model\n"
        )
        results = check_makefile_targets(tmp_path, config)
        fails = [r for r in results if r.status == Status.FAIL]
        fail_msgs = [r.message for r in fails]
        assert any("debug" in m for m in fail_msgs)
        assert any("install" in m for m in fail_msgs)

    def test_no_sorc_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_makefile_targets(tmp_path, config)
        assert results == []

    def test_sorc_no_makefile_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "sorc").mkdir()
        results = check_makefile_targets(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.WARN

    def test_complete_makefile_all_pass(
        self, tmp_path: Path, config: Config
    ) -> None:
        sorc = tmp_path / "sorc" / "app.fd"
        sorc.mkdir(parents=True)
        (sorc / "Makefile").write_text(
            "all: app\n\n"
            "debug: FFLAGS=-g\ndebug: app\n\n"
            "install:\n\tcp app ../../exec/\n\n"
            "clean:\n\trm -f app\n"
        )
        results = check_makefile_targets(tmp_path, config)
        assert all(r.status == Status.PASS for r in results)
        assert len(results) == 4


class TestCmakeBuild:
    def test_cmake_repo_passes(self, config: Config) -> None:
        cmake = FIXTURES / "cmake_repo"
        results = check_cmake_build(cmake, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) == 2  # project + install

    def test_no_sorc_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_cmake_build(tmp_path, config) == []

    def test_sorc_no_cmake_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "sorc").mkdir()
        results = check_cmake_build(tmp_path, config)
        assert results[0].status == Status.WARN

    def test_mutual_exclusion_via_runner(
        self, config: Config
    ) -> None:
        """RRFS has Makefile — R2OBLD002 should be skipped."""
        from r2o_check.engine import LintRunner

        runner = LintRunner(RRFS, config)
        results = runner.run()
        bld_ids = {
            r.rule_id
            for r in results
            if r.rule_id.startswith("R2OBLD")
        }
        # Only R2OBLD001 should run (Makefile present)
        assert "R2OBLD001" in bld_ids
        assert "R2OBLD002" not in bld_ids

    def test_cmake_only_skips_makefile_rule(
        self, config: Config
    ) -> None:
        """cmake_repo has CMake — R2OBLD001 should be skipped."""
        from r2o_check.engine import LintRunner

        cmake = FIXTURES / "cmake_repo"
        runner = LintRunner(cmake, config)
        results = runner.run()
        bld_ids = {
            r.rule_id
            for r in results
            if r.rule_id.startswith("R2OBLD")
        }
        assert "R2OBLD002" in bld_ids
        assert "R2OBLD001" not in bld_ids
