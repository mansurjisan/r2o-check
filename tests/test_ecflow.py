"""Tests for ecFlow rules (R2OECF001-005)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.ecflow import (
    check_ecf_custom_head_tail,
    check_ecf_directives,
    check_ecf_hardcoded_paths,
    check_ecf_includes,
    check_ecf_init_complete,
    check_ecf_trap,
)

FIXTURES = Path(__file__).parent / "fixtures"
COMPLIANT = FIXTURES / "ecflow_compliant"
BROKEN = FIXTURES / "ecflow_broken"
HARDCODED = FIXTURES / "ecflow_hardcoded"
CUSTOM_OK = FIXTURES / "ecflow_custom_head_ok"
CUSTOM_BROKEN = FIXTURES / "ecflow_custom_head_broken"
RRFS = FIXTURES / "rrfs_style"


@pytest.fixture
def config() -> Config:
    return Config()


# ── R2OECF001: head.h / tail.h includes ──────────────────────


class TestEcfIncludes:
    def test_compliant_all_pass(self, config: Config) -> None:
        results = check_ecf_includes(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)
        assert len(results) == 2

    def test_broken_missing_both(self, config: Config) -> None:
        results = check_ecf_includes(BROKEN, config)
        bad = [r for r in results if "jmodel_bad" in r.message]
        assert bad[0].status == Status.FAIL
        assert "head.h" in bad[0].message

    def test_broken_missing_tail(self, config: Config) -> None:
        results = check_ecf_includes(BROKEN, config)
        notail = [
            r for r in results if "jmodel_notail" in r.message
        ]
        assert notail[0].status == Status.FAIL
        assert "tail.h" in notail[0].message

    def test_no_ecf_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_ecf_includes(tmp_path, config) == []

    def test_rrfs_passes(self, config: Config) -> None:
        results = check_ecf_includes(RRFS, config)
        assert all(r.status == Status.PASS for r in results)


# ── R2OECF002: paired init/complete ──────────────────────────


class TestEcfInitComplete:
    def test_compliant_passes_via_includes(
        self, config: Config
    ) -> None:
        results = check_ecf_init_complete(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)

    def test_broken_missing_complete(
        self, config: Config
    ) -> None:
        results = check_ecf_init_complete(BROKEN, config)
        bad = [r for r in results if "jmodel_bad" in r.message]
        assert bad[0].status == Status.FAIL
        assert "ecflow_client --complete" in bad[0].message

    def test_broken_notail_passes_via_head(
        self, config: Config
    ) -> None:
        """notail has head.h but not tail.h — R2OECF002 checks
        for both head+tail, so this should FAIL."""
        results = check_ecf_init_complete(BROKEN, config)
        notail = [
            r for r in results if "jmodel_notail" in r.message
        ]
        assert notail[0].status == Status.FAIL


# ── R2OECF003: trap handler ──────────────────────────────────


class TestEcfTrap:
    def test_compliant_passes(self, config: Config) -> None:
        results = check_ecf_trap(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)

    def test_broken_no_trap(self, config: Config) -> None:
        results = check_ecf_trap(BROKEN, config)
        bad = [r for r in results if "jmodel_bad" in r.message]
        assert bad[0].status == Status.FAIL

    def test_head_h_counts_as_trap(
        self, config: Config
    ) -> None:
        """Files with %include <head.h> pass trap check."""
        results = check_ecf_trap(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)


# ── R2OECF004: PBS/Slurm directives ──────────────────────────


class TestEcfDirectives:
    def test_compliant_pbs_passes(
        self, config: Config
    ) -> None:
        results = check_ecf_directives(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)

    def test_no_directives_skipped(
        self, config: Config
    ) -> None:
        """Files without any scheduler directives are skipped."""
        results = check_ecf_directives(BROKEN, config)
        # broken ecf files have no PBS/SBATCH directives
        assert len(results) == 0

    def test_malformed_directive_warns(
        self, tmp_path: Path, config: Config
    ) -> None:
        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (ecf / "bad.ecf").write_text(
            "#!/bin/bash\n#PBS walltime=01:00:00\n"
        )
        results = check_ecf_directives(tmp_path, config)
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert results[0].line == 2


# ── R2OECF005: hard-coded paths ──────────────────────────────


class TestEcfHardcodedPaths:
    def test_compliant_no_hardcoded(
        self, config: Config
    ) -> None:
        results = check_ecf_hardcoded_paths(COMPLIANT, config)
        assert all(r.status == Status.PASS for r in results)

    def test_hardcoded_paths_warn(
        self, config: Config
    ) -> None:
        results = check_ecf_hardcoded_paths(
            HARDCODED, config
        )
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) >= 1
        assert all(w.line is not None for w in warns)
        assert any(
            "/lfs/" in w.message or "/gpfs/" in w.message
            for w in warns
        )

    def test_assignment_lines_excluded(
        self, tmp_path: Path, config: Config
    ) -> None:
        """Variable assignments with paths are not flagged."""
        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (ecf / "ok.ecf").write_text(
            "#!/bin/bash\n"
            "DATA=/lfs/h1/tmp/$jobid\n"
            "$HOMEmodel/jobs/JMODEL\n"
        )
        results = check_ecf_hardcoded_paths(tmp_path, config)
        assert all(r.status == Status.PASS for r in results)

    def test_hardcoded_paths_record_line_numbers(
        self, config: Config
    ) -> None:
        results = check_ecf_hardcoded_paths(
            HARDCODED, config
        )
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) == 2
        lines = sorted(w.line for w in warns if w.line)
        assert lines == [7, 8]

    def test_export_assignment_excluded(
        self, tmp_path: Path, config: Config
    ) -> None:
        """`export VAR=/lfs/...` is also an assignment."""
        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (ecf / "ok.ecf").write_text(
            "#!/bin/bash\n"
            "export DATA=/lfs/h1/tmp/$jobid\n"
            "readonly TMP=/scratch/x\n"
        )
        results = check_ecf_hardcoded_paths(tmp_path, config)
        assert all(r.status == Status.PASS for r in results)

    def test_no_ecf_returns_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_ecf_hardcoded_paths(tmp_path, config) == []


# ── Integration ───────────────────────────────────────────────


class TestEcflowIntegration:
    def test_rrfs_ecflow_all_pass(self) -> None:
        from r2o_check.engine import LintRunner

        runner = LintRunner(RRFS)
        results = runner.run()
        ecf_fails = [
            r
            for r in results
            if r.rule_id.startswith("R2OECF")
            and r.status == Status.FAIL
        ]
        assert len(ecf_fails) == 0

    def test_broken_ecflow_has_failures(self) -> None:
        from r2o_check.engine import LintRunner

        runner = LintRunner(BROKEN)
        results = runner.run()
        ecf_fails = [
            r
            for r in results
            if r.rule_id.startswith("R2OECF")
            and r.status == Status.FAIL
        ]
        assert len(ecf_fails) >= 3  # includes, init/complete, trap


# ── R2OECF006: custom head.h/tail.h ──────────────────────────


class TestCustomHeadTail:
    def test_ok_head_tail_pass(self, config: Config) -> None:
        results = check_ecf_custom_head_tail(CUSTOM_OK, config)
        assert len(results) == 2
        assert all(r.status == Status.PASS for r in results)

    def test_broken_head_tail_warn(
        self, config: Config
    ) -> None:
        results = check_ecf_custom_head_tail(
            CUSTOM_BROKEN, config
        )
        assert len(results) == 2
        assert all(r.status == Status.WARN for r in results)

    def test_no_include_dir_empty(
        self, tmp_path: Path, config: Config
    ) -> None:
        assert check_ecf_custom_head_tail(tmp_path, config) == []

    def test_no_head_file_skipped(
        self, tmp_path: Path, config: Config
    ) -> None:
        inc = tmp_path / "include"
        inc.mkdir()
        # Only tail.h, no head.h
        (inc / "tail.h").write_text("ecflow_client --complete\n")
        results = check_ecf_custom_head_tail(tmp_path, config)
        assert len(results) == 1
        assert results[0].rule_id == "R2OECF006"


# ── R2OECF005 config integration ─────────────────────────────


class TestHardcodedPathsConfig:
    def test_custom_prefixes(
        self, tmp_path: Path
    ) -> None:
        """Config overrides hardcoded path prefixes."""
        from r2o_check.config import Config, EcflowConfig

        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (ecf / "test.ecf").write_text(
            "#!/bin/bash\n"
            "cp /custom/data/input.dat $DATA/\n"
        )
        config = Config(
            ecflow=EcflowConfig(
                hardcoded_path_prefixes=["/custom/"]
            )
        )
        results = check_ecf_hardcoded_paths(tmp_path, config)
        warns = [r for r in results if r.status == Status.WARN]
        assert len(warns) == 1

    def test_default_prefixes_ignore_custom(
        self, tmp_path: Path, config: Config
    ) -> None:
        """Default prefixes don't flag /custom/."""
        ecf = tmp_path / "ecf"
        ecf.mkdir()
        (ecf / "test.ecf").write_text(
            "#!/bin/bash\ncp /custom/data/in.dat $DATA/\n"
        )
        results = check_ecf_hardcoded_paths(tmp_path, config)
        assert all(r.status == Status.PASS for r in results)
