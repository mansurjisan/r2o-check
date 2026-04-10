"""Rich-based CLI table formatter for lint results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from r2o_check.engine import LintResult, Status

# Map statuses to Rich markup colours.
_STATUS_STYLE = {
    Status.PASS: "[green]\u2714 PASS[/green]",
    Status.WARN: "[yellow]\u26a0 WARN[/yellow]",
    Status.FAIL: "[red]\u2718 FAIL[/red]",
    Status.ERROR: "[bold red]ERROR[/bold red]",
}


def format_results(results: list[LintResult], console: Console | None = None) -> int:
    """Print results as a Rich table.

    Returns the exit code (0 = all pass, 1 = failures).
    """
    if console is None:
        console = Console(stderr=False)

    table = Table(title="r2o-check lint results", show_lines=False)
    table.add_column("Status", width=10)
    table.add_column("Rule", width=12)
    table.add_column("Message")
    table.add_column("Fix hint", style="dim")

    for r in results:
        table.add_row(
            _STATUS_STYLE.get(r.status, str(r.status.value)),
            r.rule_id,
            r.message,
            r.fix_hint or "",
        )

    console.print(table)

    # Summary line.
    counts = {s: 0 for s in Status}
    for r in results:
        counts[r.status] += 1

    parts = []
    if counts[Status.PASS]:
        parts.append(f"[green]{counts[Status.PASS]} passed[/green]")
    if counts[Status.WARN]:
        parts.append(f"[yellow]{counts[Status.WARN]} warnings[/yellow]")
    if counts[Status.FAIL]:
        parts.append(f"[red]{counts[Status.FAIL]} failed[/red]")
    if counts[Status.ERROR]:
        parts.append(f"[bold red]{counts[Status.ERROR]} errors[/bold red]")

    console.print("\n" + ", ".join(parts))

    has_failures = counts[Status.FAIL] > 0 or counts[Status.ERROR] > 0
    return 1 if has_failures else 0
