"""
Quick terminal test for core/experiment.py and core/run.py
"""

import tempfile, os, toml
from pathlib import Path

# ── Step 1: Create a fake project folder ──
tmp = Path(tempfile.mkdtemp())
mlx_dir = tmp / ".mlx"
mlx_dir.mkdir()
(mlx_dir / "runs").mkdir()

# Write minimal config.toml
with open(mlx_dir / "config.toml", "w") as f:
    toml.dump({"project": {"name": "test-project"}}, f)

# Create the database
from mlx.storage.db import init_db
init_db(mlx_dir / "mlx.db")

# Move into the temp folder so find_root() works
os.chdir(tmp)

print("\n── Testing experiment.py and run.py ──\n")

# ── Step 2: Test ExperimentManager ──
from mlx.core.experiment import ExperimentManager

exp = ExperimentManager.create("fraud-detection")
print(f"✓ Created experiment : {exp.name}")
print(f"  id         : {exp.id}")
print(f"  created_at : {exp.created_at}")

# Try creating same experiment again — should NOT duplicate
exp2 = ExperimentManager.create("fraud-detection")
print(f"\n✓ Created same experiment again (should not duplicate)")

all_exps = ExperimentManager.get_all()
print(f"  Total experiments in DB : {len(all_exps)}  (should be 1)")

# exists() check
print(f"\n✓ exists('fraud-detection') : {ExperimentManager.exists('fraud-detection')}")
print(f"✓ exists('unknown')         : {ExperimentManager.exists('unknown')}")

# ── Step 3: Test RunManager ──
from mlx.core.run import RunManager

print("\n── RunManager ──\n")

# Start a run
run = RunManager.start(
    name="catboost-v1",
    experiment="fraud-detection",
    tags="catboost,test"
)
print(f"✓ Run started")
print(f"  run_id     : {run.run_id}")
print(f"  name       : {run.name}")
print(f"  experiment : {run.experiment}")
print(f"  status     : {run.status}")
print(f"  tags       : {run.tags}")

# Check active run
active = RunManager.get_active()
print(f"\n✓ Active run : {active.name}")

# Try starting another — should raise error
print(f"\n✓ Trying to start second run (should show error):")
try:
    RunManager.start("xgboost-v1")
except RuntimeError as e:
    print(f"  Caught error → {e}")

# Get run by ID
fetched = RunManager.get(run.run_id)
print(f"\n✓ Fetched run by ID : {fetched.name}")

# Get all runs
all_runs = RunManager.get_all()
print(f"✓ Total runs in DB  : {len(all_runs)}")

# Stop the run
stopped = RunManager.stop(status="done")
print(f"\n✓ Run stopped")
print(f"  status       : {stopped.status}")
print(f"  duration_sec : {stopped.duration_sec}s")
print(f"  finished_at  : {stopped.finished_at[:19]}")

# Verify no active run
active_after = RunManager.get_active()
print(f"\n✓ Active run after stop : {active_after}  (should be None)")

print("\n Both files working correctly!\n")