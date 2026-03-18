# mlx — ML Experiment Manager

> Track experiments, runs, params and metrics.
> 100% local. No server. No account. No cloud.

## Why mlx?

Every ML engineer has this problem:

- Trained 20 models last week
- Can't remember which settings gave the best result
- No way to compare runs side by side
- Results scattered across notebooks and print statements

mlx fixes this with one simple workflow:
```bash
mlx run start --name "catboost-v1"
python train.py
mlx run stop
mlx compare catboost-v1 catboost-v2
```

## How it works

mlx stores everything in a local SQLite database at `.mlx/mlx.db`.
No internet connection needed. Your data never leaves your machine.
```
your-project/
└── .mlx/
    ├── mlx.db        ← all runs, params, metrics
    ├── config.toml   ← project settings
    └── runs/
        └── catboost-v1_20240301/
            └── stdout.log
```

## Install
```bash
pip install mlx-tracker
```

## Commands

| Command | Description |
|---------|-------------|
| `mlx init` | Initialize project |
| `mlx run start` | Start a run |
| `mlx run stop` | Stop active run |
| `mlx log metric` | Log a metric |
| `mlx log param` | Log a param |
| `mlx ls` | List all runs |
| `mlx status` | Show active run |
| `mlx compare` | Compare runs |
| `mlx export` | Export to CSV/JSON |