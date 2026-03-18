#it is the most important command, see exactly which model won and why ??
# uasge: mlx compare run-id-1 run-id-2 , mlx compare run-id-1 run-id-2 --params-only 


import typer 
from rich.console import Console
from rich.table import Table
from rich.text import Text 
from rich import box

from mlx.core.run import RunManager 
from mlx.core.metrics import MetricManager
from mlx.core.params import ParamManager
from mlx.utils.display import error, warn

app = typer.Typer(help="Compare two or more runs side by side")

console = Console()

def _print_header(runs: list):
    console.print(
        f"[bold white]Comparing {len(runs)} runs[/bold white]\n"
    )

    for i, run in enumerate(runs):
        # Last item gets └── others get ├──
        prefix = "└──" if i == len(runs) - 1 else "├──"

        status_color = {
            "done":    "green",
            "running": "yellow",
            "failed":  "red",
        }.get(run.status, "white")

        duration = ""
        if run.duration_sec:
            m, s = divmod(int(run.duration_sec), 60)
            duration = f"{m}m {s}s" if m > 0 else f"{s}s"
            duration = f"  [dim]{duration}[/dim]"

        console.print(
            f"  {prefix} [bold white]{run.name}[/bold white]"
            f"  [{status_color}]{run.status}[/{status_color}]"
            f"{duration}"
            f"  [dim]{run.run_id}[/dim]"
        )

    console.print()
    
def _print_params_table(
    runs: list,
    params_by_run: dict,
    show_all: bool = False,
):

    # Collect all unique param keys across all runs
    all_keys = set()
    for params in params_by_run.values():
        all_keys.update(params.keys())
    all_keys = sorted(all_keys)

    if not all_keys:
        console.print("[dim]  No params logged for these runs.[/dim]\n")
        return

    # Figure out which params actually changed
    changed_keys = set()
    for key in all_keys:
        values = [
            params_by_run[run.run_id].get(key, "—")
            for run in runs
        ]
        # If not all values are the same → it changed
        if len(set(values)) > 1:
            changed_keys.add(key)

    # Filter to only changed params unless show_all
    display_keys = all_keys if show_all else [
        k for k in all_keys if k in changed_keys
    ]

    if not display_keys:
        console.print(
            "[dim]  All params are identical across runs.[/dim]"
        )
        if not show_all:
            console.print(
                "[dim]  Use [cyan]--all-params[/cyan] "
                "to see them anyway.[/dim]"
            )
        console.print()
        return

    # ── Build the table ────────────────────────
    table = Table(
        box=box.SIMPLE_HEAD,
        border_style="dim",
        header_style="bold cyan",
        show_edge=True,
        pad_edge=True,
    )

    # First column: param name
    table.add_column(
        "Param",
        style="dim",
        no_wrap=True,
        min_width=18,
    )

    # One column per run
    for run in runs:
        table.add_column(
            run.name,
            justify="right",
            style="white",
            min_width=12,
        )

    # Last column: changed indicator
    table.add_column("", justify="center", min_width=6)

    # ── Add rows ───────────────────────────────
    for key in display_keys:
        values = [
            params_by_run[run.run_id].get(key, "—")
            for run in runs
        ]

        is_changed = key in changed_keys

        # Style each cell
        styled_values = []
        for v in values:
            if v == "—":
                # Not logged for this run
                styled_values.append(Text("—", style="dim"))
            elif is_changed:
                # Changed — highlight yellow
                styled_values.append(Text(str(v), style="bold yellow"))
            else:
                styled_values.append(Text(str(v), style="white"))

        # Changed indicator
        indicator = Text("← diff", style="dim yellow") if is_changed else Text("")

        table.add_row(
            key,
            *styled_values,
            indicator,
        )

    console.print("[bold]Params[/bold]")
    console.print(table)

    # Note about hidden unchanged params
    hidden = len(all_keys) - len(display_keys)
    if hidden > 0 and not show_all:
        console.print(
            f"  [dim]{hidden} unchanged param(s) hidden — "
            f"use [cyan]--all-params[/cyan] to show[/dim]"
        )
    console.print()

