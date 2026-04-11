"""Tests for extended content rules (R2OCNT005-007)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.content import (
    check_no_absolute_symlinks,
    check_production_utilities,
    check_working_dir_hygiene,
)


@pytest.fixture
def config() -> Config:
    return Config()


class TestAbsoluteSymlinks:
    def test_no_symlinks_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "jobs" / "JMODEL").write_text("#!/bin/bash\n")
        results = check_no_absolute_symlinks(tmp_path, config)
        assert results[0].status == Status.PASS

    def test_absolute_symlink_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "fix").mkdir()
        target = tmp_path / "fix" / "bad_link"
        target.symlink_to("/usr/local/lib/libfoo.so")
        results = check_no_absolute_symlinks(tmp_path, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) == 1
        assert "absolute path" in fails[0].message

    def test_relative_symlink_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "real_file").write_text("data")
        (tmp_path / "link").symlink_to("real_file")
        results = check_no_absolute_symlinks(tmp_path, config)
        assert results[0].status == Status.PASS


class TestProductionUtilities:
    def test_dbn_with_senddbn_passes(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n"
            "if [ $SENDDBN = YES ]; then\n"
            "  dbn_alert MODEL DATA $job $COMOUT/file\n"
            "fi\n"
        )
        results = check_production_utilities(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_dbn_without_senddbn_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\n"
            "dbn_alert MODEL DATA $job $COMOUT/file\n"
        )
        results = check_production_utilities(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1

    def test_no_scripts_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_production_utilities(tmp_path, config) == []


class TestWorkingDirHygiene:
    def test_keepdata_referenced(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text(
            '#!/bin/bash\nif [ $KEEPDATA != YES ]; then\n'
            '  rm -rf $DATA\nfi\n'
        )
        results = check_working_dir_hygiene(tmp_path, config)
        passes = [r for r in results if r.status == Status.PASS]
        assert len(passes) >= 1

    def test_missing_keepdata_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        jobs.mkdir()
        (jobs / "JMODEL").write_text("#!/bin/bash\necho hi\n")
        results = check_working_dir_hygiene(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1

    def test_dangerous_rm_fails(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exmodel_task.sh").write_text(
            "#!/bin/bash\nrm -rf $COMROOT/$NET\n"
        )
        results = check_working_dir_hygiene(tmp_path, config)
        fails = [r for r in results if r.status == Status.FAIL]
        assert len(fails) >= 1
        assert "dangerous" in fails[0].message
