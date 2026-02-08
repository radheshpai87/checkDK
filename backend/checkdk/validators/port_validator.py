"""Port conflict validator."""

import socket
import psutil
from typing import List, Dict, Set
from ..models import Issue, IssueType, Severity, DockerComposeConfig, Fix
from .base import BaseValidator


class PortValidator(BaseValidator):
    """Validate port configurations and detect conflicts."""
    
    def validate(self, config: DockerComposeConfig) -> List[Issue]:
        """Validate port configurations."""
        self.clear_issues()
        
        # Track used ports across services
        used_ports: Dict[int, str] = {}
        
        for service_name, service_config in config.services.items():
            if not isinstance(service_config, dict):
                continue
            
            ports = service_config.get('ports', [])
            
            for port_mapping in ports:
                host_port = self._extract_host_port(port_mapping)
                
                if host_port is None:
                    continue
                
                # Check for duplicate ports across services
                if host_port in used_ports:
                    self.issues.append(Issue(
                        type=IssueType.PORT_CONFLICT,
                        severity=Severity.CRITICAL,
                        message=f"Port {host_port} is used by multiple services: '{used_ports[host_port]}' and '{service_name}'",
                        service_name=service_name,
                        details={
                            "port": host_port,
                            "conflicting_service": used_ports[host_port]
                        }
                    ))
                else:
                    used_ports[host_port] = service_name
                
                # Check if port is already in use on the system
                if self._is_port_in_use(host_port):
                    process_info = self._get_process_using_port(host_port)
                    message = f"Port {host_port} on service '{service_name}' is already in use"
                    
                    if process_info:
                        message += f" by {process_info['name']} (PID {process_info['pid']})"
                    
                    self.issues.append(Issue(
                        type=IssueType.PORT_CONFLICT,
                        severity=Severity.CRITICAL,
                        message=message,
                        service_name=service_name,
                        details={
                            "port": host_port,
                            "process": process_info
                        }
                    ))
        
        return self.issues
    
    def _extract_host_port(self, port_mapping) -> int | None:
        """Extract the host port from various port mapping formats."""
        if isinstance(port_mapping, int):
            return port_mapping
        
        if isinstance(port_mapping, str):
            # Format: "8080:80" or "8080"
            parts = port_mapping.split(':')
            try:
                return int(parts[0])
            except (ValueError, IndexError):
                return None
        
        if isinstance(port_mapping, dict):
            # Long syntax: {published: 8080, target: 80}
            published = port_mapping.get('published')
            if published:
                try:
                    return int(published)
                except ValueError:
                    return None
        
        return None
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False
    
    def _get_process_using_port(self, port: int) -> Dict[str, any] | None:
        """Get information about the process using a specific port."""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid)
                        return {
                            "pid": conn.pid,
                            "name": process.name(),
                            "cmdline": " ".join(process.cmdline()[:3])  # First 3 args
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return {"pid": conn.pid, "name": "unknown"}
        except Exception:
            pass
        return None
    
    @staticmethod
    def generate_fix(issue: Issue) -> Fix:
        """Generate a fix suggestion for a port conflict."""
        port = issue.details.get('port')
        process_info = issue.details.get('process')
        
        steps = []
        
        if process_info:
            steps.append(f"Option 1: Stop the process using port {port}")
            if process_info.get('name'):
                steps.append(f"  sudo kill {process_info['pid']}  # Stop {process_info['name']}")
        
        steps.append(f"Option 2: Change the port mapping in docker-compose.yml")
        steps.append(f"  ports:")
        steps.append(f"    - \"{port + 1}:80\"  # Change {port} to {port + 1}")
        
        return Fix(
            description=f"Fix port {port} conflict",
            steps=steps,
            auto_applicable=False
        )
