"""
Random Forest predictor for pod/container failure detection.

Artifacts are stored in checkdk/ml/artifacts/ (gitignored).
Run train.py once to generate them:
    python -m checkdk.ml.train
"""

import os
from dataclasses import dataclass
from typing import Optional

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
MODEL_PATH    = os.path.join(ARTIFACTS_DIR, "rf_model.pkl")
SCALER_PATH   = os.path.join(ARTIFACTS_DIR, "scaler.pkl")

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


@dataclass
class PodMetrics:
    """Runtime metrics collected from a running pod or container."""
    cpu_usage: float            # 0-100 %
    memory_usage: float         # 0-100 %
    disk_usage: float           # 0-100 %
    network_latency: float      # ms
    restart_count: int          # total restarts
    probe_failures: int         # liveness/readiness probe failures
    node_cpu_pressure: int      # 0 or 1
    node_memory_pressure: int   # 0 or 1
    pod_age_minutes: int        # age in minutes
    # Optional metadata for richer LLM context
    service_name: Optional[str] = None
    namespace: Optional[str] = None
    platform: Optional[str] = None   # "docker" | "kubernetes"

    def to_feature_dict(self) -> dict:
        return {f: getattr(self, f) for f in FEATURES}


@dataclass
class PredictionResult:
    """Result from the Random Forest classifier."""
    prediction: int           # 0 = healthy, 1 = failure
    label: str                # "healthy" | "failure"
    confidence: float         # probability of failure [0, 1]
    metrics: PodMetrics

    @property
    def is_failure(self) -> bool:
        return self.prediction == 1

    @property
    def risk_level(self) -> str:
        if self.confidence >= 0.85:
            return "critical"
        if self.confidence >= 0.60:
            return "high"
        if self.confidence >= 0.35:
            return "medium"
        return "low"

    def to_summary(self) -> str:
        """Human-readable one-liner for logging / display."""
        pct = round(self.confidence * 100, 1)
        svc = f"[{self.metrics.service_name}] " if self.metrics.service_name else ""
        return (
            f"{svc}Prediction: {self.label.upper()} "
            f"(confidence: {pct}%, risk: {self.risk_level})"
        )


class RFPredictor:
    """
    Loads the trained Random Forest model and runs predictions.

    Raises RuntimeError if artifacts are missing — run train.py first.
    """

    _instance: Optional["RFPredictor"] = None   # singleton cache

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                "Random Forest model not found. "
                "Run: python -m checkdk.ml.train"
            )
        import joblib
        import numpy as np
        self._np = np
        self._model  = joblib.load(MODEL_PATH)
        self._scaler = joblib.load(SCALER_PATH)

    @classmethod
    def get(cls) -> Optional["RFPredictor"]:
        """
        Get a cached singleton instance.
        Returns None (instead of raising) if artifacts are missing,
        so callers can gracefully skip ML.
        """
        if cls._instance is None:
            try:
                cls._instance = cls()
            except (RuntimeError, Exception):
                return None
        return cls._instance

    def predict(self, metrics: PodMetrics) -> PredictionResult:
        """Run prediction on a PodMetrics instance."""
        row = self._np.array(
            [[metrics.to_feature_dict()[f] for f in FEATURES]],
            dtype=float
        )
        row_scaled = self._scaler.transform(row)
        pred  = int(self._model.predict(row_scaled)[0])
        proba = float(self._model.predict_proba(row_scaled)[0][1])
        return PredictionResult(
            prediction=pred,
            label="failure" if pred == 1 else "healthy",
            confidence=round(proba, 4),
            metrics=metrics,
        )

    @classmethod
    def is_available(cls) -> bool:
        """True if the model artifacts exist on disk."""
        return os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH)
