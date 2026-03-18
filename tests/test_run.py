"""Tests for RunManager."""

import pytest
from mlx.core.run import RunManager
from mlx.storage.filesystem import get_active_run


def test_start_run(mlx_project):
    run = RunManager.start("catboost-v1")
    assert run.name == "catboost-v1"
    assert run.status == "running"
    assert run.run_id is not None
    assert "catboost-v1" in run.run_id


def test_start_run_sets_active(mlx_project):
    run = RunManager.start("catboost-v1")
    assert get_active_run() == run.run_id


def test_start_run_with_experiment(mlx_project):
    run = RunManager.start("catboost-v1", experiment="fraud")
    assert run.experiment == "fraud"


def test_start_run_with_tags(mlx_project):
    run = RunManager.start("catboost-v1", tags="catboost,v1")
    assert run.tags == "catboost,v1"


def test_cannot_start_two_runs(mlx_project):
    """Starting a second run while one is active should raise."""
    RunManager.start("run-1")
    with pytest.raises(RuntimeError, match="already active"):
        RunManager.start("run-2")


def test_stop_run(mlx_project):
    run = RunManager.start("catboost-v1")
    stopped = RunManager.stop()

    assert stopped.status == "done"
    assert stopped.finished_at is not None
    assert stopped.duration_sec is not None


def test_stop_run_clears_active(mlx_project):
    RunManager.start("catboost-v1")
    RunManager.stop()
    assert get_active_run() is None


def test_stop_run_failed_status(mlx_project):
    RunManager.start("catboost-v1")
    stopped = RunManager.stop(status="failed")
    assert stopped.status == "failed"


def test_stop_with_no_active_run_raises(mlx_project):
    with pytest.raises(RuntimeError):
        RunManager.stop()


def test_get_run(mlx_project):
    run = RunManager.start("catboost-v1")
    RunManager.stop()

    fetched = RunManager.get(run.run_id)
    assert fetched is not None
    assert fetched.name == "catboost-v1"


def test_get_missing_run_returns_none(mlx_project):
    result = RunManager.get("does-not-exist")
    assert result is None


def test_get_active_run(mlx_project):
    run = RunManager.start("catboost-v1")
    active = RunManager.get_active()
    assert active is not None
    assert active.run_id == run.run_id


def test_get_active_when_none(mlx_project):
    result = RunManager.get_active()
    assert result is None


def test_get_all_runs(mlx_project):
    RunManager.start("run-1"); RunManager.stop()
    RunManager.start("run-2"); RunManager.stop()
    RunManager.start("run-3"); RunManager.stop()

    runs = RunManager.get_all()
    assert len(runs) == 3


def test_get_all_filter_by_status(mlx_project):
    RunManager.start("run-1"); RunManager.stop(status="done")
    RunManager.start("run-2"); RunManager.stop(status="failed")

    done_runs = RunManager.get_all(status="done")
    assert len(done_runs) == 1
    assert done_runs[0].name == "run-1"


def test_get_all_filter_by_experiment(mlx_project):
    RunManager.start("run-1", experiment="fraud"); RunManager.stop()
    RunManager.start("run-2", experiment="images"); RunManager.stop()

    fraud_runs = RunManager.get_all(experiment="fraud")
    assert len(fraud_runs) == 1
    assert fraud_runs[0].name == "run-1"


def test_delete_run(mlx_project):
    run = RunManager.start("to-delete")
    RunManager.stop()

    RunManager.delete(run.run_id)
    assert RunManager.get(run.run_id) is None


def test_run_id_contains_name(mlx_project):
    run = RunManager.start("my-special-run")
    RunManager.stop()
    assert "my-special-run" in run.run_id