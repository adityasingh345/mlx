"""
tests/conftest.py

Shared fixtures for all tests.
pytest automatically loads this file — no imports needed.

The `mlx_project` fixture creates a fresh temporary
.mlx project before each test and cleans up after.
"""

import pytest
import toml
import os
from pathlib import Path
from mlx.storage.db import init_db


@pytest.fixture
def mlx_project(tmp_path, monkeypatch):
    """
    Creates a fresh temporary mlx project for each test.

    tmp_path  → pytest built-in: gives a fresh temp folder per test
    monkeypatch → pytest built-in: lets us safely change cwd

    Every test that uses this fixture gets:
        - A clean .mlx/ folder
        - A fresh SQLite database
        - A config.toml
        - cwd set to the project root so find_root() works

    Usage in tests:
        def test_something(mlx_project):
            # mlx_project is the Path to the project root
            run = RunManager.start("my-run")
            assert run.status == "running"
    """

    # Create folder structure
    mlx_dir = tmp_path / ".mlx"
    mlx_dir.mkdir()
    (mlx_dir / "runs").mkdir()
    (mlx_dir / "artifacts").mkdir()

    # Create config.toml
    config = {
        "project": {
            "name": "test-project",
            "description": "test",
        },
        "settings": {
            "default_experiment": "default",
        }
    }
    with open(mlx_dir / "config.toml", "w") as f:
        toml.dump(config, f)

    # Create database
    init_db(mlx_dir / "mlx.db")

    # Move into project so find_root() works
    monkeypatch.chdir(tmp_path)

    return tmp_path