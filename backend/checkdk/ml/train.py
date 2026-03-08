"""
Train the Random Forest model and save artifacts to checkdk/ml/artifacts/.

Usage (from backend/ directory):
    python -m checkdk.ml.train

The dataset is resolved from the following locations in order:
  1. CHECKDK_DATASET environment variable
  2. ../../ml-models/datasets/pod_failure_dataset.csv  (monorepo path)
  3. ~/.checkdk/pod_failure_dataset.csv                (user-installed path)
"""

import json
import os
import sys
from datetime import datetime, timezone

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

MODEL_PATH   = os.path.join(ARTIFACTS_DIR, "rf_model.pkl")
SCALER_PATH  = os.path.join(ARTIFACTS_DIR, "scaler.pkl")
METRICS_PATH = os.path.join(ARTIFACTS_DIR, "metrics.json")

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


def _find_dataset() -> str:
    # 1. Env var
    path = os.getenv("CHECKDK_DATASET")
    if path and os.path.exists(path):
        return path

    # 2. Monorepo path (backend is sibling to ml-models/)
    monorepo = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "ml-models", "datasets", "pod_failure_dataset.csv"
    )
    monorepo = os.path.normpath(monorepo)
    if os.path.exists(monorepo):
        return monorepo

    # 3. User home
    home = os.path.expanduser("~/.checkdk/pod_failure_dataset.csv")
    if os.path.exists(home):
        return home

    raise FileNotFoundError(
        "Dataset not found. Set CHECKDK_DATASET=/path/to/pod_failure_dataset.csv "
        "or place the file at ~/.checkdk/pod_failure_dataset.csv"
    )


def train():
    try:
        import pandas as pd
        import numpy as np
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        print(f"[train] Missing dependency: {e}")
        print("Run: pip install scikit-learn pandas numpy joblib")
        sys.exit(1)

    dataset = _find_dataset()
    print(f"[train] Dataset: {dataset}")

    df = pd.read_csv(dataset)
    X = df[FEATURES].values
    y = df[TARGET].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    print("[train] Training Random Forest...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred  = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix,
    )

    accuracy  = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall    = float(recall_score(y_test, y_pred, zero_division=0))
    f1        = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc   = float(roc_auc_score(y_test, y_proba))
    cm        = confusion_matrix(y_test, y_pred).tolist()

    feature_importances = [
        {"feature": feat, "importance": round(float(imp), 6)}
        for feat, imp in sorted(
            zip(FEATURES, clf.feature_importances_),
            key=lambda x: x[1],
            reverse=True,
        )
    ]

    print("\n=== Random Forest — Evaluation ===")
    from sklearn.metrics import classification_report
    print(classification_report(y_test, y_pred, target_names=["healthy", "failure"]))
    print(f"ROC-AUC: {roc_auc:.4f}")

    joblib.dump(clf,    MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[train] Model  → {MODEL_PATH}")
    print(f"[train] Scaler → {SCALER_PATH}")

    metrics_data = {
        "trained_at":          datetime.now(timezone.utc).isoformat(),
        "accuracy":            round(accuracy, 4),
        "precision":           round(precision, 4),
        "recall":              round(recall, 4),
        "f1":                  round(f1, 4),
        "roc_auc":             round(roc_auc, 4),
        "confusion_matrix":    cm,
        "feature_importances": feature_importances,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as fh:
        json.dump(metrics_data, fh, indent=2)
    print(f"[train] Metrics → {METRICS_PATH}")


if __name__ == "__main__":
    train()
