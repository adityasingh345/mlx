"""
mlx/cli.py — The main entry point for the mlx CLI tool.

When the user types `mlx` in their terminal, Python runs this file
and calls `app`. Everything starts here.
"""


import typer
from rich.console import Console

from mlx import __version__

app = typer.Typer(
    help="🧪 [bold cyan]MLX[/bold cyan] — Local ML Experiment Manager.\n\n"
         "Track experiments, runs, params and metrics. 100% local. No server needed.",
    no_args_is_help=True,       # Show help when user types just `mlx`
    rich_markup_mode="rich",    # Allow [bold], [cyan] etc in help text
    add_completion=True, 
)

console = Console()

@app.callback()
def main():
    """
    🚀 MLX CLI
    """
    pass

@app.command("version")
def version():
    """Show the mlx version and exit."""
    console.print(f"mlx [bold cyan]v{__version__}[/bold cyan]")
    
if __name__ == "__main__":
    app()