"""
examples/pytorch_example.py

PyTorch training loop tracked with mlx.
Logs metrics at every epoch.

Usage:
    pip install torch
    mlx run start --name "pytorch-v1" --tags "pytorch,mlp"
    python examples/pytorch_example.py
    mlx run stop
"""

import subprocess
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np


def mlx(cmd):
    subprocess.run(f"mlx {cmd}", shell=True, capture_output=True)


# ── Data ─────────────────────────────────────
X, y = make_classification(n_samples=5000, n_features=20,
                            n_informative=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

scaler  = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)

# Convert to tensors
X_tr = torch.FloatTensor(X_train)
y_tr = torch.FloatTensor(y_train)
X_te = torch.FloatTensor(X_test)
y_te = torch.FloatTensor(y_test)

loader = DataLoader(TensorDataset(X_tr, y_tr), batch_size=64, shuffle=True)

# ── Model ─────────────────────────────────────
model = nn.Sequential(
    nn.Linear(20, 64), nn.ReLU(),
    nn.Linear(64, 32), nn.ReLU(),
    nn.Linear(32, 1),  nn.Sigmoid(),
)

lr         = 0.001
epochs     = 20
optimizer  = torch.optim.Adam(model.parameters(), lr=lr)
criterion  = nn.BCELoss()

# ── Log params ────────────────────────────────
mlx(f"log param learning_rate {lr}")
mlx(f"log param epochs        {epochs}")
mlx(f"log param batch_size    64")
mlx(f"log param optimizer     adam")
mlx(f"log param architecture  MLP-64-32-1")

# ── Training loop ─────────────────────────────
for epoch in range(1, epochs + 1):

    model.train()
    total_loss = 0
    for xb, yb in loader:
        optimizer.zero_grad()
        loss = criterion(model(xb).squeeze(), yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    avg_loss = total_loss / len(loader)

    # Evaluate
    model.eval()
    with torch.no_grad():
        preds = model(X_te).squeeze()
        test_loss = criterion(preds, y_te).item()
        accuracy  = ((preds > 0.5).float() == y_te).float().mean().item()

    # Log every epoch
    mlx(f"log metric train_loss {avg_loss:.4f}  --step {epoch}")
    mlx(f"log metric test_loss  {test_loss:.4f} --step {epoch}")
    mlx(f"log metric accuracy   {accuracy:.4f}  --step {epoch}")

    print(f"Epoch {epoch:2d} | train={avg_loss:.4f} | test={test_loss:.4f} | acc={accuracy:.4f}")

print("\nDone! Run: mlx run stop && mlx ls")