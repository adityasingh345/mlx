"""
examples/sklearn_example.py

Scikit-learn RandomForest tracked with mlx.

Usage:
    mlx run start --name "rf-v1" --tags "sklearn,random-forest"
    python examples/sklearn_example.py
    mlx run stop
"""

import subprocess
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
import numpy as np


def mlx(cmd):
    subprocess.run(f"mlx {cmd}", shell=True, capture_output=True)


# ── Data ─────────────────────────────────────
X, y = make_classification(n_samples=5000, n_features=20,
                            n_informative=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# ── Params ────────────────────────────────────
params = {
    "n_estimators":   100,
    "max_depth":      10,
    "min_samples_split": 5,
    "random_state":   42,
}

for key, value in params.items():
    mlx(f"log param {key} {value}")

# ── Train ─────────────────────────────────────
model = RandomForestClassifier(**params)
model.fit(X_train, y_train)

# ── Cross-validation scores ───────────────────
cv_scores = cross_val_score(model, X_train, y_train, cv=5)
for i, score in enumerate(cv_scores):
    mlx(f"log metric cv_accuracy {score:.4f} --step {i+1}")

mlx(f"log metric cv_mean {cv_scores.mean():.4f}")
mlx(f"log metric cv_std  {cv_scores.std():.4f}")

# ── Final metrics ─────────────────────────────
y_pred      = model.predict(X_test)
y_pred_prob = model.predict_proba(X_test)[:, 1]

mlx(f"log metric test_accuracy {accuracy_score(y_test, y_pred):.4f}")
mlx(f"log metric test_auc      {roc_auc_score(y_test, y_pred_prob):.4f}")

print("Done! Run: mlx run stop && mlx ls")