"""Analysis routes – Docker Compose and Kubernetes manifest validation."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models import AnalysisResult

router = APIRouter()


class AnalyzeRequest(BaseModel):
    content: str  # Raw YAML content of the config file


# ── Docker Compose ────────────────────────────────────────────────────────────

@router.post(
    "/docker-compose",
    response_model=AnalysisResult,
    summary="Analyse a Docker Compose file",
    description=(
        "Pass the raw YAML content of a `docker-compose.yml` and get back a full "
        "list of issues, severities, and AI-enhanced fix suggestions."
    ),
)
async def analyze_docker_compose_endpoint(request: AnalyzeRequest) -> AnalysisResult:
    # Write to a temp file so existing parser logic can use a file path
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(request.content)
        tmp.close()

        from ...services.analysis import analyze_docker_compose

        result = analyze_docker_compose(Path(tmp.name), use_ai=True)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── Kubernetes ────────────────────────────────────────────────────────────────

@router.post(
    "/kubernetes",
    response_model=AnalysisResult,
    summary="Analyse a Kubernetes manifest",
    description=(
        "Pass the raw YAML content of any Kubernetes manifest (Deployment, Service, "
        "ConfigMap, …) and get back issues and AI-powered fix suggestions."
    ),
)
async def analyze_kubernetes_endpoint(request: AnalyzeRequest) -> AnalysisResult:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(request.content)
        tmp.close()

        from ...services.analysis import analyze_kubernetes

        result = analyze_kubernetes(tmp.name)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
