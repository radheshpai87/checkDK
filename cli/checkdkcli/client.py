"""HTTP client for the checkDK backend API.

All communication between the CLI and the backend happens here.
The base URL is read from $CHECKDK_API_URL (required).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests

_DEFAULT_TIMEOUT = 60  # seconds


def get_api_url() -> str:
    """Return the backend API base URL.

    Priority:
        1. $CHECKDK_API_URL environment variable
        2. ~/.checkdk/.env  (loaded by python-dotenv at startup)
        3. Fallback to https://checkdk.app/api (production) — override with
           CHECKDK_API_URL=http://localhost:8000 for local dev
    """
    url = os.getenv("CHECKDK_API_URL", "https://checkdk.app/api").strip().rstrip("/")
    return url


def get_stored_token() -> Optional[str]:
    """Read a stored JWT from ~/.checkdk/.env, if present."""
    token = os.getenv("CHECKDK_TOKEN")
    if token:
        return token.strip()
    env_file = Path.home() / ".checkdk" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("CHECKDK_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _auth_headers() -> dict:
    """Return Authorization header dict if a token is stored, else empty dict."""
    token = get_stored_token()
    return {"Authorization": f"Bearer {token}"} if token else {}


def _post(path: str, payload: dict, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """POST to the API and return the parsed JSON body.

    Raises requests.HTTPError on non-2xx responses.
    """
    url = f"{get_api_url()}{path}"
    resp = requests.post(url, json=payload, headers=_auth_headers(), timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _get(path: str, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """GET from the API and return the parsed JSON body."""
    url = f"{get_api_url()}{path}"
    resp = requests.get(url, headers=_auth_headers(), timeout=timeout)
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

def analyze_docker_compose(content: str, filename: Optional[str] = None,
                           timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """POST docker-compose YAML content and return the analysis result dict."""
    payload: dict = {"content": content}
    if filename:
        payload["filename"] = filename
    return _post("/analyze/docker-compose", payload, timeout=timeout)


def analyze_kubernetes(content: str, filename: Optional[str] = None,
                       timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """POST Kubernetes manifest YAML content and return the analysis result dict."""
    payload: dict = {"content": content}
    if filename:
        payload["filename"] = filename
    return _post("/analyze/kubernetes", payload, timeout=timeout)


def analyze_playground(content: str, filename: Optional[str] = None,
                       timeout: int = _DEFAULT_TIMEOUT) -> dict:
    """POST any config to the hybrid AI+rules playground endpoint."""
    payload: dict = {"content": content}
    if filename:
        payload["filename"] = filename
    return _post("/analyze/playground", payload, timeout=timeout)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def validate_token(token: str) -> dict:
    """POST a JWT to /auth/cli-token to validate it; returns user info dict."""
    url = f"{get_api_url()}/auth/cli-token"
    resp = requests.post(
        url, json={"token": token},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_current_user() -> dict:
    """GET /auth/me — returns current user info (requires stored token)."""
    return _get("/auth/me", timeout=10)


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
    timeout: int = 30,
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
        timeout=timeout,
    )
