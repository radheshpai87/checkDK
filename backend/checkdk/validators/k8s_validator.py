"""Kubernetes configuration validator."""
from typing import List, Dict, Any
from ..models import Issue, IssueType, Severity, Fix


class KubernetesValidator:
    """Validates Kubernetes configurations."""
    
    @staticmethod
    def validate_security(resources: List[Dict[str, Any]]) -> List[Issue]:
        """Validate security configurations."""
        issues = []
        deployments = [r for r in resources if r.get('kind') in ['Deployment', 'Pod', 'StatefulSet', 'DaemonSet']]
        
        for resource in deployments:
            name = resource.get('metadata', {}).get('name', 'unknown')
            namespace = resource.get('metadata', {}).get('namespace', 'default')
            kind = resource.get('kind')
            
            # Get containers from appropriate location
            if kind == 'Pod':
                containers = resource.get('spec', {}).get('containers', [])
            else:
                containers = resource.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            
            for container in containers:
                container_name = container.get('name', 'unknown')
                security_context = container.get('securityContext', {})
                
                # Check for privileged containers
                if security_context.get('privileged'):
                    issues.append(Issue(
                        type=IssueType.SECURITY_ISSUE,
                        severity=Severity.CRITICAL,
                        message=f"{kind} '{name}' container '{container_name}' runs in privileged mode",
                        service_name=name,
                        details={
                            'container': container_name,
                            'namespace': namespace,
                            'reason': 'Privileged containers have access to all devices and can compromise security'
                        }
                    ))
                
                # Check for running as root
                if not security_context.get('runAsNonRoot'):
                    run_as_user = security_context.get('runAsUser')
                    if run_as_user is None or run_as_user == 0:
                        issues.append(Issue(
                            type=IssueType.SECURITY_ISSUE,
                            severity=Severity.WARNING,
                            message=f"{kind} '{name}' container '{container_name}' may run as root",
                            service_name=name,
                            details={
                                'container': container_name,
                                'namespace': namespace,
                                'reason': 'Running as root increases security risk'
                            }
                        ))
        
        return issues
    
    @staticmethod
    def validate_probes(resources: List[Dict[str, Any]]) -> List[Issue]:
        """Validate liveness and readiness probes."""
        issues = []
        deployments = [r for r in resources if r.get('kind') in ['Deployment', 'StatefulSet']]
        
        for deployment in deployments:
            name = deployment.get('metadata', {}).get('name', 'unknown')
            namespace = deployment.get('metadata', {}).get('namespace', 'default')
            containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
            
            for container in containers:
                container_name = container.get('name', 'unknown')
                
                # Check for liveness probe
                if 'livenessProbe' not in container:
                    issues.append(Issue(
                        type=IssueType.HEALTH_CHECK,
                        severity=Severity.WARNING,
                        message=f"Deployment '{name}' container '{container_name}' has no liveness probe",
                        service_name=name,
                        details={
                            'container': container_name,
                            'namespace': namespace,
                            'reason': 'Liveness probes help Kubernetes restart unhealthy containers'
                        }
                    ))
                
                # Check for readiness probe
                if 'readinessProbe' not in container:
                    issues.append(Issue(
                        type=IssueType.HEALTH_CHECK,
                        severity=Severity.WARNING,
                        message=f"Deployment '{name}' container '{container_name}' has no readiness probe",
                        service_name=name,
                        details={
                            'container': container_name,
                            'namespace': namespace,
                            'reason': 'Readiness probes ensure traffic only goes to ready pods'
                        }
                    ))
        
        return issues
    
    @staticmethod
    def validate_labels(resources: List[Dict[str, Any]]) -> List[Issue]:
        """Validate label selectors and matching."""
        issues = []
        
        for resource in resources:
            kind = resource.get('kind')
            if kind not in ['Deployment', 'StatefulSet', 'DaemonSet']:
                continue
            
            name = resource.get('metadata', {}).get('name', 'unknown')
            namespace = resource.get('metadata', {}).get('namespace', 'default')
            spec = resource.get('spec', {})
            
            # Get selector and template labels
            selector = spec.get('selector', {}).get('matchLabels', {})
            template_labels = spec.get('template', {}).get('metadata', {}).get('labels', {})
            
            # Check if selector matches template labels
            for key, value in selector.items():
                if key not in template_labels or template_labels[key] != value:
                    issues.append(Issue(
                        type=IssueType.LABEL_MISMATCH,
                        severity=Severity.CRITICAL,
                        message=f"{kind} '{name}' selector doesn't match pod template labels",
                        service_name=name,
                        details={
                            'namespace': namespace,
                            'selector': selector,
                            'template_labels': template_labels,
                            'reason': 'Mismatched labels will prevent the deployment from managing pods'
                        }
                    ))
                    break
        
        return issues
    
    @staticmethod
    def validate_services(resources: List[Dict[str, Any]]) -> List[Issue]:
        """Validate Kubernetes Services for common issues."""
        issues = []
        services = [r for r in resources if r.get('kind') == 'Service']
        
        # Check for NodePort conflicts
        nodeport_map = {}
        
        for service in services:
            name = service.get('metadata', {}).get('name', 'unknown')
            namespace = service.get('metadata', {}).get('namespace', 'default')
            spec = service.get('spec', {})
            
            # Check for NodePort conflicts
            if spec.get('type') == 'NodePort':
                for port_config in spec.get('ports', []):
                    node_port = port_config.get('nodePort')
                    if node_port:
                        key = f"{namespace}:{node_port}"
                        if key in nodeport_map:
                            issues.append(Issue(
                                type=IssueType.PORT_CONFLICT,
                                severity=Severity.CRITICAL,
                                message=f"NodePort {node_port} is used by multiple services: '{nodeport_map[key]}' and '{name}'",
                                service_name=name,
                                details={
                                    'port': node_port,
                                    'namespace': namespace,
                                    'conflicting_service': nodeport_map[key]
                                }
                            ))
                        else:
                            nodeport_map[key] = name
            
            # Check for port conflicts within service
            port_numbers = {}
            for port_config in spec.get('ports', []):
                port = port_config.get('port')
                protocol = port_config.get('protocol', 'TCP')
                key = f"{port}:{protocol}"
                
                if key in port_numbers:
                    issues.append(Issue(
                        type=IssueType.PORT_CONFLICT,
                        severity=Severity.CRITICAL,
                        message=f"Service '{name}' has duplicate port {port}/{protocol}",
                        service_name=name,
                        details={
                            'port': port,
                            'protocol': protocol,
                            'namespace': namespace
                        }
                    ))
                else:
                    port_numbers[key] = True
        
        return issues
    
    @staticmethod
    def validate_deployments(resources: List[Dict[str, Any]]) -> List[Issue]:
        """Validate Kubernetes Deployments."""
        issues = []
        deployments = [r for r in resources if r.get('kind') == 'Deployment']
        
        for deployment in deployments:
            name = deployment.get('metadata', {}).get('name', 'unknown')
            namespace = deployment.get('metadata', {}).get('namespace', 'default')
            spec = deployment.get('spec', {})
            template = spec.get('template', {})
            
            # Check for latest tag usage
            containers = template.get('spec', {}).get('containers', [])
            for container in containers:
                image = container.get('image', '')
                if image.endswith(':latest') or ':' not in image:
                    issues.append(Issue(
                        type=IssueType.IMAGE_VERSION,
                        severity=Severity.WARNING,
                        message=f"Deployment '{name}' uses 'latest' tag for container '{container.get('name')}'",
                        service_name=name,
                        details={
                            'container': container.get('name'),
                            'image': image,
                            'namespace': namespace,
                            'reason': 'Using :latest can lead to unpredictable deployments'
                        }
                    ))
            
            # Check for missing resource limits
            for container in containers:
                resources = container.get('resources', {})
                if not resources.get('limits'):
                    issues.append(Issue(
                        type=IssueType.RESOURCE_LIMITS,
                        severity=Severity.WARNING,
                        message=f"Deployment '{name}' container '{container.get('name')}' has no resource limits",
                        service_name=name,
                        details={
                            'container': container.get('name'),
                            'namespace': namespace,
                            'reason': 'Missing limits can cause resource exhaustion'
                        }
                    ))
        
        return issues
    
    @staticmethod
    def generate_fix(issue: Issue) -> Fix:
        """Generate fix for Kubernetes issues."""
        if issue.type == IssueType.PORT_CONFLICT:
            port = issue.details.get('port')
            namespace = issue.details.get('namespace', 'default')
            
            # Suggest new port
            new_port = port + 1
            
            return Fix(
                description=f"Fix NodePort {port} conflict in namespace '{namespace}'",
                steps=[
                    f"Option 1: Change one service's nodePort to {new_port}",
                    "  spec:",
                    "    ports:",
                    f"    - nodePort: {new_port}",
                    "",
                    "Option 2: Remove nodePort specification to let Kubernetes assign automatically",
                    "  spec:",
                    "    ports:",
                    "    - port: 8080",
                    "      targetPort: 80"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.IMAGE_VERSION:
            container = issue.details.get('container')
            image = issue.details.get('image', '')
            base_image = image.split(':')[0]
            
            return Fix(
                description=f"Pin specific version for {container}",
                steps=[
                    f"Replace 'latest' with specific version tag:",
                    "  containers:",
                    f"  - name: {container}",
                    f"    image: {base_image}:1.21.0  # Use specific version",
                    "",
                    "Check available versions at: https://hub.docker.com"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.RESOURCE_LIMITS:
            container = issue.details.get('container')
            
            return Fix(
                description=f"Add resource limits for {container}",
                steps=[
                    "Add resource limits to prevent resource exhaustion:",
                    "  containers:",
                    f"  - name: {container}",
                    "    resources:",
                    "      limits:",
                    "        memory: \"256Mi\"",
                    "        cpu: \"500m\"",
                    "      requests:",
                    "        memory: \"128Mi\"",
                    "        cpu: \"250m\""
                ],
                auto_applicable=False
            )
        
        return Fix(
            description="Manual review required",
            steps=["Review the configuration manually"],
            auto_applicable=False
        )
