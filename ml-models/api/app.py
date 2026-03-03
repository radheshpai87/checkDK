"""
FastAPI inference server for pod/container failure detection.

Exposes individual model endpoints and an ensemble endpoint.

Endpoints:
    GET  /health                  - Health check
    POST /predict/random-forest   - Random Forest prediction
    POST /predict/xgboost         - XGBoost prediction
    POST /predict/lstm            - LSTM prediction (requires PyTorch models)
    POST /predict/ensemble        - Majority-vote ensemble of all loaded models
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add api/ dir (for schemas) and models/ dir to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")
sys.path.insert(0, BASE_DIR)       # so `schemas` is importable
sys.path.insert(0, MODELS_DIR)     # so model packages are importable

from schemas import PodMetrics, PredictionResult, EnsembleResult

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy model registry
# ---------------------------------------------------------------------------
_predictors: Dict[str, object] = {}


def _load_models():
    """Attempt to load each model; skip gracefully on missing artifacts."""

    # Random Forest
    try:
        from random_forest.predict import RFPredictor
        _predictors["random_forest"] = RFPredictor()
        logger.info("Random Forest model loaded.")
    except FileNotFoundError as e:
        logger.warning(f"Random Forest not loaded: {e}")
    except Exception as e:
        logger.error(f"Random Forest load error: {e}")

    # XGBoost
    try:
        from xgboost_model.predict import XGBPredictor
        _predictors["xgboost"] = XGBPredictor()
        logger.info("XGBoost model loaded.")
    except FileNotFoundError as e:
        logger.warning(f"XGBoost not loaded: {e}")
    except Exception as e:
        logger.error(f"XGBoost load error: {e}")

    # LSTM (optional – requires PyTorch)
    try:
        from lstm_model.predict import LSTMPredictor
        _predictors["lstm"] = LSTMPredictor()
        logger.info("LSTM model loaded.")
    except FileNotFoundError as e:
        logger.warning(f"LSTM not loaded: {e}")
    except ImportError:
        logger.warning("PyTorch not installed – LSTM model skipped.")
    except Exception as e:
        logger.error(f"LSTM load error: {e}")


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ML models...")
    _load_models()
    loaded = list(_predictors.keys())
    logger.info(f"Models ready: {loaded if loaded else 'NONE – run train_all.py first'}")
    yield
    _predictors.clear()
    logger.info("Models unloaded.")


app = FastAPI(
    title="Pod Failure Detection API",
    description=(
        "ML-powered API to detect potential pod/container failures "
        "in Docker and Kubernetes workloads."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_predictor(name: str):
    predictor = _predictors.get(name)
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Model '{name}' is not available. "
                "Run train_all.py to train and save models first."
            ),
        )
    return predictor


def _to_result(model_name: str, raw: dict) -> PredictionResult:
    return PredictionResult(model=model_name, **raw)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health():
    """Returns which models are currently loaded."""
    return {
        "status": "ok",
        "loaded_models": list(_predictors.keys()),
    }


@app.post("/predict/random-forest", response_model=PredictionResult, tags=["Predict"])
def predict_rf(metrics: PodMetrics):
    """Run Random Forest prediction on pod metrics."""
    predictor = _get_predictor("random_forest")
    result = predictor.predict(metrics.model_dump())
    return _to_result("random_forest", result)


@app.post("/predict/xgboost", response_model=PredictionResult, tags=["Predict"])
def predict_xgb(metrics: PodMetrics):
    """Run XGBoost prediction on pod metrics."""
    predictor = _get_predictor("xgboost")
    result = predictor.predict(metrics.model_dump())
    return _to_result("xgboost", result)


@app.post("/predict/lstm", response_model=PredictionResult, tags=["Predict"])
def predict_lstm(metrics: PodMetrics):
    """Run LSTM prediction on pod metrics (requires PyTorch)."""
    predictor = _get_predictor("lstm")
    result = predictor.predict(metrics.model_dump())
    return _to_result("lstm", result)


@app.post("/predict/ensemble", response_model=EnsembleResult, tags=["Predict"])
def predict_ensemble(metrics: PodMetrics):
    """
    Run all available models and return a majority-vote ensemble result.

    Confidence is the average failure probability across loaded models.
    Requires at least one model to be loaded.
    """
    if not _predictors:
        raise HTTPException(
            status_code=503,
            detail="No models loaded. Run train_all.py first.",
        )

    data = metrics.model_dump()
    results: Dict[str, Optional[PredictionResult]] = {
        "random_forest": None,
        "xgboost": None,
        "lstm": None,
    }

    confidences = []
    for name, predictor in _predictors.items():
        raw = predictor.predict(data)
        results[name] = _to_result(name, raw)
        confidences.append(raw["confidence"])

    avg_conf = sum(confidences) / len(confidences)
    ensemble_label = "failure" if avg_conf >= 0.5 else "healthy"

    return EnsembleResult(
        random_forest=results["random_forest"],
        xgboost=results["xgboost"],
        lstm=results["lstm"],
        ensemble_label=ensemble_label,
        ensemble_confidence=round(avg_conf, 4),
    )
