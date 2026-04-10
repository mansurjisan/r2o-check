"""Tests for build system rules (R2OBLD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.build import check_makefile_targets

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
