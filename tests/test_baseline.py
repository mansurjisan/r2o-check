"""Tests for baseline module."""

from __future__ import annotations

from pathlib import Path

from r2o_check.baseline import (
    Baseline,
    fingerprint,
)
from r2o_check.engine import LintResult, Status


def _result(
    status: Status,
    rule_id: str = "R2OXRF002",
    path: Path | None = None,
    line: int | None = None,
) -> LintResult:
    return LintResult(
        status=status,
        rule_id=rule_id,
        message=f"{rule_id} finding",
        path=path,
        line=line,
    )


def test_fingerprint_uses_relative_path(tmp_path: Path) -> None:
    sub = tmp_path / "jobs"
    sub.mkdir()
    jf = sub / "JMODEL"
    jf.touch()
    r = _result(Status.FAIL, path=jf, line=7)
    fp = fingerprint(r, tmp_path)
    # Four-component format: rule|relpath|line|detail
    parts = fp.split("|")
    assert parts[0] == "R2OXRF002"
    assert parts[1] == "jobs/JMODEL"
    assert parts[2] == "7"
    assert len(parts[3]) == 8


def test_fingerprint_includes_message_detail(
    tmp_path: Path,
) -> None:
    """Same rule / path / line but different messages → different fingerprints."""
    (tmp_path / "x").touch()
    r1 = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:3 calls 'exfoo.sh' — not found.",
        path=tmp_path / "x",
        line=3,
    )
    r2 = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:3 calls 'exbar.sh' — not found.",
        path=tmp_path / "x",
        line=3,
    )
    assert fingerprint(r1, tmp_path) != fingerprint(r2, tmp_path)


def test_fingerprint_stable_across_line_prefix_drift(
    tmp_path: Path,
) -> None:
    """Leading file:line in the message is stripped before hashing."""
    (tmp_path / "x").touch()
    r_line3 = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:3 calls 'exfoo.sh' — not found.",
        path=tmp_path / "x",
        line=3,
    )
    r_line7 = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:7 calls 'exfoo.sh' — not found.",
        path=tmp_path / "x",
        line=7,
    )
    fp3 = fingerprint(r_line3, tmp_path).rsplit("|", 1)[-1]
    fp7 = fingerprint(r_line7, tmp_path).rsplit("|", 1)[-1]
    # Detail digest ignores the file:line prefix so the
    # distinguishing text ('exfoo.sh') hashes the same.
    assert fp3 == fp7


def test_fingerprint_no_line_is_empty(tmp_path: Path) -> None:
    (tmp_path / "x").touch()
    r = _result(Status.WARN, path=tmp_path / "x")
    parts = fingerprint(r, tmp_path).split("|")
    assert parts[2] == ""  # empty line
    assert len(parts[3]) == 8


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    (jobs / "JMODEL").touch()
    results = [
        _result(
            Status.FAIL, path=jobs / "JMODEL", line=3,
        ),
        _result(
            Status.WARN, "R2OCNT004",
            path=jobs / "JMODEL", line=5,
        ),
        _result(Status.PASS),  # passes are excluded
    ]
    bl = Baseline.from_results(results, tmp_path)
    out = tmp_path / ".r2o-check-baseline.json"
    bl.save(out)

    loaded = Baseline.load(out)
    assert loaded.fingerprints == bl.fingerprints
    assert len(loaded.fingerprints) == 2


def test_filter_drops_baselined_fail(tmp_path: Path) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    jf = jobs / "JMODEL"
    jf.touch()
    baseline_results = [
        _result(Status.FAIL, path=jf, line=3),
    ]
    bl = Baseline.from_results(baseline_results, tmp_path)

    current = [
        _result(Status.FAIL, path=jf, line=3),     # baselined
        _result(Status.FAIL, path=jf, line=10),    # new
        _result(Status.PASS, path=jf),
    ]
    kept = bl.filter(current, tmp_path)
    assert len(kept) == 2
    assert {r.status for r in kept} == {
        Status.FAIL, Status.PASS,
    }
    fails = [r for r in kept if r.status == Status.FAIL]
    assert fails[0].line == 10


def test_find_stale_returns_dropped_entries(
    tmp_path: Path,
) -> None:
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    jf = jobs / "JMODEL"
    jf.touch()

    # Baseline captures two findings.
    baselined = [
        _result(Status.FAIL, path=jf, line=3),
        _result(Status.FAIL, path=jf, line=10),
    ]
    bl = Baseline.from_results(baselined, tmp_path)

    # Current run only has one of them (the other was fixed).
    current = [
        _result(Status.FAIL, path=jf, line=3),
    ]
    stale = bl.find_stale(current, tmp_path)
    assert len(stale) == 1
    assert any("|10" in fp for fp in stale)


def test_find_stale_empty_when_all_still_present(
    tmp_path: Path,
) -> None:
    jf = tmp_path / "x"
    jf.touch()
    results = [_result(Status.WARN, path=jf, line=1)]
    bl = Baseline.from_results(results, tmp_path)
    assert bl.find_stale(results, tmp_path) == set()


def test_rejects_unknown_version(tmp_path: Path) -> None:
    bl_file = tmp_path / "bl.json"
    bl_file.write_text(
        '{"version": 99, "findings": []}',
        encoding="utf-8",
    )
    import pytest
    with pytest.raises(ValueError):
        Baseline.load(bl_file)


def test_rejects_v1_baseline_with_regenerate_hint(
    tmp_path: Path,
) -> None:
    """Previously-produced v1 baselines must error out with guidance."""
    bl_file = tmp_path / "bl.json"
    bl_file.write_text(
        '{"version": 1, "findings": ["R2OSTR001|ecf|"]}',
        encoding="utf-8",
    )
    import pytest
    with pytest.raises(ValueError, match="Regenerate"):
        Baseline.load(bl_file)


def test_filter_does_not_conflate_same_line_different_finding(
    tmp_path: Path,
) -> None:
    """Two FAILs at same path/line/rule but different target
    should produce distinct fingerprints, so baselining one
    must not suppress the other."""
    jf = tmp_path / "jobs" / "JMODEL"
    jf.parent.mkdir()
    jf.touch()
    r_missing_foo = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:3 calls 'exfoo.sh' — not found.",
        path=jf,
        line=3,
    )
    r_missing_bar = LintResult(
        status=Status.FAIL,
        rule_id="R2OXRF002",
        message="JMODEL:3 calls 'exbar.sh' — not found.",
        path=jf,
        line=3,
    )

    bl = Baseline.from_results([r_missing_foo], tmp_path)
    kept = bl.filter(
        [r_missing_foo, r_missing_bar], tmp_path,
    )
    # The baselined finding is suppressed, the new one is kept.
    assert len(kept) == 1
    assert "exbar.sh" in kept[0].message
