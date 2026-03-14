from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def success(msg: str):
    """Green checkmark message."""
    console.print(f"[bold green]✓[/bold green] {msg}")
    
def error(msg: str):
    """Red cross message."""
    console.print(f"[bold red]✗[/bold red] {msg}")


def info(msg: str):
    """Cyan arrow message."""
    console.print(f"[bold cyan]→[/bold cyan] {msg}")


def warn(msg: str):
    """Yellow warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")

def runs_table(runs: list) -> Table:
    
    table = Table(
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold cyan",
        show_lines=False,
        pad_edge=True,
    )

    table.add_column("Run ID",     style="bold white",  no_wrap=True)
    table.add_column("Name",       style="white")
    table.add_column("Experiment", style="magenta")
    table.add_column("Status",     justify="center")
    table.add_column("Tags",       style="dim")
    table.add_column("Created",    style="dim",   no_wrap=True)
    table.add_column("Duration",   justify="right", style="yellow")

    for run in runs:

        # Status gets an icon and color
        status_display = {
            "running": "[bold yellow]⟳ running[/bold yellow]",
            "done":    "[bold green]✓ done[/bold green]",
            "failed":  "[bold red]✗ failed[/bold red]",
        }.get(run.status, run.status)

        # Format duration nicely
        duration = "-"
        if run.duration_sec is not None:
            m, s = divmod(int(run.duration_sec), 60)
            duration = f"{m}m {s}s" if m > 0 else f"{s}s"

        # Trim created_at to just date and time
        created = run.created_at[:16].replace("T", " ")

        table.add_row(
            run.run_id,
            run.name,
            run.experiment,
            status_display,
            run.tags or "-",
            created,
            duration,
        )

    return table



# RUN DETAIL PANEL
# Used by `mlx status` and `mlx run status`

def run_detail_panel(run, metrics: list, params: list):
    
    lines = []

    # Basic info
    lines.append(f"[dim]Name       :[/dim]  [bold]{run.name}[/bold]")
    lines.append(f"[dim]Experiment :[/dim]  [magenta]{run.experiment}[/magenta]")
    lines.append(f"[dim]Tags       :[/dim]  {run.tags or '-'}")
    lines.append(f"[dim]Started    :[/dim]  {run.created_at[:19].replace('T', ' ')}")

    if run.finished_at:
        lines.append(
            f"[dim]Finished   :[/dim]  {run.finished_at[:19].replace('T', ' ')}"
        )

    if run.duration_sec is not None:
        m, s = divmod(int(run.duration_sec), 60)
        dur = f"{m}m {s}s" if m > 0 else f"{s}s"
        lines.append(f"[dim]Duration   :[/dim]  [yellow]{dur}[/yellow]")

    # Params section
    if params:
        lines.append("")
        lines.append("[bold cyan]── Params ──[/bold cyan]")
        for p in params:
            lines.append(
                f"  [dim]{p.key:20}[/dim] [yellow]{p.value}[/yellow]"
            )

    # Metrics section
    if metrics:
        lines.append("")
        lines.append("[bold cyan]── Metrics ──[/bold cyan]")
        for m in metrics:
            lines.append(
                f"  [dim]{m.key:20}[/dim] [green]{m.value}[/green]"
                f"  [dim]@ step {m.step}[/dim]"
            )

    # Status color
    status_color = {
        "running": "yellow",
        "done":    "green",
        "failed":  "red",
    }.get(run.status, "white")

    console.print(Panel(
        "\n".join(lines),
        title=(
            f"[bold white]{run.run_id}[/bold white]  "
            f"[{status_color}]{run.status}[/{status_color}]"
        ),
        border_style="cyan",
        padding=(1, 2),
    ))