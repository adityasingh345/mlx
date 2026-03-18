# mlx init

Initialize a new mlx project in the current directory.

## Usage
```bash
mlx init [OPTIONS]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--name` | `-n` | folder name | Project name |
| `--desc` | `-d` | `""` | Project description |
| `--force` | `-f` | `False` | Re-initialize existing project |

## Examples
```bash
# Basic init
mlx init

# With custom name
mlx init --name "fraud-detection"

# With name and description
mlx init --name "fraud-detection" --desc "Fraud model v2"

# Re-initialize (keeps existing data)
mlx init --force
```

## What it creates
```
.mlx/
├── mlx.db        ← SQLite database
├── config.toml   ← project config
├── runs/         ← log files per run
└── artifacts/    ← saved models (future)
```