"""Real-time WebSocket monitor endpoint.

Clients (e.g. ``checkdk monitor docker``) stream pod/container metrics as
JSON frames and receive back a prediction for every frame.

Protocol
--------
Client → Server (JSON per message):
    {
        "cpu_usage":         <float 0-100>,
        "memory_usage":      <float 0-100>,
        "disk_usage":        <float 0-100>,   // optional, default 50.0
        "network_latency":   <float ms>,      // optional, default 0.0
        "restart_count":     <int>,           // optional, default 0
        "probe_failures":    <int>,           // optional, default 0
        "cpu_pressure":      <int 0|1>,       // optional, default 0
        "memory_pressure":   <int 0|1>,       // optional, default 0
        "pod_age_minutes":   <int>,           // optional, default 60
        "service_name":      <str|null>       // optional
    }

Server → Client (JSON per message):
    {
        "label":       "healthy" | "failure",
        "confidence":  <float>,
        "risk_level":  "low" | "medium" | "high" | "critical",
        "is_failure":  <bool>
    }
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


def _risk_level(confidence: float, label: str) -> str:
    if label == "healthy":
        if confidence < 0.3:
            return "low"
        return "medium"
    else:
        if confidence >= 0.9:
            return "critical"
        if confidence >= 0.7:
            return "high"
        return "medium"


@router.websocket("/ws/monitor")
async def monitor_websocket(websocket: WebSocket) -> None:
    """Stream pod metrics in and receive failure predictions."""
    await websocket.accept()
    client = websocket.client
    logger.info("Monitor WS connected: %s:%s", client.host if client else "?", client.port if client else "?")

    try:
        # Lazy-import to avoid hard failure when ML artifacts aren't present.
        from ...ml.predictor import PodMetrics, Predictor

        predictor = Predictor()
        model_loaded = True
    except Exception as exc:
        logger.warning("ML predictor unavailable: %s", exc)
        model_loaded = False

    try:
        while True:
            data: dict = await websocket.receive_json()

            if not model_loaded:
                await websocket.send_json({
                    "error": "ML model not available",
                    "label": "unknown",
                    "confidence": 0.0,
                    "risk_level": "unknown",
                    "is_failure": False,
                })
                continue

            try:
                metrics = PodMetrics(
                    cpu_usage=float(data.get("cpu_usage", 0)),
                    memory_usage=float(data.get("memory_usage", 0)),
                    disk_usage=float(data.get("disk_usage", 50.0)),
                    network_latency=float(data.get("network_latency", 0.0)),
                    restart_count=int(data.get("restart_count", 0)),
                    probe_failures=int(data.get("probe_failures", 0)),
                    node_cpu_pressure=int(data.get("cpu_pressure", 0)),
                    node_memory_pressure=int(data.get("memory_pressure", 0)),
                    pod_age_minutes=int(data.get("pod_age_minutes", 60)),
                    service_name=data.get("service_name"),
                )
                result = predictor.predict(metrics)
                await websocket.send_json({
                    "label":      result.label,
                    "confidence": round(result.confidence, 4),
                    "risk_level": _risk_level(result.confidence, result.label),
                    "is_failure": result.is_failure,
                })
            except Exception as exc:
                logger.exception("Prediction error: %s", exc)
                await websocket.send_json({
                    "error": str(exc),
                    "label": "unknown",
                    "confidence": 0.0,
                    "risk_level": "unknown",
                    "is_failure": False,
                })

    except WebSocketDisconnect:
        logger.info("Monitor WS disconnected")
    except Exception as exc:
        logger.exception("Monitor WS error: %s", exc)
        try:
            await websocket.close()
        except Exception:
            pass
