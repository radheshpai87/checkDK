"""HTTP client for the checkDK backend API.

All communication between the CLI and the backend happens here.
The base URL is read from $CHECKDK_API_URL (required).
"""

from __future__ import annotations

import os
from typing import Optional

import requests

_DEFAULT_TIMEOUT = 60  # seconds


def get_api_url() -> str:
    """Return the backend API base URL.

    Priority:
        1. $CHECKDK_API_URL environment variable
        2. ~/.checkdk/.env  (loaded by python-dotenv at startup)
        3. Fallback to http://localhost:8000 so local dev works without config
    """
    url = os.getenv("CHECKDK_API_URL", "http://localhost:8000").strip().rstrip("/")
    return url


def _post(path: str, payload: dict, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """POST to the API and return the parsed JSON body.

    Raises requests.HTTPError on non-2xx responses.
    """
    url = f"{get_api_url()}{path}"
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def health_check() -> bool:
    """Return True if the backend is reachable and healthy."""
    try:
        resp = requests.get(f"{get_api_url()}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ── Analysis helpers ──────────────────────────────────────────────────────────

def analyze_docker_compose(content: str) -> dict:
    """POST docker-compose YAML content and return the analysis result dict."""
    return _post("/analyze/docker-compose", {"content": content})


def analyze_kubernetes(content: str) -> dict:
    """POST Kubernetes manifest YAML content and return the analysis result dict."""
    return _post("/analyze/kubernetes", {"content": content})


# ── Pod health prediction ─────────────────────────────────────────────────────

def predict_pod_health(
    cpu: float,
    memory: float,
    disk: float = 50.0,
    latency: float = 10.0,
    restarts: int = 0,
    probe_failures: int = 0,
    cpu_pressure: int = 0,
    mem_pressure: int = 0,
    age: int = 60,
    service: Optional[str] = None,
    platform: str = "docker",
    no_ai: bool = False,
) -> dict:
    """POST pod metrics to the /predict endpoint and return the result dict."""
    return _post(
        "/predict",
        {
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "latency": latency,
            "restarts": restarts,
            "probe_failures": probe_failures,
            "cpu_pressure": cpu_pressure,
            "mem_pressure": mem_pressure,
            "age": age,
            "service": service,
            "platform": platform,
            "no_ai": no_ai,
        },
        timeout=30,
    )
