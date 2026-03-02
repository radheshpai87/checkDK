"""
Pydantic request / response schemas for the inference API.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class PodMetrics(BaseModel):
    """Metrics collected from a running pod or container."""

    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage (0-100)")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage (0-100)")
    disk_usage: float = Field(..., ge=0.0, le=100.0, description="Disk usage percentage (0-100)")
    network_latency: float = Field(..., ge=0.0, description="Network latency in milliseconds")
    restart_count: int = Field(..., ge=0, description="Number of container restarts")
    probe_failures: int = Field(..., ge=0, description="Number of liveness/readiness probe failures")
    node_cpu_pressure: int = Field(..., ge=0, le=1, description="Node under CPU pressure (0 or 1)")
    node_memory_pressure: int = Field(..., ge=0, le=1, description="Node under memory pressure (0 or 1)")
    pod_age_minutes: int = Field(..., ge=0, description="Pod age in minutes")

    model_config = {
        "json_schema_extra": {
            "example": {
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
        }
    }


class PredictionResult(BaseModel):
    model: str
    prediction: int
    label: Literal["healthy", "failure"]
    confidence: float = Field(..., description="Probability of failure [0, 1]")


class EnsembleResult(BaseModel):
    random_forest: PredictionResult
    xgboost: PredictionResult
    lstm: Optional[PredictionResult] = None
    ensemble_label: Literal["healthy", "failure"]
    ensemble_confidence: float
