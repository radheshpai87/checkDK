"""Data models for checkDK."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueType(str, Enum):
    """Types of issues that can be detected."""
    PORT_CONFLICT = "port_conflict"
    MISSING_IMAGE = "missing_image"
    RESOURCE_LIMIT = "resource_limit"
    RESOURCE_LIMITS = "resource_limits"  # Alias for Kubernetes
    IMAGE_VERSION = "image_version"
    INVALID_YAML = "invalid_yaml"
    MISSING_ENV_VAR = "missing_env_var"
    VOLUME_MOUNT = "volume_mount"
    NETWORK_CONFIG = "network_config"
    SERVICE_DEPENDENCY = "service_dependency"
    SECURITY_ISSUE = "security_issue"
    HEALTH_CHECK = "health_check"
    LABEL_MISMATCH = "label_mismatch"


class Issue(BaseModel):
    """Represents a detected issue."""
    type: IssueType
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    service_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class Fix(BaseModel):
    """Represents a suggested fix."""
    description: str
    steps: List[str]
    code_snippet: Optional[str] = None
    auto_applicable: bool = False
    # AI-specific fields
    explanation: Optional[str] = None
    root_cause: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of configuration analysis."""
    success: bool
    issues: List[Issue] = Field(default_factory=list)
    fixes: List[Fix] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == Severity.CRITICAL for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(issue.severity == Severity.WARNING for issue in self.issues) or bool(self.warnings)


class DockerComposeConfig(BaseModel):
    """Parsed Docker Compose configuration."""
    version: Optional[str] = None
    services: Dict[str, Any] = Field(default_factory=dict)
    networks: Dict[str, Any] = Field(default_factory=dict)
    volumes: Dict[str, Any] = Field(default_factory=dict)
    raw_config: Dict[str, Any] = Field(default_factory=dict)


class CommandContext(BaseModel):
    """Context for a command execution."""
    original_command: str
    parsed_command: List[str]
    command_type: str  # 'docker', 'docker-compose', 'kubectl'
    config_files: List[str] = Field(default_factory=list)
    flags: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
