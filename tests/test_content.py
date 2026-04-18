"""Tests for content validation rules (R2OCNT001-004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.content import (
    check_err_chk_usage,
    check_jjob_debug_settings,
    check_no_background_procs,
    check_production_utilities,
    check_shebang,
    check_working_dir_hygiene,
)

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


class TestDebugSettings:
    def test_rrfs_has_set_x(self, config: Config) -> None:
        results = check_jjob_debug_settings(RRFS, config)
        forecast = [
            r for r in results if "JRRFS_FORECAST" in r.message
        ]
        assert forecast[0].status == Status.PASS

    def test_missing_set_x(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\necho hi\n")
        results = check_jjob_debug_settings(tmp_path, config)
        assert results[0].status == Status.FAIL
        assert "set -x" in results[0].message

    def test_no_jobs_dir(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_jjob_debug_settings(tmp_path, config) == []


class TestCommentStripping:
    def test_commented_set_x_does_not_pass(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\n"
            "# set -x\n"
            "# export PS4='+ $SECONDS + '\n"
        )
        results = check_jjob_debug_settings(tmp_path, config)
        assert results[0].status == Status.FAIL

    def test_commented_keepdata_does_not_pass(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\n"
            "# KEEPDATA used to be set here\n"
        )
        results = check_working_dir_hygiene(tmp_path, config)
        warns = [
            r for r in results
            if r.status == Status.WARN
            and "KEEPDATA" in r.message
        ]
        assert len(warns) == 1


class TestErrChk:
    def test_no_exec_calls_skipped(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\necho done\n"
        )
        results = check_err_chk_usage(tmp_path, config)
        assert results == []

    def test_exec_with_err_chk_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n"
            "$EXECmodel/model.x\n"
            "export err=$?; err_chk\n"
        )
        results = check_err_chk_usage(tmp_path, config)
        assert results[0].status == Status.PASS

    def test_exec_without_err_chk_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n$EXECmodel/model.x\n"
        )
        results = check_err_chk_usage(tmp_path, config)
        assert results[0].status == Status.WARN


class TestShebang:
    def test_with_shebang_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\nset -x\n")
        results = check_shebang(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_missing_shebang_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("set -x\necho hi\n")
        results = check_shebang(tmp_path, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) >= 1
        assert "shebang" in fails[0].message

    def test_no_dirs_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_shebang(tmp_path, config) == []


class TestNoBackground:
    def test_clean_script_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\nset -x\necho done\n"
        )
        results = check_no_background_procs(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_background_detected(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n"
            "$EXECmodel/model.x &\n"
            "wait\n"
            "$EXECmodel/post.x &\n"
        )
        results = check_no_background_procs(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) == 2
        lines = sorted(w.line for w in warns if w.line)
        assert lines == [2, 4]

    def test_ampersand_in_and_not_flagged(
        self, tmp_path: Path, config: Config
    ) -> None:
        """&& should not be flagged as background."""
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\nmkdir -p $DATA && cd $DATA\n"
        )
        results = check_no_background_procs(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1


class TestProductionUtilities:
    def test_bare_cp_warns_with_line(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel.sh").write_text(
            "#!/bin/bash\n"
            "cp input.dat $COMOUT/\n"
            "cpreq other.dat $COMOUT/\n"
            "cp again.dat $COMOUT/\n"
        )
        results = check_production_utilities(tmp_path, config)
        cp_warns = [
            r for r in results
            if r.status == Status.WARN
            and "'cp'" in r.message
        ]
        assert len(cp_warns) == 2
        lines = sorted(w.line for w in cp_warns if w.line)
        assert lines == [2, 4]

    def test_cp_with_flags_not_flagged(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel.sh").write_text(
            "#!/bin/bash\n"
            "cp -p input.dat $COMOUT/\n"
        )
        results = check_production_utilities(tmp_path, config)
        cp_warns = [
            r for r in results
            if r.status == Status.WARN
            and "'cp'" in r.message
        ]
        assert cp_warns == []
