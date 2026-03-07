"""
Routes: /models

Exposes ML model metadata (metrics, feature importances) by reading metrics.json
files written by the training scripts, and proxies prediction requests to the
standalone ml-models inference service.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Configuration ──────────────────────────────────────────────────────────────

# Path where ./ml-models/models/ is bind-mounted (read-only) into the backend.
ML_MODELS_DIR = os.getenv("ML_MODELS_DIR", "/app/ml_models_data")

# Internal Docker hostname for the ml-models FastAPI inference service.
ML_MODELS_API_URL = os.getenv("ML_MODELS_API_URL", "http://ml-models:8000")

# Registry: (key used in API) → (subdirectory name, display info)
_REGISTRY = [
    {
        "key": "random_forest",
        "display_name": "Random Forest",
        "algorithm": "RandomForestClassifier (200 trees, balanced)",
        "dir": "random_forest",
        "endpoint": "random-forest",
    },
    {
        "key": "xgboost",
        "display_name": "XGBoost",
        "algorithm": "XGBClassifier (300 trees, lr=0.05, hist)",
        "dir": "xgboost_model",
        "endpoint": "xgboost",
    },
    {
        "key": "lstm",
        "display_name": "LSTM",
        "algorithm": "Stacked LSTM (2 layers, hidden=64, dropout=0.3)",
        "dir": "lstm_model",
        "endpoint": "lstm",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _read_metrics(model_dir: str) -> Optional[Dict[str, Any]]:
    """Read metrics.json for a model; return None if not found or unreadable."""
    path = Path(ML_MODELS_DIR) / model_dir / "metrics.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Corrupt metrics.json for %s: %s", model_dir, exc)
        return None
    except OSError as exc:
        logger.error("Cannot read metrics.json for %s: %s", model_dir, exc)
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
    Return metadata and performance metrics for all three ML models.
    Models that haven't been trained yet return `trained: false`.
    """
    result: List[Dict[str, Any]] = []

    for entry in _REGISTRY:
        raw = _read_metrics(entry["dir"])
        if raw:
            fi = raw.get("feature_importances")
            result.append({
                "key": entry["key"],
                "display_name": entry["display_name"],
                "algorithm": entry["algorithm"],
                "trained": True,
                "trained_at": raw.get("trained_at"),
                "metrics": {
                    "accuracy": raw.get("accuracy"),
                    "precision": raw.get("precision"),
                    "recall": raw.get("recall"),
                    "f1": raw.get("f1"),
                    "roc_auc": raw.get("roc_auc"),
                    "confusion_matrix": raw.get("confusion_matrix"),
                    "feature_importances": fi,
                },
            })
        else:
            result.append({
                "key": entry["key"],
                "display_name": entry["display_name"],
                "algorithm": entry["algorithm"],
                "trained": False,
                "trained_at": None,
                "metrics": None,
            })

    return {"models": result}


@router.post("/models/predict/{model_key}", response_model=Dict[str, Any])
async def predict_with_model(model_key: str, metrics: PodMetricsInput, current_user: dict = Depends(get_current_user)):
    """
    Proxy a prediction request to the ml-models inference service.
    model_key: one of 'random_forest', 'xgboost', or 'lstm'.
    """
    entry = next((e for e in _REGISTRY if e["key"] == model_key), None)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown model key '{model_key}'. Valid: random_forest, xgboost, lstm.",
        )

    url = f"{ML_MODELS_API_URL}/predict/{entry['endpoint']}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json=metrics.model_dump())
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="ML models service is unavailable. Start it with docker compose up.",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=503,
                detail="ML models service timed out. The model may still be loading.",
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.text,
            )
