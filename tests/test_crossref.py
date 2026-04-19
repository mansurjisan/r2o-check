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


class TestCommentStripping:
    def test_commented_exscript_call_ignored(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "jobs" / "JMODEL").write_text(
            "#!/bin/bash\n"
            "# $SCRIPTS/exmissing.sh\n"
            "echo ok\n"
        )
        results = check_jjob_exscript_exists(tmp_path, config)
        # The only call was commented — no FAIL should result.
        assert results == []

    def test_commented_ush_call_ignored(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (tmp_path / "ush").mkdir()
        (scripts / "exmodel.sh").write_text(
            "#!/bin/bash\n"
            "# $USH/helper.sh\n"
        )
        results = check_exscript_ush_exists(tmp_path, config)
        assert results == []

    def test_orphan_not_rescued_by_commented_call(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        scripts = tmp_path / "scripts"
        ush = tmp_path / "ush"
        jobs.mkdir()
        scripts.mkdir()
        ush.mkdir()
        # J-job has the call, but it's commented out.
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\n"
            "# $SCRIPTS/exorphan.sh\n"
        )
        (scripts / "exorphan.sh").touch()
        (ush / "helper.sh").touch()
        # An ex-script exists with a commented ush reference.
        (scripts / "exmodel.sh").write_text(
            "#!/bin/bash\n"
            "# $USH/helper.sh\n"
        )
        results = check_orphan_scripts(tmp_path, config)
        # Both 'helper.sh' and 'exorphan.sh' should be WARN
        # orphans — their only callers are commented out.
        warns = {
            r.message for r in results
            if r.status == Status.WARN
        }
        assert any("exorphan.sh" in m for m in warns)
        assert any("helper.sh" in m for m in warns)


class TestLineNumbers:
    def test_exscript_call_records_line(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "exfoo.sh").touch()
        (tmp_path / "jobs" / "JMODEL").write_text(
            "#!/bin/bash\n"
            "set -x\n"
            "$SCRIPTS/exfoo.sh\n"
        )
        results = check_jjob_exscript_exists(tmp_path, config)
        assert len(results) == 1
        assert results[0].line == 3
        assert ":3" in results[0].message


class TestNestedPaths:
    def test_nested_exscript_call_found(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        scripts = tmp_path / "scripts" / "forecast"
        scripts.mkdir(parents=True)
        (scripts / "exfoo.sh").touch()
        (tmp_path / "jobs" / "JMODEL").write_text(
            "#!/bin/bash\n$SCRIPTS/forecast/exfoo.sh\n"
        )
        results = check_jjob_exscript_exists(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.PASS

    def test_nested_ush_call_found(
        self, tmp_path: Path, config: Config
    ) -> None:
        scripts = tmp_path / "scripts"
        ush_sub = tmp_path / "ush" / "helpers"
        scripts.mkdir()
        ush_sub.mkdir(parents=True)
        (ush_sub / "go.sh").touch()
        (scripts / "exmodel.sh").write_text(
            "#!/bin/bash\n$USH/helpers/go.sh\n"
        )
        results = check_exscript_ush_exists(tmp_path, config)
        assert any(r.status == Status.PASS for r in results)

    def test_path_qualified_call_is_not_basename_matched(
        self, tmp_path: Path, config: Config
    ) -> None:
        (tmp_path / "jobs").mkdir()
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        # real file is at the root, not under 'other/'
        (scripts / "exfoo.sh").touch()
        (tmp_path / "jobs" / "JMODEL").write_text(
            "#!/bin/bash\n$SCRIPTS/other/exfoo.sh\n"
        )
        results = check_jjob_exscript_exists(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.FAIL

    def test_nested_script_orphan_detected_by_path(
        self, tmp_path: Path, config: Config
    ) -> None:
        jobs = tmp_path / "jobs"
        scripts_a = tmp_path / "scripts"
        scripts_b = tmp_path / "scripts" / "subdir"
        jobs.mkdir()
        scripts_a.mkdir()
        scripts_b.mkdir()
        # J-job only references the flat version.
        (jobs / "JMODEL").write_text(
            "#!/bin/bash\n$SCRIPTS/exfoo.sh\n"
        )
        (scripts_a / "exfoo.sh").touch()
        (scripts_b / "exfoo.sh").touch()
        results = check_orphan_scripts(tmp_path, config)
        ex_results = [
            r for r in results if "exfoo.sh" in r.message
        ]
        statuses = {(r.status, "subdir" in r.message) for r in ex_results}
        # The subdir copy should be an orphan, the top-level one should pass.
        assert (Status.PASS, False) in statuses
        assert (Status.WARN, True) in statuses


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
