"""Tests for cross-reference rules (R2OXRF001-002)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.crossref import (
    check_jjob_ecf_match,
    check_jjob_exscript_exists,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestJjobEcfMatch:
    def test_rrfs_has_match(self, config: Config) -> None:
        results = check_jjob_ecf_match(RRFS, config)
        # JRRFS_FORECAST -> jrrfs_forecast.ecf exists
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_missing_ecf_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "ecf").mkdir()
        (tmp_path / "jobs" / "JMODEL_TASK").touch()
        results = check_jjob_ecf_match(tmp_path, config)
        assert results[0].status == Status.WARN

    def test_no_dirs_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_jjob_ecf_match(tmp_path, config) == []


class TestJjobExscriptExists:
    def test_rrfs_script_found(self, config: Config) -> None:
        results = check_jjob_exscript_exists(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        # JRRFS_FORECAST calls exrrfs_forecast.sh
        assert len(passes) >= 1

    def test_missing_script_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "scripts").mkdir()
        jf = tmp_path / "jobs" / "JMODEL_TASK"
        jf.write_text(
            '#!/bin/bash\n$SCRIPTSmodel/exmodel_task.sh\n'
        )
        results = check_jjob_exscript_exists(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.FAIL

    def test_no_dirs_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_jjob_exscript_exists(tmp_path, config) == []
