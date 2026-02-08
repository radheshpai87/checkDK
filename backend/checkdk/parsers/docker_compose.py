"""Docker Compose configuration parser."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from rich.console import Console

from ..models import DockerComposeConfig, Issue, IssueType, Severity

console = Console()


class DockerComposeParser:
    """Parse and validate Docker Compose files."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.config: Optional[DockerComposeConfig] = None
        self.issues: list[Issue] = []
    
    def parse(self) -> DockerComposeConfig:
        """Parse the Docker Compose file."""
        if not self.file_path.exists():
            self.issues.append(Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"Docker Compose file not found: {self.file_path}",
                file_path=str(self.file_path)
            ))
            return DockerComposeConfig()
        
        try:
            with open(self.file_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            if not isinstance(raw_config, dict):
                self.issues.append(Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message="Invalid Docker Compose file: root must be a dictionary",
                    file_path=str(self.file_path)
                ))
                return DockerComposeConfig()
            
            # Resolve environment variables
            resolved_config = self._resolve_env_vars(raw_config)
            
            # Extract components
            version = resolved_config.get('version')
            services = resolved_config.get('services', {})
            networks = resolved_config.get('networks', {})
            volumes = resolved_config.get('volumes', {})
            
            self.config = DockerComposeConfig(
                version=version,
                services=services,
                networks=networks,
                volumes=volumes,
                raw_config=resolved_config
            )
            
            # Validate structure
            self._validate_structure()
            
            return self.config
            
        except yaml.YAMLError as e:
            self.issues.append(Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"YAML parsing error: {str(e)}",
                file_path=str(self.file_path)
            ))
            return DockerComposeConfig()
        except Exception as e:
            self.issues.append(Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"Unexpected error parsing file: {str(e)}",
                file_path=str(self.file_path)
            ))
            return DockerComposeConfig()
    
    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in the configuration."""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Simple ${VAR} resolution
            if config.startswith('${') and config.endswith('}'):
                var_name = config[2:-1]
                default_value = None
                if ':-' in var_name:
                    var_name, default_value = var_name.split(':-', 1)
                
                value = os.getenv(var_name, default_value)
                if value is None:
                    self.issues.append(Issue(
                        type=IssueType.MISSING_ENV_VAR,
                        severity=Severity.WARNING,
                        message=f"Environment variable not set: {var_name}",
                        details={"variable": var_name}
                    ))
                return value or config
        return config
    
    def _validate_structure(self):
        """Validate the basic structure of the Docker Compose file."""
        if not self.config:
            return
        
        # Check if services are defined
        if not self.config.services:
            self.issues.append(Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message="No services defined in Docker Compose file",
                file_path=str(self.file_path)
            ))
            return
        
        # Validate each service
        for service_name, service_config in self.config.services.items():
            if not isinstance(service_config, dict):
                self.issues.append(Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message=f"Service '{service_name}' configuration must be a dictionary",
                    service_name=service_name,
                    file_path=str(self.file_path)
                ))
                continue
            
            # Check for image or build
            if 'image' not in service_config and 'build' not in service_config:
                self.issues.append(Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message=f"Service '{service_name}' must specify 'image' or 'build'",
                    service_name=service_name,
                    file_path=str(self.file_path)
                ))
    
    def get_services(self) -> Dict[str, Any]:
        """Get all services from the configuration."""
        return self.config.services if self.config else {}
    
    def get_ports(self, service_name: str) -> list[str]:
        """Get port mappings for a service."""
        if not self.config or service_name not in self.config.services:
            return []
        
        service = self.config.services[service_name]
        ports = service.get('ports', [])
        
        # Normalize port formats
        normalized_ports = []
        for port in ports:
            if isinstance(port, str):
                normalized_ports.append(port)
            elif isinstance(port, dict):
                # Handle long syntax
                target = port.get('target')
                published = port.get('published', target)
                if published:
                    normalized_ports.append(f"{published}:{target}")
        
        return normalized_ports
