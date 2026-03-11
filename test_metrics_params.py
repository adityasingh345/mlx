"""
Test for core/metrics.py and core/params.py
Run with: python test_metrics_params.py
"""

import tempfile, os, toml
from pathlib import Path

# ── ARRANGE: build fake project ─────────────
tmp = Path(tempfile.mkdtemp())
mlx_dir = tmp / ".mlx"
mlx_dir.mkdir()
(mlx_dir / "runs").mkdir()

with open(mlx_dir / "config.toml", "w") as f:
    toml.dump({"project": {"name": "test"}}, f)

from mlx.storage.db import init_db
init_db(mlx_dir / "mlx.db")
os.chdir(tmp)

# Start a run so metrics/params have somewhere to go
from mlx.core.run import RunManager
run = RunManager.start("catboost-v1", experiment="fraud-detection")
print(f"\n── Run started: {run.run_id} ──\n")

# ── TEST ParamManager ────────────────────────
from mlx.core.params import ParamManager

print("── ParamManager ──\n")

# Log one param
p = ParamManager.log("learning_rate", 0.05)
print(f"✓ Logged param    : {p.key} = {p.value}")

# Log more params
ParamManager.log("depth",      6)
ParamManager.log("iterations", 500)
ParamManager.log("optimizer",  "adam")   # string value

# Log a duplicate — should UPDATE not create new row
ParamManager.log("learning_rate", 0.01)
print(f"✓ Updated param   : learning_rate → 0.01 (was 0.05)")

# Get all params
params = ParamManager.get_for_run(run.run_id)
print(f"✓ Total params    : {len(params)}  (should be 4, not 5)")

# Get as dict
d = ParamManager.as_dict(run.run_id)
print(f"✓ Params as dict  : {d}")
print(f"✓ learning_rate   : {d['learning_rate']}  (should be 0.01 not 0.05)")

# Log many at once
ParamManager.log_many({
    "batch_size":    32,
    "loss_function": "Logloss",
})
all_params = ParamManager.as_dict(run.run_id)
print(f"✓ After log_many  : {len(all_params)} params total")

# ── TEST MetricManager ───────────────────────
from mlx.core.metrics import MetricManager

print("\n── MetricManager ──\n")

# Log metrics at different steps — simulating training
MetricManager.log("accuracy", 0.81, step=100)
MetricManager.log("accuracy", 0.88, step=200)
MetricManager.log("accuracy", 0.94, step=300)
print(f"✓ Logged accuracy at 3 steps")

MetricManager.log("loss", 0.42, step=100)
MetricManager.log("loss", 0.31, step=200)
MetricManager.log("loss", 0.21, step=300)
print(f"✓ Logged loss at 3 steps")

# Log many at once
MetricManager.log_many({
    "auc":      0.97,
    "f1_score": 0.93,
}, step=300)
print(f"✓ Logged auc and f1_score via log_many")

# Get all metrics — should be 8 rows total
all_metrics = MetricManager.get_for_run(run.run_id)
print(f"\n✓ Total metric rows : {len(all_metrics)}  (should be 8)")

# Get latest — should be 4 rows (one per key)
latest = MetricManager.get_latest(run.run_id)
print(f"✓ Latest metrics    : {len(latest)}  (should be 4)")
for m in latest:
    print(f"   {m.key:12} = {m.value}  @ step {m.step}")

# Get history for one metric
history = MetricManager.get_history(run.run_id, "accuracy")
print(f"\n✓ Accuracy history  : {len(history)} entries")
for m in history:
    print(f"   step {m.step:4} → {m.value}")

# Get all metric keys
keys = MetricManager.get_keys(run.run_id)
print(f"\n✓ Metric keys : {keys}")

# Test validation — should reject non-numbers
print(f"\n✓ Testing bad value (should show error):")
try:
    MetricManager.log("accuracy", "not-a-number")
except ValueError as e:
    print(f"  Caught error → {e}")

# ── TEST compare (both managers) ─────────────
print("\n── Compare (both) ──\n")

# Start a second run
RunManager.stop()
run2 = RunManager.start("catboost-v2")
ParamManager.log_many({"learning_rate": 0.01, "depth": 8})
MetricManager.log("accuracy", 0.97, step=300)
MetricManager.log("loss",     0.18, step=300)
RunManager.stop()

# Compare params
param_compare = ParamManager.compare([run.run_id, run2.run_id])
print(f"✓ Param compare:")
for rid, params in param_compare.items():
    name = rid.split("_")[0]
    print(f"   {name:15} → lr={params.get('learning_rate')}  depth={params.get('depth')}")

# Compare metrics
metric_compare = MetricManager.compare([run.run_id, run2.run_id])
print(f"\n✓ Metric compare:")
for rid, metrics in metric_compare.items():
    name = rid.split("_")[0]
    print(f"   {name:15} → accuracy={metrics.get('accuracy')}  loss={metrics.get('loss')}")

print("\n All metrics and params tests passed!\n")