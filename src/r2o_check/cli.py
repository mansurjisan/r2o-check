"""Click CLI entry point for r2o-check."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from r2o_check.config import load_config
from r2o_check.engine import LintRunner, Status
from r2o_check.formatters.cli_table import format_results
from r2o_check.formatters.html import format_results_html
from r2o_check.formatters.json_report import format_results_json
from r2o_check.formatters.markdown import format_results_markdown


@click.group()
@click.version_option(package_name="r2o-check")
def main() -> None:
    """r2o-check: NCO Implementation Standards v11.0 checker."""


@main.command()
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True
    ),
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "markdown", "html"]),
    default="table",
    help="Output format (default: table).",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    default=None,
    help="Write output to file instead of stdout.",
)
def lint(path: str, fmt: str, output_file: str | None) -> None:
    """Lint a repo for NCO Implementation Standards compliance."""
    repo_path = Path(path)
    config = load_config(repo_path)
    runner = LintRunner(repo_path, config)
    results = runner.run()

    has_failures = any(
        r.status in (Status.FAIL, Status.ERROR)
        for r in results
    )

    if fmt == "json":
        text = format_results_json(results, config)
        _write_output(text, output_file)
    elif fmt == "markdown":
        text = format_results_markdown(results, config)
        _write_output(text, output_file)
    elif fmt == "html":
        text = format_results_html(results, config)
        _write_output(text, output_file)
    else:
        console = Console()
        format_results(results, console)

    raise SystemExit(1 if has_failures else 0)


def _write_output(text: str, output_file: str | None) -> None:
    """Write text to file or stdout."""
    if output_file:
        Path(output_file).write_text(text, encoding="utf-8")
    else:
        click.echo(text)
