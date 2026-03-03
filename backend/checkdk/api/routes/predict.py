"""Prediction route – pod failure risk via Random Forest + LLM."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Request / Response schemas ────────────────────────────────────────────────

class PredictRequest(BaseModel):
    cpu: float = Field(..., ge=0, le=100, description="CPU usage %")
    memory: float = Field(..., ge=0, le=100, description="Memory usage %")
    disk: float = Field(50.0, ge=0, le=100, description="Disk usage %")
    latency: float = Field(10.0, ge=0, description="Network latency in ms")
    restarts: int = Field(0, ge=0, description="Container restart count")
    probe_failures: int = Field(0, ge=0, description="Liveness/readiness probe failures")
    cpu_pressure: int = Field(0, ge=0, le=1, description="Node CPU pressure (0 or 1)")
    mem_pressure: int = Field(0, ge=0, le=1, description="Node memory pressure (0 or 1)")
    age: int = Field(60, ge=0, description="Pod age in minutes")
    service: Optional[str] = Field(None, description="Service/pod name (optional)")
    platform: str = Field("docker", pattern="^(docker|kubernetes)$")
    no_ai: bool = Field(False, description="When true, skip LLM analysis")


class MLPrediction(BaseModel):
    label: str
    confidence: float
    risk_level: str
    is_failure: bool


class LLMAssessment(BaseModel):
    assessment: str
    root_cause: str
    recommendations: list[str]


class PredictResponse(BaseModel):
    prediction: MLPrediction
    assessment: Optional[LLMAssessment] = None


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predict pod / container failure risk",
    description=(
        "Runs a trained Random Forest model against runtime metrics to produce a "
        "failure probability, risk level, and (optionally) an LLM health assessment."
    ),
)
async def predict_endpoint(request: PredictRequest) -> PredictResponse:
    from ...ml.predictor import RFPredictor, PodMetrics

    predictor = RFPredictor.get()
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Random Forest model not loaded. "
                "Train it first with: python -m checkdk.ml.train"
            ),
        )

    metrics = PodMetrics(
        cpu_usage=request.cpu,
        memory_usage=request.memory,
        disk_usage=request.disk,
        network_latency=request.latency,
        restart_count=request.restarts,
        probe_failures=request.probe_failures,
        node_cpu_pressure=request.cpu_pressure,
        node_memory_pressure=request.mem_pressure,
        pod_age_minutes=request.age,
        service_name=request.service,
        platform=request.platform,
    )

    result = predictor.predict(metrics)

    ml_prediction = MLPrediction(
        label=result.label,
        confidence=result.confidence,
        risk_level=result.risk_level,
        is_failure=result.is_failure,
    )

    assessment: Optional[LLMAssessment] = None

    if not request.no_ai:
        try:
            from ...config import get_config
            from ...ai import get_ai_provider

            cfg = get_config()
            if cfg.ai.enabled:
                ai_provider = get_ai_provider(cfg)
                if ai_provider:
                    payload = {
                        "label": result.label,
                        "confidence": result.confidence,
                        "risk_level": result.risk_level,
                        "metrics": metrics.to_feature_dict(),
                        "service_name": request.service,
                        "platform": request.platform,
                    }
                    ai_result = ai_provider.analyze_pod_health(payload)
                    if "error" not in ai_result:
                        assessment = LLMAssessment(
                            assessment=ai_result.get("assessment", ""),
                            root_cause=ai_result.get("root_cause", ""),
                            recommendations=ai_result.get("recommendations", []),
                        )
        except Exception:
            logger.warning("LLM health assessment failed – skipping", exc_info=True)

    return PredictResponse(prediction=ml_prediction, assessment=assessment)
