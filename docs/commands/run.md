# mlx run

Manage experiment runs.

## Subcommands

### mlx run start

Start a new run and begin tracking.
```bash
mlx run start --name "catboost-v1"
mlx run start --name "catboost-v1" --experiment "fraud"
mlx run start --name "catboost-v1" --tags "catboost,baseline"
```

| Option | Short | Description |
|--------|-------|-------------|
| `--name` | `-n` | **Required.** Run name |
| `--experiment` | `-e` | Experiment group (default: "default") |
| `--tags` | `-t` | Comma-separated tags |

---

### mlx run stop

Stop the active run.
```bash
mlx run stop
mlx run stop --status failed
```

| Option | Description |
|--------|-------------|
| `--status` | `done` or `failed` (default: done) |
| `--run-id` | Stop specific run instead of active |

---

### mlx run list

List all runs.
```bash
mlx run list
mlx run list --experiment fraud
mlx run list --status done
mlx run list --limit 10
```

---

### mlx run delete

Delete a run and all its data permanently.
```bash
mlx run delete --run-id "catboost-v1_..."
mlx run delete --run-id "catboost-v1_..." --yes
```