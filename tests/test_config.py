"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from r2o_check.config import Config, RepoType, load_config

COMPLIANT = Path(__file__).parent / "fixtures" / "compliant_minimal"


def test_default_config() -> None:
    c = Config()
    assert c.standards_version == "11.0.0"
    assert c.repo_type == RepoType.OPERATIONAL_MODEL
    assert c.disabled_rules == []
    assert c.variants == {}


def test_load_from_compliant_fixture() -> None:
    c = load_config(COMPLIANT)
    assert c.standards_version == "11.0.0"


def test_load_missing_file_returns_defaults(
    tmp_path: Path,
) -> None:
    c = load_config(tmp_path)
    assert c.standards_version == "11.0.0"
    assert c.repo_type == RepoType.OPERATIONAL_MODEL


def test_load_empty_file(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text("")
    c = load_config(tmp_path)
    assert c.standards_version == "11.0.0"


def test_load_with_disabled_rules(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        'standards_version: "11.0.0"\n'
        "disabled_rules:\n  - R2OSTR001\n"
    )
    c = load_config(tmp_path)
    assert c.disabled_rules == ["R2OSTR001"]


def test_load_with_variants(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "variants:\n  coupled: true\n"
    )
    c = load_config(tmp_path)
    assert c.variants == {"coupled": True}


def test_load_with_repo_type(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "repo_type: workflow\n"
    )
    c = load_config(tmp_path)
    assert c.repo_type == RepoType.WORKFLOW


def test_unknown_key_raises(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text("bogus_key: true\n")
    with pytest.raises(ValueError, match="Unknown keys"):
        load_config(tmp_path)


def test_invalid_standards_version_type(
    tmp_path: Path,
) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "standards_version: 11\n"
    )
    with pytest.raises(
        ValueError, match="standards_version must be a string"
    ):
        load_config(tmp_path)


def test_invalid_disabled_rules_type(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "disabled_rules: not_a_list\n"
    )
    with pytest.raises(
        ValueError, match="disabled_rules must be a list"
    ):
        load_config(tmp_path)


def test_non_mapping_raises(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "- item1\n- item2\n"
    )
    with pytest.raises(ValueError, match="must be a YAML mapping"):
        load_config(tmp_path)


# ── Namespaced config sections ────────────────────────────────


def test_ecflow_config_defaults() -> None:
    c = Config()
    from r2o_check.config import DEFAULT_HARDCODED_PATHS

    assert c.ecflow.hardcoded_path_prefixes == DEFAULT_HARDCODED_PATHS


def test_ecflow_config_custom(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "ecflow:\n"
        "  hardcoded_path_prefixes:\n"
        "    - /custom/\n"
        "    - /mysite/\n"
    )
    c = load_config(tmp_path)
    assert c.ecflow.hardcoded_path_prefixes == [
        "/custom/",
        "/mysite/",
    ]


def test_ecflow_config_invalid(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "ecflow:\n  hardcoded_path_prefixes: not_a_list\n"
    )
    with pytest.raises(
        ValueError, match="hardcoded_path_prefixes"
    ):
        load_config(tmp_path)


def test_ecflow_key_accepted(tmp_path: Path) -> None:
    """ecflow is a valid top-level key, not rejected."""
    (tmp_path / ".r2o-check.yml").write_text("ecflow: {}\n")
    c = load_config(tmp_path)
    assert c.ecflow is not None


# ── Severity overrides ────────────────────────────────────────


def test_severity_overrides_default() -> None:
    c = Config()
    assert c.severity_overrides == {}


def test_severity_overrides_parsed(tmp_path: Path) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "severity_overrides:\n"
        "  R2OSTR009: fail\n"
        "  R2OENV001: warn\n"
    )
    c = load_config(tmp_path)
    assert c.severity_overrides == {
        "R2OSTR009": "fail",
        "R2OENV001": "warn",
    }


def test_severity_overrides_invalid_value(
    tmp_path: Path,
) -> None:
    (tmp_path / ".r2o-check.yml").write_text(
        "severity_overrides:\n  R2OSTR009: critical\n"
    )
    with pytest.raises(ValueError, match="must be one of"):
        load_config(tmp_path)


def test_severity_override_applied(tmp_path: Path) -> None:
    """Override changes the result severity."""
    from r2o_check.engine import LintRunner, Status

    (tmp_path / "jobs").mkdir()
    (tmp_path / "jobs" / "JMODEL").write_text("#!/bin/bash\n")
    c = Config(severity_overrides={"R2OENV001": "warn"})
    runner = LintRunner(tmp_path, c)
    results = runner.run()
    env_results = [
        r for r in results if r.rule_id == "R2OENV001"
    ]
    # All R2OENV001 results overridden from FAIL to WARN
    for r in env_results:
        if r.status != Status.PASS:
            assert r.status == Status.WARN
