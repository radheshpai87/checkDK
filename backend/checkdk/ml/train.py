"""
Train the Random Forest model and save artifacts to checkdk/ml/artifacts/.

Usage (from backend/ directory):
    python -m checkdk.ml.train

The dataset is resolved from the following locations in order:
  1. CHECKDK_DATASET environment variable
  2. ../../ml-models/datasets/pod_failure_dataset.csv  (monorepo path)
  3. ~/.checkdk/pod_failure_dataset.csv                (user-installed path)
"""

import os
import sys

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

MODEL_PATH  = os.path.join(ARTIFACTS_DIR, "rf_model.pkl")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.pkl")

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
        from sklearn.metrics import classification_report, roc_auc_score
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

    print("\n=== Random Forest — Evaluation ===")
    print(classification_report(y_test, y_pred, target_names=["healthy", "failure"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    joblib.dump(clf,    MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[train] Model  → {MODEL_PATH}")
    print(f"[train] Scaler → {SCALER_PATH}")


if __name__ == "__main__":
    train()
