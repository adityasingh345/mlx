"""
mlx/commands/status.py

The `mlx status` command.
Shortcut for `mlx run status` — shows the active run.

This is the command you run when you want to quickly
check what's currently being tracked.

Usage:
    mlx status
    mlx status --run-id "catboost-v1_20240301_143201"
    mlx status --logs
"""

import typer
from rich.console import Console
from rich.panel import Panel

from mlx.core.run import RunManager
from mlx.core.metrics import MetricManager
from mlx.core.params import ParamManager
from mlx.storage.filesystem import read_logs, get_active_run
from mlx.utils.display import info, error, run_detail_panel

app = typer.Typer(help="Show the active run. Shortcut for `mlx run status`.")
console = Console()


@app.callback(invoke_without_command=True)
def status(
    run_id: str = typer.Option(
        None,
        "--run-id",
        help="Specific run ID (default: active run)"
    ),
    logs: bool = typer.Option(
        False,
        "--logs", "-l",
        help="Also show last 20 lines of the run log"
    ),
):
    """
    Show the active run's details — params, metrics, timing.

    If no run is active, tells you how to start one.
    Use --run-id to inspect any past run by ID.

    Examples:
        mlx status
        mlx status --run-id "catboost-v1_20240301_143201"
        mlx status --logs
    """

    # ── Find which run to show ─────────────────
    if run_id:
        # Specific run requested
        run = RunManager.get(run_id)
        if not run:
            error(f"Run not found: [bold]{run_id}[/bold]")
            console.print()
            console.print(
                "  Check your run IDs with: "
                "[cyan]mlx ls[/cyan]"
            )
            raise typer.Exit(1)
    else:
        # Show active run
        run = RunManager.get_active()

        if not run:
            # No active run — show helpful message
            console.print()
            info("No active run right now.")
            console.print()

            # Show the most recent run as a suggestion
            recent = RunManager.get_all(limit=1)
            if recent:
                console.print(
                    f"  [dim]Last run:[/dim]  "
                    f"[white]{recent[0].run_id}[/white]  "
                    f"[dim]({recent[0].status})[/dim]"
                )
                console.print(
                    f"\n  To inspect it:  "
                    f"[cyan]mlx status --run-id "
                    f"\"{recent[0].run_id}\"[/cyan]"
                )
            else:
                console.print(
                    "  Start a run with: "
                    "[cyan]mlx run start --name 'my-run'[/cyan]"
                )

            console.print()
            raise typer.Exit()

    # ── Fetch associated data ──────────────────
    params  = ParamManager.get_for_run(run.run_id)
    metrics = MetricManager.get_latest(run.run_id)

    # ── Show the detail panel ──────────────────
    console.print()
    run_detail_panel(run, metrics, params)

    # ── Optionally show logs ───────────────────
    if logs:
        log_lines = read_logs(run.run_id, tail=20)

        if log_lines:
            console.print(Panel(
                "\n".join(
                    f"[dim]{line}[/dim]"
                    for line in log_lines
                ),
                title="[bold white]Recent Logs[/bold white]",
                border_style="dim",
                padding=(1, 2),
            ))
        else:
            info("No log file found for this run.")

    console.print()