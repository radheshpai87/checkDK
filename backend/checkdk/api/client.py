"""Thin HTTP client that lets the CLI delegate work to a remote checkDK API.

When $CHECKDK_API_URL is set the CLI will POST config/metrics to the server
instead of running analysis locally.  If the server is unreachable the CLI
falls back to local analysis automatically.
"""

import os
from typing import Optional

import requests

from ..models import AnalysisResult


def get_api_url() -> Optional[str]:
    """Return the API base URL from env (without trailing slash), or None."""
    url = os.getenv("CHECKDK_API_URL", "").strip().rstrip("/")
    return url or None


# ── Analysis helpers ──────────────────────────────────────────────────────────

def analyze_docker_compose_remote(content: str, api_url: str) -> AnalysisResult:
    """POST docker-compose YAML content to the remote API."""
    resp = requests.post(
        f"{api_url}/analyze/docker-compose",
        json={"content": content},
        timeout=60,
    )
    resp.raise_for_status()
    return AnalysisResult.model_validate(resp.json())


def analyze_kubernetes_remote(content: str, api_url: str) -> AnalysisResult:
    """POST Kubernetes manifest YAML content to the remote API."""
    resp = requests.post(
        f"{api_url}/analyze/kubernetes",
        json={"content": content},
        timeout=60,
    )
    resp.raise_for_status()
    return AnalysisResult.model_validate(resp.json())


def predict_remote(metrics: dict, api_url: str) -> dict:
    """POST pod metrics to the remote API and return the raw JSON response."""
    resp = requests.post(
        f"{api_url}/predict",
        json=metrics,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
