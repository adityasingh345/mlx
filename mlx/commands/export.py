"""

Usage:
    mlx export                          → CSV to stdout
    mlx export --format json            → JSON to stdout
    mlx export --out runs.csv           → save to file
    mlx export --out runs.json --format json
    mlx export --experiment fraud       → filter by experiment
    mlx export --status done            → filter by status
"""

import json
import csv
import io
import typer
from pathlib import Path
from rich.console import Console

from mlx.core.run import RunManager
from mlx.core.metrics import MetricManager
from mlx.core.params import ParamManager
from mlx.utils.display import success, error, info, warn

app = typer.Typer(help="Export runs to CSV or JSON.")
console = Console()


@app.callback(invoke_without_command=True)
def export(
    format: str = typer.Option(
        "csv",
        "--format", "-f",
        help="Export format: csv or json"
    ),
    out: str = typer.Option(
        None,
        "--out", "-o",
        help="Output file path  e.g. runs.csv"
    ),
    experiment: str = typer.Option(
        None,
        "--experiment", "-e",
        help="Filter by experiment name"
    ),
    status: str = typer.Option(
        None,
        "--status", "-s",
        help="Filter by status: done, running, failed"
    ),
    limit: int = typer.Option(
        None,
        "--limit", "-l",
        help="Max number of runs to export"
    ),
    latest_metrics: bool = typer.Option(
        True,
        "--latest-metrics/--all-metrics",
        help="Export only latest metric per key (default) or all steps"
    ),
):

    # ── Validate format 
    if format not in ("csv", "json"):
        error(f"Unknown format: '{format}'")
        console.print("  Supported formats: [cyan]csv[/cyan], [cyan]json[/cyan]")
        raise typer.Exit(1)

    # ── Fetch runs 
    runs = RunManager.get_all(
        experiment=experiment,
        status=status,
        limit=limit or 999999,
    )

    if not runs:
        warn("No runs found to export.")
        if experiment or status:
            console.print("  Try removing filters.")
        raise typer.Exit()

    # ── Build export data 
    # Each item = one run with all its params and metrics
    export_data = _build_export_data(runs, latest_metrics)

    # ── Generate output 
    if format == "csv":
        output = _to_csv(export_data)
    else:
        output = _to_json(export_data)

    # ── Write to file or stdout 
    if out:
        _save_to_file(output, out, format, len(runs))
    else:
        # Print to terminal
        # Use print() not console.print() to avoid Rich markup
        print(output)


# DATA BUILDER

def _build_export_data(runs: list, latest_only: bool) -> list[dict]:
    data = []

    for run in runs:

        # Base run fields
        row = {
            "run_id":       run.run_id,
            "name":         run.name,
            "experiment":   run.experiment,
            "status":       run.status,
            "tags":         run.tags,
            "created_at":   run.created_at[:19].replace("T", " "),
            "finished_at":  run.finished_at[:19].replace("T", " ") if run.finished_at else "",
            "duration_sec": run.duration_sec or "",
        }

        # Add params — prefix with "param_" to avoid name collisions
        params = ParamManager.as_dict(run.run_id)
        for key, value in sorted(params.items()):
            row[f"param_{key}"] = value

        # Add metrics — prefix with "metric_"
        if latest_only:
            # One value per metric key — the final/best one
            metrics = {
                m.key: m.value
                for m in MetricManager.get_latest(run.run_id)
            }
            for key, value in sorted(metrics.items()):
                row[f"metric_{key}"] = value
        else:
            # All steps — creates columns like metric_accuracy_step_100
            all_metrics = MetricManager.get_for_run(run.run_id)
            for m in all_metrics:
                row[f"metric_{m.key}_step_{m.step}"] = m.value

        data.append(row)

    return data


# CSV FORMATTER

def _to_csv(data: list[dict]) -> str:

    if not data:
        return ""

    # Collect ALL unique column names across all runs
    # Preserve order: base fields first, then params, then metrics
    all_columns = []
    seen = set()

    for row in data:
        for key in row.keys():
            if key not in seen:
                all_columns.append(key)
                seen.add(key)

    # Write CSV to a string buffer
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=all_columns,
        extrasaction="ignore",    # ignore extra keys
        restval="",               # empty string for missing values
        lineterminator="\n",
    )

    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()



# JSON FORMATTER


def _to_json(data: list[dict]) -> str:

    # Rebuild as nested structure for JSON
    nested = []

    for row in data:
        # Separate base fields, params, metrics
        base    = {}
        params  = {}
        metrics = {}

        for key, value in row.items():
            if key.startswith("param_"):
                params[key[6:]] = value      # strip "param_" prefix
            elif key.startswith("metric_"):
                metrics[key[7:]] = value     # strip "metric_" prefix
            else:
                base[key] = value

        nested.append({
            **base,
            "params":  params,
            "metrics": metrics,
        })

    return json.dumps(nested, indent=2)



# FILE SAVER


def _save_to_file(
    content: str,
    path: str,
    format: str,
    run_count: int,
):
    """
    Save exported content to a file.
    Creates parent directories if needed.
    """
    out_path = Path(path)

    # Auto-add extension if missing
    if not out_path.suffix:
        out_path = out_path.with_suffix(f".{format}")

    # Create parent dirs if needed
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    out_path.write_text(content)

    success(
        f"Exported [bold]{run_count}[/bold] run(s) "
        f"to [bold cyan]{out_path}[/bold cyan]"
    )
    console.print(
        f"  [dim]Format  :[/dim]  {format.upper()}"
    )
    console.print(
        f"  [dim]Size    :[/dim]  "
        f"{out_path.stat().st_size / 1024:.1f} KB"
    )
    console.print()

    # Show a helpful next step
    if format == "csv":
        console.print("[dim]Open in pandas:[/dim]")
        console.print(
            f"  [cyan]import pandas as pd[/cyan]\n"
            f"  [cyan]df = pd.read_csv('{out_path}')[/cyan]\n"
            f"  [cyan]print(df.head())[/cyan]"
        )
    else:
        console.print("[dim]Load in Python:[/dim]")
        console.print(
            f"  [cyan]import json[/cyan]\n"
            f"  [cyan]data = json.load(open('{out_path}'))[/cyan]\n"
            f"  [cyan]print(data[0]['metrics'])[/cyan]"
        )
    console.print()