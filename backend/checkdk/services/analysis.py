"""Core analysis services – Docker Compose and Kubernetes manifest validation.

These functions are the single source of truth for analysis logic used by
both the FastAPI routes and (optionally) other consumers.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Union

from ..models import AnalysisResult, Issue, IssueType, Severity, Fix
from ..parsers import DockerComposeParser
from ..validators import PortValidator
from ..config import get_config
from ..ai import get_ai_provider


# ── Docker Compose ────────────────────────────────────────────────────────────

def analyze_docker_compose(
    file_path: Union[str, Path],
    use_ai: bool = True,
) -> AnalysisResult:
    """Analyse a Docker Compose YAML file and return an AnalysisResult."""

    from ..validators.compose_validator import DockerComposeValidator

    parser = DockerComposeParser(str(file_path))
    config = parser.parse()

    all_issues = parser.issues.copy()

    # Rule-based validators
    for validator in [PortValidator()]:
        all_issues.extend(validator.validate(config))

    compose_dict = {
        "services": config.services,
        "volumes": config.volumes,
        "networks": config.networks,
    }
    all_issues.extend(DockerComposeValidator.validate_images(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_environment_variables(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_dependencies(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_volumes(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_networks(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_resource_limits(compose_dict))

    # AI provider (optional)
    ai_provider = None
    if use_ai:
        try:
            cfg = get_config()
            if cfg.ai.enabled:
                ai_provider = get_ai_provider(cfg)
        except Exception:
            pass

    fixes: list[Fix] = []
    for issue in all_issues:
        if issue.severity == Severity.CRITICAL and ai_provider:
            try:
                service_config = config.services.get(issue.service_name, {})
                if issue.type == IssueType.PORT_CONFLICT:
                    snippet = str(service_config.get("ports", []))
                elif issue.type == IssueType.SERVICE_DEPENDENCY:
                    snippet = str(service_config.get("depends_on", []))
                else:
                    snippet = str(service_config)[:500]

                ai_result = ai_provider.analyze_error(
                    error_message=issue.message,
                    config_snippet=snippet,
                    context={
                        "service_name": issue.service_name,
                        "issue_type": issue.type.value,
                        "platform": "docker-compose",
                    },
                )
                if "error" not in ai_result and ai_result.get("fix_steps"):
                    fixes.append(
                        Fix(
                            description=ai_result.get("explanation", "AI-generated fix"),
                            steps=ai_result.get("fix_steps", []),
                            auto_applicable=False,
                            explanation=ai_result.get("explanation", ""),
                            root_cause=ai_result.get("root_cause", ""),
                        )
                    )
                    continue
            except Exception:
                pass

        # Rule-based fallback
        if issue.type == IssueType.PORT_CONFLICT:
            fixes.append(PortValidator.generate_fix(issue))
        else:
            fixes.append(DockerComposeValidator.generate_fix(issue))

    return AnalysisResult(
        success=not any(i.severity == Severity.CRITICAL for i in all_issues),
        issues=all_issues,
        fixes=fixes,
    )


# ── Kubernetes ────────────────────────────────────────────────────────────────

def analyze_kubernetes(file_path: Union[str, Path]) -> AnalysisResult:
    """Analyse a Kubernetes manifest YAML file and return an AnalysisResult."""

    from ..parsers.kubernetes_parser import KubernetesParser
    from ..validators.k8s_validator import KubernetesValidator

    try:
        resources = KubernetesParser.parse(str(file_path))
        if not resources:
            return AnalysisResult(
                success=False,
                issues=[
                    Issue(
                        type=IssueType.INVALID_YAML,
                        severity=Severity.CRITICAL,
                        message="No valid Kubernetes resources found in file",
                        file_path=str(file_path),
                    )
                ],
            )

        all_issues: list[Issue] = []
        all_issues.extend(KubernetesValidator.validate_services(resources))
        all_issues.extend(KubernetesValidator.validate_deployments(resources))
        all_issues.extend(KubernetesValidator.validate_security(resources))
        all_issues.extend(KubernetesValidator.validate_probes(resources))
        all_issues.extend(KubernetesValidator.validate_labels(resources))

        ai_provider = None
        try:
            cfg = get_config()
            if cfg.ai.enabled:
                ai_provider = get_ai_provider(cfg)
        except Exception:
            pass

        fixes: list[Fix] = []
        for issue in all_issues:
            if issue.severity == Severity.CRITICAL and ai_provider:
                try:
                    if issue.type == IssueType.PORT_CONFLICT:
                        port = issue.details.get("port")
                        namespace = issue.details.get("namespace", "default")
                        snippet = f"""apiVersion: v1
kind: Service
metadata:
  name: {issue.service_name}
  namespace: {namespace}
spec:
  type: NodePort
  ports:
  - nodePort: {port}
    port: 8080
    targetPort: 80
"""
                    else:
                        snippet = f"Service: {issue.service_name}, Details: {issue.details}"

                    ai_result = ai_provider.analyze_error(
                        error_message=issue.message,
                        config_snippet=snippet,
                        context={
                            "service_name": issue.service_name,
                            "issue_type": issue.type.value,
                            "platform": "kubernetes",
                            "namespace": issue.details.get("namespace", "default"),
                        },
                    )
                    if "error" not in ai_result and ai_result.get("fix_steps"):
                        fixes.append(
                            Fix(
                                description=ai_result.get("explanation", "AI-generated fix"),
                                steps=ai_result.get("fix_steps", []),
                                auto_applicable=False,
                                explanation=ai_result.get("explanation", ""),
                                root_cause=ai_result.get("root_cause", ""),
                            )
                        )
                        continue
                except Exception:
                    pass

            fixes.append(KubernetesValidator.generate_fix(issue))

        return AnalysisResult(
            success=not any(i.severity == Severity.CRITICAL for i in all_issues),
            issues=all_issues,
            fixes=fixes,
        )

    except FileNotFoundError:
        return AnalysisResult(
            success=False,
            issues=[
                Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message=f"File not found: {file_path}",
                    file_path=str(file_path),
                )
            ],
        )
    except yaml.YAMLError as exc:
        return AnalysisResult(
            success=False,
            issues=[
                Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message=f"Invalid YAML: {exc}",
                    file_path=str(file_path),
                )
            ],
        )
    except Exception as exc:
        return AnalysisResult(
            success=False,
            issues=[
                Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message=f"Analysis failed: {exc}",
                    file_path=str(file_path),
                )
            ],
        )
