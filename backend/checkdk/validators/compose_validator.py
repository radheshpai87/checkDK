"""Docker Compose configuration validator."""
import os
import re
from typing import List, Dict, Any
from ..models import Issue, IssueType, Severity, Fix


class DockerComposeValidator:
    """Comprehensive Docker Compose configuration validator."""
    
    @staticmethod
    def validate_images(config: Dict[str, Any]) -> List[Issue]:
        """Validate image specifications."""
        issues = []
        services = config.get('services', {})
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            # Check if image is specified
            if 'image' not in service_config and 'build' not in service_config:
                issues.append(Issue(
                    type=IssueType.MISSING_IMAGE,
                    severity=Severity.CRITICAL,
                    message=f"Service '{service_name}' has no image or build specification",
                    service_name=service_name,
                    details={'reason': 'Every service needs either an image or build directive'}
                ))
            
            # Check for latest tag usage
            image = service_config.get('image', '')
            if image:
                if image.endswith(':latest') or ':' not in image:
                    issues.append(Issue(
                        type=IssueType.IMAGE_VERSION,
                        severity=Severity.WARNING,
                        message=f"Service '{service_name}' uses 'latest' tag or no tag for image '{image}'",
                        service_name=service_name,
                        details={
                            'image': image,
                            'reason': 'Using :latest can lead to unpredictable deployments'
                        }
                    ))
        
        return issues
    
    @staticmethod
    def validate_environment_variables(config: Dict[str, Any]) -> List[Issue]:
        """Validate environment variable references."""
        issues = []
        services = config.get('services', {})
        
        # Pattern to match ${VAR_NAME} or $VAR_NAME
        env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)')
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            environment = service_config.get('environment', [])
            
            # Handle both list and dict format
            if isinstance(environment, list):
                env_entries = environment
            elif isinstance(environment, dict):
                env_entries = [f"{k}={v}" if v else k for k, v in environment.items()]
            else:
                continue
            
            for entry in env_entries:
                if not isinstance(entry, str):
                    continue
                
                # Find all env var references
                matches = env_var_pattern.findall(entry)
                for match in matches:
                    var_name = match[0] or match[1]
                    
                    # Check if the variable exists in the environment
                    if not os.getenv(var_name):
                        issues.append(Issue(
                            type=IssueType.MISSING_ENV_VAR,
                            severity=Severity.WARNING,
                            message=f"Service '{service_name}' references undefined environment variable '${{{var_name}}}'",
                            service_name=service_name,
                            details={
                                'variable': var_name,
                                'entry': entry
                            }
                        ))
        
        return issues
    
    @staticmethod
    def validate_dependencies(config: Dict[str, Any]) -> List[Issue]:
        """Validate service dependencies."""
        issues = []
        services = config.get('services', {})
        service_names = set(services.keys())
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            # Check depends_on
            depends_on = service_config.get('depends_on', [])
            if isinstance(depends_on, dict):
                depends_on = list(depends_on.keys())
            
            for dep in depends_on:
                if dep not in service_names:
                    issues.append(Issue(
                        type=IssueType.SERVICE_DEPENDENCY,
                        severity=Severity.CRITICAL,
                        message=f"Service '{service_name}' depends on non-existent service '{dep}'",
                        service_name=service_name,
                        details={
                            'missing_dependency': dep,
                            'available_services': list(service_names)
                        }
                    ))
            
            # Check links (deprecated but still used)
            links = service_config.get('links', [])
            for link in links:
                link_service = link.split(':')[0]
                if link_service not in service_names:
                    issues.append(Issue(
                        type=IssueType.SERVICE_DEPENDENCY,
                        severity=Severity.CRITICAL,
                        message=f"Service '{service_name}' links to non-existent service '{link_service}'",
                        service_name=service_name,
                        details={'missing_link': link_service}
                    ))
        
        return issues
    
    @staticmethod
    def validate_volumes(config: Dict[str, Any]) -> List[Issue]:
        """Validate volume configurations."""
        issues = []
        services = config.get('services', {})
        defined_volumes = set(config.get('volumes', {}).keys())
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            volumes = service_config.get('volumes', [])
            
            for volume in volumes:
                if not isinstance(volume, str):
                    continue
                
                # Named volume reference (e.g., "db_data:/var/lib/mysql")
                if ':' in volume:
                    source = volume.split(':')[0]
                    
                    # Check if it's a named volume (not a path)
                    if not source.startswith('/') and not source.startswith('./') and not source.startswith('~'):
                        if source not in defined_volumes:
                            issues.append(Issue(
                                type=IssueType.VOLUME_MOUNT,
                                severity=Severity.WARNING,
                                message=f"Service '{service_name}' uses undefined volume '{source}'",
                                service_name=service_name,
                                details={
                                    'volume': source,
                                    'defined_volumes': list(defined_volumes),
                                    'suggestion': 'Define the volume in the top-level volumes section'
                                }
                            ))
        
        return issues
    
    @staticmethod
    def validate_networks(config: Dict[str, Any]) -> List[Issue]:
        """Validate network configurations."""
        issues = []
        services = config.get('services', {})
        defined_networks = set(config.get('networks', {}).keys())
        
        # Add default network
        defined_networks.add('default')
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            networks = service_config.get('networks', [])
            
            # Handle both list and dict format
            if isinstance(networks, dict):
                networks = list(networks.keys())
            
            for network in networks:
                if network not in defined_networks:
                    issues.append(Issue(
                        type=IssueType.NETWORK_CONFIG,
                        severity=Severity.WARNING,
                        message=f"Service '{service_name}' uses undefined network '{network}'",
                        service_name=service_name,
                        details={
                            'network': network,
                            'defined_networks': list(defined_networks)
                        }
                    ))
        
        return issues
    
    @staticmethod
    def validate_resource_limits(config: Dict[str, Any]) -> List[Issue]:
        """Validate resource limit configurations."""
        issues = []
        services = config.get('services', {})
        
        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue
            
            deploy = service_config.get('deploy', {})
            resources = deploy.get('resources', {})
            limits = resources.get('limits', {})
            
            # Check if production-like services have resource limits
            # (services with restart policies or multiple replicas)
            restart = service_config.get('restart', '')
            replicas = deploy.get('replicas', 1)
            
            if (restart in ['always', 'unless-stopped'] or replicas > 1) and not limits:
                issues.append(Issue(
                    type=IssueType.RESOURCE_LIMIT,
                    severity=Severity.WARNING,
                    message=f"Production service '{service_name}' has no resource limits",
                    service_name=service_name,
                    details={
                        'reason': 'Services without limits can consume all available resources',
                        'restart': restart,
                        'replicas': replicas
                    }
                ))
        
        return issues
    
    @staticmethod
    def generate_fix(issue: Issue) -> Fix:
        """Generate fix suggestions for Docker Compose issues."""
        if issue.type == IssueType.MISSING_IMAGE:
            return Fix(
                description=f"Add image specification to service '{issue.service_name}'",
                steps=[
                    "Add an image directive to the service:",
                    "  services:",
                    f"    {issue.service_name}:",
                    "      image: nginx:1.21.0  # Use specific version",
                    "",
                    "OR specify a build context:",
                    "  services:",
                    f"    {issue.service_name}:",
                    "      build: ./path/to/dockerfile"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.IMAGE_VERSION:
            image = issue.details.get('image', '')
            base_image = image.split(':')[0] if ':' in image else image
            
            return Fix(
                description=f"Pin specific version for '{issue.service_name}'",
                steps=[
                    "Replace 'latest' with a specific version:",
                    "  services:",
                    f"    {issue.service_name}:",
                    f"      image: {base_image}:1.21.0  # Choose appropriate version",
                    "",
                    "Check available versions at hub.docker.com"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.MISSING_ENV_VAR:
            var_name = issue.details.get('variable', '')
            
            return Fix(
                description=f"Define environment variable '{var_name}'",
                steps=[
                    "Option 1: Create a .env file in the same directory:",
                    f"  {var_name}=your_value_here",
                    "",
                    "Option 2: Export in your shell:",
                    f"  export {var_name}=your_value_here",
                    "",
                    "Option 3: Use a default value in docker-compose.yml:",
                    "  environment:",
                    f"    - MY_VAR=${{{var_name}:-default_value}}"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.SERVICE_DEPENDENCY:
            missing_dep = issue.details.get('missing_dependency') or issue.details.get('missing_link')
            
            return Fix(
                description=f"Fix missing service dependency '{missing_dep}'",
                steps=[
                    f"Option 1: Remove the dependency on '{missing_dep}':",
                    "  depends_on:",
                    f"    # Remove '{missing_dep}'",
                    "",
                    f"Option 2: Add the '{missing_dep}' service:",
                    "  services:",
                    f"    {missing_dep}:",
                    "      image: appropriate/image:tag"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.VOLUME_MOUNT:
            volume = issue.details.get('volume', '')
            
            return Fix(
                description=f"Define volume '{volume}'",
                steps=[
                    "Add the volume to the top-level volumes section:",
                    "volumes:",
                    f"  {volume}:",
                    "    driver: local",
                    "",
                    "OR use a bind mount with absolute path:",
                    f"  volumes:",
                    f"    - /absolute/path/to/data:/container/path"
                ],
                auto_applicable=False
            )
        
        elif issue.type == IssueType.RESOURCE_LIMIT:
            return Fix(
                description=f"Add resource limits to '{issue.service_name}'",
                steps=[
                    "Add resource limits using deploy section:",
                    "  services:",
                    f"    {issue.service_name}:",
                    "      deploy:",
                    "        resources:",
                    "          limits:",
                    "            cpus: '0.5'",
                    "            memory: 512M",
                    "          reservations:",
                    "            cpus: '0.25'",
                    "            memory: 256M"
                ],
                auto_applicable=False
            )
        
        return Fix(
            description="Manual review required",
            steps=["Review the configuration manually"],
            auto_applicable=False
        )