def _print_metrics_table(runs: list, metrics_by_run: dict):

    # Collect all unique metric keys
    all_keys = set()
    for metrics in metrics_by_run.values():
        all_keys.update(metrics.keys())
    all_keys = sorted(all_keys)

    if not all_keys:
        console.print("[dim]  No metrics logged for these runs.[/dim]\n")
        return

    # ── Decide which direction is "better" ────
    # Lower is better for these metric name patterns
    lower_is_better_patterns = [
        "loss", "error", "mse", "mae", "rmse",
        "mape", "logloss", "cross_entropy",
    ]

    def lower_is_better(key: str) -> bool:
        key_lower = key.lower()
        return any(p in key_lower for p in lower_is_better_patterns)

    # ── Build the table ────────────────────────
    table = Table(
        box=box.SIMPLE_HEAD,
        border_style="dim",
        header_style="bold cyan",
        show_edge=True,
        pad_edge=True,
    )

    # First column: metric name
    table.add_column(
        "Metric",
        style="dim",
        no_wrap=True,
        min_width=18,
    )

    # One column per run
    for run in runs:
        table.add_column(
            run.name,
            justify="right",
            style="white",
            min_width=12,
        )

    # Last column: difference
    table.add_column(
        "diff",
        justify="right",
        style="dim",
        min_width=10,
    )

    # ── Add rows ───────────────────────────────
    for key in all_keys:

        # Get values for all runs — None if not logged
        values = [
            metrics_by_run[run.run_id].get(key)
            for run in runs
        ]

        # Filter out None for calculations
        real_values = [v for v in values if v is not None]

        if not real_values:
            continue

        # Find best value
        if lower_is_better(key):
            best_val = min(real_values)
            worst_val = max(real_values)
        else:
            best_val = max(real_values)
            worst_val = min(real_values)

        # Calculate difference
        if len(real_values) >= 2:
            diff = best_val - worst_val
            # Format diff with sign
            diff_str = f"{diff:+.4f}"
            diff_color = "green" if diff > 0 else "red" if diff < 0 else "dim"
            diff_display = Text(diff_str, style=diff_color)
        else:
            diff_display = Text("—", style="dim")

        # Style each cell
        styled_values = []
        for v in values:
            if v is None:
                styled_values.append(Text("—", style="dim"))
            elif v == best_val and len(real_values) > 1:
                # Best value — green and bold
                styled_values.append(
                    Text(f"{v:.4f}", style="bold green")
                )
            else:
                styled_values.append(Text(f"{v:.4f}", style="white"))

        table.add_row(
            key,
            *styled_values,
            diff_display,
        )

    console.print("[bold]Metrics[/bold]")
    console.print(table)
    console.print(
        "  [dim][bold green]green[/bold green] = best value  "
        "·  diff = best − worst[/dim]"
    )
    console.print()

@app.callback(invoke_without_command=True)
def compare(
    run_ids: list[str] = typer.Argument(
        ...,
        help="Two or more run IDS to compare"
    ),
    params_only: bool = typer.Option(
        False,
        "--params-only", "-p",
        help="Show only params, no metrics"
    ),
    metrics_only: bool = typer.Option(
        False,
        "--metrics-only", "-m",
        help="Show only metrics, no params"
    ),
    all_params: bool = typer.Option(
        False,
        "--all-params",
        help="Show all params including unchanged ones"
    ),
):
    # first of all we will checks that we have at least 2 ids 
    if len(run_ids) < 2:
        error("Please provide at least 2 run IDs to compare.")
        console.print()
        console.print(
            "  Usage: [cyan]mlx compare run-id-1 run-id-2[/cyan]"
        )
        console.print(
            "  Get run IDs from: [cyan]mlx ls[/cyan]"
        )
        raise typer.Exit(1)

    # fetch all runs
    runs = []
    for rid in run_ids:
        run = RunManager.get(rid)
        if not run:
            error(f"Run not found: [bold]{rid}[/bold]")
            console.print(
                f"  Check your run IDs with: [cyan]mlx ls[/cyan]"
            )
            raise typer.Exit(1)
        
        runs.append(run)
        
    # fetch params and metrics for each run 
    params_by_run = {r.run_id: ParamManager.as_dict(r.run_id) for r in runs}
    metrics_by_run = {
        r.run_id: {m.key: m.value for m in MetricManager.get_latest(r.run_id)}
        for r in runs
    }
    
    console.print()
    _print_header(runs)
    
    if not metrics_only:
        _print_params_table(runs, params_by_run, show_all=all_params)
        
    if not params_only:
        _print_metrics_table(runs, metrics_by_run)

    console.print()

