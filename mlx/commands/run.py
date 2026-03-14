
import typer
from rich.console import Console
from rich.panel import Panel

from mlx.core.run import RunManager
from mlx.core.metrics import MetricManager
from mlx.core.params import ParamManager
from mlx.utils.display import (
    success, error, info, warn,
    runs_table, run_detail_panel,
)

app = typer.Typer(help="Manage experiment runs.")
console = Console()

@app.command("start")
def run_start(
    name: str = typer.Option(
        ...,              # ← three dots means REQUIRED — user must provide this
        "--name", "-n",
        help="Name for this run  e.g. 'catboost-v1'"
    ),
    experiment: str = typer.Option(
        "default",
        "--experiment", "-e",
        help="Experiment to log this run under"
    ),
    tags: str = typer.Option(
        "",
        "--tags", "-t",
        help="Comma-separated tags  e.g. 'catboost,baseline,v2'"
    ),
):
    """
    Start a new run and begin tracking.

    This creates a new run in the database and marks it as active.
    All subsequent `mlx log` commands will attach to this run
    until you call `mlx run stop`.

    Examples:
        mlx run start --name "catboost-v1"
        mlx run start --name "xgboost-v2" --experiment "fraud"
        mlx run start --name "resnet-v1"  --tags "cnn,imagenet"
    """

    # RunManager.start() does all the real work
    # We just handle display here
    try:
        run = RunManager.start(
            name=name,
            experiment=experiment,
            tags=tags,
        )
    except RuntimeError as e:
        # Already active run — show clear error
        error(str(e))
        raise typer.Exit(1)

    # Success output
    console.print()
    
    console.print(Panel(
        f"[bold green] Run started![/bold green]\n\n"
        f"  [dim]Run ID    :[/dim]  [bold white]{run.run_id}[/bold white]\n"
        f"  [dim]Name      :[/dim]  [bold white]{run.name}[/bold white]\n"
        f"  [dim]Experiment:[/dim]  [bold white]{run.experiment}[/bold white]\n"
        + (f"  [dim]Tags      :[/dim]  [bold white]{run.tags}[/bold white]\n"
           if run.tags else ""),
        border_style="green",
        padding=(1, 2),
    ))

    console.print("[dim]Now log your params and metrics:[/dim]")
    console.print()
    console.print(
        "  [cyan]mlx log param  learning_rate 0.05[/cyan]"
    )
    console.print(
        "  [cyan]mlx log metric accuracy 0.94 --step 100[/cyan]"
    )
    console.print(
        "  [cyan]mlx run stop[/cyan]  [dim]when done[/dim]"
    )
    console.print()
    
@app.command("stop")
def run_stop(
    status: str = typer.Option(
        "done",
        "--status", "-s",
        help="Final status: done or failed"
    ),
    run_id: str = typer.Option(
        None,
        "--run-id",
        help="Specific run to stop (default: active run)"
    ),
):
    """
    Stop the active run and mark it as done or failed.

    Calculates how long the run took and saves it.
    Clears the active run so you can start a new one.

    Examples:
        mlx run stop
        mlx run stop --status failed
        mlx run stop --run-id "catboost-v1_20240301_143201"
    """

    # Validate status value
    if status not in ("done", "failed"):
        error(f"Status must be 'done' or 'failed'. Got: '{status}'")
        raise typer.Exit(1)

    try:
        run = RunManager.stop(status=status, run_id=run_id)
    except RuntimeError as e:
        error(str(e))
        raise typer.Exit(1)

    # ── Format duration nicely 
    duration = "-"
    if run.duration_sec is not None:
        m, s = divmod(int(run.duration_sec), 60)
        h, m = divmod(m, 60)
        if h > 0:
            duration = f"{h}h {m}m {s}s"
        elif m > 0:
            duration = f"{m}m {s}s"
        else:
            duration = f"{s}s"

    # ── Color based on status 
    icon  = "✓" if status == "done" else "✗"
    color = "green" if status == "done" else "red"

    console.print()
    console.print(Panel(
        f"[bold {color}]{icon} Run {status}![/bold {color}]\n\n"
        f"  [dim]Run ID  :[/dim]  [bold white]{run.run_id}[/bold white]\n"
        f"  [dim]Duration:[/dim]  [bold white]{duration}[/bold white]",
        border_style=color,
        padding=(1, 2),
    ))

    console.print("[dim]See your results:[/dim]")
    console.print(f"  [cyan]mlx ls[/cyan]")
    console.print()
    
