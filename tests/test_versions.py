"""Tests for version file content rules (R2OVER)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.versions import (
    check_build_ver_content,
    check_run_ver_content,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"
BAD = FIXTURES / "bad_naming"


@pytest.fixture
def config() -> Config:
    return Config()


class TestRunVer:
    def test_rrfs_run_ver_valid(self, config: Config) -> None:
        results = check_run_ver_content(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_bad_run_ver_warns(self, config: Config) -> None:
        results = check_run_ver_content(BAD, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1

    def test_no_versions_dir(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_run_ver_content(tmp_path, config)
        assert results == []

    def test_empty_run_ver_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        ver = tmp_path / "versions"
        ver.mkdir()
        (ver / "run.ver").write_text("")
        results = check_run_ver_content(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.WARN

    def test_non_ver_suffix_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        ver = tmp_path / "versions"
        ver.mkdir()
        (ver / "run.ver").write_text("export MY_VAR=1.0.0\n")
        results = check_run_ver_content(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert any("_ver" in w.message for w in warns)


class TestBuildVer:
    def test_rrfs_build_ver_valid(
        self, config: Config
    ) -> None:
        results = check_build_ver_content(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_no_build_ver_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_build_ver_content(tmp_path, config)
        assert results == []

    def test_good_build_ver_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        ver = tmp_path / "versions"
        ver.mkdir()
        (ver / "build.ver").write_text(
            "export intel_ver=2022.1.2\n"
            "export model_ver=v1.0.0\n"
        )
        results = check_build_ver_content(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1
