"""Core lint engine: LintResult, LintRunner, and rule discovery."""

from __future__ import annotations

import importlib
import inspect
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, overload

from r2o_check.config import Config, RepoType


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
    line: int | None = None


# Type alias for a rule function.
RuleFunc = Callable[[Path, Config], list[LintResult]]


@dataclass
class RuleEntry:
    """A registered rule with its metadata."""

    func: RuleFunc
    applies_to: list[RepoType]
    mutually_exclusive_with: list[str] | None = None


# Registry populated by @register_rule decorator.
_RULE_REGISTRY: dict[str, RuleEntry] = {}

# All repo types, for rules that apply universally.
ALL_REPO_TYPES: list[RepoType] = list(RepoType)

# Default applies_to for model-specific rules.
MODEL_REPO_TYPES: list[RepoType] = [
    RepoType.OPERATIONAL_MODEL,
    RepoType.WORKFLOW,
]

# Repos that build compiled code.
BUILD_REPO_TYPES: list[RepoType] = [
    RepoType.OPERATIONAL_MODEL,
    RepoType.WORKFLOW,
    RepoType.MODEL_SOURCE,
    RepoType.LIBRARY,
]

# Repos that have modulefiles.
MODULE_REPO_TYPES: list[RepoType] = [
    RepoType.OPERATIONAL_MODEL,
    RepoType.WORKFLOW,
    RepoType.MODEL_SOURCE,
]


@overload
def register_rule(func: RuleFunc) -> RuleFunc: ...


@overload
def register_rule(
    *,
    applies_to: list[RepoType],
    mutually_exclusive_with: list[str] | None = ...,
) -> Callable[[RuleFunc], RuleFunc]: ...


def register_rule(
    func: RuleFunc | None = None,
    *,
    applies_to: list[RepoType] | None = None,
    mutually_exclusive_with: list[str] | None = None,
) -> RuleFunc | Callable[[RuleFunc], RuleFunc]:
    """Register a rule function.

    Use as @register_rule or @register_rule(applies_to=[...]).
    mutually_exclusive_with: list of rule IDs. If any of
    those rules produced PASS results, this rule is skipped.
    """
    effective = (
        applies_to if applies_to is not None
        else list(ALL_REPO_TYPES)
    )

    def _decorator(fn: RuleFunc) -> RuleFunc:
        _RULE_REGISTRY[fn.__name__] = RuleEntry(
            func=fn,
            applies_to=effective,
            mutually_exclusive_with=mutually_exclusive_with,
        )
        return fn

    if func is not None:
        return _decorator(func)
    return _decorator


def get_registered_rules() -> dict[str, RuleEntry]:
    """Return a copy of the current rule registry."""
    return dict(_RULE_REGISTRY)


# Mapping from module names to their dotted import paths.
RULE_MODULES: list[str] = [
    "r2o_check.rules.structure",
    "r2o_check.rules.naming",
    "r2o_check.rules.environment",
    "r2o_check.rules.build",
    "r2o_check.rules.modules",
    "r2o_check.rules.versions",
    "r2o_check.rules.ecflow",
    "r2o_check.rules.ecflow_def",
    "r2o_check.rules.crossref",
    "r2o_check.rules.content",
]


class LintRunner:
    """Discovers and executes lint rules against a repo path."""

    def __init__(
        self, repo_path: Path, config: Config | None = None
    ) -> None:
        self.repo_path = repo_path.resolve()
        self.config = config or Config()
        self._rules: dict[str, RuleEntry] = {}

    def discover_rules(self) -> None:
        """Import rule modules to trigger @register_rule."""
        for module_name in RULE_MODULES:
            importlib.import_module(module_name)
        self._rules = get_registered_rules()

    def _applies(self, entry: RuleEntry) -> bool:
        """Check if a rule applies to the current repo type."""
        return self.config.repo_type in entry.applies_to

    def _is_suppressed(self, result: LintResult) -> bool:
        """Check if a result is suppressed by inline comment."""
        if result.path is None or not result.path.is_file():
            return False
        try:
            content = result.path.read_text(
                encoding="utf-8", errors="replace"
            )
        except Exception:
            return False
        # Look for: # r2o-check:disable=RULE_ID
        marker = f"r2o-check:disable={result.rule_id}"
        return marker in content

    def _apply_override(self, result: LintResult) -> LintResult:
        """Apply severity override from config if present."""
        overrides = self.config.severity_overrides
        if result.rule_id in overrides:
            new_status = Status(overrides[result.rule_id])
            if new_status != result.status:
                result = LintResult(
                    status=new_status,
                    rule_id=result.rule_id,
                    message=result.message,
                    path=result.path,
                    fix_hint=result.fix_hint,
                    line=result.line,
                )
        return result

    def _execute_rule(
        self, name: str, entry: RuleEntry
    ) -> list[LintResult]:
        """Run a rule function and catch exceptions as ERROR."""
        try:
            return entry.func(self.repo_path, self.config)
        except Exception:
            return [
                LintResult(
                    status=Status.ERROR,
                    rule_id=_infer_rule_id(entry.func),
                    message=(
                        f"Rule {name!r} raised an"
                        f" exception:"
                        f" {traceback.format_exc()}"
                    ),
                )
            ]

    def _post_process(
        self, rule_results: list[LintResult]
    ) -> tuple[list[LintResult], bool]:
        """Apply disabled/suppression/override to raw results.

        Returns (kept_results, has_pass).
        """
        kept: list[LintResult] = []
        has_pass = False
        for result in rule_results:
            if result.rule_id in self.config.disabled_rules:
                continue
            if self._is_suppressed(result):
                continue
            result = self._apply_override(result)
            kept.append(result)
            if result.status == Status.PASS:
                has_pass = True
        return kept, has_pass

    def run(self) -> list[LintResult]:
        """Run all applicable, non-disabled rules."""
        if not self._rules:
            self.discover_rules()

        results: list[LintResult] = []
        # Track which rule IDs have run (produced any results),
        # for mutual-exclusion logic.
        ran_rule_ids: set[str] = set()

        for name, entry in sorted(self._rules.items()):
            if not self._applies(entry):
                continue
            # Check mutual exclusion: skip if an exclusive
            # partner already ran successfully.
            if entry.mutually_exclusive_with:
                if ran_rule_ids & set(
                    entry.mutually_exclusive_with
                ):
                    continue
            rule_results = self._execute_rule(name, entry)
            kept, has_pass = self._post_process(rule_results)
            results.extend(kept)
            if has_pass:
                ran_rule_ids.add(_infer_rule_id(entry.func))
        return results

    def run_rules(self, rule_ids: Sequence[str]) -> list[LintResult]:
        """Run only the specified rule IDs.

        Shares the post-processing pipeline with ``run`` so
        disabled rules, severity overrides, and inline
        suppression behave identically. ``applies_to`` is still
        honored — requesting a rule outside the repo_type
        matrix yields no results.
        """
        if not self._rules:
            self.discover_rules()

        wanted = set(rule_ids)
        results: list[LintResult] = []
        for name, entry in sorted(self._rules.items()):
            rid = _infer_rule_id(entry.func)
            if rid not in wanted:
                continue
            if not self._applies(entry):
                continue
            rule_results = self._execute_rule(name, entry)
            kept, _ = self._post_process(rule_results)
            results.extend(kept)
        return results


def _infer_rule_id(func: RuleFunc) -> str:
    """Extract a rule ID from docstring or fall back to name."""
    doc = inspect.getdoc(func) or ""
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("R2O"):
            return stripped.split()[0].rstrip(".:,")
    return func.__name__
