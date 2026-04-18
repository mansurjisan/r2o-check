"""Tests for optional ecFlow .def validation (R2OECF007)."""

from __future__ import annotations

from pathlib import Path

from r2o_check.config import Config
from r2o_check.rules.ecflow_def import check_ecf_def_parses


def test_no_def_files_returns_empty(tmp_path: Path) -> None:
    config = Config()
    assert check_ecf_def_parses(tmp_path, config) == []


def test_def_files_without_ecflow_lib_is_inert(
    tmp_path: Path,
) -> None:
    """If ecflow lib is not importable, rule emits nothing.

    This test reflects the production reality that the ecflow
    Python module is typically not installed. When it IS
    installed the rule behaves differently, but either way
    the presence of .def files alone must not raise.
    """
    ecf = tmp_path / "ecf"
    ecf.mkdir()
    (ecf / "main.def").write_text(
        "suite main\nendsuite\n", encoding="utf-8"
    )
    config = Config()

    try:
        import ecflow  # noqa: F401
        ecflow_available = True
    except Exception:
        ecflow_available = False

    results = check_ecf_def_parses(tmp_path, config)
    if ecflow_available:
        # If available, at least one result; shape depends on
        # whether the toy .def above parses in the installed
        # version.
        assert len(results) == 1
    else:
        assert results == []
