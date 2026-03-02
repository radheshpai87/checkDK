"""
XGBoost inference helper.

Usage:
    from predict import XGBPredictor
    predictor = XGBPredictor()
    result = predictor.predict({...})
"""

import os
import joblib
import numpy as np
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "xgb_model.pkl")
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


class XGBPredictor:
    """Load the trained XGBoost model and run predictions."""

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run train.py first."
            )
        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

    def predict(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict pod/container failure from a metrics dict.

        Args:
            metrics: dict with keys matching FEATURES list.

        Returns:
            {
                "prediction": 0 | 1,
                "label": "healthy" | "failure",
                "confidence": float,   # probability of failure
            }
        """
        row = np.array([[metrics[f] for f in FEATURES]], dtype=float)
        row_scaled = self.scaler.transform(row)
        pred = int(self.model.predict(row_scaled)[0])
        proba = float(self.model.predict_proba(row_scaled)[0][1])
        return {
            "prediction": pred,
            "label": "failure" if pred == 1 else "healthy",
            "confidence": round(proba, 4),
        }


if __name__ == "__main__":
    predictor = XGBPredictor()
    sample = {
        "cpu_usage": 91.5,
        "memory_usage": 93.0,
        "disk_usage": 45.0,
        "network_latency": 34.0,
        "restart_count": 5,
        "probe_failures": 3,
        "node_cpu_pressure": 1,
        "node_memory_pressure": 1,
        "pod_age_minutes": 120,
    }
    print(predictor.predict(sample))
