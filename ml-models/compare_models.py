"""
compare_models.py
-----------------
Evaluates all three trained models on the same held-out test split,
generates comparison charts, and prints the best model recommendation.

Output (saved to reports/):
  - metrics_comparison.png   – grouped bar chart (Accuracy / F1 / ROC-AUC)
  - roc_curves.png           – ROC curve overlay for all models
  - confusion_matrices.png   – 1x3 confusion matrix grid
  - metrics_summary.txt      – plaintext table + best model recommendation

Run:
    python compare_models.py
"""

import os
import sys
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # headless – no display needed
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
    classification_report,
)

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATASET    = os.path.join(BASE_DIR, "datasets", "pod_failure_dataset.csv")
REPORTS    = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS, exist_ok=True)

FEATURES = [
    "cpu_usage", "memory_usage", "disk_usage", "network_latency",
    "restart_count", "probe_failures", "node_cpu_pressure",
    "node_memory_pressure", "pod_age_minutes",
]
TARGET = "failure_label"

# ---------------------------------------------------------------------------
# Load & split (same seed as training)
# ---------------------------------------------------------------------------
def load_test_data():
    df = pd.read_csv(DATASET)
    X = df[FEATURES].values.astype(np.float32)
    y = df[TARGET].values
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return X_test, y_test


# ---------------------------------------------------------------------------
# Model loaders – each returns (y_pred, y_proba)
# ---------------------------------------------------------------------------
def load_rf(X_test):
    rf_dir = os.path.join(BASE_DIR, "models", "random_forest")
    clf    = joblib.load(os.path.join(rf_dir, "rf_model.pkl"))
    scaler = joblib.load(os.path.join(rf_dir, "scaler.pkl"))
    Xs     = scaler.transform(X_test)
    return clf.predict(Xs), clf.predict_proba(Xs)[:, 1]


def load_xgb(X_test):
    xgb_dir = os.path.join(BASE_DIR, "models", "xgboost_model")
    clf     = joblib.load(os.path.join(xgb_dir, "xgb_model.pkl"))
    scaler  = joblib.load(os.path.join(xgb_dir, "scaler.pkl"))
    Xs      = scaler.transform(X_test)
    return clf.predict(Xs), clf.predict_proba(Xs)[:, 1]


def load_lstm(X_test):
    import torch
    import torch.nn as nn

    device   = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lstm_dir = os.path.join(BASE_DIR, "models", "lstm_model")
    ckpt     = torch.load(os.path.join(lstm_dir, "lstm_model.pt"),
                          map_location=device, weights_only=True)
    scaler   = joblib.load(os.path.join(lstm_dir, "scaler.pkl"))
    hp       = ckpt["hyperparams"]

    # Inline model definition so we don't depend on a relative import
    class PodFailureLSTM(nn.Module):
        def __init__(self, input_size, hidden_size, num_layers, dropout):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                                batch_first=True,
                                dropout=dropout if num_layers > 1 else 0.0)
            self.classifier = nn.Sequential(
                nn.Linear(hidden_size, 32), nn.ReLU(),
                nn.Dropout(dropout), nn.Linear(32, 1),
            )
        def forward(self, x):
            out, _ = self.lstm(x)
            return self.classifier(out[:, -1, :]).squeeze(-1)

    model = PodFailureLSTM(**hp)
    model.load_state_dict(ckpt["state_dict"])
    model.to(device)
    model.eval()

    Xs = scaler.transform(X_test).astype(np.float32)
    tensor = torch.tensor(Xs).unsqueeze(-1).to(device)   # (N, seq, 1)
    with torch.no_grad():
        logits = model(tensor)
        proba  = torch.sigmoid(logits).numpy()
    preds = (proba >= 0.5).astype(int)
    return preds, proba


# ---------------------------------------------------------------------------
# Metrics helper
# ---------------------------------------------------------------------------
def compute_metrics(y_true, y_pred, y_proba):
    return {
        "Accuracy":  round(accuracy_score(y_true, y_pred),           4),
        "Precision": round(precision_score(y_true, y_pred,           zero_division=0), 4),
        "Recall":    round(recall_score(y_true, y_pred,              zero_division=0), 4),
        "F1":        round(f1_score(y_true, y_pred,                  zero_division=0), 4),
        "ROC-AUC":   round(roc_auc_score(y_true, y_proba),           4),
    }


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
PALETTE = {"Random Forest": "#4C72B0", "XGBoost": "#DD8452", "LSTM": "#55A868"}


