# mlx log

Log metrics, params and notes to the active run.

## mlx log metric
```bash
mlx log metric accuracy 0.94
mlx log metric accuracy 0.94 --step 100
mlx log metric val_loss 0.21 --step 50
```

| Argument | Description |
|----------|-------------|
| `key` | Metric name — accuracy, loss, auc |
| `value` | Numeric value — 0.94 |
| `--step` | Training step or epoch |

---

## mlx log param
```bash
mlx log param learning_rate 0.05
mlx log param depth 6
mlx log param optimizer adam
```

Logging the same param twice **updates** it — no duplicates.

---

## mlx log note
```bash
mlx log note "val loss stopped improving at step 150"
mlx log note "model saved to artifacts/model.cbm"
```

Notes are saved to the run's log file and shown in `mlx logs`.