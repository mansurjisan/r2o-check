"""Tests for environment variable rules (R2OENV)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.environment import check_jjob_env_vars

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestJjobEnvVars:
    def test_rrfs_forecast_sets_all_vars(
        self, config: Config
    ) -> None:
        results = check_jjob_env_vars(RRFS, config)
        forecast = [
            r for r in results if "JRRFS_FORECAST" in r.message
        ]
        passes = [r for r in forecast if r.status == Status.PASS]
        # 7 exact vars + 4 pattern vars = 11 passes
        assert len(passes) == 11

    def test_empty_jjob_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL_TASK").write_text("#!/bin/bash\necho hi\n")
        results = check_jjob_env_vars(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        # Should warn for all 11 vars
        assert len(warns) == 11

    def test_no_jobs_dir_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        results = check_jjob_env_vars(tmp_path, config)
        assert results == []

    def test_detects_default_assignment(
        self, tmp_path: Path, config: Config
    ) -> None:
        """${VAR:-default} syntax should count as setting."""
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            '#!/bin/bash\n'
            'export NET="model"\n'
            'RUN=${RUN:-"model"}\n'
            'export PDY=${PDY:-$(date +%Y%m%d)}\n'
        )
        results = check_jjob_env_vars(tmp_path, config)
        net_r = [r for r in results if "$NET" in r.message]
        assert net_r[0].status == Status.PASS
        run_r = [r for r in results if "$RUN" in r.message]
        assert run_r[0].status == Status.PASS
        pdy_r = [r for r in results if "$PDY" in r.message]
        assert pdy_r[0].status == Status.PASS
