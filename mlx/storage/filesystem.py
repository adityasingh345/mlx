"""
mlx/storage/filesystem.py

Handles everything outside the database:
- Finding the .mlx project root
- Reading and writing config.toml
- Managing log files for each run
- Tracking which run is currently active
"""

from pathlib import Path
from typing import Optional
import datetime
import toml


# ─────────────────────────────────────────────
# CONSTANTS
# These are the fixed folder/file names mlx uses
# ─────────────────────────────────────────────

MLX_DIR     = ".mlx"              # The hidden project folder
CONFIG_FILE = "config.toml"       # Project config inside .mlx/
RUNS_DIR    = "runs"              # Log files live here
ARTIFACTS   = "artifacts"         # Saved models, plots etc (future use)

# ─────────────────────────────────────────────
# ROOT FINDER
# ─────────────────────────────────────────────

def find_root() -> Path:
    """
    Walk up from the current directory to find the mlx project root.

    This lets you run mlx commands from ANY subfolder of your project,
    not just from the root. Same behaviour as git.

    Example:
        Your project is at:  ~/projects/fraud-detection/
        You're working in:   ~/projects/fraud-detection/notebooks/
        mlx still works because we walk up and find .mlx/ one level up.

    Raises FileNotFoundError if no .mlx folder is found.
    """
    cwd = Path.cwd()

    # Walk: current folder → parent → grandparent → ... → /
    for directory in [cwd, *cwd.parents]:
        candidate = directory / MLX_DIR
        if candidate.is_dir():
            return directory   # Return the PROJECT ROOT, not the .mlx folder

    raise FileNotFoundError(
        "\n✗ No mlx project found in this directory or any parent.\n"
        "  Run 'mlx init' to initialize a project here."
    )


def get_mlx_dir() -> Path:
    """Return the .mlx/ folder path."""
    return find_root() / MLX_DIR


def get_config_path() -> Path:
    """Return the config.toml file path."""
    return get_mlx_dir() / CONFIG_FILE


def get_runs_dir() -> Path:
    """Return the runs/ folder path."""
    return get_mlx_dir() / RUNS_DIR


def get_run_dir(run_id: str) -> Path:
    """
    Return the folder for a specific run's files.
    Creates it if it doesn't exist yet.
    """
    run_dir = get_runs_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

# ─────────────────────────────────────────────
# CONFIG HELPERS
# Read and write .mlx/config.toml
# ─────────────────────────────────────────────

def load_config() -> dict:
    """
    Load the project config from .mlx/config.toml

    Returns an empty dict if config doesn't exist yet —
    this prevents crashes during early setup.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    return toml.load(config_path)


def save_config(config: dict):
    """
    Write the full config dict back to .mlx/config.toml

    Always pass the complete config — this overwrites the file.
    Pattern: load → modify → save
    """
    config_path = get_config_path()
    with open(config_path, "w") as f:
        toml.dump(config, f)


def get_project_name() -> str:
    """Return the project name from config."""
    config = load_config()
    # Use .get() with a fallback so it never crashes
    return config.get("project", {}).get("name", "unnamed-project")

# ─────────────────────────────────────────────
# ACTIVE RUN TRACKER
# The active run ID is stored in config.toml
# so mlx log knows where to send data
# ─────────────────────────────────────────────

def save_active_run(run_id: str):
    """
    Mark a run as the currently active run.

    Called by: `mlx run start`

    Writes the run_id into config.toml:
        active_run = "catboost-v1_20240301_143201"
    """
    config = load_config()
    config["active_run"] = run_id
    save_config(config)


def clear_active_run():
    """
    Remove the active run marker.

    Called by: `mlx run stop`

    After this, get_active_run() returns None,
    which tells mlx log there's nothing to log to.
    """
    config = load_config()

    # pop() removes the key if it exists, does nothing if it doesn't
    config.pop("active_run", None)
    save_config(config)


def get_active_run() -> Optional[str]:
    """
    Get the currently active run ID.

    Returns None if no run is active.

    Called by: `mlx log`, `mlx status`, `mlx logs`

    Usage pattern in commands:
        run_id = get_active_run()
        if not run_id:
            error("No active run. Start one with: mlx run start")
            raise typer.Exit(1)
    """
    try:
        config = load_config()
        return config.get("active_run", None)
    except FileNotFoundError:
        # No project found — return None gracefully
        return None
    
# ─────────────────────────────────────────────
# LOG FILE HELPERS
# Each run has its own stdout.log file
# ─────────────────────────────────────────────

def get_log_file(run_id: str) -> Path:
    """Return the path to a run's log file."""
    return get_run_dir(run_id) / "stdout.log"


def append_log(run_id: str, text: str):
    """
    Append a line to a run's log file with a timestamp.

    Called every time something important happens:
    - Run starts
    - Metric is logged
    - Param is logged
    - Run stops

    Format: [14:32:01] accuracy = 0.94 @ step 100
    """
    log_file = get_log_file(run_id)

    # Timestamp in HH:MM:SS format
    ts = datetime.datetime.utcnow().strftime("%H:%M:%S")

    with open(log_file, "a") as f:   # "a" = append, never overwrites
        f.write(f"[{ts}] {text}\n")


def read_logs(run_id: str, tail: int = 50) -> list:
    """
    Read the last N lines from a run's log file.

    Args:
        run_id: which run to read
        tail:   how many lines from the end (like `tail -n 50`)

    Returns empty list if log file doesn't exist yet.
    """
    log_file = get_log_file(run_id)

    if not log_file.exists():
        return []

    lines = log_file.read_text().splitlines()

    # Return only the last `tail` lines
    return lines[-tail:]


def log_exists(run_id: str) -> bool:
    """Check if a log file exists for a run."""
    return get_log_file(run_id).exists()