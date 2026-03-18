"""Tests for ExperimentManager."""

import pytest
from mlx.core.experiment import ExperimentManager


def test_create_experiment(mlx_project):
    exp = ExperimentManager.create("fraud-detection")
    assert exp.name == "fraud-detection"
    assert exp.id is not None
    assert exp.created_at is not None


def test_create_experiment_with_description(mlx_project):
    exp = ExperimentManager.create("fraud", "My fraud model")
    assert exp.description == "My fraud model"


def test_create_duplicate_does_not_duplicate(mlx_project):
    """Creating same experiment twice should return existing one."""
    exp1 = ExperimentManager.create("fraud-detection")
    exp2 = ExperimentManager.create("fraud-detection")

    all_exps = ExperimentManager.get_all()
    assert len(all_exps) == 1
    assert exp1.id == exp2.id


def test_get_existing_experiment(mlx_project):
    ExperimentManager.create("fraud-detection")
    exp = ExperimentManager.get("fraud-detection")
    assert exp is not None
    assert exp.name == "fraud-detection"


def test_get_missing_experiment_returns_none(mlx_project):
    result = ExperimentManager.get("does-not-exist")
    assert result is None


def test_exists_true(mlx_project):
    ExperimentManager.create("fraud-detection")
    assert ExperimentManager.exists("fraud-detection") is True


def test_exists_false(mlx_project):
    assert ExperimentManager.exists("not-there") is False


def test_get_all_returns_all(mlx_project):
    ExperimentManager.create("exp-1")
    ExperimentManager.create("exp-2")
    ExperimentManager.create("exp-3")

    all_exps = ExperimentManager.get_all()
    assert len(all_exps) == 3


def test_get_all_empty(mlx_project):
    all_exps = ExperimentManager.get_all()
    assert all_exps == []