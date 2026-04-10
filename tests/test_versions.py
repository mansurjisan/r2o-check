"""Tests for version file rules (R2OVER001-004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.versions import (
    check_build_ver_content,
    check_build_ver_exists,
    check_run_ver_content,
    check_run_ver_exists,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"
BAD = FIXTURES / "bad_naming"


@pytest.fixture
def config() -> Config:
    return Config()


# ── R2OVER001/002: presence checks (FAIL) ─────────────────────


class TestRunVerExists:
    def test_rrfs_pass(self, config: Config) -> None:
        results = check_run_ver_exists(RRFS, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OVER001"

    def test_missing_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "versions").mkdir()
        results = check_run_ver_exists(tmp_path, config)
        assert results[0].status == Status.FAIL


class TestBuildVerExists:
    def test_rrfs_pass(self, config: Config) -> None:
        results = check_build_ver_exists(RRFS, config)
        assert results[0].status == Status.PASS
        assert results[0].rule_id == "R2OVER002"

    def test_bad_naming_missing(
        self, config: Config
    ) -> None:
        results = check_build_ver_exists(BAD, config)
        assert results[0].status == Status.FAIL

    def test_no_versions_dir(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_build_ver_exists(tmp_path, config)
        assert results[0].status == Status.FAIL


# ── R2OVER003/004: content checks (WARN) ──────────────────────


class TestRunVerContent:
    def test_rrfs_valid(self, config: Config) -> None:
        results = check_run_ver_content(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1
        assert results[0].rule_id == "R2OVER003"

    def test_bad_format_warns(self, config: Config) -> None:
        results = check_run_ver_content(BAD, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1

    def test_no_file_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_run_ver_content(tmp_path, config) == []

    def test_empty_file_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        ver = tmp_path / "versions"
        ver.mkdir()
        (ver / "run.ver").write_text("")
        results = check_run_ver_content(tmp_path, config)
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


class TestBuildVerContent:
    def test_rrfs_valid(self, config: Config) -> None:
        results = check_build_ver_content(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1
        assert results[0].rule_id == "R2OVER004"

    def test_no_file_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_build_ver_content(tmp_path, config) == []

    def test_good_format_passes(
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
