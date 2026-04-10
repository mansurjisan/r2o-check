"""Configuration loader for .r2o-check.yml files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class RepoType(Enum):
    """Type of repository being linted."""

    OPERATIONAL_MODEL = "operational_model"
    WORKFLOW = "workflow"
    TOOL = "tool"
    LIBRARY = "library"
    MODEL_SOURCE = "model_source"


DEFAULTS: dict[str, Any] = {
    "standards_version": "11.0.0",
    "repo_type": RepoType.OPERATIONAL_MODEL.value,
    "disabled_rules": [],
    "variants": {},
}

VALID_KEYS = {
    "standards_version",
    "repo_type",
    "disabled_rules",
    "variants",
}

# Accepted string values for repo_type.
_REPO_TYPE_VALUES = {rt.value for rt in RepoType}


@dataclass
class Config:
    """Parsed and validated project configuration."""

    standards_version: str = DEFAULTS["standards_version"]
    repo_type: RepoType = RepoType.OPERATIONAL_MODEL
    disabled_rules: list[str] = field(default_factory=list)
    variants: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> Config:
        """Load configuration from a YAML file."""
        text = path.read_text(encoding="utf-8")
        raw = yaml.safe_load(text)
        if raw is None:
            return cls()
        if not isinstance(raw, dict):
            msg = (
                ".r2o-check.yml must be a YAML mapping, "
                f"got {type(raw).__name__}"
            )
            raise ValueError(msg)
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Config:
        unknown = set(data.keys()) - VALID_KEYS
        if unknown:
            keys = ", ".join(sorted(unknown))
            raise ValueError(
                f"Unknown keys in .r2o-check.yml: {keys}"
            )

        standards_version = data.get(
            "standards_version", DEFAULTS["standards_version"]
        )
        if not isinstance(standards_version, str):
            raise ValueError("standards_version must be a string")

        repo_type_str = data.get(
            "repo_type", DEFAULTS["repo_type"]
        )
        if not isinstance(repo_type_str, str):
            raise ValueError("repo_type must be a string")
        if repo_type_str not in _REPO_TYPE_VALUES:
            valid = ", ".join(sorted(_REPO_TYPE_VALUES))
            raise ValueError(
                f"repo_type must be one of: {valid}"
            )
        repo_type = RepoType(repo_type_str)

        disabled_rules = data.get("disabled_rules", [])
        if not isinstance(disabled_rules, list) or not all(
            isinstance(r, str) for r in disabled_rules
        ):
            raise ValueError(
                "disabled_rules must be a list of strings"
            )

        variants = data.get("variants", {})
        if not isinstance(variants, dict):
            raise ValueError("variants must be a mapping")

        return cls(
            standards_version=standards_version,
            repo_type=repo_type,
            disabled_rules=disabled_rules,
            variants=variants,
        )


def load_config(repo_path: Path) -> Config:
    """Load config from repo_path/.r2o-check.yml, or defaults."""
    config_file = repo_path / ".r2o-check.yml"
    if config_file.is_file():
        return Config.from_file(config_file)
    return Config()
