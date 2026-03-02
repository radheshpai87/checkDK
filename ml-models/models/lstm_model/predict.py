"""
LSTM inference helper.

Usage:
    from predict import LSTMPredictor
    predictor = LSTMPredictor()
    result = predictor.predict({...})
"""

import os
import joblib
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        return self.classifier(last_hidden).squeeze(-1)


class LSTMPredictor:
    """Load the trained LSTM model and run predictions."""

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run train.py first."
            )
        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
        hp = checkpoint["hyperparams"]
        self.model = PodFailureLSTM(
            input_size=hp["input_size"],
            hidden_size=hp["hidden_size"],
            num_layers=hp["num_layers"],
            dropout=hp["dropout"],
        )
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()
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
        row = np.array([[metrics[f] for f in FEATURES]], dtype=np.float32)
        row_scaled = self.scaler.transform(row)
        # Shape: (1, seq_len, 1)
        tensor = torch.tensor(row_scaled, dtype=torch.float32).unsqueeze(-1)
        with torch.no_grad():
            logit = self.model(tensor)
            proba = float(torch.sigmoid(logit).item())
        pred = 1 if proba >= 0.5 else 0
        return {
            "prediction": pred,
            "label": "failure" if pred == 1 else "healthy",
            "confidence": round(proba, 4),
        }


if __name__ == "__main__":
    predictor = LSTMPredictor()
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
