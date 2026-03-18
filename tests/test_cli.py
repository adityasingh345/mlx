"""
Tests for CLI commands using Typer's CliRunner.
Tests the full command pipeline end to end.
"""

import pytest
from typer.testing import CliRunner
from mlx.cli import app

runner = CliRunner()


def test_version_command(mlx_project):
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "v0.1.0" in result.output


def test_mlx_help(mlx_project):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MLX" in result.output


def test_init_command(tmp_path, monkeypatch):
    """mlx init should create .mlx folder and config."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--name", "test-project"])

    assert result.exit_code == 0
    assert (tmp_path / ".mlx").exists()
    assert (tmp_path / ".mlx" / "mlx.db").exists()
    assert (tmp_path / ".mlx" / "config.toml").exists()


def test_init_already_exists(mlx_project):
    """mlx init on existing project should warn not crash."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Already" in result.output


def test_run_start_command(mlx_project):
    result = runner.invoke(app, ["run", "start", "--name", "test-run"])
    assert result.exit_code == 0
    assert "started" in result.output.lower()


def test_run_stop_command(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "test-run"])
    result = runner.invoke(app, ["run", "stop"])
    assert result.exit_code == 0
    assert "done" in result.output.lower()


def test_run_stop_no_active_run(mlx_project):
    """Stopping with no active run should exit with error."""
    result = runner.invoke(app, ["run", "stop"])
    assert result.exit_code == 1


def test_log_metric_command(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "test-run"])
    result = runner.invoke(app, ["log", "metric", "accuracy", "0.94", "--step", "100"])
    assert result.exit_code == 0
    assert "accuracy" in result.output
    assert "0.94" in result.output


def test_log_param_command(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "test-run"])
    result = runner.invoke(app, ["log", "param", "learning_rate", "0.05"])
    assert result.exit_code == 0
    assert "learning_rate" in result.output


def test_log_note_command(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "test-run"])
    result = runner.invoke(app, ["log", "note", "this is a test note"])
    assert result.exit_code == 0
    assert "test note" in result.output


def test_log_without_active_run_fails(mlx_project):
    result = runner.invoke(app, ["log", "metric", "accuracy", "0.94"])
    assert result.exit_code == 1


def test_ls_empty(mlx_project):
    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "No runs" in result.output


def test_ls_shows_runs(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "run-1"])
    runner.invoke(app, ["run", "stop"])
    runner.invoke(app, ["run", "start", "--name", "run-2"])
    runner.invoke(app, ["run", "stop"])

    result = runner.invoke(app, ["ls"])
    assert result.exit_code == 0
    assert "run-1" in result.output
    assert "run-2" in result.output


def test_status_no_active_run(mlx_project):
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "No active run" in result.output


def test_status_active_run(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "active-run"])
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "active-run" in result.output


def test_compare_needs_two_runs(mlx_project):
    result = runner.invoke(app, ["compare", "only-one-id"])
    assert result.exit_code == 1


def test_compare_two_runs(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "run-1"])
    runner.invoke(app, ["log", "metric", "accuracy", "0.94"])
    runner.invoke(app, ["log", "param", "lr", "0.05"])
    r1 = runner.invoke(app, ["run", "stop"])

    runner.invoke(app, ["run", "start", "--name", "run-2"])
    runner.invoke(app, ["log", "metric", "accuracy", "0.97"])
    runner.invoke(app, ["log", "param", "lr", "0.01"])
    runner.invoke(app, ["run", "stop"])

    from mlx.core.run import RunManager
    runs = RunManager.get_all()
    assert len(runs) == 2

    result = runner.invoke(app, ["compare", runs[0].run_id, runs[1].run_id])
    assert result.exit_code == 0
    assert "Comparing 2 runs" in result.output


def test_export_csv(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "export-test"])
    runner.invoke(app, ["log", "metric", "accuracy", "0.94"])
    runner.invoke(app, ["log", "param", "lr", "0.05"])
    runner.invoke(app, ["run", "stop"])

    result = runner.invoke(app, ["export"])
    assert result.exit_code == 0
    assert "export-test" in result.output
    assert "accuracy" in result.output


def test_export_json(mlx_project):
    runner.invoke(app, ["run", "start", "--name", "json-test"])
    runner.invoke(app, ["log", "metric", "accuracy", "0.94"])
    runner.invoke(app, ["run", "stop"])

    result = runner.invoke(app, ["export", "--format", "json"])
    assert result.exit_code == 0

    import json
    # Find the JSON part of output
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["name"] == "json-test"
    assert data[0]["metrics"]["accuracy"] == 0.94