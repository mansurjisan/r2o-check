"""Tests for ecFlow rules (R2OECF001-005)."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config
from r2o_check.engine import Status
from r2o_check.rules.ecflow import (
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
        assert len(warns) == 1
        assert "/lfs/" in warns[0].message or "hard-coded" in warns[0].message

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
