"""
Random Forest model for pod/container failure detection.

Trains on pod_failure_dataset.csv and saves the model + scaler to disk.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
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

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "../../datasets/pod_failure_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "rf_model.pkl")
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


def load_data(path: str):
    df = pd.read_csv(path)
    X = df[FEATURES].values
    y = df[TARGET].values
    return X, y


def train():
    print("[RandomForest] Loading dataset...")
    X, y = load_data(DATASET_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    print("[RandomForest] Training model...")
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # Evaluation
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    print("\n=== Random Forest Results ===")
    print(classification_report(y_test, y_pred, target_names=["healthy", "failure"]))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    # Feature importance
    importances = clf.feature_importances_
    print("\nFeature Importances:")
    for feat, imp in sorted(zip(FEATURES, importances), key=lambda x: -x[1]):
        print(f"  {feat:<25} {imp:.4f}")

    # Persist model + scaler
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[RandomForest] Model saved to {MODEL_PATH}")
    print(f"[RandomForest] Scaler saved to {SCALER_PATH}")

    # Persist metrics to JSON for the dashboard
    metrics_data = {
        "name": "random_forest",
        "display_name": "Random Forest",
        "algorithm": "RandomForestClassifier (200 trees, balanced)",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "feature_importances": [
            {"feature": feat, "importance": round(float(imp), 4)}
            for feat, imp in sorted(zip(FEATURES, importances), key=lambda x: -x[1])
        ],
    }
    metrics_path = os.path.join(BASE_DIR, "metrics.json")
    with open(metrics_path, "w") as mf:
        json.dump(metrics_data, mf, indent=2)
    print(f"[RandomForest] Metrics saved to {metrics_path}")


if __name__ == "__main__":
    train()
