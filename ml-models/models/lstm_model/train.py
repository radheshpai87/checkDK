"""
LSTM model for pod/container failure detection.

The feature vector (9 metrics) is treated as a sequence of 9 time steps
with 1 feature each, fed into a stacked LSTM for binary classification.

Trains on pod_failure_dataset.csv and saves the model + scaler to disk.
"""

import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from datetime import datetime, timezone
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
import joblib

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "../../datasets/pod_failure_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "lstm_model.pt")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

FEATURES = [
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    "network_latency",
    "restart_count",
    "probe_failures",
    "node_cpu_pressure",
    "node_memory_pressure",
    "pod_age_minutes",
]
TARGET = "failure_label"

# Hyperparameters
BATCH_SIZE = 256
EPOCHS = 30
LR = 1e-3
HIDDEN_SIZE = 64
NUM_LAYERS = 2
DROPOUT = 0.3

INPUT_SIZE = 1           # one feature per time step
SEQ_LEN = len(FEATURES)  # 9 time steps


# ---------------------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------------------
class PodFailureLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        # x: (batch, seq_len, 1)
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]   # take last time step
        return self.classifier(last_hidden).squeeze(-1)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def load_data(path: str):
    df = pd.read_csv(path)
    X = df[FEATURES].values.astype(np.float32)
    y = df[TARGET].values.astype(np.float32)
    return X, y


def make_weighted_sampler(y_train):
    """Over-sample the minority class to handle imbalance."""
    counts = np.bincount(y_train.astype(int))
    weights = 1.0 / counts
    sample_weights = torch.tensor(weights[y_train.astype(int)], dtype=torch.float)
    return WeightedRandomSampler(sample_weights, len(sample_weights))


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[LSTM] Using device: {device}")

    print("[LSTM] Loading dataset...")
    X, y = load_data(DATASET_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Reshape to (N, seq_len, 1) for LSTM
    X_train_t = torch.tensor(X_train, dtype=torch.float32).unsqueeze(-1)
    X_test_t = torch.tensor(X_test, dtype=torch.float32).unsqueeze(-1)
    y_train_t = torch.tensor(y_train, dtype=torch.float32)
    y_test_t = torch.tensor(y_test, dtype=torch.float32)

    sampler = make_weighted_sampler(y_train)
    train_ds = TensorDataset(X_train_t, y_train_t)
    test_ds = TensorDataset(X_test_t, y_test_t)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    model = PodFailureLSTM(
        input_size=INPUT_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT,
    ).to(device)

    # Positive weight for BCEWithLogitsLoss
    pos_weight = torch.tensor(
        [int(np.sum(y_train == 0)) / max(int(np.sum(y_train == 1)), 1)],
        dtype=torch.float32,
    ).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=3, factor=0.5
    )

    print("[LSTM] Training model...")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item() * len(xb)

        avg_loss = total_loss / len(train_loader.dataset)
        scheduler.step(avg_loss)
        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch {epoch:03d}/{EPOCHS} | loss={avg_loss:.4f}")

    # Evaluation
    model.eval()
    all_proba, all_pred, all_true = [], [], []
    with torch.no_grad():
        for xb, yb in test_loader:
            xb = xb.to(device)
            logits = model(xb)
            proba = torch.sigmoid(logits).cpu().numpy()
            preds = (proba >= 0.5).astype(int)
            all_proba.extend(proba.tolist())
            all_pred.extend(preds.tolist())
            all_true.extend(yb.numpy().astype(int).tolist())

    print("\n=== LSTM Results ===")
    print(classification_report(all_true, all_pred, target_names=["healthy", "failure"]))
    print("Confusion Matrix:")
    print(confusion_matrix(all_true, all_pred))
    print(f"ROC-AUC: {roc_auc_score(all_true, all_proba):.4f}")

    # Persist
    torch.save(
        {
            "state_dict": model.state_dict(),
            "hyperparams": {
                "input_size": INPUT_SIZE,
                "hidden_size": HIDDEN_SIZE,
                "num_layers": NUM_LAYERS,
                "dropout": DROPOUT,
            },
        },
        MODEL_PATH,
    )
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[LSTM] Model saved to {MODEL_PATH}")
    print(f"[LSTM] Scaler saved to {SCALER_PATH}")

    # Persist metrics to JSON for the dashboard
    metrics_data = {
        "name": "lstm",
        "display_name": "LSTM",
        "algorithm": "Stacked LSTM (2 layers, hidden=64, dropout=0.3)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "accuracy": round(float(accuracy_score(all_true, all_pred)), 4),
        "precision": round(float(precision_score(all_true, all_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(all_true, all_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(all_true, all_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(all_true, all_proba)), 4),
        "confusion_matrix": confusion_matrix(all_true, all_pred).tolist(),
        "feature_importances": None,
    }
    metrics_path = os.path.join(BASE_DIR, "metrics.json")
    with open(metrics_path, "w") as mf:
        json.dump(metrics_data, mf, indent=2)
    print(f"[LSTM] Metrics saved to {metrics_path}")


if __name__ == "__main__":
    train()
