"""
Random Forest model for pod/container failure detection.

Trains on pod_failure_dataset.csv and saves the model + scaler to disk.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
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

    # Persist
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n[RandomForest] Model saved to {MODEL_PATH}")
    print(f"[RandomForest] Scaler saved to {SCALER_PATH}")


if __name__ == "__main__":
    train()
