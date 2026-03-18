"""
examples/catboost_example.py

Full CatBoost training tracked with mlx.

Setup:
    pip install catboost scikit-learn

Usage:
    cd your-project
    mlx init
    mlx run start --name "catboost-v1" --tags "catboost,baseline"
    python examples/catboost_example.py
    mlx run stop
    mlx ls
"""

import subprocess
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from catboost import CatBoostClassifier


def mlx(cmd: str):
    """Call mlx CLI from Python."""
    result = subprocess.run(
        f"mlx {cmd}", shell=True,
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")


# ── Data ────────────────────────────────────
X, y = make_classification(n_samples=10000, n_features=20,
                            n_informative=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
X_train, X_val, y_train, y_val   = train_test_split(X_train, y_train, test_size=0.2)

# ── Params ───────────────────────────────────
params = {
    "learning_rate": 0.05,
    "depth":         6,
    "iterations":    200,
    "loss_function": "Logloss",
    "eval_metric":   "AUC",
    "random_seed":   42,
    "verbose":       False,
}

for key, value in params.items():
    mlx(f"log param {key} {value}")

# ── Train ────────────────────────────────────
model = CatBoostClassifier(**params)
model.fit(X_train, y_train, eval_set=(X_val, y_val), use_best_model=True)

# ── Log metrics per iteration ────────────────
evals = model.get_evals_result()
for i, (tl, vl) in enumerate(zip(
    evals["learn"]["Logloss"],
    evals["validation"]["Logloss"]
)):
    step = i + 1
    if step % 20 == 0:
        mlx(f"log metric train_logloss {tl:.4f} --step {step}")
        mlx(f"log metric val_logloss   {vl:.4f} --step {step}")

# ── Final metrics ─────────────────────────────
y_pred      = model.predict(X_test)
y_pred_prob = model.predict_proba(X_test)[:, 1]

mlx(f"log metric test_accuracy {accuracy_score(y_test, y_pred):.4f}")
mlx(f"log metric test_auc      {roc_auc_score(y_test, y_pred_prob):.4f}")
mlx(f"log param  best_iteration {model.get_best_iteration()}")
mlx("log note 'Training complete'")

print("\nDone! Run: mlx run stop && mlx ls")