def plot_metrics_bar(metrics_dict: dict):
    """Grouped bar chart for Accuracy, F1, ROC-AUC."""
    keys   = ["Accuracy", "F1", "ROC-AUC"]
    models = list(metrics_dict.keys())
    x      = np.arange(len(keys))
    width  = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    for i, model in enumerate(models):
        vals = [metrics_dict[model][k] for k in keys]
        bars = ax.bar(x + i * width, vals, width,
                      label=model, color=PALETTE[model], alpha=0.88)
        ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels(keys, fontsize=11)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison – Accuracy / F1 / ROC-AUC", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    path = os.path.join(REPORTS, "metrics_comparison.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def plot_roc(y_true, roc_data: dict):
    """Overlaid ROC curves."""
    fig, ax = plt.subplots(figsize=(7, 6))
    for model, y_proba in roc_data.items():
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        auc = roc_auc_score(y_true, y_proba)
        ax.plot(fpr, tpr, label=f"{model} (AUC={auc:.3f})",
                color=PALETTE[model], linewidth=2)

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curves", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(linestyle="--", alpha=0.4)
    plt.tight_layout()
    path = os.path.join(REPORTS, "roc_curves.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def plot_confusion_matrices(y_true, pred_dict: dict):
    """1×N grid of confusion matrices."""
    n      = len(pred_dict)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]

    for ax, (model, y_pred) in zip(axes, pred_dict.items()):
        cm = confusion_matrix(y_true, y_pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                    xticklabels=["healthy", "failure"],
                    yticklabels=["healthy", "failure"],
                    cbar=False)
        ax.set_title(model, fontsize=11, fontweight="bold")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    plt.suptitle("Confusion Matrices", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = os.path.join(REPORTS, "confusion_matrices.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Text summary
# ---------------------------------------------------------------------------
def write_summary(metrics_dict: dict, best_model: str):
    lines = []
    lines.append("=" * 62)
    lines.append("  Pod Failure Detection – Model Comparison Summary")
    lines.append("=" * 62)
    lines.append(f"\n{'Model':<18} {'Accuracy':>9} {'Precision':>10} "
                 f"{'Recall':>8} {'F1':>8} {'ROC-AUC':>9}")
    lines.append("-" * 62)
    for model, m in metrics_dict.items():
        marker = " ◄ BEST" if model == best_model else ""
        lines.append(
            f"{model:<18} {m['Accuracy']:>9.4f} {m['Precision']:>10.4f} "
            f"{m['Recall']:>8.4f} {m['F1']:>8.4f} {m['ROC-AUC']:>9.4f}{marker}"
        )
    lines.append("=" * 62)
    lines.append(f"\n  ★  Recommended model: {best_model}")
    lines.append("     (ranked by ROC-AUC score)\n")

    text = "\n".join(lines)
    print(text)

    path = os.path.join(REPORTS, "metrics_summary.txt")
    with open(path, "w") as f:
        f.write(text)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("\n[compare] Loading test data...")
    X_test, y_test = load_test_data()

    loaders = {
        "Random Forest": load_rf,
        "XGBoost":       load_xgb,
        "LSTM":          load_lstm,
    }

    metrics_dict = {}
    pred_dict    = {}
    roc_data     = {}

    for name, loader in loaders.items():
        print(f"[compare] Evaluating {name}...")
        try:
            y_pred, y_proba = loader(X_test)
            metrics_dict[name] = compute_metrics(y_test, y_pred, y_proba)
            pred_dict[name]    = y_pred
            roc_data[name]     = y_proba
        except FileNotFoundError as e:
            print(f"  [SKIP] {name}: {e}")

    if not metrics_dict:
        print("[compare] No models found – run train_all.py first.")
        sys.exit(1)

    # Pick best by ROC-AUC
    best_model = max(metrics_dict, key=lambda m: metrics_dict[m]["ROC-AUC"])

    print("\n[compare] Generating plots...")
    plot_metrics_bar(metrics_dict)
    plot_roc(y_test, roc_data)
    plot_confusion_matrices(y_test, pred_dict)
    write_summary(metrics_dict, best_model)

    print(f"\n[compare] Done. Charts saved to reports/")


if __name__ == "__main__":
    main()
