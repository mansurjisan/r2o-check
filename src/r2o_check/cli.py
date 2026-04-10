"""Click CLI entry point for r2o-check."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from r2o_check.config import load_config
from r2o_check.engine import LintRunner
from r2o_check.formatters.cli_table import format_results


@click.group()
@click.version_option(package_name="r2o-check")
def main() -> None:
    """r2o-check: NCO Implementation Standards v11.0 compliance checker."""


@main.command()
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table"]),
    default="table",
    help="Output format (default: table).",
)
def lint(path: str, fmt: str) -> None:
    """Lint a repository for NCO Implementation Standards compliance."""
    repo_path = Path(path)
    config = load_config(repo_path)
    runner = LintRunner(repo_path, config)
    results = runner.run()

    console = Console()
    exit_code = format_results(results, console)
    raise SystemExit(exit_code)
