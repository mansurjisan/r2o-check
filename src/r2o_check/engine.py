"""Core lint engine: LintResult, LintRunner, and rule discovery."""

from __future__ import annotations

import importlib
import inspect
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from r2o_check.config import Config


class Status(Enum):
    """Result status for a lint check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class LintResult:
    """Outcome of a single lint rule execution."""

    status: Status
    rule_id: str
    message: str
    path: Path | None = None
    fix_hint: str | None = None


# Type alias for a rule function.
RuleFunc = Callable[[Path, Config], list[LintResult]]

# Registry populated by @register_rule decorator.
_RULE_REGISTRY: dict[str, RuleFunc] = {}


def register_rule(func: RuleFunc) -> RuleFunc:
    """Decorator that registers a rule function by its name."""
    _RULE_REGISTRY[func.__name__] = func
    return func


def get_registered_rules() -> dict[str, RuleFunc]:
    """Return a copy of the current rule registry."""
    return dict(_RULE_REGISTRY)


# Mapping from module names to their dotted import paths.
RULE_MODULES: list[str] = [
    "r2o_check.rules.structure",
]


class LintRunner:
    """Discovers and executes lint rules against a repository path."""

    def __init__(self, repo_path: Path, config: Config | None = None) -> None:
        self.repo_path = repo_path.resolve()
        self.config = config or Config()
        self._rules: dict[str, RuleFunc] = {}

    def discover_rules(self) -> None:
        """Import rule modules so their @register_rule decorators fire."""
        for module_name in RULE_MODULES:
            importlib.import_module(module_name)
        self._rules = get_registered_rules()

    def run(self) -> list[LintResult]:
        """Run all discovered rules that are not disabled in config."""
        if not self._rules:
            self.discover_rules()

        results: list[LintResult] = []
        for name, func in sorted(self._rules.items()):
            try:
                rule_results = func(self.repo_path, self.config)
            except Exception:
                rule_results = [
                    LintResult(
                        status=Status.ERROR,
                        rule_id=_infer_rule_id(func),
                        message=(
                            f"Rule {name!r} raised an exception: "
                            f"{traceback.format_exc()}"
                        ),
                    )
                ]
            for result in rule_results:
                if result.rule_id not in self.config.disabled_rules:
                    results.append(result)
        return results

    def run_rules(self, rule_ids: Sequence[str]) -> list[LintResult]:
        """Run only the specified rule IDs."""
        if not self._rules:
            self.discover_rules()

        results: list[LintResult] = []
        for name, func in sorted(self._rules.items()):
            rid = _infer_rule_id(func)
            if rid not in rule_ids:
                continue
            try:
                rule_results = func(self.repo_path, self.config)
            except Exception:
                rule_results = [
                    LintResult(
                        status=Status.ERROR,
                        rule_id=rid,
                        message=(
                            f"Rule {name!r} raised an exception: "
                            f"{traceback.format_exc()}"
                        ),
                    )
                ]
            results.extend(rule_results)
        return results


def _infer_rule_id(func: RuleFunc) -> str:
    """Try to extract a rule ID from the function's docstring or name."""
    doc = inspect.getdoc(func) or ""
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("R2O"):
            return stripped.split()[0].rstrip(".:,")
    return func.__name__
