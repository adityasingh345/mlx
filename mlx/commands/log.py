"""
mlx/commands/log.py

CLI commands for logging to the active run.

Commands:
    mlx log metric   → log a metric value
    mlx log param    → log a hyperparameter
    mlx log note     → log a free text note

All three commands:
    1. Read active_run from config.toml
    2. Call the right Manager from core/
    3. Print one clean confirmation line
"""

import typer
from rich.console import Console

from mlx.core.metrics import MetricManager
from mlx.core.params import ParamManager
from mlx.storage.filesystem import append_log, get_active_run
from mlx.utils.display import error

app = typer.Typer(help="Log metrics, params, and notes to the active run.")
console = Console()


# ─────────────────────────────────────────────
# SHARED HELPER
# ─────────────────────────────────────────────


def _require_active_run() -> str:
    """
    Get the active run ID or exit with a clear error.

    Every log command calls this first.
    If no run is active — stop immediately and tell the user why.

    Returns the active run_id string if one exists.
    """
    rid = get_active_run()

    if not rid:
        error("No active run.")
        console.print()
        console.print("  Start one with: [cyan]mlx run start --name 'my-run'[/cyan]")
        raise typer.Exit(1)

    return rid


# mlx log metric


@app.command("metric")
def log_metric(
    key: str = typer.Argument(..., help="Metric name  e.g. accuracy, loss, auc"),
    value: float = typer.Argument(..., help="Metric value  e.g. 0.94"),
    step: int = typer.Option(0, "--step", "-s", help="Training step or epoch"),
    run_id: str = typer.Option(
        None, "--run-id", help="Run ID to log to (default: active run)"
    ),
):
    """
    Log a metric value to the active run.

    Call this during training to track how your model
    is performing at each step or epoch.

    Examples:
        mlx log metric accuracy 0.94
        mlx log metric accuracy 0.94 --step 100
        mlx log metric val_loss 0.21 --step 50
        mlx log metric auc 0.97 --step 100
    """

    # Use provided run_id or get active run
    rid = run_id or _require_active_run()

    # Validate the value is a real number
    # Typer handles this automatically since value is typed as float
    # but we add a friendly message just in case
    try:
        MetricManager.log(key=key, value=value, step=step, run_id=rid)
    except RuntimeError as e:
        error(str(e))
        raise typer.Exit(1)

    # ── One clean output line ──────────────────
    # Short enough to log 200 times without flooding the terminal
    console.print(
        f"  [dim]metric[/dim]  "
        f"[cyan]{key}[/cyan] = "
        f"[green]{value}[/green]  "
        f"[dim]@ step {step}[/dim]"
    )


# mlx log param


@app.command("param")
def log_param(
    key: str = typer.Argument(..., help="Param name  e.g. learning_rate, depth"),
    value: str = typer.Argument(..., help="Param value  e.g. 0.05, 6, adam"),
    run_id: str = typer.Option(
        None, "--run-id", help="Run ID to log to (default: active run)"
    ),
):
    """
    Log a hyperparameter to the active run.

    Call this before training starts to record
    what settings you used.

    Logging the same param twice updates the value —
    it does NOT create a duplicate.

    Examples:
        mlx log param learning_rate 0.05
        mlx log param depth 6
        mlx log param optimizer adam
        mlx log param batch_size 32
    """

    rid = run_id or _require_active_run()

    try:
        ParamManager.log(key=key, value=value, run_id=rid)
    except RuntimeError as e:
        error(str(e))
        raise typer.Exit(1)

    # ── One clean output line ──────────────────
    console.print(
        f"  [dim]param[/dim]   [magenta]{key}[/magenta] = [yellow]{value}[/yellow]"
    )


# mlx log note


@app.command("note")
def log_note(
    text: str = typer.Argument(..., help="Free text note to attach to this run"),
    run_id: str = typer.Option(
        None, "--run-id", help="Run ID to log to (default: active run)"
    ),
):
    """
    Log a free text note to the active run.

    Use this for observations, reminders, or anything
    that doesn't fit into a metric or param.

    Notes are saved to the run's log file and shown
    in mlx logs.

    Examples:
        mlx log note "trying deeper trees"
        mlx log note "val loss stopped improving at step 150"
        mlx log note "model saved to artifacts/model.cbm"
    """

    rid = run_id or _require_active_run()

    # Notes go straight to the log file — not the database
    # They're human observations, not structured data
    append_log(rid, f"note   | {text}")

    # ── One clean output line ──────────────────
    console.print(f"  [dim]note[/dim]    [white]{text}[/white]")
