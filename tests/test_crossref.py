"""Tests for cross-reference rules (R2OXRF001-002)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.crossref import (
    check_ecf_references_jjob,
    check_exscript_ush_exists,
    check_jjob_ecf_match,
    check_jjob_exscript_exists,
    check_orphan_scripts,
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


class TestEcfReferencesJjob:
    def test_rrfs_ecf_calls_jjob(
        self, config: Config
    ) -> None:
        results = check_ecf_references_jjob(RRFS, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_missing_jjob_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (tmp_path / "jobs").mkdir()
        (ecf / "test.ecf").write_text(
            "$HOMEmodel/jobs/JMODEL_MISSING\n"
        )
        results = check_ecf_references_jjob(tmp_path, config)
        assert results[0].status == Status.WARN

    def test_no_dirs_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_ecf_references_jjob(tmp_path, config) == []


class TestExscriptUshExists:
    def test_missing_ush_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (tmp_path / "ush").mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n$USHmodel/helper.sh\n"
        )
        results = check_exscript_ush_exists(tmp_path, config)
        assert results[0].status == Status.WARN

    def test_no_dirs_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_exscript_ush_exists(tmp_path, config) == []


class TestOrphanScripts:
    def test_referenced_script_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        scripts = tmp_path / "scripts"
        jobs.mkdir()
        scripts.mkdir()
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\n$SCRIPTS/exmodel_task.sh\n"
        )
        (scripts / "exmodel_task.sh").touch()
        results = check_orphan_scripts(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_orphan_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        scripts = tmp_path / "scripts"
        jobs.mkdir()
        scripts.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\necho hi\n")
        (scripts / "exmodel_orphan.sh").touch()
        results = check_orphan_scripts(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1
        assert "orphan" in warns[0].message
