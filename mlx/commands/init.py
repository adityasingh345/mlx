import typer
import toml
from pathlib import Path 
from rich.console import Console
from rich.panel import Panel


from mlx.storage.db import init_db
from mlx.core.experiment import ExperimentManager
from mlx.utils.display import success, error, info, warn 

app = typer.Typer(help="Initialize a new mlx project.")
console = Console()

def _update_gitignore(project_root: Path):
    """
    Add .mlx/ to .gitignore if this is a git repo.
    Only runs if .git/ folder exists.
    Won't add duplicate entries.
    """
    git_dir   = project_root / ".git"
    gitignore = project_root / ".gitignore"

    # Only do this inside a git repo
    if not git_dir.exists():
        return

    mlx_entry = "\n# MLX — local experiment data\n.mlx/\n"

    if gitignore.exists():
        content = gitignore.read_text()

        # Don't add it twice
        if ".mlx" in content:
            return

        # Append to existing .gitignore
        with open(gitignore, "a") as f:
            f.write(mlx_entry)

        info("Added [bold].mlx/[/bold] to .gitignore")

    else:
        # Create a brand new .gitignore
        gitignore.write_text(mlx_entry.strip())
        info("Created .gitignore with [bold].mlx/[/bold] entry")


def _print_success(
    project_name: str,
    cwd: Path,
    mlx_dir: Path,
    db_path: Path,
):
    """
    Print a clean success panel with next steps.
    """
    console.print()
    console.print(Panel(
        f"[bold green]🧪 MLX project initialized![/bold green]\n\n"
        f"  [dim]Project :[/dim]  [bold white]{project_name}[/bold white]\n"
        f"  [dim]Location:[/dim]  [bold white]{mlx_dir}[/bold white]\n"
        f"  [dim]Database:[/dim]  [bold white]{db_path}[/bold white]",
        border_style="green",
        padding=(1, 2),
    ))

    console.print("[bold]Next steps:[/bold]")
    console.print()
    console.print(
        "  [dim]1.[/dim] Start a run   "
        "[cyan]mlx run start --name \"my-first-run\"[/cyan]"
    )
    console.print(
        "  [dim]2.[/dim] Log a param   "
        "[cyan]mlx log param learning_rate 0.05[/cyan]"
    )
    console.print(
        "  [dim]3.[/dim] Log a metric  "
        "[cyan]mlx log metric accuracy 0.94 --step 100[/cyan]"
    )
    console.print(
        "  [dim]4.[/dim] Stop the run  "
        "[cyan]mlx run stop[/cyan]"
    )
    console.print(
        "  [dim]5.[/dim] See results   "
        "[cyan]mlx ls[/cyan]"
    )
    console.print()

@app.callback(invoke_without_command = True)
def init(
    name: str = typer.Option(
        None,
        "--name", "-n",
        help="Project name (defaults to current folder name)"
    ),
    description:  str = typer.Option(
        "",
        "--desc", "-d",
        help = "Re-initialize an existing project (keeps data)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Re-initialize an existing project (keeps data)"
    ),
):
    # initalize the mlx in current directory 
    # we create a .mlx folder with a sqlite databse and config file, run this once at the start of every new ml project 
    
    cwd = Path.cwd()
    mlx_dir = cwd / ".mlx"
    db_path = mlx_dir / "mlx.db"
    config_path = mlx_dir / "config.toml"
    runs_dir = mlx_dir / "runs"
    artifacts_dir = mlx_dir / "artifacts"
    
    # we will check if it is already initialized 
    if mlx_dir.exists() and not force:
        warn(f"Already an mlx project here: [bold]{cwd}[/bold]")
        console.print("  Use [bold cyan]--force[/bold cyan] to re-initialize.")
        raise typer.Exit()

    # Check 1b: Is there a .mlx/ in a PARENT folder?
    # This catches running mlx init inside a subfolder
    if not force:
        for parent in cwd.parents:
            if (parent / ".mlx").exists():
                warn(
                    f"Already an mlx project at "
                    f"[bold]{parent}[/bold]"
                )
                console.print(
                    f"\n  You are currently inside: "
                    f"[dim]{cwd}[/dim]"
                )
                console.print(
                    f"  Go to your project root or use "
                    f"[bold cyan]--force[/bold cyan] to create a nested project."
                )
                raise typer.Exit()
    
    #next step create folder structure
    mlx_dir.mkdir(exist_ok = True)
    runs_dir.mkdir(exist_ok = True)
    artifacts_dir.mkdir(exist_ok = True)
    
    # create the database
    init_db(db_path)
    
    #create config toml 
    
    project_name = name or cwd.name
    
    config = {
        "project": {
            "name":        project_name,
            "description": description,
            "version":     "0.1.0",
        },
        "settings": {
            "default_experiment": "default",
            "log_level":          "INFO",
        }
    }
    with open(config_path, "w") as f:
        toml.dump(config, f)
        
    # create a default experiment, every project start with deault experiment, so users can start loggin immediately without creating an experiment first
    ExperimentManager.create(
        name="default",
        description="Default experiment"
    )
    
    _update_gitignore(cwd)
    
    _print_success(project_name, cwd, mlx_dir, db_path)