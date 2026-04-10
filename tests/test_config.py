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
