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
from r2o_check.formatters.sarif import format_results_sarif


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
    type=click.Choice(["table", "json", "markdown", "html", "sarif"]),
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
@click.option(
    "--markdown-include-passes",
    is_flag=True,
    default=False,
    help="Include passing rules in markdown output.",
)
def lint(
    path: str,
    fmt: str,
    output_file: str | None,
    markdown_include_passes: bool,
) -> None:
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
        text = format_results_markdown(
            results, config,
            include_passes=markdown_include_passes,
        )
        _write_output(text, output_file)
    elif fmt == "html":
        text = format_results_html(results, config)
        _write_output(text, output_file)
    elif fmt == "sarif":
        text = format_results_sarif(results, config)
        _write_output(text, output_file)
    else:
        if output_file:
            with open(
                output_file, "w", encoding="utf-8"
            ) as fh:
                console = Console(
                    file=fh,
                    force_terminal=False,
                    color_system=None,
                    width=120,
                )
                format_results(results, console)
        else:
            console = Console()
            format_results(results, console)

    raise SystemExit(1 if has_failures else 0)


@main.command()
@click.argument(
    "path",
    type=click.Path(
        exists=True, file_okay=False, resolve_path=True
    ),
)
@click.option(
    "--apply",
    "apply_fixes",
    is_flag=True,
    default=False,
    help="Apply fixes (default: dry-run only).",
)
def fix(path: str, apply_fixes: bool) -> None:
    """Auto-fix safe, unambiguous rule violations."""
    from r2o_check.config import RepoType
    from r2o_check.fixers.structure import fix_missing_directories
    from r2o_check.fixers.versions import fix_missing_version_files

    repo_path = Path(path)
    config = load_config(repo_path)
    dry_run = not apply_fixes
    mode = "DRY RUN" if dry_run else "APPLYING"

    console = Console()
    console.print(f"[bold]r2o-check fix ({mode})[/bold]\n")

    scaffoldable = {
        RepoType.OPERATIONAL_MODEL, RepoType.WORKFLOW,
    }
    actions = []
    if config.repo_type in scaffoldable:
        actions.extend(
            fix_missing_directories(repo_path, dry_run=dry_run)
        )
        actions.extend(
            fix_missing_version_files(repo_path, dry_run=dry_run)
        )
    else:
        console.print(
            f"No auto-fixes apply to repo_type"
            f" '{config.repo_type.value}'."
        )
        return

    if not actions:
        console.print("[green]Nothing to fix![/green]")
        return

    for a in actions:
        status = (
            "[green]APPLIED[/green]" if a.applied
            else "[yellow]WOULD FIX[/yellow]"
        )
        console.print(
            f"  {status} {a.rule_id}: {a.description}"
        )

    console.print(
        f"\n[bold]{len(actions)} fix(es)"
        f" {'applied' if apply_fixes else 'proposed'}."
        f"[/bold]"
    )
    if dry_run:
        console.print(
            "Run with --apply to apply fixes."
        )


@main.command()
@click.argument(
    "path",
    type=click.Path(resolve_path=True),
    default=".",
)
def init(path: str) -> None:
    """Initialize a repo for r2o-check compliance."""
    from r2o_check.config import RepoType
    from r2o_check.fixers.structure import fix_missing_directories
    from r2o_check.fixers.versions import fix_missing_version_files

    repo_path = Path(path)
    repo_path.mkdir(parents=True, exist_ok=True)
    console = Console()
    console.print("[bold]r2o-check init[/bold]\n")

    # Ask repo type.
    type_map = {str(i): rt for i, rt in enumerate(RepoType, 1)}
    console.print("Select repo type:")
    for num, rt in type_map.items():
        console.print(f"  {num}) {rt.value}")
    choice = click.prompt(
        "Choice", type=click.Choice(list(type_map.keys())),
        default="1",
    )
    repo_type = type_map[choice]

    # Write .r2o-check.yml.
    config_path = repo_path / ".r2o-check.yml"
    if config_path.exists():
        console.print(
            "[yellow].r2o-check.yml already exists[/yellow]"
        )
    else:
        config_path.write_text(
            f'repo_type: {repo_type.value}\n'
            f'standards_version: "11.0.0"\n',
            encoding="utf-8",
        )
        console.print(
            f"[green]Created .r2o-check.yml"
            f" (repo_type: {repo_type.value})[/green]"
        )

    # Scaffold directories.
    if repo_type in (
        RepoType.OPERATIONAL_MODEL, RepoType.WORKFLOW
    ):
        actions = fix_missing_directories(
            repo_path, dry_run=False
        )
        actions.extend(
            fix_missing_version_files(
                repo_path, dry_run=False
            )
        )
        for a in actions:
            console.print(
                f"  [green]Created[/green] {a.description}"
            )
        if not actions:
            console.print(
                "  All directories already exist."
            )

    console.print("\n[bold]Done![/bold] Run"
                  " 'r2o-check lint .' to check compliance.")


def _write_output(text: str, output_file: str | None) -> None:
    """Write text to file or stdout."""
    if output_file:
        Path(output_file).write_text(text, encoding="utf-8")
    else:
        click.echo(text)
