# Quickstart

Get tracking in under 5 minutes.

## 1. Install
```bash
pip install mlx-tracker
```

## 2. Initialize your project
```bash
cd your-ml-project
mlx init
```

## 3. Start a run
```bash
mlx run start --name "my-first-run" --experiment "fraud-detection"
```

## 4. Log params and metrics
```bash
mlx log param learning_rate 0.05
mlx log param depth 6

mlx log metric accuracy 0.94 --step 100
mlx log metric loss 0.21 --step 100
```

## 5. Stop the run
```bash
mlx run stop
```

## 6. See your results
```bash
mlx ls
mlx status --run-id "my-first-run_..."
```

## 7. Train another model and compare
```bash
mlx run start --name "my-second-run"
mlx log param learning_rate 0.01
mlx log metric accuracy 0.97 --step 100
mlx run stop

mlx compare my-first-run_... my-second-run_...
```

## Next steps

- [Commands reference](commands/init.md)
- [CatBoost example](../examples/catboost_example.py)
- [sklearn example](../examples/sklearn_example.py)