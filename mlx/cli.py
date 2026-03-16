"""
mlx/cli.py — The main entry point for the mlx CLI tool.

When the user types `mlx` in their terminal, Python runs this file
and calls `app`. Everything starts here.
"""


import typer
from rich.console import Console

from mlx import __version__

app = typer.Typer(
    help="[bold cyan]MLX[/bold cyan] — Local ML Experiment Manager.\n\n"
         "Track experiments, runs, params and metrics. 100% local. No server needed.",
    no_args_is_help=True,       # Show help when user types just `mlx`
    rich_markup_mode="rich",    # Allow [bold], [cyan] etc in help text
    add_completion=True, 
)

console = Console()

from mlx.commands.init import init 
from mlx.commands import run as run_cmd 
from mlx.commands import log as log_cmd 
from mlx.commands import ls as ls_cmd 
from mlx.commands import status as status_cmd  


from mlx.commands.init import init
app.command("init", help="Initialize a new mlx project")(init)
app.add_typer(run_cmd.app,  name="run",  help="Manage experiment runs")
app.add_typer(log_cmd.app, name="log", help="Log Metric, params and notes")
app.add_typer(ls_cmd.app , name="ls", help="list all runs")
app.add_typer(status_cmd.app, name="status", help="show the active run")


@app.command("version")
def version():
    console.print(f"mlx [bold cyan]v{__version__}[/bold cyan]")
    
if __name__ == "__main__":
    app()