@app.command("list")
def run_list(
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
        help="Maximum number of runs to show"
    ),
):
    """
    List all runs in a table.

    Examples:
        mlx run list
        mlx run list --experiment "fraud-detection"
        mlx run list --status done
        mlx run list --limit 50
    """

    runs = RunManager.get_all(
        experiment=experiment,
        status=status,
        limit=limit,
    )

    if not runs:
        info("No runs found.")
        console.print()
        console.print(
            "[dim]Start your first run with:[/dim] "
            "[cyan]mlx run start --name 'my-run'[/cyan]"
        )
        return

    # ── Print the table 
    console.print()
    console.print(runs_table(runs))
    console.print()

    # ── Summary line 
    done_count    = sum(1 for r in runs if r.status == "done")
    running_count = sum(1 for r in runs if r.status == "running")
    failed_count  = sum(1 for r in runs if r.status == "failed")

    console.print(
        f"[dim]  {len(runs)} run(s)  ·  "
        f"[green]{done_count} done[/green]  ·  "
        f"[yellow]{running_count} running[/yellow]  ·  "
        f"[red]{failed_count} failed[/red][/dim]"
    )
    console.print()
    
@app.command("status")
def run_status(
    run_id: str = typer.Option(
        None,
        "--run-id",
        help="Specific run ID (default: active run)"
    ),
):
    """
    Show detailed info about the active run (or a specific run).

    Displays: name, experiment, status, timing,
              all logged params, latest metrics.

    Examples:
        mlx run status
        mlx run status --run-id "catboost-v1_20240301_143201"
    """

    # Find which run to show
    if run_id:
        run = RunManager.get(run_id)
        if not run:
            error(f"Run not found: [bold]{run_id}[/bold]")
            raise typer.Exit(1)
    else:
        run = RunManager.get_active()
        if not run:
            info("No active run.")
            console.print()
            console.print(
                "[dim]Start one with:[/dim] "
                "[cyan]mlx run start --name 'my-run'[/cyan]"
            )
            raise typer.Exit()

    # Fetch all params and latest metrics for this run
    params  = ParamManager.get_for_run(run.run_id)
    metrics = MetricManager.get_latest(run.run_id)

    # Display the detail panel
    run_detail_panel(run, metrics, params)
    
@app.command("delete")
def run_delete(
    run_id: str = typer.Option(
        ...,
        "--run-id",
        help="Run ID to delete"
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompt"
    ),
):
    """
    Delete a run and all its params and metrics.

    This is permanent — deleted runs cannot be recovered.

    Examples:
        mlx run delete --run-id "catboost-v1_20240301_143201"
        mlx run delete --run-id "catboost-v1_20240301_143201" --yes
    """

    # Verify the run exists first
    run = RunManager.get(run_id)
    if not run:
        error(f"Run not found: [bold]{run_id}[/bold]")
        raise typer.Exit(1)

    # Confirm unless --yes flag passed
    if not yes:
        console.print()
        warn(
            f"About to delete run [bold]{run_id}[/bold] "
            f"and all its data."
        )
        console.print(
            "[dim]This cannot be undone.[/dim]"
        )
        console.print()

        # Typer's built in confirmation prompt
        confirmed = typer.confirm("Are you sure?")
        if not confirmed:
            info("Cancelled.")
            raise typer.Exit()

    # Delete it
    RunManager.delete(run_id)
    success(f"Deleted run [bold]{run_id}[/bold]")