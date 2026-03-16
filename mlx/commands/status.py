"""
mlx/commands/ls.py

The `mlx ls` command — shortcut for listing all runs.

Supports filtering and sorting so you can quickly
find the run you're looking for.

Usage:
    mlx ls
    mlx ls --experiment fraud-detection
    mlx ls --status done
    mlx ls --limit 5
    mlx ls --all
"""

import typer
from rich.console import Console
from rich.text import Text

from mlx.core.run import RunManager
from mlx.core.metrics import MetricManager
from mlx.utils.display import runs_table, info, warn

app = typer.Typer(help="List all runs. Shortcut for `mlx run list`.")
console = Console()


@app.callback(invoke_without_command=True)
def ls(
    experiment: str = typer.Option(
        None,
        "--experiment", "-e",
        help="Filter by experiment name"
    ),
    status: str = typer.Option(
        None,
        "--status", "-s",
        help="Filter by status: running, done, failed"
    ),
    limit: int = typer.Option(
        20,
        "--limit", "-l",
        help="Max runs to show (default 20)"
    ),
    show_all: bool = typer.Option(
        False,
        "--all", "-a",
        help="Show all runs ignoring limit"
    ),
    metrics: bool = typer.Option(
        False,
        "--metrics", "-m",
        help="Show latest metric values in the table"
    ),
):
    """
    List all runs in a clean table.

    Shows run ID, name, experiment, status, tags,
    created time and duration at a glance.

    Examples:
        mlx ls
        mlx ls --experiment fraud-detection
        mlx ls --status done
        mlx ls --limit 5
        mlx ls --all
        mlx ls --metrics
    """

    # --all overrides --limit
    actual_limit = 999999 if show_all else limit

    # Fetch runs with filters
    runs = RunManager.get_all(
        experiment=experiment,
        status=status,
        limit=actual_limit,
    )

    # ── Empty state ────────────────────────────
    if not runs:
        console.print()

        if experiment or status:
            # Filters returned nothing
            warn("No runs found matching your filters.")
            console.print()
            if experiment:
                console.print(f"  [dim]experiment:[/dim] {experiment}")
            if status:
                console.print(f"  [dim]status    :[/dim] {status}")
            console.print()
            console.print(
                "  Try [cyan]mlx ls[/cyan] without filters "
                "to see all runs."
            )
        else:
            # No runs at all yet
            info("No runs yet.")
            console.print()
            console.print(
                "  Start your first run: "
                "[cyan]mlx run start --name 'my-run'[/cyan]"
            )

        console.print()
        return

    # ── Build and print table ──────────────────
    console.print()

    if metrics:
        # Enhanced table with metric columns
        _print_table_with_metrics(runs)
    else:
        # Standard table
        console.print(runs_table(runs))

    # ── Footer summary ─────────────────────────
    _print_summary(runs, limit, show_all, actual_limit)


def _print_table_with_metrics(runs: list):
    """
    Print runs table with an extra column showing
    the latest metric values for each run.

    Collects all unique metric keys across all runs
    then adds one column per metric.
    """
    from rich.table import Table
    from rich import box

    # Find all unique metric keys across all runs
    all_keys = set()
    metrics_by_run = {}

    for run in runs:
        m_dict = {
            m.key: m.value
            for m in MetricManager.get_latest(run.run_id)
        }
        metrics_by_run[run.run_id] = m_dict
        all_keys.update(m_dict.keys())

    # Sort metric keys alphabetically
    metric_keys = sorted(all_keys)

    # Build table
    table = Table(
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold cyan",
        show_lines=False,
    )

    # Standard columns
    table.add_column("Name",       style="bold white")
    table.add_column("Experiment", style="magenta")
    table.add_column("Status",     justify="center")
    table.add_column("Duration",   justify="right", style="yellow")

    # One column per metric
    for key in metric_keys:
        table.add_column(key, justify="right", style="green")

    # Add rows
    for run in runs:
        status_display = {
            "running": "[bold yellow]⟳ running[/bold yellow]",
            "done":    "[bold green]✓ done[/bold green]",
            "failed":  "[bold red]✗ failed[/bold red]",
        }.get(run.status, run.status)

        duration = "-"
        if run.duration_sec is not None:
            m, s = divmod(int(run.duration_sec), 60)
            duration = f"{m}m {s}s" if m > 0 else f"{s}s"

        # Base columns
        row = [
            run.name,
            run.experiment,
            status_display,
            duration,
        ]

        # Metric columns — show value or dash if not logged
        run_metrics = metrics_by_run.get(run.run_id, {})
        for key in metric_keys:
            val = run_metrics.get(key)
            row.append(f"{val:.4f}" if val is not None else "-")

        table.add_row(*row)

    console.print(table)


def _print_summary(runs, limit, show_all, actual_limit):
    """Print a summary line below the table."""

    done_count    = sum(1 for r in runs if r.status == "done")
    running_count = sum(1 for r in runs if r.status == "running")
    failed_count  = sum(1 for r in runs if r.status == "failed")

    # Warning if results were cut off by limit
    limit_note = ""
    if not show_all and len(runs) == limit:
        limit_note = (
            f"  [dim](showing last {limit} — "
            f"use [cyan]--all[/cyan] to see everything)[/dim]"
        )

    console.print(
        f"\n  [dim]{len(runs)} run(s)  ·  "
        f"[green]{done_count} done[/green]  ·  "
        f"[yellow]{running_count} running[/yellow]  ·  "
        f"[red]{failed_count} failed[/red][/dim]"
        f"{limit_note}"
    )
    console.print()