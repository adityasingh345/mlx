import typer

app = typer.Typer(help="🚀 MLX – ML Experiment Manager")


@app.callback()
def main():
    """
    MLX CLI root.
    """
    pass


@app.command()
def hello():
    """Temporary test command."""
    print("mlx is alive! 🚀")