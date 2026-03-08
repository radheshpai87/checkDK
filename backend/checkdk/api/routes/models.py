"""
Routes: /models

Exposes Random Forest model metadata (metrics, feature importances) from the
artifacts baked into the Docker image at build time, and handles prediction
requests in-process using RFPredictor.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...auth.dependencies import get_current_user
from ...ml.predictor import ARTIFACTS_DIR as _ARTIFACTS_DIR
from ...ml.predictor import PodMetrics, RFPredictor

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Registry (single trained model) ───────────────────────────────────────────

_REGISTRY = [
    {
        "key": "random_forest",
        "display_name": "Random Forest",
        "algorithm": "RandomForestClassifier (200 trees, balanced weights)",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _read_metrics() -> Optional[Dict[str, Any]]:
    """Read metrics.json saved by train.py; return None if unavailable."""
    path = os.path.join(_ARTIFACTS_DIR, "metrics.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Cannot read metrics.json: %s", exc)
        return None


# ── Schemas ────────────────────────────────────────────────────────────────────

class FeatureImportance(BaseModel):
    feature: str
    importance: float


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: List[List[int]]
    feature_importances: Optional[List[FeatureImportance]] = None


class ModelInfo(BaseModel):
    key: str
    display_name: str
    algorithm: str
    trained: bool
    trained_at: Optional[str] = None
    metrics: Optional[ModelMetrics] = None


class PodMetricsInput(BaseModel):
    cpu_usage: float = Field(..., ge=0.0, le=100.0)
    memory_usage: float = Field(..., ge=0.0, le=100.0)
    disk_usage: float = Field(..., ge=0.0, le=100.0)
    network_latency: float = Field(..., ge=0.0)
    restart_count: int = Field(..., ge=0)
    probe_failures: int = Field(..., ge=0)
    node_cpu_pressure: int = Field(..., ge=0, le=1)
    node_memory_pressure: int = Field(..., ge=0, le=1)
    pod_age_minutes: int = Field(..., ge=0)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/models", response_model=Dict[str, Any])
async def list_models(current_user: dict = Depends(get_current_user)):
    """
    Return metadata and performance metrics for the Random Forest model.
    """
    raw = _read_metrics()
    entry = _REGISTRY[0]

    if raw:
        fi = raw.get("feature_importances")
        model_data: Dict[str, Any] = {
            "key": entry["key"],
            "display_name": entry["display_name"],
            "algorithm": entry["algorithm"],
            "trained": True,
            "trained_at": raw.get("trained_at"),
            "metrics": {
                "accuracy":            raw.get("accuracy"),
                "precision":           raw.get("precision"),
                "recall":              raw.get("recall"),
                "f1":                  raw.get("f1"),
                "roc_auc":             raw.get("roc_auc"),
                "confusion_matrix":    raw.get("confusion_matrix"),
                "feature_importances": fi,
            },
        }
    else:
        model_data = {
            "key":          entry["key"],
            "display_name": entry["display_name"],
            "algorithm":    entry["algorithm"],
            "trained":      RFPredictor.is_available(),
            "trained_at":   None,
            "metrics":      None,
        }

    return {"models": [model_data]}


@router.post("/models/predict/{model_key}", response_model=Dict[str, Any])
async def predict_with_model(
    model_key: str,
    metrics: PodMetricsInput,
    current_user: dict = Depends(get_current_user),
):
    """
    Run a pod failure prediction using the Random Forest model.
    """
    if model_key != "random_forest":
        raise HTTPException(
            status_code=404,
            detail=f"Unknown model key '{model_key}'. Valid: random_forest.",
        )

    predictor = RFPredictor.get()
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Random Forest model artifacts are unavailable. "
                "The model may not have been trained before deployment."
            ),
        )

    pod_metrics = PodMetrics(
        cpu_usage=metrics.cpu_usage,
        memory_usage=metrics.memory_usage,
        disk_usage=metrics.disk_usage,
        network_latency=metrics.network_latency,
        restart_count=metrics.restart_count,
        probe_failures=metrics.probe_failures,
        node_cpu_pressure=metrics.node_cpu_pressure,
        node_memory_pressure=metrics.node_memory_pressure,
        pod_age_minutes=metrics.pod_age_minutes,
    )

    result = predictor.predict(pod_metrics)
    return {
        "model":      "random_forest",
        "prediction": result.prediction,
        "label":      result.label,
        "confidence": result.confidence,
    }
