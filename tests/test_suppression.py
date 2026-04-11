"""Tests for inline suppression."""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import LintRunner, Status


def test_inline_suppression(tmp_path: Path) -> None:
    """# r2o-check:disable=RULE suppresses that rule."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    # J-job missing set -x but has suppression comment
    (jobs / "JMODEL").write_text(
        "#!/bin/bash\n"
        "# r2o-check:disable=R2OCNT001\n"
        "echo hi\n"
    )
    config = Config()
    runner = LintRunner(tmp_path, config)
    results = runner.run()
    cnt001 = [
        r for r in results
        if r.rule_id == "R2OCNT001"
        and "JMODEL" in r.message
    ]
    # Should be suppressed — no results for this rule+file
    assert len(cnt001) == 0


def test_suppression_only_affects_target_rule(
    tmp_path: Path,
) -> None:
    """Suppressing one rule doesn't suppress others."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    (jobs / "JMODEL").write_text(
        "#!/bin/bash\n"
        "# r2o-check:disable=R2OCNT001\n"
        "echo hi\n"
    )
    config = Config()
    runner = LintRunner(tmp_path, config)
    results = runner.run()
    # R2OCNT003 (shebang) should still fire — not suppressed
    # Wait, this file HAS a shebang. Check other rules.
    env_results = [
        r for r in results if r.rule_id == "R2OENV001"
    ]
    # ENV rules should still run
    assert len(env_results) > 0


def test_no_suppression_without_comment(
    tmp_path: Path,
) -> None:
    """Without the comment, rule fires normally."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    (jobs / "JMODEL").write_text("#!/bin/bash\necho hi\n")
    config = Config()
    runner = LintRunner(tmp_path, config)
    results = runner.run()
    cnt001 = [
        r for r in results
        if r.rule_id == "R2OCNT001"
        and "JMODEL" in r.message
    ]
    assert len(cnt001) > 0
    assert cnt001[0].status == Status.FAIL
