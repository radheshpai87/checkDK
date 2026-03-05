"""Analysis routes – Docker Compose, Kubernetes, and hybrid Playground."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ...auth.dependencies import get_optional_user
from ...db.dynamodb import save_history
from ...models import (
    AnalysisResult,
    PlaygroundHighlight,
    PlaygroundIssue,
    PlaygroundResult,
)

router = APIRouter()
logger = logging.getLogger(__name__)

_MAX_CONTENT_BYTES = 1_048_576  # 1 MB


class AnalyzeRequest(BaseModel):
    content: str  # Raw YAML content of the config file
    filename: Optional[str] = Field(
        None,
        description="Optional filename hint (e.g. 'docker-compose.yml', 'deployment.yaml')",
    )


# ── History helpers ────────────────────────────────────────────────────────────

def _analysis_result_to_history_data(result: "AnalysisResult") -> dict:
    """Derive score / status / topCategories from a rule-based AnalysisResult."""
    issues = result.issues or []
    total = len(issues)

    # Severity → weight for score
    severity_weight = {"critical": 20, "high": 10, "medium": 5, "low": 2, "info": 0}
    penalty = sum(severity_weight.get(str(i.severity).lower(), 0) for i in issues)
    score = max(0, min(100, 100 - penalty))

    if score >= 80:
        hist_status = "good"
    elif score >= 50:
        hist_status = "warning"
    else:
        hist_status = "critical"

    # Collect top issue types as category strings
    from collections import Counter
    cat_counter: Counter = Counter()
    for issue in issues:
        cat = str(issue.type).lower().replace("issuetype.", "")
        cat_counter[cat] += 1
    top_categories = [cat for cat, _ in cat_counter.most_common(3)]

    return {"score": score, "status": hist_status, "top_categories": top_categories, "issue_count": total}


class PlaygroundRequest(BaseModel):
    """Request body for the LLM-powered playground analysis."""
    content: str = Field(..., description="Raw config content to audit")
    filename: Optional[str] = Field(
        None,
        description="Optional filename hint (e.g. 'docker-compose.yml', 'deployment.yaml')",
    )


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
async def analyze_docker_compose_endpoint(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> AnalysisResult:
    # Write to a temp file so existing parser logic can use a file path
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(request.content)
        tmp.close()

        from ...services.analysis import analyze_docker_compose

        result = analyze_docker_compose(Path(tmp.name), use_ai=True)

        if current_user:
            hist = _analysis_result_to_history_data(result)
            background_tasks.add_task(
                save_history,
                user_id=current_user["sub"],
                config_type="docker-compose",
                filename=request.filename,
                score=hist["score"],
                status=hist["status"],
                issue_count=hist["issue_count"],
                top_categories=hist["top_categories"],
            )

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
async def analyze_kubernetes_endpoint(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> AnalysisResult:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(request.content)
        tmp.close()

        from ...services.analysis import analyze_kubernetes

        result = analyze_kubernetes(tmp.name)

        if current_user:
            hist = _analysis_result_to_history_data(result)
            background_tasks.add_task(
                save_history,
                user_id=current_user["sub"],
                config_type="kubernetes",
                filename=request.filename,
                score=hist["score"],
                status=hist["status"],
                issue_count=hist["issue_count"],
                top_categories=hist["top_categories"],
            )

        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ═════════════════════════════════════════════════════════════════════════════
# Hybrid Playground — LLM primary, rule-based secondary
# ═════════════════════════════════════════════════════════════════════════════


# ── Config-type detection ────────────────────────────────────────────────────

def _detect_config_type(content: str, filename: str | None) -> str:
    """Return 'docker-compose', 'kubernetes', or 'unknown'."""
    fname = (filename or "").lower()
    if any(k in fname for k in ("compose", "docker")):
        return "docker-compose"
    if any(k in fname for k in ("deploy", "service", "pod", "stateful", "daemon",
                                 "job", "ingress", "k8s", "kube")):
        return "kubernetes"
    # Sniff content
    if "apiVersion" in content and "kind" in content:
        return "kubernetes"
    if "services:" in content:
        return "docker-compose"
    return "unknown"


# ── Rule-based validators ───────────────────────────────────────────────────

def _find_line(lines: list[str], needle: str) -> int | None:
    """Find 1-based line number containing *needle*."""
    if not needle:
        return None
    for i, line in enumerate(lines):
        if needle in line:
            return i + 1
    return None


def _run_rule_based(content: str, filename: str | None) -> list[PlaygroundIssue]:
    """Run deterministic validators and return issues as PlaygroundIssue."""
    issues: list[PlaygroundIssue] = []
    config_type = _detect_config_type(content, filename)

    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        issues.append(PlaygroundIssue(
            severity="critical",
            title="Invalid YAML syntax",
            description=f"Failed to parse YAML: {exc}",
            line=mark.line + 1 if mark else None,
            recommendation="Fix the YAML syntax errors before deploying.",
            category="syntax",
        ))
        return issues

    if not isinstance(parsed, dict):
        issues.append(PlaygroundIssue(
            severity="critical",
            title="Invalid configuration",
            description="The YAML content is not a valid configuration object.",
            recommendation="Ensure the file contains a valid Docker Compose or Kubernetes manifest.",
            category="syntax",
        ))
        return issues

    if config_type == "docker-compose":
        issues.extend(_validate_compose(parsed, content))
    elif config_type == "kubernetes":
        issues.extend(_validate_kubernetes(parsed, content))

    return issues


def _validate_compose(parsed: dict, content: str) -> list[PlaygroundIssue]:
    issues: list[PlaygroundIssue] = []
    services = parsed.get("services", {})
    if not services:
        issues.append(PlaygroundIssue(
            severity="high", title="No services defined",
            description="Docker Compose file has no services.",
            recommendation="Add at least one service under the 'services:' key.",
            category="structure",
        ))
        return issues

    lines = content.splitlines()
    seen_ports: dict[str, str] = {}

    for svc, cfg in services.items():
        if not isinstance(cfg, dict):
            continue

        # Missing image / build
        if "image" not in cfg and "build" not in cfg:
            issues.append(PlaygroundIssue(
                severity="critical",
                title=f"'{svc}' has no image or build",
                description=f"Service '{svc}' must specify 'image' or 'build'.",
                line=_find_line(lines, svc),
                recommendation=f"Add 'image: <name>' or 'build: .' to '{svc}'.",
                category="missing_image",
            ))

        # :latest tag
        image = cfg.get("image", "")
        if image and (":latest" in image or (":" not in image and image)):
            issues.append(PlaygroundIssue(
                severity="medium",
                title=f"'{svc}' uses unpinned image tag",
                description=f"Image '{image}' uses ':latest' or no tag, making builds non-reproducible.",
                line=_find_line(lines, image),
                recommendation="Pin a specific version, e.g. 'nginx:1.25.3'.",
                category="image_tag",
            ))

        # Port conflicts
        for port_def in cfg.get("ports", []):
            parts = str(port_def).split(":")
            if len(parts) >= 2:
                host_port = parts[-2]
                try:
                    int(host_port)
                except ValueError:
                    continue
                if host_port in seen_ports and seen_ports[host_port] != svc:
                    issues.append(PlaygroundIssue(
                        severity="critical",
                        title=f"Port {host_port} conflict",
                        description=f"Host port {host_port} used by both '{seen_ports[host_port]}' and '{svc}'.",
                        line=_find_line(lines, str(port_def)),
                        recommendation="Change one of the services to a different host port.",
                        category="port_conflict",
                    ))
                seen_ports[host_port] = svc

        # Privileged
        if cfg.get("privileged"):
            issues.append(PlaygroundIssue(
                severity="high",
                title=f"'{svc}' runs in privileged mode",
                description="Privileged mode gives full host access — a major security risk.",
                line=_find_line(lines, "privileged"),
                recommendation="Remove 'privileged: true'. Use specific capabilities instead.",
                category="security",
            ))

        # Hardcoded secrets in environment
        env = cfg.get("environment", [])
        env_list = env if isinstance(env, list) else [f"{k}={v}" for k, v in env.items()] if isinstance(env, dict) else []
        secret_keys = ("password", "secret", "key", "token", "api_key", "apikey")
        for entry in env_list:
            entry_str = str(entry)
            if "=" in entry_str:
                key, _, val = entry_str.partition("=")
                if any(s in key.lower() for s in secret_keys) and val and not val.startswith("${"):
                    issues.append(PlaygroundIssue(
                        severity="high",
                        title=f"Hardcoded secret in '{svc}'",
                        description=f"Environment variable '{key}' contains a hardcoded value.",
                        line=_find_line(lines, entry_str),
                        recommendation=f"Use a variable reference like ${{{key}}} or Docker secrets.",
                        category="hardcoded_secret",
                    ))

        # No resource limits
        deploy = cfg.get("deploy", {})
        resources = deploy.get("resources", {}) if isinstance(deploy, dict) else {}
        if not resources.get("limits") if isinstance(resources, dict) else True:
            issues.append(PlaygroundIssue(
                severity="medium",
                title=f"No resource limits for '{svc}'",
                description=f"Service '{svc}' has no CPU/memory limits — risk of resource exhaustion.",
                line=_find_line(lines, svc),
                recommendation="Add deploy.resources.limits with cpus and memory.",
                category="resource_limits",
            ))

        # No healthcheck
        if "healthcheck" not in cfg:
            issues.append(PlaygroundIssue(
                severity="low",
                title=f"No healthcheck for '{svc}'",
                description=f"Without a healthcheck, Docker can't detect if '{svc}' is actually healthy.",
                line=_find_line(lines, svc),
                recommendation="Add a healthcheck with test, interval, timeout, and retries.",
                category="health_check",
            ))

    return issues


def _validate_kubernetes(parsed: dict, content: str) -> list[PlaygroundIssue]:
    issues: list[PlaygroundIssue] = []
    lines = content.splitlines()
    kind = parsed.get("kind", "")
    containers = _extract_k8s_containers(parsed)

    for c in containers:
        name = c.get("name", "unnamed")
        image = c.get("image", "")

        # Unpinned image tag
        if image and (":latest" in image or ":" not in image):
            issues.append(PlaygroundIssue(
                severity="high",
                title=f"Unpinned image tag: {image}",
                description="Using ':latest' or no tag makes deployments non-reproducible.",
                line=_find_line(lines, image) or _find_line(lines, "image:"),
                recommendation="Pin a specific version, e.g. 'nginx:1.25.3'.",
                category="image_tag",
            ))

        # No resource requests/limits
        if not c.get("resources"):
            issues.append(PlaygroundIssue(
                severity="medium",
                title=f"No resource limits for '{name}'",
                description="Without limits a container can consume all node resources.",
                line=_find_line(lines, name),
                recommendation="Add resources.requests and resources.limits for cpu and memory.",
                category="resource_limits",
            ))

        # No probes
        if not c.get("livenessProbe") and not c.get("readinessProbe"):
            issues.append(PlaygroundIssue(
                severity="medium",
                title=f"No liveness/readiness probes for '{name}'",
                description="Kubernetes can't detect if the app is healthy or ready.",
                line=_find_line(lines, name),
                recommendation="Add livenessProbe and readinessProbe to the container spec.",
                category="health_check",
            ))

        # Running as root
        sc = c.get("securityContext", {}) or {}
        if not sc.get("runAsNonRoot") and not sc.get("runAsUser"):
            issues.append(PlaygroundIssue(
                severity="medium",
                title=f"'{name}' may run as root",
                description="Running as root inside a container is a security risk.",
                line=_find_line(lines, name),
                recommendation="Set securityContext.runAsNonRoot: true and runAsUser to a non-zero UID.",
                category="security",
            ))

        # Privileged container
        if sc.get("privileged"):
            issues.append(PlaygroundIssue(
                severity="critical",
                title=f"'{name}' runs in privileged mode",
                description="Privileged containers have full host access.",
                line=_find_line(lines, "privileged"),
                recommendation="Remove securityContext.privileged or set it to false.",
                category="security",
            ))

    # Single replica
    if kind == "Deployment":
        replicas = (parsed.get("spec") or {}).get("replicas", 1)
        if replicas == 1:
            issues.append(PlaygroundIssue(
                severity="low",
                title="Single replica deployment",
                description="1 replica = zero HA. Any pod failure causes downtime.",
                line=_find_line(lines, "replicas"),
                recommendation="Set replicas to at least 2 for production workloads.",
                category="availability",
            ))

    # Host networking
    pod_spec = _extract_pod_spec(parsed)
    if pod_spec and pod_spec.get("hostNetwork"):
        issues.append(PlaygroundIssue(
            severity="high",
            title="Host networking enabled",
            description="hostNetwork: true exposes the pod on the host's network stack.",
            line=_find_line(lines, "hostNetwork"),
            recommendation="Remove hostNetwork: true unless absolutely required.",
            category="security",
        ))

    return issues


def _extract_k8s_containers(parsed: dict) -> list[dict]:
    """Pull container specs from any common K8s resource."""
    containers: list[dict] = []
    spec = parsed.get("spec", {})
    if not isinstance(spec, dict):
        return containers
    # Pod
    containers.extend(spec.get("containers", []))
    # Deployment / StatefulSet / DaemonSet / Job
    template = spec.get("template", {})
    if isinstance(template, dict):
        tspec = template.get("spec", {})
        if isinstance(tspec, dict):
            containers.extend(tspec.get("containers", []))
            containers.extend(tspec.get("initContainers", []))
    # CronJob
    jt = spec.get("jobTemplate", {})
    if isinstance(jt, dict):
        jspec = jt.get("spec", {}).get("template", {}).get("spec", {})
        if isinstance(jspec, dict):
            containers.extend(jspec.get("containers", []))
    return containers


def _extract_pod_spec(parsed: dict) -> dict | None:
    """Return the pod-level spec dict (for hostNetwork etc.)."""
    spec = parsed.get("spec", {})
    if not isinstance(spec, dict):
        return None
    template = spec.get("template", {})
    if isinstance(template, dict):
        return template.get("spec")
    if "containers" in spec:
        return spec
    return None


# ── Merge logic ──────────────────────────────────────────────────────────────

def _merge_results(
    llm_result: PlaygroundResult | None,
    rule_issues: list[PlaygroundIssue],
) -> PlaygroundResult:
    """
    Merge LLM (primary) + rule-based (secondary).
    LLM issues win when there's overlap.  Rule-based issues fill gaps.
    """
    if llm_result is None:
        # Total LLM failure → pure rule-based
        score = _score_from_rules(rule_issues)
        return PlaygroundResult(
            score=score,
            status=_status_from_score(score),
            summary=_summary_from_rules(rule_issues),
            issues=rule_issues,
            highlights=[],
            provider="rule-engine",
        )

    if not rule_issues:
        return llm_result

    # Categories the LLM already covers
    llm_categories: set[str] = set()
    llm_titles_lower: set[str] = set()
    for iss in llm_result.issues:
        if iss.category:
            llm_categories.add(iss.category)
        llm_titles_lower.add(iss.title.lower().strip())

    added: list[PlaygroundIssue] = []
    for ri in rule_issues:
        if ri.category and ri.category in llm_categories:
            continue
        if ri.title.lower().strip() in llm_titles_lower:
            continue
        core = _extract_core(ri.title)
        if core and any(core in t for t in llm_titles_lower):
            continue
        added.append(ri)

    merged_issues = list(llm_result.issues) + added

    # Adjust score down if rules found critical/high issues LLM missed
    score = llm_result.score
    critical_missed = sum(1 for i in added if i.severity in ("critical", "high"))
    if critical_missed:
        score = max(0, round(score - critical_missed * 1.5))

    prov = llm_result.provider or "llm"

    return PlaygroundResult(
        score=score,
        status=_status_from_score(score),
        summary=llm_result.summary,
        issues=merged_issues,
        highlights=llm_result.highlights or [],
        provider=f"{prov}+rules" if added else prov,
    )


def _extract_core(title: str) -> str | None:
    skip = {"no", "missing", "service", "container", "the", "a", "an", "for", "has", "is", "in", "uses"}
    for w in title.lower().replace("'", "").replace('"', '').split():
        if len(w) > 3 and w not in skip:
            return w
    return None


def _score_from_rules(issues: list[PlaygroundIssue]) -> int:
    score = 100
    for i in issues:
        sev = i.severity
        if sev == "critical":
            score -= 20
        elif sev == "high":
            score -= 12
        elif sev == "medium":
            score -= 6
        elif sev == "low":
            score -= 2
    return max(0, score)


def _status_from_score(score: int | float) -> str:
    if score >= 80:
        return "secure"
    if score >= 50:
        return "warning"
    return "critical"


def _summary_from_rules(issues: list[PlaygroundIssue]) -> str:
    if not issues:
        return "No issues detected by rule-based analysis. Config looks clean."
    crit = sum(1 for i in issues if i.severity == "critical")
    high = sum(1 for i in issues if i.severity == "high")
    med = sum(1 for i in issues if i.severity == "medium")
    low = sum(1 for i in issues if i.severity == "low")
    parts = []
    if crit: parts.append(f"{crit} critical")
    if high: parts.append(f"{high} high")
    if med:  parts.append(f"{med} medium")
    if low:  parts.append(f"{low} low")
    total = len(issues)
    return f"Rule-based analysis found {total} issue{'s' if total != 1 else ''} ({', '.join(parts)})."


# ── Playground endpoint ──────────────────────────────────────────────────────

@router.post(
    "/playground",
    response_model=PlaygroundResult,
    summary="Hybrid config audit (LLM + rules)",
    description=(
        "Send any Docker Compose, Kubernetes, or AWS config and receive an "
        "AI-generated audit (primary) supplemented by deterministic rule-based "
        "checks (secondary). If LLM providers fail, falls back to pure rule-based."
    ),
)
async def analyze_playground_endpoint(
    request: PlaygroundRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> PlaygroundResult:
    if len(request.content.encode("utf-8")) > _MAX_CONTENT_BYTES:
        raise HTTPException(status_code=413, detail="Content exceeds 1 MB limit")

    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Empty content")

    filename = request.filename

    # ── Step 1: LLM analysis (primary, with per-provider fallback) ────────────
    llm_result: PlaygroundResult | None = None

    def _call_provider(prov) -> "PlaygroundResult | None":
        """Call analyze_config and normalise the result. Returns None on failure."""
        try:
            raw = prov.analyze_config(content, filename=filename)
        except Exception as exc:
            logger.warning("Provider %s raised during analyze_config: %s", type(prov).__name__, exc)
            return None
        if not isinstance(raw, dict) or "error" in raw:
            logger.warning("Provider %s returned error/bad response: %s", type(prov).__name__, raw)
            return None
        norm_issues = []
        for ri in raw.get("issues", []):
            if isinstance(ri, dict):
                norm_issues.append(PlaygroundIssue(
                    severity=ri.get("severity", "info"),
                    title=ri.get("title", "Untitled"),
                    description=ri.get("description", ""),
                    line=ri.get("line"),
                    recommendation=ri.get("recommendation") or ri.get("suggestion"),
                    category=ri.get("category"),
                ))
        norm_highlights = []
        for rh in raw.get("highlights", []):
            if isinstance(rh, dict):
                norm_highlights.append(PlaygroundHighlight(
                    type=rh.get("type"),
                    text=rh.get("text"),
                    title=rh.get("title"),
                    description=rh.get("description"),
                ))
        return PlaygroundResult(
            score=raw.get("score", 50),
            status=raw.get("status", "warning"),
            summary=raw.get("summary", ""),
            issues=norm_issues,
            highlights=norm_highlights,
            provider=raw.get("provider", "llm"),
        )

    try:
        from ...ai.providers import get_ai_provider, MistralProvider, GroqProvider

        provider = get_ai_provider()
        if provider is not None:
            llm_result = _call_provider(provider)
            # If primary failed, try the other provider explicitly
            if llm_result is None:
                logger.warning("Primary provider %s failed — trying fallback", type(provider).__name__)
                if isinstance(provider, MistralProvider):
                    fallback = GroqProvider()
                else:
                    fallback = MistralProvider()
                if fallback.is_available():
                    llm_result = _call_provider(fallback)
    except Exception as exc:
        logger.warning("LLM analysis failed, falling back to rules: %s", exc)

    # ── Step 2: Rule-based analysis (secondary) ────────────────────────────
    rule_issues: list[PlaygroundIssue] = []
    try:
        rule_issues = _run_rule_based(content, filename)
    except Exception as exc:
        logger.warning("Rule-based analysis failed: %s", exc)

    # ── Step 3: Merge ──────────────────────────────────────────────────────
    final_result = _merge_results(llm_result, rule_issues)

    if current_user:
        config_type = _detect_config_type(content, request.filename) if request.filename else "unknown"
        top_cats = [i.category for i in final_result.issues if i.category][:3]
        background_tasks.add_task(
            save_history,
            user_id=current_user["sub"],
            config_type=config_type,
            filename=request.filename,
            score=final_result.score,
            status=final_result.status,
            issue_count=len(final_result.issues),
            top_categories=list(dict.fromkeys(top_cats)),  # deduplicated, order-preserving
            provider=final_result.provider,
        )

    return final_result
