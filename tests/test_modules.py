"""Tests for modulefile content rules (R2OMOD)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.modules import check_modulefile_deps

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestModulefileDeps:
    def test_rrfs_build_module_has_compiler(
        self, config: Config
    ) -> None:
        results = check_modulefile_deps(RRFS, config)
        build_results = [
            r for r in results if "build_wcoss2" in r.message
        ]
        assert len(build_results) == 1
        assert build_results[0].status == Status.PASS

    def test_empty_module_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        mf = tmp_path / "modulefiles"
        mf.mkdir()
        (mf / "empty.lua").write_text("-- empty module\n")
        results = check_modulefile_deps(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.WARN

    def test_no_modulefiles_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_modulefile_deps(tmp_path, config)
        assert results == []

    def test_build_module_no_compiler_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        mf = tmp_path / "modulefiles"
        mf.mkdir()
        (mf / "build_test.lua").write_text(
            'load("w3nco/2.4.1")\nload("bacio/2.4.1")\n'
        )
        results = check_modulefile_deps(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) == 1
        assert "compiler" in warns[0].message

    def test_non_build_module_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        mf = tmp_path / "modulefiles"
        mf.mkdir()
        (mf / "runtime.lua").write_text(
            'load("prod_util/2.0.0")\n'
        )
        results = check_modulefile_deps(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS
