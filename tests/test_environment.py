"""Tests for environment variable rules (R2OENV001-002)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.environment import (
    check_jjob_context_vars,
    check_jjob_core_vars,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestCoreVars:
    def test_rrfs_forecast_sets_all_core(
        self, config: Config
    ) -> None:
        results = check_jjob_core_vars(RRFS, config)
        forecast = [
            r for r in results if "JRRFS_FORECAST" in r.message
        ]
        passes = [r for r in forecast if r.status == Status.PASS]
        assert len(passes) == 7  # 7 core vars

    def test_empty_jjob_fails_core(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL_TASK").write_text("#!/bin/bash\necho hi\n")
        results = check_jjob_core_vars(tmp_path, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 7

    def test_no_jobs_dir(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_jjob_core_vars(tmp_path, config) == []

    def test_core_vars_are_fail_severity(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\n")
        results = check_jjob_core_vars(tmp_path, config)
        missing = [r for r in results if r.status != Status.PASS]
        assert all(r.status == Status.FAIL for r in missing)


class TestCommentStripping:
    def test_commented_core_var_does_not_pass(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL_TASK").write_text(
            "#!/bin/bash\n"
            "# export NET=rrfs\n"
            "  # export RUN=rrfs\n"
        )
        results = check_jjob_core_vars(tmp_path, config)
        fails = [
            r for r in results
            if r.status == Status.FAIL
            and ("$NET" in r.message or "$RUN" in r.message)
        ]
        assert len(fails) == 2

    def test_inline_comment_after_assignment_still_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL_TASK").write_text(
            "#!/bin/bash\n"
            "export NET=rrfs  # the network name\n"
        )
        results = check_jjob_core_vars(tmp_path, config)
        net_results = [r for r in results if "$NET" in r.message]
        assert all(r.status == Status.PASS for r in net_results)


class TestContextVars:
    def test_rrfs_forecast_sets_all_context(
        self, config: Config
    ) -> None:
        results = check_jjob_context_vars(RRFS, config)
        forecast = [
            r for r in results if "JRRFS_FORECAST" in r.message
        ]
        passes = [r for r in forecast if r.status == Status.PASS]
        assert len(passes) == 4  # USH, EXEC, PARM, FIX

    def test_empty_jjob_warns_context(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL_TASK").write_text("#!/bin/bash\necho hi\n")
        results = check_jjob_context_vars(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) == 4

    def test_context_vars_are_warn_severity(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\n")
        results = check_jjob_context_vars(tmp_path, config)
        missing = [r for r in results if r.status != Status.PASS]
        assert all(r.status == Status.WARN for r in missing)
